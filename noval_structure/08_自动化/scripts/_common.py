#!/usr/bin/env python3
"""Common helpers for automation scripts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CHAPTER_ID_RE = re.compile(r"^v(?P<volume>\d{2})-c(?P<chapter>\d{3})$")
TASK_TYPES = {"chapter_outline", "scene_skeleton", "draft_expand", "continuity_check"}


def default_project_root() -> Path:
    # scripts/ -> 08_自动化/ -> final/
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").lstrip("\ufeff")


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def parse_chapter_id(chapter_id: str) -> tuple[int, int]:
    match = CHAPTER_ID_RE.fullmatch(chapter_id.strip())
    if not match:
        raise ValueError(f"invalid chapter_id: {chapter_id!r}, expected vNN-cNNN")
    return int(match.group("volume")), int(match.group("chapter"))


def make_chapter_id(volume: int, chapter: int) -> str:
    return f"v{volume:02d}-c{chapter:03d}"


def chapter_file_candidates(root: Path, volume: int, chapter: int) -> list[Path]:
    vol = f"\u7b2c{volume:02d}\u5377"
    ch = f"\u7b2c{chapter:03d}\u7ae0"
    return [
        root / "05_\u5b9a\u7a3f\u5c42" / vol / f"{ch}.md",
        root / "04_\u8349\u7a3f\u5c42" / "\u4fee\u8ba2\u8349\u7a3f" / vol / f"{ch}_\u4fee\u8ba2\u7a3f.md",
        root / "04_\u8349\u7a3f\u5c42" / "\u539f\u59cb\u8349\u7a3f" / vol / f"{ch}_\u539f\u59cb\u8349\u7a3f.md",
        root / "03_\u89c4\u5212\u5c42" / "\u7ae0\u7eb2" / vol / f"{ch}_\u7ae0\u7eb2.md",
    ]


def find_chapter_file(root: Path, chapter_id: str) -> Path | None:
    volume, chapter = parse_chapter_id(chapter_id)
    for path in chapter_file_candidates(root, volume, chapter):
        if path.exists():
            return path
    return None


def split_comma_items(raw: str) -> list[str]:
    if not raw.strip():
        return []
    result: list[str] = []
    buff: list[str] = []
    quote: str | None = None
    for char in raw:
        if quote:
            buff.append(char)
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            buff.append(char)
            continue
        if char == ",":
            result.append("".join(buff).strip())
            buff = []
            continue
        buff.append(char)
    if buff:
        result.append("".join(buff).strip())
    return result


def parse_inline_value(raw: str) -> Any:
    value = raw.strip()
    if value == "":
        return ""
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    lower = value.lower()
    if lower in {"null", "none", "~"}:
        return None
    if lower == "true":
        return True
    if lower == "false":
        return False
    if value == "{}":
        return {}
    if value.startswith("[") and value.endswith("]"):
        items = split_comma_items(value[1:-1].strip())
        return [parse_inline_value(item) for item in items]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def parse_simple_mapping(lines: list[str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, raw = stripped.split(":", 1)
        data[key.strip()] = parse_inline_value(raw.strip())
    return data


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines:
        return {}, text
    if lines[0].startswith("\ufeff"):
        lines[0] = lines[0].lstrip("\ufeff")
    if lines[0].strip() != "---":
        return {}, text
    end = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end = idx
            break
    if end is None:
        return {}, text
    meta = parse_simple_mapping(lines[1:end])
    body = "\n".join(lines[end + 1 :]).lstrip("\n")
    return meta, body


def parse_yaml_mapping(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.lstrip().startswith("- "):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            continue
        key, raw = stripped.split(":", 1)
        key = key.strip()
        raw = raw.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        current = stack[-1][1] if stack else root
        if raw == "":
            nested: dict[str, Any] = {}
            current[key] = nested
            stack.append((indent, nested))
        else:
            current[key] = parse_inline_value(raw)
    return root


def parse_yaml_list_of_dicts(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("- "):
            if current is not None:
                rows.append(current)
            current = {}
            tail = line[2:].strip()
            if tail and ":" in tail:
                key, raw = tail.split(":", 1)
                current[key.strip()] = parse_inline_value(raw.strip())
            continue
        if current is None:
            continue
        if line.startswith("  "):
            stripped = line.strip()
            if ":" in stripped:
                key, raw = stripped.split(":", 1)
                current[key.strip()] = parse_inline_value(raw.strip())
    if current is not None:
        rows.append(current)
    return rows


def to_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def markdown_excerpt(text: str, limit: int = 240) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    if not lines:
        return ""
    joined = " ".join(lines)
    return joined[:limit]


def load_foreshadow_ledger(root: Path) -> list[dict[str, Any]]:
    path = root / "02_\u6b63\u53f2\u8d44\u4ea7_Canon" / "\u4f0f\u7b14\u8d26\u672c.yml"
    if not path.exists():
        return []
    return parse_yaml_list_of_dicts(read_text(path))


def load_character_cards(root: Path) -> list[dict[str, Any]]:
    person_dir = root / "02_\u6b63\u53f2\u8d44\u4ea7_Canon" / "\u4eba\u7269"
    if not person_dir.exists():
        return []
    cards: list[dict[str, Any]] = []
    for file in sorted(person_dir.glob("*.yml")):
        if "\u6a21\u677f" in file.name:
            continue
        data = parse_yaml_mapping(read_text(file))
        voice = data.get("voice") if isinstance(data.get("voice"), dict) else {}
        card = {
            "id": str(data.get("id", "")).strip(),
            "name": str(data.get("name", "")).strip(),
            "role": str(data.get("role", "")).strip(),
            "last_updated_chapter": str(data.get("last_updated_chapter", "")).strip(),
            "keywords": to_string_list(voice.get("keywords")),
            "taboo": to_string_list(voice.get("taboo")),
            "file": str(file.relative_to(root)).replace("\\", "/"),
        }
        cards.append(card)
    return cards


def schema_path(root: Path, name: str) -> Path:
    return root / "08_\u81ea\u52a8\u5316" / "schemas" / f"{name}.schema.json"


def load_schema(root: Path, name: str) -> dict[str, Any]:
    path = schema_path(root, name)
    if not path.exists():
        raise FileNotFoundError(f"schema file not found: {path}")
    schema = load_json(path)
    if not isinstance(schema, dict):
        raise ValueError(f"schema must be JSON object: {path}")
    return schema


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _type_label(schema_type: str | list[str]) -> str:
    if isinstance(schema_type, list):
        return "|".join(schema_type)
    return schema_type


def validate_schema(data: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []

    schema_type = schema.get("type")
    if schema_type is not None:
        allowed_types = schema_type if isinstance(schema_type, list) else [schema_type]
        if not any(_matches_type(data, item) for item in allowed_types):
            errors.append(f"{path}: type mismatch, expected {_type_label(allowed_types)}, got {type(data).__name__}")
            return errors

    if "enum" in schema and data not in schema["enum"]:
        errors.append(f"{path}: value {data!r} not in enum {schema['enum']!r}")

    if isinstance(data, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(data) < min_length:
            errors.append(f"{path}: string length {len(data)} < minLength {min_length}")
        max_length = schema.get("maxLength")
        if isinstance(max_length, int) and len(data) > max_length:
            errors.append(f"{path}: string length {len(data)} > maxLength {max_length}")
        pattern = schema.get("pattern")
        if isinstance(pattern, str):
            if re.fullmatch(pattern, data) is None:
                errors.append(f"{path}: string {data!r} does not match pattern {pattern!r}")

    if isinstance(data, (int, float)) and not isinstance(data, bool):
        minimum = schema.get("minimum")
        if isinstance(minimum, (int, float)) and data < minimum:
            errors.append(f"{path}: number {data} < minimum {minimum}")
        maximum = schema.get("maximum")
        if isinstance(maximum, (int, float)) and data > maximum:
            errors.append(f"{path}: number {data} > maximum {maximum}")

    if isinstance(data, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(data) < min_items:
            errors.append(f"{path}: array length {len(data)} < minItems {min_items}")
        max_items = schema.get("maxItems")
        if isinstance(max_items, int) and len(data) > max_items:
            errors.append(f"{path}: array length {len(data)} > maxItems {max_items}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for idx, item in enumerate(data):
                errors.extend(validate_schema(item, item_schema, f"{path}[{idx}]"))

    if isinstance(data, dict):
        required = schema.get("required")
        if isinstance(required, list):
            for key in required:
                if key not in data:
                    errors.append(f"{path}: missing required property {key!r}")

        properties = schema.get("properties", {})
        addl = schema.get("additionalProperties", True)

        for key, value in data.items():
            if isinstance(properties, dict) and key in properties:
                prop_schema = properties[key]
                if isinstance(prop_schema, dict):
                    errors.extend(validate_schema(value, prop_schema, f"{path}.{key}"))
                continue
            if addl is False:
                errors.append(f"{path}: additional property {key!r} is not allowed")
            elif isinstance(addl, dict):
                errors.extend(validate_schema(value, addl, f"{path}.{key}"))

    return errors
