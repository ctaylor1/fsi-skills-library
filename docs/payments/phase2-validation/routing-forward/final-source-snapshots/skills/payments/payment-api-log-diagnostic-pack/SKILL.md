---
name: payment-api-log-diagnostic-pack
description: >-
  Analyze payment-gateway API logs for a failing integration — classify error codes against the
  documented cause taxonomy, aggregate failures by category and endpoint, identify the top
  failing endpoint and the most-frequent category (not a causal conclusion), and assemble a redacted diagnostic
  evidence pack with suggested next checks for a payments implementation engineer. Use when an
  engineer asks to "diagnose these payment API errors", "why are these charges failing",
  "classify the gateway error codes", or "build a diagnostic pack from these logs". HARD
  BOUNDARY: R2 read-only investigation — it NEVER changes configuration, rotates keys, disables
  rules, deploys a fix, or auto-remediates; it evidences and suggests checks only. All cardholder
  data (PAN) is redacted; the output is screened for leakage. Routes go-live packaging to
  payment-integration-readiness-reviewer.
license: MIT
compatibility: Python 3.10+ offline JSON analysis. Expected source-system integrations must be supplied by deployment; no connectors or actions bundled.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Payments implementation engineer"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-17"
---

# Payment API Log Diagnostic Pack

## Purpose and outcome
Given payment-gateway API log entries, deterministically classify each error against the
documented cause taxonomy, aggregate failures by category and endpoint, identify the top failing
endpoint and the most-frequent category (not a causal conclusion), and assemble a **redacted** diagnostic evidence
pack with suggested next checks. A successful output lets an engineer investigate — no
configuration is changed and no fix is deployed by this skill.

## Use when
- "Diagnose these payment API errors", "why are these charges failing".
- "Classify the gateway error codes", "build a diagnostic pack from these logs".
- An engineer needs a consistent, redacted failure-analysis bundle.

## Do not use
- The user wants you to **change config, rotate keys, disable a rule, or deploy a fix** → out of
  scope; a human acts.
- The task is **go-live readiness** packaging → route to `payment-integration-readiness-reviewer`.
- The task is **fraud-rule impact** → `payment-fraud-rule-impact-analyzer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a diagnostic pack with a durable
`diagnostic_id`; it does not remediate.

## Inputs and prerequisites
- The **integration** context, an error **taxonomy** (code→category map), and **log_entries**
  (ts, endpoint, http_status, error_code, message, request_id). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Error-taxonomy config — a versioned contract. See
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Gateway/API logs are the evidence;
taxonomy from versioned config. Cite aggregates to the classified entries.

## Workflow
1. **Validate input** — run `validate_input`; confirm log entries and a taxonomy are present.
2. **Analyze (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): **redact PAN**,
   classify each entry, aggregate by category and endpoint, pick the top endpoint and most-frequent category, and map categories to suggested next checks.
3. **Assemble the pack** — counts, top endpoint, most-frequent category, next checks, redacted samples.
4. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for the
   **PAN-leakage screen**, the no-remediation screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If any unredacted PAN pattern remains, or the
text contains remediation/config-change language, **fix or fail closed**.

## Human approval
`external-delivery`: the pack may be produced for investigation, but external delivery requires
human sign-off, and no configuration is ever changed by this skill.

## Failure handling
- **Unknown error code** → classify as `unclassified` and count it; never guess a category.
- **PAN or cardholder data in a message** → redact before any aggregation or output; if
  redaction cannot be confirmed, fail closed.
- **Empty/garbled logs** → report coverage honestly; do not infer failures that are not logged.
- **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — integration (masked), total failures, top endpoint, most-frequent category.
2. **Breakdown** — counts by category and by endpoint.
3. **Next checks** — deterministic, per observed category (all human-performed).
4. **Machine-readable** — aggregates + redacted sample entries + `diagnostic_id`.
5. **Standing disclaimer** — "Diagnostic evidence only; no configuration has been changed, no key
   rotated, and no fix deployed. Cardholder data is redacted."
See [references/controls.md](references/controls.md).

## Privacy and records
Cardholder data (PCI) + NPI/PII. **Redact PAN** (13–19 digit sequences) everywhere. Retain the
redacted pack + citations + taxonomy version. Log read + external-delivery approval. Never
exfiltrate cardholder data.

## Gotchas
- **Correlation is not cause.** The most-frequent category does not establish a cause; the engineer
  confirms.
- **Redaction first**: never aggregate or print a message until PAN is redacted.
- **Unclassified codes are signal** — surface them, do not force them into a bucket.
- **Never suggest a remediation as an action taken** — suggested checks are for a human to run.

## Phase 1 implementation boundary

Phase 1 boundary: the calculator categorizes supplied log entries; no success denominator, retry-chain/lifecycle reconstruction or causal incident analysis is implemented. Counts are not an authorization failure rate and most-common error is not proven root cause. A service-incident investigator is later-phase work.

Read [references/payment-contract.md](references/payment-contract.md) for shared lifecycle, evidence and handoff semantics.
