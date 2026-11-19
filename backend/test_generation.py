"""Dataset-level test case generation, shared by the CLI (generate_tests.py) and the API.

Inputs: CSV, TXT (comma-separated) or JSON (list of records) files. The loader finds the
id and requirement-text columns by name, and creates row ids when the file has none.

Results go to <out_dir>/<template>__<input name>.jsonl as each row finishes, then to a
.json array and a _meta.json file. Re-running into the same out_dir skips saved rows.
"""
import json
import os
import threading
import time
import uuid
from collections import Counter
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

from backend.config import AppConfig, ModelType
from backend.llm_interface import list_ollama_models, OLLAMA_URL
from backend.llm_interface_v2 import (
    PROVIDER_KEY_ENV, call_provider, default_model, provider_key_configured, resolve_provider,
)
from backend.logger import get_logger
from backend.prompt_engineering import TEMPLATES, get_template

logger = get_logger(__name__)

DATA_DIR = AppConfig.DATA_DIR
RESULTS_DIR = os.path.join(AppConfig.OUTPUT_DIR, "results")
DATA_SUFFIXES = (".csv", ".txt", ".json")
ID_CANDIDATES = ("requirement_id", "bug_id", "Bug ID", "id")
BUG_SUMMARY_COLUMN = "Short Description"  # bug-report datasets (e.g. Filtered_bugs.csv)
TEXT_CANDIDATES = ("requirement_text", "requirement", "Requirement", "text")


# ---------------------------------------------------------------------------
# Loading inputs
# ---------------------------------------------------------------------------

def _read_table(path: str, ext: str) -> pd.DataFrame:
    if ext == ".json":
        return pd.read_json(path)
    try:
        return pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:  # exports from Windows tools are often cp1252
        return pd.read_csv(path, encoding="cp1252")


def load_input(path: str, id_col: Optional[str] = None) -> Tuple[pd.DataFrame, str, str]:
    """Read one input file. Returns (dataframe, id column, text column).

    Requirement files get a 'requirement_text' column. Bug-report files (with a
    'Short Description' column) get 'title', 'description' and 'severity' columns, which
    the bug_test_cases template reads.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".csv", ".txt", ".json"):
        raise ValueError(f"Unsupported input type {ext!r}; use one of {', '.join(DATA_SUFFIXES)}")
    df = _read_table(path, ext)

    is_bugs = BUG_SUMMARY_COLUMN in df.columns
    if is_bugs:
        df["title"] = df[BUG_SUMMARY_COLUMN].astype(str)
        df["severity"] = df["Severity Label"].astype(str) if "Severity Label" in df.columns else ""
        project = df["Project"].astype(str) if "Project" in df.columns else "the product"
        status = df["Resolution Status"].astype(str) if "Resolution Status" in df.columns else "unknown"
        df["description"] = "Bug reported in " + project + ", resolution: " + status
        text_col = BUG_SUMMARY_COLUMN
    else:
        text_col = next((c for c in TEXT_CANDIDATES if c in df.columns), None)
        if text_col is None:
            raise ValueError(f"No requirement text column found; expected one of {TEXT_CANDIDATES}")
        if "requirement_text" not in df.columns:
            df["requirement_text"] = df[text_col]

    if id_col:
        if id_col not in df.columns:
            raise ValueError(f"id column {id_col!r} is not in the input")
    else:
        id_col = next((c for c in ID_CANDIDATES if c in df.columns), None)
    if id_col is None:
        df.insert(0, "row_id", [f"ROW_{i + 1:04d}" for i in range(len(df))])
        id_col = "row_id"

    # Some datasets have one row per entity, so an id can repeat. Keep the first.
    df = df.drop_duplicates(subset=[id_col], keep="first").reset_index(drop=True)
    return df, id_col, text_col


def row_to_record(row: pd.Series) -> Dict[str, str]:
    return {k: ("" if pd.isna(v) else str(v)) for k, v in row.items()}


def resolve_dataset(file_name: str) -> str:
    """Path of a dataset file under data/. Rejects names that point outside data/."""
    if os.path.basename(file_name) != file_name:
        raise ValueError("dataset must be a file name under data/")
    path = os.path.join(DATA_DIR, file_name)
    if not os.path.isfile(path) or os.path.splitext(file_name)[1].lower() not in DATA_SUFFIXES:
        raise ValueError(f"No dataset named {file_name!r} under data/")
    return path


def list_datasets() -> List[Dict[str, Any]]:
    """Every usable file under data/, with its row count and detected columns."""
    datasets = []
    for name in sorted(os.listdir(DATA_DIR)):
        if os.path.splitext(name)[1].lower() not in DATA_SUFFIXES:
            continue
        info: Dict[str, Any] = {"file": name, "format": os.path.splitext(name)[1].lower().lstrip(".")}
        try:
            df, id_col, text_col = load_input(os.path.join(DATA_DIR, name))
            is_bugs = "title" in df.columns
            info.update(rows=len(df), id_column=id_col, text_column=text_col,
                        type="bugs" if is_bugs else "requirements",
                        columns=[c for c in df.columns if c not in ("requirement_text", "title", "description", "severity")])
        except Exception as e:  # unreadable file: list it, with the reason
            info.update(rows=None, error=str(e))
        datasets.append(info)
    return datasets


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def check_template_fields(template_name: str, columns: List[str]) -> None:
    """Fail early if the dataset lacks the input fields the template needs."""
    template = get_template(template_name)
    if "requirement_text" in template.fields and "requirement_text" not in columns:
        raise ValueError(f"Template {template_name!r} needs a requirement text column; "
                         f"this dataset has {', '.join(columns)}")
    if "title" in template.fields and not any(f in columns for f in ("title", "description")):
        raise ValueError(f"Template {template_name!r} needs a bug title or description; "
                         f"this dataset has {', '.join(columns)}")


def make_generator(template_name: str, provider: str = "ollama",
                   model: Optional[str] = None) -> Callable[[Dict[str, str]], List[str]]:
    """Return a function that turns one input record into a list of test cases.

    provider: "ollama", "groq", "openai", "claude" or "gemini" (see llm_interface_v2).
    model: the model name for that provider; None uses the .env default.
    Ollama with no model keeps the original pipeline path, which uses OLLAMA_MODEL.
    """
    template = get_template(template_name)
    if provider == "ollama" and model is None:
        from backend.pipeline import REPipeline  # heavy import: only when needed
        pipeline = REPipeline()

        def generate_default(record: Dict[str, str]) -> List[str]:
            cases = pipeline.generate_test_cases(record, template=template.name, provider="ollama")
            if not cases:
                # Same rule as the explicit-model path: an empty reply fails the row.
                raise RuntimeError("the model returned no test cases")
            return cases

        return generate_default

    from backend.pipeline import parse_test_cases
    temperature = AppConfig.get_model_config(ModelType.GPT_4O).temperature

    # Reasoning models on cloud providers spend output tokens on hidden reasoning, so they get a
    # larger budget than the template's default. Ollama keeps the template's value.
    max_tokens = template.max_tokens if provider == "ollama" else max(template.max_tokens, 2048)

    def generate(record: Dict[str, str]) -> List[str]:
        text, _ = call_provider(provider, template.build_prompt(record), model=model,
                                max_tokens=max_tokens, temperature=temperature)
        cases = parse_test_cases(text) if text.strip() else []
        if not cases:
            # Fail the row instead of saving an empty result, so a re-run retries it.
            raise RuntimeError("the model returned no test cases")
        return cases

    return generate


def run_generation(input_path: str, template_name: str, out_dir: str,
                   generator: Callable[[Dict[str, str]], List[str]],
                   limit: Optional[int] = None, id_col: Optional[str] = None,
                   model: Optional[str] = None, provider: str = "ollama",
                   on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
                   should_stop: Optional[Callable[[], bool]] = None) -> Dict[str, Any]:
    """Generate test cases for every row of input_path. Returns a summary dict."""
    template = get_template(template_name)
    df, id_col, _ = load_input(input_path, id_col)
    check_template_fields(template_name, list(df.columns))
    if limit:
        df = df.head(limit)

    os.makedirs(out_dir, exist_ok=True)
    stem = f"{template.name}__{os.path.splitext(os.path.basename(input_path))[0]}"
    jsonl_path = os.path.join(out_dir, f"{stem}.jsonl")
    json_path = os.path.join(out_dir, f"{stem}.json")
    meta_path = os.path.join(out_dir, f"{stem}_meta.json")

    done = load_done_ids(jsonl_path)
    todo = df[~df[id_col].astype(str).isin(done)]
    used_model = model or default_model(provider)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "template": template.name, "input": os.path.abspath(input_path),
            "provider": provider, "model": used_model,
            "ollama_url": OLLAMA_URL if provider == "ollama" else None,
            "rows": len(df), "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, f, indent=2)

    progress = {"total": len(todo), "done": 0, "failed": 0, "skipped": len(df) - len(todo)}
    statuses = Counter()
    stopped_early = None
    report = lambda: on_progress and on_progress(dict(progress))

    report()
    with open(jsonl_path, "a", encoding="utf-8") as out:
        for _, row in todo.iterrows():
            if should_stop and should_stop():
                stopped_early = "stopped by user"
                break
            input_id = str(row[id_col])
            record = row_to_record(row)
            try:
                cases = generator(record)
            except ConnectionError as e:
                stopped_early = str(e)
                break
            except Exception as e:  # bad row or model error: skip, re-run later
                statuses["failed"] += 1
                progress["failed"] += 1
                logger.warning(f"{input_id}: failed ({e})")
                report()
                continue
            entry = {"input_id": input_id, "template": template.name, "input": record, "test_cases": cases}
            out.write(json.dumps(entry, ensure_ascii=False) + "\n")
            out.flush()
            os.fsync(out.fileno())
            statuses["completed"] += 1
            progress["done"] += 1
            report()

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

    return {
        "template": template.name, "model": used_model, "out_dir": out_dir,
        "json_path": json_path, "jsonl_path": jsonl_path,
        "this_run": dict(statuses), "saved": len(records), "rows": len(df),
        "stopped": stopped_early,
    }


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


def new_run_dir() -> str:
    return os.path.join(RESULTS_DIR, time.strftime("%Y-%m-%d_%H-%M-%S"))


# ---------------------------------------------------------------------------
# Background jobs (used by the API)
# ---------------------------------------------------------------------------

_JOBS: Dict[str, Dict[str, Any]] = {}
_JOBS_LOCK = threading.Lock()


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
        return dict(job) if job else None


def start_job(file_name: str, template_name: str, provider: str, model: Optional[str],
              limit: Optional[int]) -> Dict[str, Any]:
    """Validate the request, then run generation in a background thread.

    provider: "ollama", "groq", "openai", "claude", "gemini" or "auto" (first usable one).
    """
    path = resolve_dataset(file_name)
    if template_name not in TEMPLATES:
        raise ValueError(f"Unknown template {template_name!r}")
    provider = resolve_provider(provider.lower())  # "auto" -> a concrete provider
    if provider == "ollama":
        if model is not None:
            available = list_ollama_models()  # raises ConnectionError if Ollama is down
            if model not in available:
                raise ValueError(f"Model {model!r} is not installed in Ollama")
    elif provider not in PROVIDER_KEY_ENV:
        raise ValueError(f"Unknown provider {provider!r}")
    elif not provider_key_configured(provider):
        raise ValueError(f"{PROVIDER_KEY_ENV[provider]} is not set in .env")
    df, _, _ = load_input(path)
    check_template_fields(template_name, list(df.columns))

    job_id = uuid.uuid4().hex[:12]
    job = {
        "job_id": job_id, "dataset": file_name, "template": template_name,
        "provider": provider, "model": model,
        "limit": limit, "status": "running", "total": 0, "done": 0, "failed": 0, "skipped": 0,
        "out_dir": None, "error": None, "summary": None,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "finished_at": None,
    }
    with _JOBS_LOCK:
        _JOBS[job_id] = job

    def worker():
        def on_progress(p):
            with _JOBS_LOCK:
                job.update(p)

        try:
            generator = make_generator(template_name, provider, model)
            out_dir = new_run_dir()
            with _JOBS_LOCK:
                job["out_dir"] = out_dir
            summary = run_generation(
                path, template_name, out_dir, generator, limit=limit, model=model, provider=provider,
                on_progress=on_progress,
                should_stop=lambda: job.get("status") == "stopping",
            )
            with _JOBS_LOCK:
                job["summary"] = summary
                job["status"] = "stopped" if summary["stopped"] else "completed"
                if summary["stopped"] and summary["stopped"] != "stopped by user":
                    job["error"] = summary["stopped"]
        except Exception as e:
            logger.exception("test generation job failed")
            with _JOBS_LOCK:
                job["status"] = "failed"
                job["error"] = str(e)
        finally:
            with _JOBS_LOCK:
                job["finished_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    threading.Thread(target=worker, daemon=True).start()
    return dict(job)


def request_stop(job_id: str) -> Optional[Dict[str, Any]]:
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
        if job and job["status"] == "running":
            job["status"] = "stopping"
        return dict(job) if job else None
