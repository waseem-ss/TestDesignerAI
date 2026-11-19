"""Single-requirement tasks for the Process tab: run one requirement through one provider.

Each task has its own prompt. The model is asked for JSON; if the reply is not valid JSON,
the raw text is returned instead so nothing is lost.
"""
import json
import re
from typing import Any, Dict, Optional, Tuple

from backend.llm_interface_v2 import call_provider, resolve_provider
from backend.prompt_engineering import get_template
from backend.pipeline import parse_test_cases

TASKS = ("extraction", "classification", "ner", "question_answering", "test_generation")

_TASK_INSTRUCTIONS = {
    "extraction": (
        "Extract the key elements of the requirement: actors, systems, data, actions and constraints. "
        'Return JSON only: {"entities": [{"text": "...", "role": "..."}]}'
    ),
    "classification": (
        "Classify the requirement as functional or non-functional, and give your confidence from 0 to 1. "
        'Return JSON only: {"classification": "functional" or "non-functional", "confidence": 0.0}'
    ),
    "ner": (
        "Find the named entities in the requirement and give each one a type. "
        'Return JSON only: {"entities": [{"text": "...", "type": "..."}]}'
    ),
    "question_answering": (
        "Write the questions a tester must be able to answer to confirm this requirement is met. "
        'Return JSON only: {"questions": ["...", "..."]}'
    ),
}

_MAX_TOKENS = {"extraction": 512, "classification": 256, "ner": 512, "question_answering": 512}


def _parse_json(text: str) -> Optional[Dict[str, Any]]:
    """Parse a JSON object from a model reply, allowing a Markdown code fence around it."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            return None
        try:
            value = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return value if isinstance(value, dict) else None


def run_task(task: str, requirement_id: str, text: str, provider: str,
             model: Optional[str] = None) -> Tuple[Dict[str, Any], int, str]:
    """Run one task. Returns (result, tokens_used, provider_used)."""
    if task not in TASKS:
        raise ValueError(f"Unknown task {task!r}; use one of {', '.join(TASKS)}")
    provider_used = resolve_provider(provider.lower())

    if task == "test_generation":
        template = get_template("requirement_test_cases")
        prompt = template.build_prompt({"requirement_text": text})
        raw, tokens = call_provider(provider_used, prompt, model=model,
                                    max_tokens=max(template.max_tokens, 2048), temperature=0.7)
        cases = parse_test_cases(raw)
        if not cases:
            raise RuntimeError("the model returned no test cases")
        return {"task": task, "requirement_id": requirement_id, "test_cases": cases}, tokens, provider_used

    prompt = (
        f"{_TASK_INSTRUCTIONS[task]}\n\n"
        f"Requirement {requirement_id}: {text}"
    )
    raw, tokens = call_provider(provider_used, prompt, model=model,
                                max_tokens=_MAX_TOKENS[task], temperature=0.2)
    parsed = _parse_json(raw)
    if parsed is None:
        return {"task": task, "requirement_id": requirement_id, "raw_text": raw.strip()}, tokens, provider_used
    return {"task": task, "requirement_id": requirement_id, **parsed}, tokens, provider_used
