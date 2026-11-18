"""Generate test cases for a CSV of inputs using a prompt template.

Examples:
  python generate_tests.py --template requirement_test_cases --input data/requirements_test.csv
  python generate_tests.py --template bug_test_cases --input data/reported_bugs.csv --limit 10

Each run writes to its own folder, output/results/<YYYY-MM-DD_HH-MM-SS>/ (the start time).
Each result is appended to <template>__<input name>.jsonl as soon as it finishes. To resume
an interrupted run, re-run with --out-dir pointing at that run's folder: rows already saved
are skipped. When the run ends, the saved rows are also written to a .json array next to the .jsonl file.

Id column: the first of requirement_id, bug_id or id present in the CSV, unless --id-col is given.
Rows that fail (bad input or a model error) are not saved, so a re-run retries them.
A lost connection to Ollama stops the run, so it does not fail row by row.
"""
import argparse
import json
import os
import sys
import time
from collections import Counter

import pandas as pd

from llm_interface import LLM_PROVIDER, OLLAMA_MODEL, OLLAMA_URL
from pipeline import REPipeline
from prompt_engineering import get_template, TEMPLATES

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "output", "results")
ID_CANDIDATES = ("requirement_id", "bug_id", "id")


def pick_id_column(df: pd.DataFrame, requested: str | None) -> str:
    if requested:
        if requested not in df.columns:
            raise SystemExit(f"--id-col {requested!r} is not a column in the input")
        return requested
    for name in ID_CANDIDATES:
        if name in df.columns:
            return name
    raise SystemExit(f"No id column found; expected one of {ID_CANDIDATES} or pass --id-col")


def load_done_ids(path: str) -> set:
    if not os.path.exists(path):
        return set()
    done = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    done.add(str(json.loads(line)["input_id"]))
                except (json.JSONDecodeError, KeyError):
                    continue  # partial line from an interrupted write: re-run it
    return done


def row_to_record(row: pd.Series) -> dict:
    return {k: ("" if pd.isna(v) else str(v)) for k, v in row.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate test cases from a CSV of inputs.")
    parser.add_argument("--template", required=True, help=f"one of: {', '.join(sorted(TEMPLATES))}")
    parser.add_argument("--input", required=True, help="CSV file with one input per row")
    parser.add_argument("--id-col", default=None, help="column holding the input id")
    parser.add_argument("--limit", type=int, default=None, help="only the first N rows")
    parser.add_argument("--out-dir", default=None,
                        help="folder to write results (default: a new output/results/<date_time> folder; "
                             "pass an existing run folder to resume it)")
    args = parser.parse_args()
    if args.out_dir is None:
        args.out_dir = os.path.join(RESULTS_DIR, time.strftime("%Y-%m-%d_%H-%M-%S"))

    template = get_template(args.template)  # validates the name early
    df = pd.read_csv(args.input)
    if args.limit is not None:
        df = df.head(args.limit)
    id_col = pick_id_column(df, args.id_col)

    os.makedirs(args.out_dir, exist_ok=True)
    stem = f"{template.name}__{os.path.splitext(os.path.basename(args.input))[0]}"
    jsonl_path = os.path.join(args.out_dir, f"{stem}.jsonl")
    json_path = os.path.join(args.out_dir, f"{stem}.json")
    meta_path = os.path.join(args.out_dir, f"{stem}_meta.json")

    done = load_done_ids(jsonl_path)
    todo = df[~df[id_col].astype(str).isin(done)]
    print(f"Template: {template.name}; input rows: {len(df)}; already saved: {len(done)}; to run: {len(todo)}")
    print(f"Provider: {LLM_PROVIDER}, model: {OLLAMA_MODEL if LLM_PROVIDER == 'ollama' else None}")

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "template": template.name,
            "input": os.path.abspath(args.input),
            "provider": LLM_PROVIDER,
            "model": OLLAMA_MODEL if LLM_PROVIDER == "ollama" else None,
            "ollama_url": OLLAMA_URL if LLM_PROVIDER == "ollama" else None,
            "rows": len(df),
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, f, indent=2)

    pipeline = REPipeline()
    statuses = Counter()
    stopped_early = None
    with open(jsonl_path, "a", encoding="utf-8") as out:
        for i, (_, row) in enumerate(todo.iterrows(), start=1):
            input_id = str(row[id_col])
            record = row_to_record(row)
            try:
                cases = pipeline.generate_test_cases(record, template=template.name)
            except ConnectionError as e:
                stopped_early = str(e)
                break
            except Exception as e:  # bad row or model error: skip, re-run later
                statuses["failed"] += 1
                print(f"[{i}/{len(todo)}] {input_id}: failed ({e})", flush=True)
                continue
            entry = {
                "input_id": input_id,
                "template": template.name,
                "input": record,
                "test_cases": cases,
            }
            out.write(json.dumps(entry, ensure_ascii=False) + "\n")
            out.flush()
            os.fsync(out.fileno())
            statuses["completed"] += 1
            print(f"[{i}/{len(todo)}] {input_id}: completed ({len(cases)} test cases)", flush=True)

    records = []
    if os.path.exists(jsonl_path):
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    if stopped_early:
        print(f"\nStopped: {stopped_early}")
        print("Start Ollama and re-run the same command to resume.")
    print(f"This run: {dict(statuses)}")
    print(f"Saved: {len(records)} / {len(df)}")
    print(f"JSONL: {jsonl_path}\nJSON:  {json_path}")
    return 1 if stopped_early else 0


if __name__ == "__main__":
    sys.exit(main())
