#!/usr/bin/env python3
"""Validate foreshadow transitions for one chapter."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _common import (
    default_project_root,
    find_chapter_file,
    load_foreshadow_ledger,
    parse_chapter_id,
    parse_front_matter,
    read_text,
    to_string_list,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Track foreshadow status transitions by chapter.")
    parser.add_argument("--chapter-id", required=True, help="chapter id, e.g. v01-c001")
    parser.add_argument("--root", default=None, help="project root (default: auto-detect final/)")
    return parser.parse_args()


def chapter_rank(chapter_id: str) -> int:
    volume, chapter = parse_chapter_id(chapter_id)
    return volume * 10000 + chapter


def expected_range_end(item: dict[str, Any]) -> str | None:
    value = item.get("expected_payoff_range")
    if isinstance(value, list) and value:
        tail = str(value[-1]).strip()
        return tail or None
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def main() -> None:
    args = parse_args()
    root = Path(args.root) if args.root else default_project_root()

    try:
        parse_chapter_id(args.chapter_id)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    chapter_file = find_chapter_file(root, args.chapter_id)
    if chapter_file is None:
        print(f"chapter file not found for {args.chapter_id}", file=sys.stderr)
        sys.exit(1)

    meta, _ = parse_front_matter(read_text(chapter_file))
    if not meta:
        print(f"front matter not found: {chapter_file}", file=sys.stderr)
        sys.exit(1)

    add_ids = to_string_list(meta.get("foreshadow_add"))
    payoff_ids = to_string_list(meta.get("foreshadow_payoff"))

    ledger = load_foreshadow_ledger(root)
    by_id = {str(item.get("id", "")).strip(): item for item in ledger if item.get("id")}

    transitions: list[dict[str, Any]] = []
    warnings: list[str] = []
    overdue: list[dict[str, Any]] = []

    for fs_id in add_ids:
        item = by_id.get(fs_id)
        if item is None:
            warnings.append(f"foreshadow_add contains unknown id: {fs_id}")
            continue
        old = str(item.get("status", "")).strip()
        if old == "planned":
            new = "seeded"
            valid = True
        elif old in {"seeded", "active"}:
            new = "active"
            valid = True
        else:
            new = old
            valid = False
        transitions.append(
            {
                "id": fs_id,
                "from": old,
                "to": new,
                "valid": valid,
                "reason": "foreshadow_add in chapter front matter",
            }
        )

    for fs_id in payoff_ids:
        item = by_id.get(fs_id)
        if item is None:
            warnings.append(f"foreshadow_payoff contains unknown id: {fs_id}")
            continue
        old = str(item.get("status", "")).strip()
        valid = old in {"seeded", "active"}
        transitions.append(
            {
                "id": fs_id,
                "from": old,
                "to": "paid" if valid else old,
                "valid": valid,
                "reason": f"foreshadow_payoff in chapter front matter -> payoff_chapter={args.chapter_id}",
            }
        )

    current_rank = chapter_rank(args.chapter_id)
    for item in ledger:
        fs_id = str(item.get("id", "")).strip()
        status = str(item.get("status", "")).strip()
        if status not in {"seeded", "active"}:
            continue
        end = expected_range_end(item)
        if not end:
            continue
        try:
            if chapter_rank(end) < current_rank:
                overdue.append(
                    {
                        "id": fs_id,
                        "status": status,
                        "expected_payoff_end": end,
                    }
                )
        except ValueError:
            warnings.append(f"invalid expected_payoff_range value on {fs_id}: {end}")

    output = {
        "chapter_id": args.chapter_id,
        "source_chapter_file": str(chapter_file.relative_to(root)).replace("\\", "/"),
        "transitions": transitions,
        "overdue": overdue,
        "warnings": warnings,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
