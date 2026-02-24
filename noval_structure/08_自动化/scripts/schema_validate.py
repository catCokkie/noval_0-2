#!/usr/bin/env python3
"""Validate request/response/front-matter payloads against local schemas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _common import (
    default_project_root,
    load_json,
    load_schema,
    parse_front_matter,
    read_text,
    schema_path,
    validate_schema,
)

SCHEMA_NAME_BY_KIND = {
    "request": "request",
    "response": "response",
    "front_matter": "chapter_front_matter",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Schema validate request/response/front-matter data.")
    parser.add_argument("--kind", required=True, choices=sorted(SCHEMA_NAME_BY_KIND))
    parser.add_argument("--input", required=True, help="input file path")
    parser.add_argument("--root", default=None, help="project root (default: auto-detect final/)")
    return parser.parse_args()


def load_payload(kind: str, input_path: Path) -> Any:
    if kind == "front_matter":
        if input_path.suffix.lower() == ".md":
            meta, _ = parse_front_matter(read_text(input_path))
            if not meta:
                raise ValueError("front matter not found in markdown input")
            return meta
        return load_json(input_path)
    return load_json(input_path)


def main() -> None:
    args = parse_args()
    root = Path(args.root) if args.root else default_project_root()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = (Path.cwd() / input_path).resolve()
    if not input_path.exists():
        print(f"input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    schema_name = SCHEMA_NAME_BY_KIND[args.kind]
    try:
        payload = load_payload(args.kind, input_path)
        schema = load_schema(root, schema_name)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    errors = validate_schema(payload, schema)
    result = {
        "kind": args.kind,
        "schema": str(schema_path(root, schema_name).relative_to(root)).replace("\\", "/"),
        "input": str(input_path),
        "valid": not errors,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
