# Changelog — senior-investor-protection-screener

## 0.3.0 — 2026-10-04

- Add detached field review and exact-recipient draft gates; preserve unknown observations and distinguish recording from professional review.

## [0.2.0] — 2026-09-16
- Adopt the wealth-p0-v1 source/context contract and input-bound draft identity.
- Bound baselines by as-of/lookback and pre-focal timestamps; enforce coverage and limits.
- Preserve unknown observations/applicability, avoid automatic negative conclusions, and
  separate trusted-contact administration from exploitation concern counts.
- Reject empty/tampered/false-ready outputs by recomputing the structured artifact.
- Add 26 executed regressions, revised fixtures, minimized snapshot contract and draft template.
- Replace obsolete recommendation-reviewer handoff naming and remove production-default claims.

### Independent review repairs
- Require transaction lifecycle explicitly. Historical baselines and executed outflow use executed
  records only; proposed/pending focal requests retain concern screening without claiming execution.
- Add four lifecycle regressions covering proposed focal activity, nonexecuted baseline exclusions,
  absent/invalid lifecycle and separate actual outflow alongside a pending request.

### Release status
Deterministic checks implemented. Institutional SME/control/fairness acceptance, independent
behavior evaluation and production connector/source approval remain pending. Rule references
were read 2026-09-16; metadata recertification is not evidence of deployment approval.

## Historical authoring record

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable senior-investor concern signals + cited evidence + a suggested review
  disposition (Monitor / Review / Escalate). Read-only, R3 decision support; no determination,
  no hold, no filing, no trusted-contact outreach, no case closure, no advice.
- **Signals (deterministic):** unusual_disbursement, new_external_payee, rapid_liquidation,
  account_or_beneficiary_change, trusted_contact_gap, third_party_influence,
  capacity_concern_indicators (observed indicators only), communication_red_flags — each
  explainable and evidenced (see `scripts/calculate_or_transform.py`). Specified-adult status
  is recorded as context, not a concern signal.
- **Controls:** R3 with mandatory human adjudication; hard boundary against exploitation/
  capacity determinations, Rule 2165 holds, freezes/releases, SAR/APS filings, trusted-contact
  contact, and case closure; versioned-config thresholds only; benign-explanation prompts
  required; standing disclaimer enforced.
- **Scripts:** `validate_input` (case-file schema, evaluability warnings), the signal engine
  with a `--selftest` invariant check, `validate_output` (evidence/citation completeness,
  deterministic disposition tie-out, prohibited determination/decision/filing/closure screen,
  disclaimer, benign prompts). Non-compliant fixture fails closed.
- **Evaluations:** trigger/routing, golden Escalate case, thin-baseline and missing-observation
  edges, deterministic script checks, no-determination safety + injection, human-adjudication
  authorization.
- **Handoffs:** downstream to `suspicious-activity-report-drafter`, `investment-recommendation-evidence-reviewer`,
  `vulnerable-customer-support-assistant`, `complaint-resolution-assistant`,
  `client-review-preparer`; human handoffs to supervisor/compliance, BSA/AML officer, APS/
  regulator, and licensed advisor/legal.

### Pending before release
- Domain SME (senior-protection / compliance) + control-owner blind review; fairness review of
  the behavioral-observation signals.
- Confirm the versioned threshold/disposition config source and its owner, and the
  jurisdiction packs beyond US (Rule 2165 / NASAA Model Act variants).
- Wire read-only MCP integrations (OMS/portfolio, CRM, planning engine, reference data, config)
  at deployment.
