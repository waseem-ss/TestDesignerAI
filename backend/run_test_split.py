"""Run REPipeline over data/requirements_test.csv.

Each requirement's result is appended to output/test_split_results.jsonl as soon
as it finishes, so a stopped run loses nothing. Re-running resumes: requirements
already in the .jsonl file are skipped. When all requirements are done, the
.jsonl file is also written out as a JSON array to output/test_split_results.json.

The LLM backend comes from LLM_PROVIDER / OLLAMA_MODEL in .env (default: local Ollama).
"""
import argparse
import json
import os
import sys
import time
from collections import Counter

import pandas as pd

from backend.pipeline import REPipeline
from backend.llm_interface import LLM_PROVIDER, OLLAMA_MODEL, OLLAMA_URL

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_PATH = os.path.join(BASE_DIR, "data", "requirements_test.csv")
OUT_DIR = os.path.join(BASE_DIR, "output", "results")
JSONL_PATH = os.path.join(OUT_DIR, "test_split_results.jsonl")
JSON_PATH = os.path.join(OUT_DIR, "test_split_results.json")
META_PATH = os.path.join(OUT_DIR, "test_split_run_meta.json")


def load_done_ids() -> set:
    """IDs already saved in the .jsonl file (empty if none)."""
    if not os.path.exists(JSONL_PATH):
        return set()
    done = set()
    with open(JSONL_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                done.add(json.loads(line)["requirement_id"])
            except (json.JSONDecodeError, KeyError):
                # A partial last line from an interrupted write is ignored and re-run.
                continue
    return done


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate test cases for the test split.")
    parser.add_argument("--limit", type=int, default=None,
                        help="only process the first N requirements of the test split")
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    df = pd.read_csv(TEST_PATH)
    if args.limit is not None:
        df = df.head(args.limit)
    done = load_done_ids()
    todo = df[~df["requirement_id"].isin(done)]
    print(f"Test requirements: {len(df)}; already saved: {len(done)}; to run: {len(todo)}")
    print(f"Provider: {LLM_PROVIDER}, model: {OLLAMA_MODEL if LLM_PROVIDER == 'ollama' else None}")

    meta = {
        "provider": LLM_PROVIDER,
        "model": OLLAMA_MODEL if LLM_PROVIDER == "ollama" else None,
        "ollama_url": OLLAMA_URL if LLM_PROVIDER == "ollama" else None,
        "input": TEST_PATH,
        "requirements": len(df),
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    pipeline = REPipeline()
    statuses = Counter()
    with open(JSONL_PATH, "a", encoding="utf-8") as out:
        for i, (_, row) in enumerate(todo.iterrows(), start=1):
            result = pipeline.process_requirement(row["requirement_id"], row["requirement_text"])
            out.write(json.dumps(result.to_dict(), ensure_ascii=False, default=str) + "\n")
            out.flush()
            os.fsync(out.fileno())
            statuses[result.status.value] += 1
            print(f"[{i}/{len(todo)}] {row['requirement_id']}: {result.status.value} "
                  f"({len(result.test_cases)} test cases)", flush=True)

    # Build the JSON array from everything saved so far (including earlier resumed runs).
    records = []
    with open(JSONL_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"\nThis run: {dict(statuses)}")
    print(f"Saved requirements: {len(records)} / {len(df)}")
    print(f"JSONL: {JSONL_PATH}\nJSON:  {JSON_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
