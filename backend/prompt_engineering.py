"""
Prompt engineering layer for TestDesignerAI.

Each PromptTemplate turns one kind of input record into a test-generation prompt.
Templates share one output contract (a numbered list, one test case per line) so
the same parser works for every input type.

Available templates:
  requirement_test_cases  input: a software requirement (requirement_text)
  bug_test_cases          input: a reported bug (title, description, steps_to_reproduce,
                          expected_result, actual_result, severity; any may be blank)

Add a template by creating a PromptTemplate and registering it in TEMPLATES.
"""

from dataclasses import dataclass
from typing import Dict, Mapping, Tuple

OUTPUT_CONTRACT = (
    "Output format: a numbered list with one test case per line. Each line must contain "
    "'Input:', 'Action:' and 'Expected Result:' in that order. Do not use headings, bold "
    "text, sub-bullets or commentary. Output only the list."
)


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    description: str
    fields: Tuple[str, ...]        # input fields this template reads
    max_tokens: int                # output cap per call
    system: str                    # role and goal
    instructions: str              # what to cover and how many cases
    example_input: str             # one-shot example input (already rendered)
    example_output: str            # one-shot example output in the contract format

    def render_input(self, record: Mapping[str, str]) -> str:
        """Turn one input record into the text the model sees."""
        raise NotImplementedError

    def build_prompt(self, record: Mapping[str, str]) -> str:
        rendered = self.render_input(record)
        return (
            f"{self.system}\n\n"
            f"{self.instructions}\n\n"
            f"{OUTPUT_CONTRACT}\n\n"
            f"Example input:\n{self.example_input}\n\n"
            f"Example output:\n{self.example_output}\n\n"
            f"Now produce the output for this input.\n\n"
            f"Input:\n{rendered}\n\n"
            f"Output:"
        )


@dataclass(frozen=True)
class RequirementTemplate(PromptTemplate):
    def render_input(self, record: Mapping[str, str]) -> str:
        text = (record.get("requirement_text") or "").strip()
        if not text:
            raise ValueError("requirement_text is empty")
        return f"Requirement: {text}"


@dataclass(frozen=True)
class BugTemplate(PromptTemplate):
    LABELS = {
        "title": "Title",
        "description": "Description",
        "steps_to_reproduce": "Steps to reproduce",
        "expected_result": "Expected result",
        "actual_result": "Actual result",
        "severity": "Severity",
    }

    def render_input(self, record: Mapping[str, str]) -> str:
        lines = []
        for key, label in self.LABELS.items():
            value = str(record.get(key) or "").strip()
            if value and value.lower() != "nan":
                lines.append(f"{label}: {value}")
        if not any(line.startswith(("Title:", "Description:")) for line in lines):
            raise ValueError("bug record needs a title or description")
        return "\n".join(lines)


REQUIREMENT_TEST_CASES = RequirementTemplate(
    name="requirement_test_cases",
    description="Test cases for a software requirement",
    fields=("requirement_text",),
    max_tokens=512,
    system="You are a senior QA engineer who writes precise, traceable test cases.",
    instructions=(
        "Write exactly 3 test cases for the requirement. Cover normal behaviour and at least "
        "one boundary or negative case. Use only facts stated in the requirement; do not invent "
        "limits, messages or values that are not given."
    ),
    example_input="Requirement: The system shall lock an account after 3 consecutive failed login attempts.",
    example_output=(
        "1. Input: An account with a known password. Action: Log in with a wrong password 3 times in a row. "
        "Expected Result: The account is locked and the next login attempt is refused.\n"
        "2. Input: An account with a known password. Action: Log in with a wrong password twice, then the "
        "correct password. Expected Result: The account is not locked and the login succeeds.\n"
        "3. Input: An account with a known password. Action: Log in with a wrong password 4 times. "
        "Expected Result: The account remains locked after the 3rd failure."
    ),
)

BUG_TEST_CASES = BugTemplate(
    name="bug_test_cases",
    description="Regression test cases for a reported bug",
    fields=("title", "description", "steps_to_reproduce", "expected_result", "actual_result", "severity"),
    max_tokens=512,
    system="You are a senior QA engineer who writes regression tests from bug reports.",
    instructions=(
        "Write exactly 3 regression test cases for the bug. The first must follow the reported steps "
        "and check the expected result, so it fails while the bug exists. The other two must test "
        "nearby variants of the same behaviour. Use only facts stated in the report."
    ),
    example_input=(
        "Title: Checkout total ignores discount\n"
        "Description: Applying a 10% coupon leaves the total unchanged.\n"
        "Steps to reproduce: 1. Add an item priced 100. 2. Apply coupon SAVE10.\n"
        "Expected result: Total is 90.\n"
        "Actual result: Total is 100.\n"
        "Severity: High"
    ),
    example_output=(
        "1. Input: A cart with one item priced 100 and a valid coupon SAVE10. Action: Apply coupon SAVE10 "
        "and view the total. Expected Result: The total is 90.\n"
        "2. Input: A cart with one item priced 100 and an expired coupon. Action: Apply the expired coupon. "
        "Expected Result: The total stays 100 and an error is shown.\n"
        "3. Input: A cart with a total of 0 and a valid coupon SAVE10. Action: Apply coupon SAVE10. "
        "Expected Result: The total stays 0 and no negative total is shown."
    ),
)

TEMPLATES: Dict[str, PromptTemplate] = {
    REQUIREMENT_TEST_CASES.name: REQUIREMENT_TEST_CASES,
    BUG_TEST_CASES.name: BUG_TEST_CASES,
}


def get_template(name: str) -> PromptTemplate:
    if name not in TEMPLATES:
        raise ValueError(f"Unknown template {name!r}. Available: {', '.join(sorted(TEMPLATES))}")
    return TEMPLATES[name]
