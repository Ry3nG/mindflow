import json
import tempfile
import unittest
from pathlib import Path


class EvidenceLedgerTests(unittest.TestCase):
    def test_build_skeleton_from_note_metadata_and_sources(self):
        from tools.evidence_ledger import build_ledger_skeleton

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            note = root / "Papers" / "2605-Example.md"
            note.parent.mkdir(parents=True)
            note.write_text(
                "---\n"
                "title: Example Paper\n"
                "paper: https://arxiv.org/abs/2605.00001\n"
                "website: https://example.org/project\n"
                "github: https://github.com/example/project\n"
                "rating: 2\n"
                "---\n"
                "\n## Summary\nBody\n\n## Method\nClaim text\n",
                encoding="utf-8",
            )

            ledger = build_ledger_skeleton(note, root=root)

        self.assertEqual(ledger["schema_version"], "0.1")
        self.assertEqual(ledger["paper"], "Papers/2605-Example.md")
        self.assertEqual(ledger["title"], "Example Paper")
        self.assertEqual(
            [source["kind"] for source in ledger["sources"]],
            ["paper", "website", "github"],
        )
        self.assertEqual(ledger["claims"], [])

    def test_validate_ledger_requires_claim_evidence_quotes(self):
        from tools.evidence_ledger import validate_ledger

        good = {
            "schema_version": "0.1",
            "paper": "Papers/2605-Example.md",
            "title": "Example Paper",
            "sources": [{"id": "paper", "kind": "paper", "url": "https://arxiv.org/abs/2605.00001"}],
            "claims": [
                {
                    "claim": "The method improves success rate.",
                    "note_section": "## Experiments",
                    "evidence": [
                        {
                            "source": "paper",
                            "section": "Experiments",
                            "quote": "success rate improves from 50 to 60",
                        }
                    ],
                }
            ],
        }
        bad = json.loads(json.dumps(good))
        bad["claims"][0]["evidence"][0]["quote"] = ""

        self.assertEqual(validate_ledger(good).errors, [])
        self.assertIn("claims[0].evidence[0].quote is required", validate_ledger(bad).errors)

    def test_validate_ledger_can_require_nonempty_claims(self):
        from tools.evidence_ledger import validate_ledger

        skeleton = {
            "schema_version": "0.1",
            "paper": "Papers/2605-Example.md",
            "title": "Example Paper",
            "sources": [{"id": "paper", "kind": "paper", "url": "https://arxiv.org/abs/2605.00001"}],
            "claims": [],
        }

        self.assertEqual(validate_ledger(skeleton).errors, [])
        self.assertIn("claims must contain at least one item", validate_ledger(skeleton, require_claims=True).errors)


class DoctorTests(unittest.TestCase):
    def test_doctor_reports_missing_registry_and_owner_leftover(self):
        from tools.mindflow_doctor import run_checks

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Papers").mkdir()
            (root / "Workbench").mkdir()
            (root / "AGENTS.md").write_text("Owner: Qing Li\n", encoding="utf-8")
            (root / "Papers" / "2605-Example.md").write_text(
                "---\ntitle: Example\npaper: https://arxiv.org/abs/2605.1\nrating: 2\n---\n\n## Summary\n",
                encoding="utf-8",
            )

            report = run_checks(root=root)

        by_id = {check.id: check for check in report.checks}
        self.assertEqual(by_id["registry-exists"].status, "fail")
        self.assertEqual(by_id["owner-identity"].status, "warn")
        self.assertIn("Qing Li", by_id["owner-identity"].message)

    def test_doctor_passes_registry_when_paper_count_matches(self):
        from tools.mindflow_doctor import run_checks

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Papers").mkdir(parents=True)
            registry = root / "Workbench" / "registry" / "papers.json"
            registry.parent.mkdir(parents=True)
            (root / "Papers" / "2605-Example.md").write_text("---\ntitle: Example\n---\n", encoding="utf-8")
            registry.write_text(
                json.dumps({"summary": {"total": 1}, "papers": [{"path": "Papers/2605-Example.md"}]}),
                encoding="utf-8",
            )

            report = run_checks(root=root)

        by_id = {check.id: check for check in report.checks}
        self.assertEqual(by_id["registry-exists"].status, "pass")
        self.assertEqual(by_id["registry-count"].status, "pass")


if __name__ == "__main__":
    unittest.main()
