# Controls — payment-fraud-rule-impact-analyzer

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `required` — for any rule deployment/enablement or live block/allow decision.

## Prohibited (fail closed)
- No **deploying, enabling, or rolling out** a rule.
- No **block/allow decision** on any live transaction or customer.
- No **guessed evaluation** for an unsupported operator/field; no imputed labels.
- No **one-sided tradeoff** — fraud-catch and false-positive effects are both reported.

## Required output screen (`scripts/validate_output.py`)
- Confusion-matrix cells sum to the labeled sample size, for both current and proposed.
- No deployment/live-decision language (regex: deployed the rule/rolled out/enable…in
  production/we blocked/block this customer/deny the transaction).
- Standing disclaimer present (sample estimate, not a deployment or a decision).

## Segregation of duties
The analyst estimating impact is not the deployment approver; the estimate supports, never
replaces, the change/deployment process.

## Data classification, privacy, records
- **Highly Confidential (cardholder data / PCI + NPI/PII).** Reference txns by id; never echo PAN.
- Retain estimate + sample reference + rule versions; log read + external-delivery approval.

## Reproducibility
`analysis_id` binds output to the exact sample and rule versions; computation is deterministic
and stdlib-only.
