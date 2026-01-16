#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import unicodedata
from pathlib import Path

DEFAULT_DECISIONS_DIR = Path("docs/decisions")
INDEX_FILENAME = "index.md"
_STOPWORDS = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "ain",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "aren",
    "aren't",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "couldn",
    "couldn't",
    "d",
    "did",
    "didn",
    "didn't",
    "do",
    "does",
    "doesn",
    "doesn't",
    "doing",
    "don",
    "don't",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "hadn",
    "hadn't",
    "has",
    "hasn",
    "hasn't",
    "have",
    "haven",
    "haven't",
    "having",
    "he",
    "he'd",
    "he'll",
    "he's",
    "her",
    "here",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "i",
    "i'd",
    "i'll",
    "i'm",
    "i've",
    "if",
    "in",
    "into",
    "is",
    "isn",
    "isn't",
    "it",
    "it'd",
    "it'll",
    "it's",
    "its",
    "itself",
    "just",
    "ll",
    "m",
    "ma",
    "me",
    "mightn",
    "mightn't",
    "more",
    "most",
    "mustn",
    "mustn't",
    "my",
    "myself",
    "needn",
    "needn't",
    "no",
    "nor",
    "not",
    "now",
    "o",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "re",
    "s",
    "same",
    "shan",
    "shan't",
    "she",
    "she'd",
    "she'll",
    "she's",
    "should",
    "should've",
    "shouldn",
    "shouldn't",
    "so",
    "some",
    "such",
    "t",
    "than",
    "that",
    "that'll",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "these",
    "they",
    "they'd",
    "they'll",
    "they're",
    "they've",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "ve",
    "very",
    "was",
    "wasn",
    "wasn't",
    "we",
    "we'd",
    "we'll",
    "we're",
    "we've",
    "were",
    "weren",
    "weren't",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "will",
    "with",
    "won",
    "won't",
    "wouldn",
    "wouldn't",
    "y",
    "you",
    "you'd",
    "you'll",
    "you're",
    "you've",
    "your",
    "yours",
    "yourself",
    "yourselves",
}


def slugify(text: str) -> str:
    """
    Convert a human-readable sentence into a filesystem-friendly slug.

    - lowercases
    - removes accents
    - strips punctuation
    - removes common stopwords
    - replaces spaces with hyphens
    """

    if not text.strip():
        raise ValueError("slugify(): empty input")

    # Normalize accents (é → e, ò → o, …)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Lowercase
    text = text.lower()

    # Replace non-alphanumeric with spaces
    text = re.sub(r"[^a-z0-9]+", " ", text)

    # Tokenize + drop stopwords
    tokens = [t for t in text.split() if t and t not in _STOPWORDS]

    if not tokens:
        raise ValueError("slugify(): title contains only stopwords")

    return "-".join(tokens)


def next_decision_number(decisions_dir: Path) -> int:
    """
    Scan decisions directory and return next available numeric prefix.
    """
    numbers: list[int] = []

    for path in decisions_dir.glob("*.md"):
        match = re.match(r"(\d+)-", path.name)
        if match:
            numbers.append(int(match.group(1)))

    return max(numbers, default=0) + 1


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="new-decision",
        description="Create a new decision note in docs/decisions/",
    )
    parser.add_argument(
        "--decisions-dir",
        type=Path,
        default=DEFAULT_DECISIONS_DIR,
        help="Directory containing decision notes (default: docs/decisions)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without creating files",
    )

    args = parser.parse_args(argv)

    decisions_dir: Path = args.decisions_dir
    index_file = decisions_dir / INDEX_FILENAME

    if not decisions_dir.is_dir():
        fail(f"Decisions directory not found: {decisions_dir}")

    if not index_file.is_file():
        fail(f"Index file not found: {index_file}")

    today = dt.date.today().strftime("%d/%m/%Y")

    suggested_num = next_decision_number(decisions_dir)

    try:
        desc = input("One-line description: ").strip()
    except EOFError:
        fail("No description provided")

    if not desc:
        fail("Description cannot be empty")

    title = slugify(desc)
    if not title:
        fail("Description did not produce a valid title")

    num = suggested_num
    filename = f"{num:04d}-{title}.md"
    decision_path = decisions_dir / filename

    content = f"""# {num:04d} - {desc}

Date: {today}
Status: Accepted

## Context

<Describe the context>

## Decision

<Describe the decision>

## Consequences

<Describe the consequences>
"""

    index_entry = f"- [{num:04d} — {desc}]({filename})\n"

    print("Decision to be created:")
    print(f"  File:  {decision_path}")
    print(f"  Index: {index_file}")
    print()

    if args.dry_run:
        print("Dry-run enabled. No files will be created.")
        return 0

    created_file = False
    try:
        decision_path.write_text(content, encoding="utf-8")
        created_file = True

        with index_file.open("a", encoding="utf-8") as f:
            f.write(index_entry)

    except Exception as exc:
        if created_file and decision_path.exists():
            decision_path.unlink()
        fail(f"Failed to create decision: {exc}")

    print("Decision created successfully:")
    print(f"  {decision_path}")
    print("Index updated:")
    print(f"  {index_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
