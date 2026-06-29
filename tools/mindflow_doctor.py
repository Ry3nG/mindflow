#!/usr/bin/env python3
"""MindFlow repository health checks with actionable output."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

VAULT_ROOT = Path(__file__).resolve().parents[1]
Status = Literal["pass", "warn", "fail"]


@dataclass
class Check:
    id: str
    status: Status
    message: str
    fix: str | None = None


@dataclass
class DoctorReport:
    root: Path
    checks: list[Check]

    @property
    def failures(self) -> int:
        return sum(check.status == "fail" for check in self.checks)

    @property
    def warnings(self) -> int:
        return sum(check.status == "warn" for check in self.checks)


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve() if args.root else VAULT_ROOT
    report = run_checks(root=root)
    if args.json:
        print(json.dumps(report_to_json(report), ensure_ascii=False, indent=2))
    else:
        print_report(report)
    return 1 if report.failures else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MindFlow health checks.")
    parser.add_argument("--root", help="Vault root. Defaults to the current MindFlow repo inferred from this script.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    return parser.parse_args()


def run_checks(*, root: Path = VAULT_ROOT) -> DoctorReport:
    root = root.resolve()
    checks: list[Check] = []
    checks.extend(check_required_paths(root))
    checks.extend(check_registry(root))
    checks.append(check_owner_identity(root))
    checks.append(check_audit_tool(root))
    return DoctorReport(root=root, checks=checks)


def check_required_paths(root: Path) -> list[Check]:
    required = ["Papers", "Workbench", "skills", "references", "tools/paper_note_audit.py"]
    checks: list[Check] = []
    for rel in required:
        path = root / rel
        if path.exists():
            checks.append(Check(f"path:{rel}", "pass", f"{rel} exists"))
        else:
            checks.append(Check(f"path:{rel}", "fail", f"{rel} is missing", f"Restore or create {rel}"))
    return checks


def check_registry(root: Path) -> list[Check]:
    registry = root / "Workbench" / "registry" / "papers.json"
    papers = sorted((root / "Papers").glob("*.md")) if (root / "Papers").exists() else []
    if not registry.exists():
        return [
            Check(
                "registry-exists",
                "fail",
                "Workbench/registry/papers.json is missing",
                "Run: python3 tools/paper_note_audit.py --all --write-registry Workbench/registry/papers.json",
            )
        ]
    checks = [Check("registry-exists", "pass", "Workbench/registry/papers.json exists")]
    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        checks.append(Check("registry-json", "fail", f"registry JSON is invalid: {exc}"))
        return checks
    count = data.get("summary", {}).get("total")
    if count == len(papers):
        checks.append(Check("registry-count", "pass", f"registry total matches Papers/*.md count ({count})"))
    else:
        checks.append(
            Check(
                "registry-count",
                "warn",
                f"registry total {count} does not match Papers/*.md count {len(papers)}",
                "Refresh registry with: python3 tools/paper_note_audit.py --all --write-registry Workbench/registry/papers.json",
            )
        )
    return checks


def check_owner_identity(root: Path) -> Check:
    candidates = [root / "AGENTS.md", root / "README.md", root / "index.md"]
    hits: list[str] = []
    pattern = re.compile(r"Dr\. Li|Dr Li|Qing Li|李庆")
    for path in candidates:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if pattern.search(text):
            hits.append(path.relative_to(root).as_posix())
    if hits:
        return Check(
            "owner-identity",
            "warn",
            "Qing Li / Dr Li owner references remain in: " + ", ".join(hits),
            "If this local vault is Zerui-owned, update runtime identity files; do not rewrite historical paper/spec authors blindly.",
        )
    return Check("owner-identity", "pass", "No Qing Li / Dr Li owner references in runtime identity files")


def check_audit_tool(root: Path) -> Check:
    tool = root / "tools" / "paper_note_audit.py"
    if not tool.exists():
        return Check("audit-tool", "fail", "tools/paper_note_audit.py missing")
    text = tool.read_text(encoding="utf-8", errors="ignore")
    if "def audit_note" in text and "def write_registry" in text:
        return Check("audit-tool", "pass", "paper audit tool exposes audit_note and write_registry")
    return Check("audit-tool", "fail", "paper audit tool missing expected functions")


def report_to_json(report: DoctorReport) -> dict[str, object]:
    return {
        "root": str(report.root),
        "summary": {"failures": report.failures, "warnings": report.warnings, "total": len(report.checks)},
        "checks": [check.__dict__ for check in report.checks],
    }


def print_report(report: DoctorReport) -> None:
    print(f"MindFlow doctor: {report.root}")
    print(f"Summary: {report.failures} failures, {report.warnings} warnings, {len(report.checks)} checks")
    for check in report.checks:
        marker = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}[check.status]
        print(f"[{marker}] {check.id}: {check.message}")
        if check.fix:
            print(f"       fix: {check.fix}")


if __name__ == "__main__":
    raise SystemExit(main())
