# Adjacent-Skill Handoffs — financial-statement-audit-assistant

This skill **drafts audit support working papers** (tie-outs, sampling, testing evidence,
misstatement accumulation, issue tracking). It does not close the audit, form the opinion,
or package the final evidence file — those are separate control activities and separate
skills or human roles.

## Upstream (feeds this skill)

| Upstream source | Provides | Handoff artifact |
| --------------- | -------- | ---------------- |
| `month-end-close-orchestrator` | A locked, completed period close to audit against | Final trial balance + close status |
| `gl-reconciler` | GL-to-subledger reconciliations underlying the tie-out base | Reconciled balances + break status |
| `financials-normalizer` | Normalized/mapped financial-statement captions | Caption → account mapping |

## Downstream / parallel (this skill routes to)

| Skill / role | When | Handoff artifact |
| ------------ | ---- | ---------------- |
| `audit-evidence-packager` | Collecting, indexing, redacting, and cross-referencing the supporting evidence file with chain of custody | Working-paper draft + source citations |
| `fpa-variance-analyzer` | Substantive analytical procedures / investigating a variance vs. expectation | Caption + comparatives + expectation |
| `valuation-reviewer` | Testing a fair-value estimate or valuation input | Estimate + basis + support |
| `regulatory-reporting-data-validator` | A filed-return figure disagrees with the GL and needs data-quality review | Both figures + the discrepancy |
| `management-reporting-packager` | Findings need to be summarized into a management/audit-committee pack | Cited findings + misstatement summary |

## Human / licensed-specialist handoffs (not skills)

- **Forming or expressing the audit opinion**, concluding on fair presentation, materiality
  sufficiency, or **going concern** → the **engagement partner / licensed auditor**. This
  skill never does this and has no downstream skill for it — it is a human judgment.
- **Approving reliance or external delivery** of the working paper → the **engagement
  partner** (recorded approval before any issuance).
- **ICFR / SOX control-effectiveness opinions** → the engagement's controls-testing lead
  (out of scope here).

## Duplicate-execution prevention

- This skill produces a **draft**; it does not re-perform reconciliation
  (`gl-reconciler`), variance investigation (`fpa-variance-analyzer`), or evidence-file
  assembly (`audit-evidence-packager`). It cites their outputs rather than recomputing them.
- The engagement partner's opinion is a human deliverable consumed *from* this draft; the
  draft is never promoted to a conclusion here.
