#!/usr/bin/env python3
"""Assemble and validate request package for one chapter task."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from _common import (
    TASK_TYPES,
    default_project_root,
    find_chapter_file,
    load_character_cards,
    load_foreshadow_ledger,
    load_schema,
    make_chapter_id,
    markdown_excerpt,
    parse_chapter_id,
    parse_front_matter,
    read_text,
    to_string_list,
    validate_schema,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble request package for one chapter task.")
    parser.add_argument("--chapter-id", required=True, help="chapter id, e.g. v01-c001")
    parser.add_argument("--task-type", required=True, choices=sorted(TASK_TYPES))
    parser.add_argument("--goal", default="生成本次任务可执行请求包", help="request.goal")
    parser.add_argument("--must-keep", action="append", default=[], help="request.must_keep item (repeatable)")
    parser.add_argument("--forbidden", action="append", default=[], help="request.forbidden item (repeatable)")
    parser.add_argument("--word-count-target", type=int, default=0, help="constraints.word_count_target")
    parser.add_argument("--pov", default="", help="constraints.pov")
    parser.add_argument("--new-terms-budget", type=int, default=1, help="constraints.new_terms_budget")
    parser.add_argument("--hook-type", default="信息钩子", help="constraints.hook_type")
    parser.add_argument("--consistency-score-min", type=int, default=90, help="quality_target.consistency_score_min")
    parser.add_argument("--style-alignment-min", type=int, default=85, help="quality_target.style_alignment_min")
    parser.add_argument("--root", default=None, help="project root (default: auto-detect final/)")
    parser.add_argument("--no-schema-validate", action="store_true", help="skip request schema validation")
    return parser.parse_args()


def load_previous_summary(root: Path, chapter_id: str) -> str:
    volume, chapter = parse_chapter_id(chapter_id)
    if chapter > 1:
        prev_id = make_chapter_id(volume, chapter - 1)
        prev_file = find_chapter_file(root, prev_id)
        if prev_file is not None:
            _, body = parse_front_matter(read_text(prev_file))
            excerpt = markdown_excerpt(body, limit=260)
            if excerpt:
                return excerpt

    reverse_outline = root / "06_\u9a8c\u8bc1\u4e0e\u56de\u5f52" / "\u53cd\u5411\u603b\u7eb2" / f"\u7b2c{volume:02d}\u5377_\u53cd\u5411\u603b\u7eb2.md"
    if reverse_outline.exists():
        return markdown_excerpt(read_text(reverse_outline), limit=260)
    return ""


def select_character_states(root: Path, chapter_id: str) -> tuple[list[dict[str, object]], str | None]:
    all_cards = load_character_cards(root)
    chapter_file = find_chapter_file(root, chapter_id)
    if chapter_file is None:
        return all_cards, None

    meta, _ = parse_front_matter(read_text(chapter_file))
    wanted = set(to_string_list(meta.get("characters")))
    if not wanted:
        return all_cards, str(chapter_file.relative_to(root)).replace("\\", "/")

    selected = [card for card in all_cards if card.get("name") in wanted or card.get("id") in wanted]
    return selected or all_cards, str(chapter_file.relative_to(root)).replace("\\", "/")


def build_request_package(root: Path, args: argparse.Namespace) -> dict[str, object]:
    constitution_path = root / "01_\u9879\u76ee\u9a7e\u9a76\u8231" / "\u4f5c\u54c1\u5baa\u6cd5.md"
    hard_rules_path = root / "02_\u6b63\u53f2\u8d44\u4ea7_Canon" / "\u89c4\u5219" / "\u786c\u89c4\u5219_R1-R3.md"
    if not constitution_path.exists() or not hard_rules_path.exists():
        raise FileNotFoundError("missing required canon files: 作品宪法.md or 硬规则_R1-R3.md")

    constitution = read_text(constitution_path).strip()
    hard_rules = read_text(hard_rules_path).strip()
    if not constitution or not hard_rules:
        raise ValueError("empty required canon files: 作品宪法.md or 硬规则_R1-R3.md")

    character_states, source_chapter_file = select_character_states(root, args.chapter_id)
    return {
        "request": {
            "task_type": args.task_type,
            "chapter_id": args.chapter_id,
            "goal": args.goal,
            "must_keep": args.must_keep,
            "forbidden": args.forbidden,
            "inputs": {
                "constitution": constitution,
                "hard_rules": hard_rules,
                "character_states": character_states,
                "previous_summary": load_previous_summary(root, args.chapter_id),
                "foreshadow_state": load_foreshadow_ledger(root),
            },
            "constraints": {
                "word_count_target": args.word_count_target,
                "pov": args.pov,
                "new_terms_budget": args.new_terms_budget,
                "hook_type": args.hook_type,
            },
            "quality_target": {
                "consistency_score_min": args.consistency_score_min,
                "style_alignment_min": args.style_alignment_min,
            },
            "meta": {
                "source_chapter_file": source_chapter_file,
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            },
        }
    }


def main() -> None:
    args = parse_args()
    root = Path(args.root) if args.root else default_project_root()

    try:
        parse_chapter_id(args.chapter_id)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    try:
        package = build_request_package(root, args)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    if not args.no_schema_validate:
        schema = load_schema(root, "request")
        errors = validate_schema(package, schema)
        if errors:
            print("request schema validation failed:", file=sys.stderr)
            for item in errors:
                print(f"- {item}", file=sys.stderr)
            sys.exit(1)

    print(json.dumps(package, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
