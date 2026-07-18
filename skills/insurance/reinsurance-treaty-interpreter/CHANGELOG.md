# Changelog — reinsurance-treaty-interpreter

All notable changes to this skill package. Versions follow semver in `aws-fsi-version`.

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** informational, read-only plain-language interpretation of one reinsurance treaty
  (attachment, per-occurrence and aggregate limits, exclusions, reinstatements, reporting/notice
  conditions), with clause-level citations and an optional illustrative ceded-recovery
  calculation under the excess-of-loss layer terms.
- **Triggers:** positive (interpret this treaty / where does the layer attach and what is the
  limit / how do reinstatements work / illustrate the ceded recovery); negative (binding
  recoverability determination — "is this claim recoverable and how much will the reinsurer
  pay") with routing to adjacent skills and the ceded-claims function.
- **Controls:** R2; no coverage/recoverability determination on a real claim and no
  legal/actuarial/accounting advice (deterministic language screen), no treaty-term invention,
  no merging of treaties/layers/periods; external-delivery human approval.
- **Domain rules:** excess-of-loss attachment and per-occurrence limit; reinstatements and the
  band-method reinstatement premium (pro rata as to amount); aggregate limit =
  `limit × (1 + reinstatements)`; exclusions do not attach or erode; occurrence/hours-clause
  and reporting conditions; canonical layer arithmetic with a worked example.
- **Tools/data:** read-only reinsurance-contract/treaty register, claims and
  policy-administration (loss bordereaux), document-intelligence, actuarial/catastrophe data;
  durable `interpretation_id`.
- **Scripts:** `validate_input.py` (treaty/layer/clause schema, dates, citation coverage,
  data-quality warnings), `calculate_or_transform.py` (per-occurrence layer-loss, ceded
  recovery, limit erosion, reinstatement premium, normalized interpretation object), and
  `validate_output.py` (completeness, citation coverage, layer-arithmetic tie-out, no-advice /
  no-determination screen, disclaimer presence).
- **Evaluations:** trigger/routing, golden normal + multi-treaty edge, deterministic script
  checks, no-advice/no-determination safety fixture (fails closed), prompt-injection,
  external-delivery authorization.
- **Handoffs:** downstream to `policy-wording-comparator`, `reserving-analysis-assistant`,
  `catastrophe-exposure-monitor`, `claims-file-reviewer`, and `policy-document-explainer`;
  binding recoverability, collection, commutation, and contested-wording interpretation are
  reframed as human ceded-claims / reinsurance-counsel handoffs (no catalog skill invented).

### Pending before release
- Domain SME + control-owner blind review; accessibility review of the output format.
- Wire read-only MCP integrations (treaty register, claims/bordereaux, document-intelligence,
  actuarial/catastrophe data) at deployment.
- With/without benchmark vs. no-skill baseline; jurisdiction packs beyond US default.
