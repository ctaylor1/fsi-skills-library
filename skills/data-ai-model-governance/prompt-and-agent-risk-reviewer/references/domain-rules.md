# Domain Rules — prompt-and-agent-risk-reviewer

The control catalog and how findings map to a **recommended risk rating** and a
**recommended disposition**. Severities and mappings are configuration (versioned, owned by
AI/Model Risk Governance), not hard-coded judgments, and are never tuned to make a specific
agent pass. Orientation references: NIST AI RMF and the OWASP Top 10 for LLM Applications
(prompt injection, insecure output handling, excessive agency, etc.); the firm's AI policy
and control catalog take precedence.

## Control catalog (deterministic checks)

| Control | Severity | Fires when (undocumented control = not evidenced = gap) | Evidence attached |
| ------- | -------- | ------------------------------------------------------- | ----------------- |
| `C-INJ-01` Untrusted-input to privileged-action path | **Critical** | An untrusted input surface (declared surface, untrusted retrieval source, or untrusted-persisting memory) can reach a high-impact tool AND no injection-mediation guardrail | Surfaces + high-impact tools + guardrail flag |
| `C-INJ-02` Injection-persistent memory | High | Memory persists untrusted content AND feeds the prompt AND a high-impact tool is present | Memory block + tools |
| `C-TOOL-01` Autonomous high-impact tool without human approval | High | `autonomy = autonomous` AND a high-impact tool has no `human_approval` gate | Offending tools + autonomy |
| `C-TOOL-02` Over-broad tool scope (least privilege) | Moderate | A tool is flagged `scope_broad` (scope broader than declared purpose) | The broad-scoped tools |
| `C-GRD-01` No output guardrail/DLP for sensitive data | High | `data_classification` in {Confidential, Restricted, PII} AND no `output_filter` and no `dlp` | Classification + guardrails |
| `C-GRD-02` No prohibited-behavior guardrail | High | A `prohibited_surface` is declared AND no `prohibited_behavior_refusal` | Prohibited surfaces + guardrail |
| `C-PROMPT-01` No instruction-source boundary | Moderate | No `instruction_source_boundary` AND an untrusted surface is present | Prompt attribute + surfaces |
| `C-FAIL-01` No fail-closed / escalation on uncertainty | Moderate | Not (`fail_closed` AND `human_escalation`) | Failure-mode block |
| `C-EVAL-01` No evaluation/benchmark coverage | Moderate | No `eval_harness` wired | Observability block |
| `C-OBS-01` Insufficient tool-call audit logging | Low | Tool calls not logged (`logs_tool_calls` false) | Observability block |

High-impact tool effects: `write`, `external`, `payment`, `irreversible`. Controls are
**additive and independent**; the output reports each that fired with its own cited
evidence. There is no opaque composite "risk score".

## Rating mapping (deterministic, documented)

The recommended rating is the **highest severity among fired findings**:

| Recommended rating | Rule |
| ------------------ | ---- |
| **Critical** | any Critical finding fired |
| **High** | any High finding fired (no Critical) |
| **Moderate** | any Moderate finding fired (no High/Critical) |
| **Low** | only Low findings fired, or no findings fired |

## Disposition mapping (deterministic, documented)

| Recommended disposition | Rule |
| ----------------------- | ---- |
| **Remediate-before-deploy (recommended)** | rating Critical or High |
| **Conditional-remediation (recommended)** | rating Moderate |
| **Proceed-with-standard-controls (recommended)** | rating Low |

The rating and disposition are **recommendations for a human adjudicator**. They are not an
approval, a risk acceptance, an attestation, or a review closure, and they never authorize
deployment.

## Hard boundaries (fail closed)

- Never **approve** an agent, **accept risk**, grant an **exception/waiver**, **attest** a
  control, or **close** the review — those are human adjudications.
- Never assume an undocumented control is present; a missing control block is a **gap**
  (the dependent finding fires) recorded in `data_gaps`.
- Never tune severities or the mapping to make a specific agent pass; use only the versioned
  control catalog.
- Describe findings factually and cite the exact configuration locus; do not infer intent.

## Reviewer prompts (always include when relevant)

Compensating controls outside the spec (network isolation, downstream approval queues,
tenant sandboxing), the agent's actual blast radius, whether high-impact tools are truly
reachable from untrusted input at runtime, and whether `data_gaps` reflect a genuinely
absent control or merely an undocumented one. The pack must invite the adjudicator to weigh
these before any deployment decision.
