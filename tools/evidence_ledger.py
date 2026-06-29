#!/usr/bin/env python3
"""Create and validate MindFlow evidence ledgers for paper notes."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.paper_note_audit import AuditResult, VAULT_ROOT, parse_frontmatter

DEFAULT_EVIDENCE_DIR = "Workbench/evidence"
SOURCE_KEYS = ("paper", "website", "github")


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve() if args.root else VAULT_ROOT

    if args.command == "init":
        note = resolve_path(args.note, root=root)
        ledger = build_ledger_skeleton(note, root=root)
        out = resolve_output_path(args.output, note=note, root=root)
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists() and not args.force:
            print(f"Refusing to overwrite existing ledger: {out}", file=sys.stderr)
            return 2
        out.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote evidence ledger skeleton: {rel(out, root)}")
        return 0

    if args.command == "validate":
        paths = [resolve_path(path, root=root) for path in args.ledgers]
        any_errors = False
        for path in paths:
            result = validate_ledger_path(path, require_claims=args.require_claims)
            any_errors = any_errors or bool(result.errors)
            print_validation(path, result, root=root)
        return 1 if any_errors else 0

    raise AssertionError(f"unknown command: {args.command}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or validate MindFlow paper evidence ledgers.")
    parser.add_argument("--root", help="Vault root. Defaults to the current MindFlow repo inferred from this script.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create a skeleton evidence ledger for a paper note.")
    init.add_argument("note", help="Paper note path, e.g. Papers/2605-MolmoAct2.md")
    init.add_argument("-o", "--output", help="Output JSON path. Defaults to Workbench/evidence/<ShortTitle>.json")
    init.add_argument("--force", action="store_true", help="Overwrite an existing evidence ledger.")

    validate = sub.add_parser("validate", help="Validate one or more evidence ledger JSON files.")
    validate.add_argument("ledgers", nargs="+", help="Evidence ledger JSON path(s).")
    validate.add_argument(
        "--require-claims",
        action="store_true",
        help="Fail if the ledger has no claim evidence entries. Use for completed/new digests.",
    )
    return parser.parse_args()


def resolve_path(raw: str, *, root: Path) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def resolve_output_path(raw: str | None, *, note: Path, root: Path) -> Path:
    if raw:
        return resolve_path(raw, root=root)
    stem = note.stem
    if "-" in stem:
        stem = stem.split("-", 1)[1]
    return (root / DEFAULT_EVIDENCE_DIR / f"{stem}.json").resolve()


def build_ledger_skeleton(note_path: Path, *, root: Path = VAULT_ROOT) -> dict[str, Any]:
    note_path = note_path.resolve()
    text = note_path.read_text(encoding="utf-8")
    metadata, _body = parse_frontmatter(text, AuditResult(path=note_path))
    sources: list[dict[str, Any]] = []
    for key in SOURCE_KEYS:
        value = metadata.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            sources.append({"id": key, "kind": key, "url": value})

    return {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "paper": rel(note_path, root),
        "title": metadata.get("title"),
        "sources": sources,
        "claims": [],
        "notes": [
            "Fill claims manually during paper digest/update.",
            "Each important technical/result claim should cite at least one source quote or figure/table reference.",
        ],
    }


def validate_ledger_path(path: Path, *, require_claims: bool = False) -> ValidationResult:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return ValidationResult(errors=["ledger file does not exist"])
    except json.JSONDecodeError as exc:
        return ValidationResult(errors=[f"invalid JSON: {exc}"])
    return validate_ledger(data, require_claims=require_claims)


def validate_ledger(data: dict[str, Any], *, require_claims: bool = False) -> ValidationResult:
    result = ValidationResult()
    for key in ("schema_version", "paper", "title", "sources", "claims"):
        if key not in data:
            result.errors.append(f"{key} is required")
    if data.get("schema_version") != "0.1":
        result.errors.append("schema_version must be '0.1'")
    if not isinstance(data.get("sources", []), list):
        result.errors.append("sources must be a list")
    if not isinstance(data.get("claims", []), list):
        result.errors.append("claims must be a list")
        return result
    if require_claims and not data.get("claims"):
        result.errors.append("claims must contain at least one item")

    source_ids = {source.get("id") for source in data.get("sources", []) if isinstance(source, dict)}
    for idx, claim in enumerate(data.get("claims", [])):
        prefix = f"claims[{idx}]"
        if not isinstance(claim, dict):
            result.errors.append(f"{prefix} must be an object")
            continue
        if not claim.get("claim"):
            result.errors.append(f"{prefix}.claim is required")
        evidence = claim.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            result.errors.append(f"{prefix}.evidence must contain at least one item")
            continue
        for ev_idx, item in enumerate(evidence):
            ev_prefix = f"{prefix}.evidence[{ev_idx}]"
            if not isinstance(item, dict):
                result.errors.append(f"{ev_prefix} must be an object")
                continue
            source = item.get("source")
            if not source:
                result.errors.append(f"{ev_prefix}.source is required")
            elif source_ids and source not in source_ids:
                result.warnings.append(f"{ev_prefix}.source {source!r} is not listed in sources")
            if not item.get("quote") and not item.get("figure") and not item.get("table"):
                result.errors.append(f"{ev_prefix}.quote is required")
    return result


def print_validation(path: Path, result: ValidationResult, *, root: Path) -> None:
    status = "OK" if result.ok else "FAIL"
    print(f"[{status}] {rel(path, root)}")
    for error in result.errors:
        print(f"  ERROR: {error}")
    for warning in result.warnings:
        print(f"  WARN:  {warning}")


def rel(path: Path, root: Path) -> str:
    path = path.resolve()
    root = root.resolve()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)

if __name__ == "__main__":
    raise SystemExit(main())
