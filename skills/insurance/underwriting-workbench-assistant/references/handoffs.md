# Adjacent-Skill Handoffs — underwriting-workbench-assistant

Compiling the underwriter-ready risk profile (this skill) is **decision support**. The
underwriting **decision** — accept, quote, decline, bind, issue — is a regulated act that
belongs to a licensed human underwriter and is out of scope here.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `submission-intake-triager` | Ingested, normalized, appetite-triaged submission and exposure data | Normalized submission + exposure record |

The intake triager extracts and reconciles the submission; this skill compiles the
multi-source risk profile and drafts rationale on top of it. The triager does not compile the
profile or draft rationale; this skill does not re-ingest broker documents.

## Downstream / adjacent (this skill routes to)

| Target | When | Handoff artifact |
| ------ | ---- | ---------------- |
| **Human underwriter (licensed)** | Always — the accept/quote/decline/bind decision | `workbench_id` + compiled profile + draft rationale (pending adjudication) |
| `catastrophe-exposure-monitor` | `UW-CAT-ACCUM` fires (accumulation at/above threshold) | `workbench_id` + catastrophe evidence |
| `reinsurance-treaty-interpreter` | `UW-CAPACITY` fires (requested limit above authority) | `workbench_id` + requested-limit evidence |
| `coverage-gap-analyzer` | Coverage adequacy vs. exposures needs review | insured needs + exposure summary |
| `policy-wording-comparator` | Manuscript / form wording must be checked against filed forms | form references |
| `policy-renewal-reviewer` | Submission is a renewal needing expiring-vs-proposed comparison | prior + proposed terms |
| `reserving-analysis-assistant` | Reserve / loss-development context is needed for pricing input | loss history reference |

Adverse third-party flags (`UW-THIRD-PARTY`) route to the firm's referral authority /
financial-crime specialist as a human handoff; this skill flags, it does not adjudicate
sanctions or fraud.

## Duplicate-execution prevention

- This skill does **not** ingest raw broker submissions (that is the intake triager) and does
  **not** make the underwriting decision (that is the human underwriter).
- The underwriter consumes the `workbench_id` profile rather than recompiling it.
- Catastrophe, capacity, wording, and reserving questions are routed to their owning skills
  rather than answered here, so each control activity runs once in its own lane.
