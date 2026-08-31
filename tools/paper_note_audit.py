#!/usr/bin/env python3
"""Audit MindFlow paper notes and optionally materialize a file-first registry.

This is intentionally stdlib-only so any agent can run it inside the vault without
setting up the full MindFlow Python environment.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = VAULT_ROOT / "Workbench" / "registry" / "papers.json"
REQUIRED_FRONTMATTER = (
    "title",
    "authors",
    "date_publish",
    "venue",
    "tags",
    "paper",
    "rating",
    "date_added",
)
REQUIRED_SECTIONS = ("## Summary", "## 关联工作", "## 论文点评")
URL_RE = re.compile(r"^https?://")
SUMMARY_RATING_RE = re.compile(r">\s*-\s*\*\*Rating\*\*:\s*`?(\d)")
FINAL_RATING_RE = re.compile(r"\*\*分数\*\*[:：]\s*`?(\d)")
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
OBSIDIAN_EMBED_RE = re.compile(r"!\[\[([^\]]+)\]\]")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


@dataclass
class AuditResult:
    path: Path
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def registry_entry(self) -> dict[str, Any]:
        def scalar(name: str) -> Any:
            value = self.metadata.get(name)
            return value

        return {
            "path": self.path.relative_to(VAULT_ROOT).as_posix(),
            "title": scalar("title"),
            "date_publish": scalar("date_publish"),
            "venue": scalar("venue"),
            "tags": scalar("tags"),
            "rating": scalar("rating"),
            "paper": scalar("paper"),
            "website": scalar("website"),
            "github": scalar("github"),
            "date_added": scalar("date_added"),
            "audit": {
                "ok": self.ok,
                "errors": list(self.errors),
                "warnings": list(self.warnings),
            },
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit MindFlow paper notes.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Paper note path(s). If omitted, audit all Papers/*.md.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Audit all paper notes under Papers/*.md (default when no paths are given).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat new-note quality checks such as missing metrics as errors.",
    )
    parser.add_argument(
        "--write-registry",
        nargs="?",
        const=str(DEFAULT_REGISTRY),
        metavar="PATH",
        help="Write a ResearchInfra-style file-first registry JSON. Defaults to Workbench/registry/papers.json.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable audit JSON instead of text summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    note_paths = resolve_note_paths(args.paths, all_notes=args.all)
    results = [audit_note(path, strict=args.strict) for path in note_paths]

    if args.write_registry:
        write_registry(Path(args.write_registry), results)

    if args.json:
        print(json.dumps(render_json(results), ensure_ascii=False, indent=2))
    else:
        print_text_summary(results, registry_path=Path(args.write_registry) if args.write_registry else None)

    return 1 if any(result.errors for result in results) else 0


def resolve_note_paths(paths: list[str], *, all_notes: bool) -> list[Path]:
    if all_notes or not paths:
        return sorted((VAULT_ROOT / "Papers").glob("*.md"))
    out: list[Path] = []
    for raw in paths:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = (VAULT_ROOT / path).resolve()
        if path.is_dir():
            out.extend(sorted(path.glob("*.md")))
        else:
            out.append(path)
    return out


def audit_note(path: Path, *, strict: bool) -> AuditResult:
    result = AuditResult(path=path.resolve())
    if not path.exists():
        result.errors.append("file does not exist")
        return result
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        result.errors.append(f"cannot read as utf-8: {exc}")
        return result

    metadata, body = parse_frontmatter(text, result)
    result.metadata = metadata
    check_frontmatter(metadata, result, strict=strict)
    check_sections(body, result)
    check_ratings(metadata, body, result, strict=strict)
    check_metrics(body, result, strict=strict)
    check_media_links(body, path, result)
    check_wikilinks(body, result)
    check_template_leaks(body, result)
    return result


def parse_frontmatter(text: str, result: AuditResult) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        result.errors.append("missing YAML frontmatter fence at top of file")
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        result.errors.append("frontmatter opening fence has no closing fence")
        return {}, text
    raw = text[4:end]
    body = text[end + len("\n---") :]
    return parse_simple_yaml(raw, result), body


def parse_simple_yaml(raw: str, result: AuditResult) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    for line_no, line in enumerate(raw.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("-") and current_key:
            item = stripped[1:].strip()
            data.setdefault(current_key, [])
            if not isinstance(data[current_key], list):
                result.warnings.append(f"frontmatter line {line_no}: list item under non-list key {current_key!r}")
                data[current_key] = [data[current_key]]
            data[current_key].append(clean_scalar(item))
            continue
        if ":" not in line:
            result.warnings.append(f"frontmatter line {line_no}: cannot parse line: {line!r}")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if value == "":
            data[key] = []
        else:
            data[key] = clean_scalar(value)
    return data


def clean_scalar(value: str) -> Any:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [clean_scalar(part.strip()) for part in split_inline_list(inner)]
    if re.fullmatch(r"-?\d+", value):
        try:
            return int(value)
        except ValueError:
            return value
    if re.fullmatch(r"-?\d+\.\d+", value):
        try:
            return float(value)
        except ValueError:
            return value
    if value.lower() == "null":
        return None
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def split_inline_list(inner: str) -> list[str]:
    parts: list[str] = []
    cur: list[str] = []
    quote: str | None = None
    for ch in inner:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in {'"', "'"}:
            quote = ch
            cur.append(ch)
        elif ch == ",":
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append("".join(cur).strip())
    return parts


def check_frontmatter(metadata: dict[str, Any], result: AuditResult, *, strict: bool) -> None:
    for key in REQUIRED_FRONTMATTER:
        value = metadata.get(key)
        if value in (None, "", []):
            result.errors.append(f"missing required frontmatter field: {key}")
    rating = metadata.get("rating")
    if rating is not None:
        try:
            rating_int = int(rating)
        except (TypeError, ValueError):
            result.errors.append(f"frontmatter rating is not an integer: {rating!r}")
        else:
            if rating_int not in {1, 2, 3}:
                result.errors.append(f"frontmatter rating must be 1, 2, or 3, got {rating_int}")
    tags = metadata.get("tags")
    if tags is not None and not isinstance(tags, list):
        result.errors.append("frontmatter tags must be an inline or block list")
    for key in ("paper", "website", "github"):
        value = metadata.get(key)
        if value in (None, "", []):
            if key == "paper" or strict:
                result.errors.append(f"missing source URL: {key}")
            else:
                result.warnings.append(f"missing optional source URL: {key}")
        elif not isinstance(value, str) or not URL_RE.match(value):
            severity = result.errors if key == "paper" or strict else result.warnings
            severity.append(f"{key} should be an http(s) URL when present, got {value!r}")


def check_sections(body: str, result: AuditResult) -> None:
    for section in REQUIRED_SECTIONS:
        if section not in body:
            result.errors.append(f"missing required section: {section}")
    if "## Summary" in body:
        summary = body.split("## Summary", 1)[1].split("\n## ", 1)[0]
        if "[!summary]" not in summary:
            result.warnings.append("Summary section does not contain an Obsidian [!summary] callout")
        if len(summary.strip()) < 120:
            result.warnings.append("Summary section looks unusually short")


def check_ratings(metadata: dict[str, Any], body: str, result: AuditResult, *, strict: bool) -> None:
    ratings: dict[str, int] = {}
    fm_rating = metadata.get("rating")
    if fm_rating is not None:
        try:
            ratings["frontmatter"] = int(fm_rating)
        except (TypeError, ValueError):
            pass
    summary_match = SUMMARY_RATING_RE.search(body)
    if summary_match:
        ratings["summary"] = int(summary_match.group(1))
    else:
        (result.errors if strict else result.warnings).append("missing Summary rating line")
    final_match = FINAL_RATING_RE.search(body)
    if final_match:
        ratings["final"] = int(final_match.group(1))
    else:
        (result.errors if strict else result.warnings).append("missing final '**分数**' rating line")
    if len(set(ratings.values())) > 1:
        result.errors.append(f"rating mismatch across note: {ratings}")


def check_metrics(body: str, result: AuditResult, *, strict: bool) -> None:
    if "### Rating" not in body:
        result.errors.append("missing '### Rating' subsection")
        return
    rating_section = body.split("### Rating", 1)[1]
    first_nonempty = next((line.strip() for line in rating_section.splitlines() if line.strip()), "")
    if not first_nonempty.startswith("**Metrics**"):
        (result.errors if strict else result.warnings).append(
            "Rating section first non-empty line should be '**Metrics** (as of YYYY-MM-DD): ...'"
        )


def check_media_links(body: str, note_path: Path, result: AuditResult) -> None:
    for match in MD_IMAGE_RE.finditer(body):
        target = match.group(1).strip()
        if URL_RE.match(target):
            continue
        if target.startswith("#"):
            continue
        local = (VAULT_ROOT / target).resolve() if not target.startswith("/") else Path(target)
        if not local.exists():
            result.errors.append(f"broken local markdown media link: {target}")
    for match in OBSIDIAN_EMBED_RE.finditer(body):
        target = match.group(1).split("|", 1)[0].strip()
        candidates = [VAULT_ROOT / target, note_path.parent / target]
        if not any(candidate.exists() for candidate in candidates):
            result.warnings.append(f"could not resolve Obsidian embed locally: {target}")


def check_wikilinks(body: str, result: AuditResult) -> None:
    for match in WIKILINK_RE.finditer(body):
        content = match.group(1)
        if "[[" in content:
            result.errors.append(f"nested wikilink detected: [[{content}]]")
        if content.count("|") > 1:
            result.warnings.append(f"wikilink has more than one alias pipe: [[{content}]]")
    for line_no, line in enumerate(body.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("|") and "[[" in stripped:
            # In Markdown tables, alias pipes must be escaped as \|. Flag unescaped alias pipes.
            for content in WIKILINK_RE.findall(stripped):
                if "|" in content and "\\|" not in line:
                    result.errors.append(
                        f"line {line_no}: wikilink alias pipe inside table must be escaped as \\|"
                    )


def check_template_leaks(body: str, result: AuditResult) -> None:
    if "%%" in body:
        result.errors.append("template comment marker '%%' leaked into note body")
    if "TODO" in body or "待补充" in body:
        result.warnings.append("note contains TODO/待补充 marker")


def write_registry(path: Path, results: list[AuditResult]) -> None:
    if not path.is_absolute():
        path = (VAULT_ROOT / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "tools/paper_note_audit.py",
        "papers": [result.registry_entry() for result in results],
        "summary": {
            "total": len(results),
            "ok": sum(result.ok for result in results),
            "with_errors": sum(not result.ok for result in results),
            "warnings": sum(len(result.warnings) for result in results),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_json(results: list[AuditResult]) -> dict[str, Any]:
    return {
        "summary": {
            "total": len(results),
            "ok": sum(result.ok for result in results),
            "with_errors": sum(not result.ok for result in results),
            "warnings": sum(len(result.warnings) for result in results),
        },
        "results": [result.registry_entry() for result in results],
    }


def print_text_summary(results: list[AuditResult], *, registry_path: Path | None) -> None:
    print(
        f"Audited {len(results)} notes: "
        f"{sum(result.ok for result in results)} ok, "
        f"{sum(not result.ok for result in results)} with errors, "
        f"{sum(len(result.warnings) for result in results)} warnings"
    )
    if registry_path:
        print(f"Registry written: {registry_path}")
    for result in results:
        rel = result.path.relative_to(VAULT_ROOT).as_posix() if result.path.is_relative_to(VAULT_ROOT) else str(result.path)
        status = "OK" if result.ok else "FAIL"
        print(f"\n[{status}] {rel}")
        for error in result.errors:
            print(f"  ERROR: {error}")
        for warning in result.warnings[:8]:
            print(f"  WARN:  {warning}")
        if len(result.warnings) > 8:
            print(f"  WARN:  ... {len(result.warnings) - 8} more warnings")


if __name__ == "__main__":
    raise SystemExit(main())
