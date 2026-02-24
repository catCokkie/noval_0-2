#!/usr/bin/env python3
"""Run continuity and front-matter schema checks for one chapter file."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from _common import (
    default_project_root,
    load_character_cards,
    load_foreshadow_ledger,
    load_schema,
    parse_chapter_id,
    parse_front_matter,
    read_text,
    to_string_list,
    validate_schema,
)

HOOK_DELIMITERS = {"|", "/", "、", ","}
COST_MARKERS = {"代价", "损失", "暴露", "牺牲", "负担", "疼", "耗尽"}
R2_RISK_MARKERS = {"凭空", "突然明白一切", "无缘无故就知道", "莫名其妙知道"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check one chapter file for continuity constraints.")
    parser.add_argument("--chapter-file", required=True, help="markdown chapter file path")
    parser.add_argument("--root", default=None, help="project root (default: auto-detect final/)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of YAML-like output")
    return parser.parse_args()


def add_violation(violations: list[dict[str, str]], vid: str, level: str, reason: str, fix: str) -> None:
    violations.append({"id": vid, "level": level, "reason": reason, "fix": fix})


def detect_path_chapter(path: Path) -> str | None:
    text = str(path).replace("\\", "/")
    match = re.search(r"第(\d{2})卷/.+第(\d{3})章", text)
    if not match:
        return None
    return f"v{int(match.group(1)):02d}-c{int(match.group(2)):03d}"


def validate_front_matter_schema(meta: dict[str, Any], root: Path) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    schema = load_schema(root, "chapter_front_matter")
    errors = validate_schema(meta, schema)
    for idx, error in enumerate(errors, start=1):
        add_violation(
            violations,
            f"FM_SCHEMA_{idx:03d}",
            "P0",
            f"Front Matter schema 违规: {error}",
            "按 chapter_front_matter.schema.json 修正字段后重试。",
        )
    return violations


def validate_meta_business(meta: dict[str, Any], body: str, chapter_file: Path) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []

    chapter_id = str(meta.get("chapter_id", "")).strip()
    if chapter_id:
        try:
            parse_chapter_id(chapter_id)
        except ValueError:
            add_violation(
                violations,
                "FM_BAD_CHAPTER_ID",
                "P0",
                f"chapter_id 格式非法: {chapter_id}",
                "使用 vNN-cNNN 格式，例如 v01-c001。",
            )

    expected_id = detect_path_chapter(chapter_file)
    if chapter_id and expected_id and chapter_id != expected_id:
        add_violation(
            violations,
            "FM_CHAPTER_ID_MISMATCH",
            "P1",
            f"chapter_id={chapter_id} 与文件路径推导值 {expected_id} 不一致。",
            "统一 Front Matter 与文件命名中的卷章编号。",
        )

    hook_type = str(meta.get("hook_type", "")).strip()
    if hook_type and any(delim in hook_type for delim in HOOK_DELIMITERS):
        add_violation(
            violations,
            "HOOK_NOT_SINGLE",
            "P1",
            f"hook_type 非单一: {hook_type}",
            "只保留一个钩子类型。",
        )

    status = str(meta.get("status", "")).strip()
    token_in = meta.get("token_in")
    token_out = meta.get("token_out")
    if status in {"review", "final"}:
        if isinstance(token_in, (int, float)) and isinstance(token_out, (int, float)):
            if token_in <= 0 or token_out <= 0:
                add_violation(
                    violations,
                    "COST_EMPTY_ON_REVIEW",
                    "P1",
                    "review/final 状态下 token_in 或 token_out 为 0。",
                    "补充真实 token 统计后再提交。",
                )

    if body.strip() and status in {"review", "final"}:
        if not any(marker in body for marker in COST_MARKERS):
            add_violation(
                violations,
                "R1_COST_NOT_VISIBLE",
                "P1",
                "正文未检测到明显代价表达，可能违反 R1。",
                "补充体能/资源/关系/信息暴露等代价描写。",
            )

    if any(marker in body for marker in R2_RISK_MARKERS):
        add_violation(
            violations,
            "R2_TRACE_RISK",
            "P1",
            "正文出现疑似凭空得知的表述。",
            "补充情报来源链，确保信息可追溯。",
        )
    return violations


def check_character_taboo(meta: dict[str, Any], body: str, cards: list[dict[str, Any]]) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    name_to_card = {str(card.get("name", "")).strip(): card for card in cards}
    for name in to_string_list(meta.get("characters")):
        if name not in name_to_card:
            add_violation(
                violations,
                "CHAR_NOT_FOUND",
                "P1",
                f"角色 `{name}` 未在人物卡中找到。",
                "补充人物卡或更正 Front Matter.characters。",
            )
            continue
        taboo_words = to_string_list(name_to_card[name].get("taboo"))
        for taboo in taboo_words:
            if taboo and taboo in body:
                add_violation(
                    violations,
                    "CHAR_TABOO_HIT",
                    "P1",
                    f"角色 `{name}` 的禁用词 `{taboo}` 出现在正文。",
                    "改写对应句子或更新人物卡 taboo 约束。",
                )
    return violations


def check_foreshadow_ids(
    meta: dict[str, Any], ledger: list[dict[str, Any]]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    violations: list[dict[str, str]] = []
    updates: list[dict[str, str]] = []
    valid_ids = {str(item.get("id", "")).strip() for item in ledger if item.get("id")}

    for fs_id in to_string_list(meta.get("foreshadow_add")):
        if fs_id not in valid_ids:
            add_violation(
                violations,
                "FS_ADD_NOT_FOUND",
                "P0",
                f"foreshadow_add 包含未知 id: {fs_id}",
                "先在伏笔账本新增该 id，再引用。",
            )
        else:
            updates.append({"id": fs_id, "action": "seed_or_activate"})

    for fs_id in to_string_list(meta.get("foreshadow_payoff")):
        if fs_id not in valid_ids:
            add_violation(
                violations,
                "FS_PAYOFF_NOT_FOUND",
                "P0",
                f"foreshadow_payoff 包含未知 id: {fs_id}",
                "先在伏笔账本确认该 id，再登记回收。",
            )
        else:
            updates.append({"id": fs_id, "action": "mark_paid"})
    return violations, updates


def emit_yaml_like(result: dict[str, Any]) -> str:
    lines = [f"result: {result['result']}", "violations:"]
    if not result["violations"]:
        lines.append("  []")
    else:
        for item in result["violations"]:
            lines.append(f"  - id: {item['id']}")
            lines.append(f"    level: {item['level']}")
            lines.append(f"    reason: {json.dumps(item['reason'], ensure_ascii=False)}")
            lines.append(f"    fix: {json.dumps(item['fix'], ensure_ascii=False)}")
    lines.append("foreshadow_updates:")
    if not result["foreshadow_updates"]:
        lines.append("  []")
    else:
        for item in result["foreshadow_updates"]:
            lines.append(f"  - id: {item['id']}")
            lines.append(f"    action: {item['action']}")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    root = Path(args.root) if args.root else default_project_root()
    chapter_path = Path(args.chapter_file)
    if not chapter_path.is_absolute():
        chapter_path = (Path.cwd() / chapter_path).resolve()
    if not chapter_path.exists():
        print(f"chapter file not found: {chapter_path}", file=sys.stderr)
        sys.exit(1)

    text = read_text(chapter_path)
    meta, body = parse_front_matter(text)
    violations: list[dict[str, str]] = []
    if not meta:
        add_violation(
            violations,
            "FM_NOT_FOUND",
            "P0",
            "未检测到 Front Matter。",
            "在文件头部添加 `---` 包裹的 Front Matter 字段。",
        )
    else:
        violations.extend(validate_front_matter_schema(meta, root))
        violations.extend(validate_meta_business(meta, body, chapter_path))
        violations.extend(check_character_taboo(meta, body, load_character_cards(root)))

    fs_violations, fs_updates = check_foreshadow_ids(meta, load_foreshadow_ledger(root))
    violations.extend(fs_violations)

    result = {
        "result": "pass" if not violations else "fail",
        "violations": violations,
        "foreshadow_updates": fs_updates,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(emit_yaml_like(result))


if __name__ == "__main__":
    main()
