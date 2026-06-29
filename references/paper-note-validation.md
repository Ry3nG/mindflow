# Paper Note Validation & Registry

MindFlow keeps the high-quality Obsidian-native `Papers/` workflow, but adopts one ResearchInfra best practice: **generated research artifacts should be machine-auditable and mirrored into a small file-first registry**.

## Tool

```bash
python3 tools/paper_note_audit.py Papers/2605-MolmoAct2.md --strict
```

The auditor is stdlib-only and checks:

- required frontmatter: `title`, `authors`, `date_publish`, `venue`, `tags`, `paper`, `rating`, `date_added`
- source URL shape for `paper` / `website` / `github`
- required sections: `## Summary`, `## 关联工作`, `## 论文点评`, `### Rating`
- rating consistency across frontmatter, Summary, and final Rating section
- `**Metrics** (as of YYYY-MM-DD): ...` at the start of `### Rating`
- local media links under `Papers/assets/...`
- wikilink syntax pitfalls, including unescaped alias pipes inside Markdown tables
- leaked template comments such as `%% ... %%`

## Registry

To materialize a ResearchInfra-style registry without changing the Obsidian note layout:

```bash
python3 tools/paper_note_audit.py --all --write-registry Workbench/registry/papers.json
```

The registry is derived data. It records per-note metadata and audit status:

```json
{
  "schema_version": "0.1",
  "generated_at": "...",
  "generator": "tools/paper_note_audit.py",
  "papers": [
    {
      "path": "Papers/2605-MolmoAct2.md",
      "title": "...",
      "tags": ["VLA", "manipulation"],
      "rating": 2,
      "paper": "https://...",
      "audit": {"ok": true, "errors": [], "warnings": []}
    }
  ]
}
```

## Policy

- Use `--strict` for newly generated notes and notes being updated.
- Use non-strict `--all` for legacy vault audits, because older notes may predate current digest rules.
- Treat the registry as rebuildable from `Papers/*.md`; do not hand-edit it.
- Do not weaken the paper-digest writing standard to fit the validator. Fix the note or improve the validator with an explicit rule.

## ResearchInfra best practice adopted

This mirrors ResearchInfra's strengths without replacing MindFlow's native notebook layout:

- typed-ish checks before trusting generated artifacts,
- explicit source/evidence metadata,
- file-first registry that agents can inspect cheaply,
- safe failure: warnings/errors are written instead of silently accepting malformed notes.
