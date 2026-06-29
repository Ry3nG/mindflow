# Research System Upgrade Notes

This note records external systems inspected while upgrading MindFlow. The goal is not to copy their product shape, but to absorb durable practices that improve paper digest, survey, and autonomous research workflows while preserving MindFlow's Obsidian-native notes.

## Systems inspected

| System | Evidence inspected | Useful practice | What MindFlow should adopt | What not to copy |
|---|---|---|---|---|
| ResearchInfra | `qinchonghanzuibang/ResearchInfra`, local clone, tests/docs/schemas | file-first workspace, Pydantic-style schemas, dry-run CLI, source/document/claim/run lifecycle | note validator + registry; future typed `Claim`/`Evidence` objects | replacing Obsidian note layout with hidden machine folders |
| PaperQA2 | `Future-House/paper-qa`, README/code/configs | evidence-first scientific RAG: metadata-aware embeddings, LLM reranking/contextual summaries, citation traversal, citation/retraction metadata | explicit evidence ledger per digest/survey; citation traversal for related-work discovery; source snippets tied to claims | making MindFlow a generic vector-DB RAG app |
| GPT Researcher | `assafelovic/gpt-researcher`, README/default config | planner → parallel collectors → publisher; source tracking; configurable report depth/format; MCP/local-doc support | survey workflow should materialize research questions/subtopics and per-source summaries before final synthesis | optimizing for long generic web reports over durable research notes |
| Open Deep Research | `langchain-ai/open_deep_research`, README/configuration | bounded iterations/concurrency, reflection loop, compression step, evaluation against benchmark, configurable model roles | expose budgets for search breadth/depth/concurrency; add intermediate compression for long surveys; evaluate outputs with a rubric | importing heavy LangGraph runtime into the vault |
| Jina DeepResearch | `jina-ai/node-DeepResearch`, README | search → read → reason loop until answer or budget; concise answer objective; footnote citation format | use explicit stop conditions and budget exhaustion notes for targeted questions | using opaque hosted API as the source of truth |
| AI Scientist | `SakanaAI/AI-Scientist`, README | template-based experiments, literature search before ideation, generated-paper review, containerization warning | project templates for experiments; reviewer pass before promoting ideas/results | autonomous code execution without sandbox/review |
| DeerFlow | `bytedance/deer-flow`, README | setup/doctor commands, skills/subagents/sandbox/memory, deployment sizing, security notice | add `doctor`-style local health checks for MindFlow; document safe execution boundaries | turning MindFlow into a full agent platform duplicate |

## Upgrade principles

1. **Keep notes human-first, add machine checks around them.** `Papers/*.md` remains canonical for reading; registries are rebuildable indexes.
2. **Make grounding inspectable.** Claims should link to source snippets, figures, metrics, or experiments.
3. **Separate stages.** Discovery, extraction, evidence gathering, synthesis, review, and logging should be distinguishable artifacts.
4. **Use budgets explicitly.** Search breadth/depth, source count, and iteration limits should be visible in logs.
5. **Fail safely.** Missing source/metric/evidence should become warnings/errors, not fabricated prose.
6. **Prefer small stdlib tools.** MindFlow should remain usable by agents without installing a large research-agent stack.

## Adopted now

- `tools/paper_note_audit.py`: strict paper-note validation plus registry generation.
- `Workbench/registry/papers.json`: rebuildable file-first paper registry.
- `references/paper-note-validation.md`: validation policy and commands.
- `skills/1-literature/paper-digest/SKILL.md`: paper-digest now requires strict validation for new notes and registry refresh.
- `.github/workflows/paper-audit.yml`: CI checks the validator and enforces strict audit on changed paper notes.
- `tools/evidence_ledger.py` + `references/evidence-ledger.md`: claim-to-evidence ledgers for new/updated paper notes.
- `tools/mindflow_doctor.py`: local doctor checks for registry, required paths, audit tool availability, and owner-identity leftovers.

## Next high-value upgrades

### 1. Survey packet before synthesis

For `literature-survey`, create `Workbench/surveys/<Topic>/packet.json`:

- research question
- subquestions
- search queries tried
- candidate papers with inclusion/exclusion reason
- per-source summary
- contradictions/open problems
- final report link

This borrows GPT Researcher/Open Deep Research's planner/collector/publisher split without adopting their runtime.

### 2. Reviewer pass for promoted research ideas

Before moving an idea/result to a high-confidence state, run a reviewer checklist inspired by AI Scientist/Open Deep Research:

- novelty vs related work,
- falsifiability,
- experimental support,
- ablations/failure cases,
- evidence coverage,
- overclaim detection.
