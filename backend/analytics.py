"""Statistics over saved test-generation runs under output/results.

Each run folder holds a *_meta.json (template, provider, model, rows, started_at) and a
.jsonl with one line per generated row. This module reads those files and summarises them
for the Analytics tab. Runs that cannot be read are skipped and listed under "skipped".
"""
import glob
import json
import os
from collections import defaultdict
from typing import Any, Dict, List

from backend.test_generation import RESULTS_DIR


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as f:
            value = json.load(f)
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _summarise_run(folder: str) -> Dict[str, Any]:
    """Summarise one run folder. Raises ValueError when it has no generation output."""
    jsonl_files = sorted(glob.glob(os.path.join(folder, "*.jsonl")))
    if not jsonl_files:
        raise ValueError("no .jsonl output")
    jsonl_path = jsonl_files[0]
    meta_files = sorted(glob.glob(os.path.join(folder, "*_meta.json")))
    meta = _read_json(meta_files[0]) if meta_files else {}

    rows_saved = 0
    counts: List[int] = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            cases = entry.get("test_cases") or []
            rows_saved += 1
            counts.append(len(cases))

    stem = os.path.basename(jsonl_path)[: -len(".jsonl")]
    template = meta.get("template") or (stem.split("__")[0] if "__" in stem else "unknown")
    dataset = os.path.splitext(os.path.basename(meta.get("input") or jsonl_path))[0]
    if dataset.endswith("_meta"):
        dataset = dataset[: -len("_meta")]
    return {
        "run": os.path.basename(folder),
        "started_at": meta.get("started_at") or os.path.basename(folder).replace("_", " "),
        "template": template,
        "dataset": dataset,
        "provider": meta.get("provider") or "unknown",
        "model": meta.get("model") or "unknown",
        "rows_planned": int(meta.get("rows") or rows_saved),
        "rows_saved": rows_saved,
        "test_cases": sum(counts),
        "avg_cases_per_row": round(sum(counts) / rows_saved, 2) if rows_saved else 0.0,
        "min_cases_per_row": min(counts) if counts else 0,
        "max_cases_per_row": max(counts) if counts else 0,
    }


def collect_run_stats(results_dir: str = RESULTS_DIR) -> Dict[str, Any]:
    """Return every readable run plus totals and per-provider / per-template breakdowns."""
    runs: List[Dict[str, Any]] = []
    skipped: List[str] = []
    if os.path.isdir(results_dir):
        for name in sorted(os.listdir(results_dir)):
            folder = os.path.join(results_dir, name)
            if not os.path.isdir(folder):
                continue
            try:
                runs.append(_summarise_run(folder))
            except (ValueError, OSError) as e:
                skipped.append(f"{name}: {e}")

    runs.sort(key=lambda r: r["started_at"], reverse=True)

    total_rows = sum(r["rows_saved"] for r in runs)
    total_cases = sum(r["test_cases"] for r in runs)
    totals = {
        "runs": len(runs),
        "rows_generated": total_rows,
        "test_cases": total_cases,
        "avg_cases_per_row": round(total_cases / total_rows, 2) if total_rows else 0.0,
        "datasets": len({r["dataset"] for r in runs}),
    }

    def breakdown(key: str) -> List[Dict[str, Any]]:
        groups: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"runs": 0, "rows_generated": 0, "test_cases": 0})
        for r in runs:
            g = groups[r[key]]
            g["runs"] += 1
            g["rows_generated"] += r["rows_saved"]
            g["test_cases"] += r["test_cases"]
        out = []
        for name, g in sorted(groups.items(), key=lambda kv: -kv[1]["test_cases"]):
            out.append({key: name, **g,
                        "avg_cases_per_row": round(g["test_cases"] / g["rows_generated"], 2)
                        if g["rows_generated"] else 0.0})
        return out

    return {
        "totals": totals,
        "by_provider": breakdown("provider"),
        "by_model": breakdown("model"),
        "by_template": breakdown("template"),
        "runs": runs,
        "skipped": skipped,
    }
