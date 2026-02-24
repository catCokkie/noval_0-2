#!/usr/bin/env python3
"""Aggregate token/cost data from tracking CSV."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from _common import default_project_root, read_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate chapter cost statistics.")
    parser.add_argument(
        "--source",
        default="01_项目驾驶舱/进度与成本跟踪.csv",
        help="source csv relative to root",
    )
    parser.add_argument("--root", default=None, help="project root (default: auto-detect final/)")
    parser.add_argument(
        "--monthly-limit",
        type=float,
        default=None,
        help="optional monthly budget limit in USD for alerts",
    )
    return parser.parse_args()


def to_float(value: Any) -> float:
    text = str(value).strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def to_int(value: Any) -> int:
    text = str(value).strip()
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def load_default_budget(root: Path) -> float:
    route_file = root / "08_自动化" / "模型路由与成本.yml"
    if not route_file.exists():
        return 0.0
    text = read_text(route_file)
    match = re.search(r"default_budget_limit_usd_per_chapter:\s*([0-9]+(?:\.[0-9]+)?)", text)
    if not match:
        return 0.0
    return float(match.group(1))


def main() -> None:
    args = parse_args()
    root = Path(args.root) if args.root else default_project_root()
    source = root / args.source
    if not source.exists():
        print(f"source csv not found: {source}", file=sys.stderr)
        sys.exit(1)

    rows: list[dict[str, str]] = []
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if not row:
                continue
            rows.append({(k or "").lstrip("\ufeff"): v for k, v in row.items()})

    chapter_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"rows": 0, "cost_usd": 0.0, "token_in": 0, "token_out": 0}
    )
    stage_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"rows": 0, "cost_usd": 0.0})
    model_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"rows": 0, "cost_usd": 0.0})
    monthly_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"rows": 0, "cost_usd": 0.0})

    total_cost = 0.0
    total_token_in = 0
    total_token_out = 0

    for row in rows:
        chapter_id = (row.get("chapter_id") or "").strip() or "unknown"
        stage = (row.get("stage") or "").strip() or "unknown"
        model = (row.get("model_used") or "").strip() or "unknown"
        date_text = (row.get("last_update") or "").strip()
        month = date_text[:7] if len(date_text) >= 7 else "unknown"

        cost = to_float(row.get("cost_usd"))
        token_in = to_int(row.get("token_in"))
        token_out = to_int(row.get("token_out"))

        total_cost += cost
        total_token_in += token_in
        total_token_out += token_out

        chapter_stats[chapter_id]["rows"] += 1
        chapter_stats[chapter_id]["cost_usd"] += cost
        chapter_stats[chapter_id]["token_in"] += token_in
        chapter_stats[chapter_id]["token_out"] += token_out

        stage_stats[stage]["rows"] += 1
        stage_stats[stage]["cost_usd"] += cost

        model_stats[model]["rows"] += 1
        model_stats[model]["cost_usd"] += cost

        monthly_stats[month]["rows"] += 1
        monthly_stats[month]["cost_usd"] += cost

    chapter_budget_limit = load_default_budget(root)
    chapter_cost_exceeded = []
    if chapter_budget_limit > 0:
        for chapter_id, stats in sorted(chapter_stats.items()):
            if stats["cost_usd"] > chapter_budget_limit:
                chapter_cost_exceeded.append(
                    {
                        "chapter_id": chapter_id,
                        "cost_usd": round(stats["cost_usd"], 4),
                        "limit_usd": chapter_budget_limit,
                    }
                )

    monthly_cost_exceeded = []
    if args.monthly_limit is not None:
        for month, stats in sorted(monthly_stats.items()):
            if stats["cost_usd"] > args.monthly_limit:
                monthly_cost_exceeded.append(
                    {
                        "month": month,
                        "cost_usd": round(stats["cost_usd"], 4),
                        "limit_usd": args.monthly_limit,
                    }
                )

    output = {
        "source": str(source.relative_to(root)).replace("\\", "/"),
        "rows": len(rows),
        "totals": {
            "cost_usd": round(total_cost, 4),
            "token_in": total_token_in,
            "token_out": total_token_out,
        },
        "by_chapter": {k: v for k, v in sorted(chapter_stats.items())},
        "by_stage": {k: v for k, v in sorted(stage_stats.items())},
        "by_model": {k: v for k, v in sorted(model_stats.items())},
        "by_month": {k: v for k, v in sorted(monthly_stats.items())},
        "alerts": {
            "chapter_cost_exceeded": chapter_cost_exceeded,
            "monthly_cost_exceeded": monthly_cost_exceeded,
            "low_quality_high_cost": [],
        },
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
