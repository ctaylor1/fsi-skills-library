# Domain Rules — agent-audit-trail-reviewer

The explainable **control checks**, their **deterministic severity**, and how the fired set
maps to a **triage disposition band**. Thresholds and control requirements are configuration
(versioned, owned by AI/model-risk governance), not per-run judgments, and are never tuned to
make a run look better or worse. Orientation references: the firm's AI/agent governance
standard, SR 11-7 model-risk expectations, and NIST AI RMF (Govern/Measure/Manage) take
precedence.

## Check taxonomy

Checks fall in two families: **reproducibility** (can the run be re-derived from the trail?)
and **control effectiveness** (did the required controls operate?).

| Finding type | Control domain | Fires when | Evidence attached |
| ------------ | -------------- | ---------- | ----------------- |
| `reproducibility_gap` | reproducibility | A `config.required_repro_fields` entry is missing/empty in the run header (default set: model_id, model_version, prompt_version, config_version) | Run header + missing field list |
| `evidence_traceability_gap` | traceability | A `retrieval` event has no `citation` to its source | The retrieval event |
| `out_of_scope_tool` | least-privilege | A `tool_call` uses a tool not in `config.allowed_tools` | The tool_call event |
| `missing_approval` | human-oversight | A gated `tool_call` (`approval_required` true, or `action_class` in `approval_required_action_classes`) with `action_class` = `write` has no matching approved `approval` event | The tool_call event |
| `prohibited_autonomous_action` | human-oversight | A gated `tool_call` with `action_class` = `decision` (a regulated decision) has no matching approved `approval` event | The tool_call event |
| `after_the_fact_approval` | human-oversight | An `approval` for a tool_call is timestamped **after** the action executed | The approval event |
| `self_approval` | segregation-of-duties | The `approval.approver` is the agent itself (`agent` or the `agent_id`) | The approval event |
| `unauthorized_override` | human-oversight | An `override` of a guardrail/approval has a non-`human` `actor` | The override event |
| `retention_gap` | records-retention | A `config.required_retained_objects` entry has no `retention` event with `retained` true | Retention expectation (object) |
| `logging_gap` | logging-integrity | Duplicate `event_id`s, or events not in non-decreasing timestamp order | The log as a whole |

Checks are **additive and independent**; each fired check is reported with its own evidence.
There is no opaque composite "compliance score".

## Severity mapping (deterministic)

| Severity | Finding types |
| -------- | ------------- |
| **high** | `prohibited_autonomous_action`, `unauthorized_override`, `self_approval` |
| **medium** | `missing_approval`, `after_the_fact_approval`, `out_of_scope_tool`, `retention_gap` |
| **low** | `evidence_traceability_gap`, `reproducibility_gap`, `logging_gap` |

## Disposition mapping (deterministic, documented)

| Suggested band | Rule |
| -------------- | ---- |
| **No exceptions noted** | 0 findings |
| **Review** | ≥ 1 finding, but no high finding and fewer than 3 medium findings |
| **Escalate** | ≥ 1 high finding, OR ≥ 3 medium findings |

The disposition is a **triage suggestion for a human adjudicator**. It is not a control
attestation, a compliance determination, or a closure, and it never triggers a filing or a
system-of-record write.

## Hard boundaries (fail closed)

- Never state or imply that a control **is/was effective**, that the run **passed the audit**,
  or that the agent **is compliant** — describe control operation factually and attribute any
  conclusion to the human adjudicator.
- Never **close, file, log, certify, or sign off** a finding or issue.
- Never tune severity/disposition to the individual run; use only the versioned config.
- Treat **absence of an event as a finding to adjudicate**, not as proof a control operated.

## Benign-explanation prompts (always include when any finding fired)

An approval logged out-of-band in a separate system; a retention record captured in a
different retention store; a tool intentionally in scope but missing from this run's
`allowed_tools`; a reproducibility field held in the registry rather than the run header; a
timestamp skew between the log and the approval system. The pack must invite the reviewer to
reconcile these before adjudicating.
