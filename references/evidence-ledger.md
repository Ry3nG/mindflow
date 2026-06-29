# Evidence Ledger Protocol

MindFlow paper notes stay human-readable in `Papers/*.md`, but important claims should also have a small machine-readable evidence ledger. This borrows the best part of PaperQA2 and ResearchInfra: **answers/notes should be traceable to source spans, figures, tables, or metrics**.

## Commands

Create a skeleton from paper note frontmatter:

```bash
python3 tools/evidence_ledger.py init Papers/2605-MolmoAct2.md
```

This writes by default:

```text
Workbench/evidence/MolmoAct2.json
```

Validate a completed ledger:

```bash
python3 tools/evidence_ledger.py validate Workbench/evidence/MolmoAct2.json --require-claims
```

`--require-claims` should be used for new or updated digests. Without it, skeleton ledgers are allowed so agents can create the file before filling evidence.

## Schema

```json
{
  "schema_version": "0.1",
  "generated_at": "2026-06-29T...Z",
  "paper": "Papers/2605-MolmoAct2.md",
  "title": "MolmoAct2: Action Reasoning Models for Real-world Deployment",
  "sources": [
    {"id": "paper", "kind": "paper", "url": "https://arxiv.org/abs/..."},
    {"id": "website", "kind": "website", "url": "https://..."},
    {"id": "github", "kind": "github", "url": "https://github.com/..."}
  ],
  "claims": [
    {
      "claim": "Per-layer KV conditioning improves LIBERO by 1.9 points.",
      "note_section": "## 6.5 关键消融",
      "evidence": [
        {
          "source": "paper",
          "section": "Ablations",
          "quote": "...",
          "figure": null,
          "table": "Table 9"
        }
      ]
    }
  ]
}
```

## What deserves a claim entry

Add entries for claims that would matter in a survey or project decision:

- main method claims,
- quantitative result claims,
- ablation conclusions,
- dataset scale / data-mixture statements,
- artifact availability claims,
- caveats/failure modes used in your critique.

Do **not** add entries for trivial prose, section transitions, or obvious bibliographic metadata already captured in frontmatter.

## Evidence rules

Each claim needs at least one evidence item with one of:

- `quote`: short copied span from `paper.md`, `website.md`, `github.md`, or a PDF/HTML source,
- `figure`: figure id/path if the claim is visually supported,
- `table`: table id/name if the claim comes from a table.

Prefer `quote` + `table/figure` for quantitative claims. Keep quotes short enough to audit quickly.

## Policy

- New/updated paper digests must pass `validate --require-claims`.
- Legacy notes can lack ledgers until touched.
- If evidence cannot be found, weaken the note claim instead of inventing support.
- Ledgers are not a second note; they are audit scaffolding for high-value claims.
