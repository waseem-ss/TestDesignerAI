"""Generate test cases for a CSV (or TXT/JSON) of inputs using a prompt template.

Examples:
  python -m backend.generate_tests --template requirement_test_cases --input data/requirements_test.csv
  python -m backend.generate_tests --template requirement_test_cases --input data/promise_dataset.csv --model qwen3:8b --limit 10

Each run writes to output/results/<YYYY-MM-DD_HH-MM-SS>/ unless --out-dir is given.
Results are appended to <template>__<input name>.jsonl as each row finishes, then written
to a .json array. To resume an interrupted run, pass its folder with --out-dir: rows
already saved are skipped. Rows that fail (bad input or a model error) are not saved, so a
re-run retries them. A lost connection to Ollama stops the run.
"""
import argparse
import sys
import time

from backend.prompt_engineering import TEMPLATES
from backend.llm_interface_v2 import resolve_provider
from backend.test_generation import make_generator, new_run_dir, run_generation


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate test cases from a dataset of inputs.")
    parser.add_argument("--template", required=True, help=f"one of: {', '.join(sorted(TEMPLATES))}")
    parser.add_argument("--input", required=True, help="CSV, TXT or JSON file with one input per row")
    parser.add_argument("--id-col", default=None, help="column holding the input id")
    parser.add_argument("--limit", type=int, default=None, help="only the first N rows")
    parser.add_argument("--provider", default="ollama",
                        help="ollama, groq, openai, claude, gemini or auto (default: ollama)")
    parser.add_argument("--model", default=None,
                        help="model for the provider (default: the model set in .env)")
    parser.add_argument("--out-dir", default=None,
                        help="folder to write results (default: a new output/results/<date_time> folder; "
                             "pass an existing run folder to resume it)")
    args = parser.parse_args()

    out_dir = args.out_dir or new_run_dir()
    last_print = [0.0]

    def on_progress(p):
        if time.time() - last_print[0] >= 1 or p["done"] + p["failed"] == p["total"]:
            last_print[0] = time.time()
            print(f"  {p['done'] + p['failed']}/{p['total']} (saved {p['done']}, failed {p['failed']})", flush=True)

    try:
        provider = resolve_provider(args.provider.lower())  # "auto" -> a concrete provider
        summary = run_generation(
            args.input, args.template, out_dir,
            generator=make_generator(args.template, provider, args.model),
            limit=args.limit, id_col=args.id_col, model=args.model, provider=provider,
            on_progress=on_progress,
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}")
        return 2

    if summary["stopped"]:
        print(f"\nStopped: {summary['stopped']}")
        print("Start Ollama and re-run with --out-dir set to this folder to resume.")
    print(f"Template: {summary['template']}; model: {summary['model']}; rows: {summary['rows']}")
    print(f"This run: {summary['this_run']}")
    print(f"Saved: {summary['saved']} / {summary['rows']}")
    print(f"JSONL: {summary['jsonl_path']}\nJSON:  {summary['json_path']}")
    return 1 if summary["stopped"] else 0


if __name__ == "__main__":
    sys.exit(main())
