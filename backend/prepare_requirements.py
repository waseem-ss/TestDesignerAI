"""
Prepare software_requirements_extended.csv for TestDesignerAI test-case generation.

Steps:
  1. Clean and normalize requirement text (whitespace, spacing before punctuation,
     empty rows, duplicates). Original casing is preserved.
  2. Merge overlapping types: F (functional) is folded into FR (functional requirement).
  3. Create a stratified train/test split (per type) so rare types stay represented.

Outputs (written to data/):
  - requirements_clean.csv   full cleaned dataset with requirement_id, requirement_text, type, split
  - requirements_train.csv   training split
  - requirements_test.csv    test split

Usage:
  python prepare_requirements.py
"""

import os
import re
import sys

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUT_PATH = os.path.join(DATA_DIR, "software_requirements_extended.csv")

TEST_SIZE = 0.2
RANDOM_STATE = 42

# Overlapping type labels to merge into a canonical label.
TYPE_MERGE_MAP = {
    "F": "FR",  # F and FR both mean functional requirement
}


def normalize_text(text: str) -> str:
    """Collapse whitespace, remove spaces before punctuation, and trim."""
    text = re.sub(r"\s+", " ", text)                 # collapse runs of whitespace/newlines
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)     # "word ." -> "word."
    return text.strip()


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    rows_read = len(df)
    df["Type"] = df["Type"].astype(str).str.strip().str.upper()
    df["Requirement"] = df["Requirement"].astype(str)

    original = df["Requirement"].copy()
    df["Requirement"] = df["Requirement"].map(normalize_text)
    changed = int((original != df["Requirement"]).sum())

    df = df[df["Requirement"].str.len() > 0]
    empty_dropped = rows_read - len(df)

    # Deduplicate on normalized text, keeping the first occurrence.
    before_dedupe = len(df)
    df = df.drop_duplicates(subset=["Requirement"], keep="first")
    dupes_dropped = before_dedupe - len(df)

    df["Type"] = df["Type"].replace(TYPE_MERGE_MAP)

    print(f"Rows read:            {rows_read}")
    print(f"Text normalized:      {changed}")
    print(f"Empty rows dropped:   {empty_dropped}")
    print(f"Duplicates dropped:   {dupes_dropped}")
    print(f"Rows after cleaning:  {len(df)}")
    return df.reset_index(drop=True)


def stratified_split(df: pd.DataFrame, test_size: float, seed: int) -> pd.Series:
    """Return a Series of 'train'/'test' labels, stratified by Type.

    Classes with fewer than 2 samples go entirely to train, since they cannot be split.
    """
    split = pd.Series("train", index=df.index)
    for _, group in df.groupby("type"):
        if len(group) < 2:
            continue
        n_test = max(1, round(len(group) * test_size))
        test_idx = group.sample(n=n_test, random_state=seed).index
        split.loc[test_idx] = "test"
    return split


def main() -> int:
    if not os.path.exists(INPUT_PATH):
        print(f"Input file not found: {INPUT_PATH}", file=sys.stderr)
        return 1

    raw = pd.read_csv(INPUT_PATH)
    print(f"Loaded {INPUT_PATH}")
    df = clean(raw)

    # Merge and clean are done; now build the TestDesignerAI schema.
    out = pd.DataFrame({
        "requirement_id": [f"REQ_{i:04d}" for i in range(1, len(df) + 1)],
        "requirement_text": df["Requirement"].values,
        "type": df["Type"].values,
    })
    out["split"] = stratified_split(out, TEST_SIZE, RANDOM_STATE).values

    clean_path = os.path.join(DATA_DIR, "requirements_clean.csv")
    train_path = os.path.join(DATA_DIR, "requirements_train.csv")
    test_path = os.path.join(DATA_DIR, "requirements_test.csv")

    out.to_csv(clean_path, index=False, encoding="utf-8")
    out[out["split"] == "train"].drop(columns="split").to_csv(train_path, index=False, encoding="utf-8")
    out[out["split"] == "test"].drop(columns="split").to_csv(test_path, index=False, encoding="utf-8")

    print("\nType distribution (after merge):")
    summary = out.groupby("type")["split"].value_counts().unstack(fill_value=0)
    summary["total"] = summary.sum(axis=1)
    print(summary.sort_values("total", ascending=False).to_string())

    print(f"\nTrain rows: {(out['split'] == 'train').sum()}")
    print(f"Test rows:  {(out['split'] == 'test').sum()}")
    print(f"\nWrote:\n  {clean_path}\n  {train_path}\n  {test_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
