<!--
RCSA package template (RCSA-PKG-v1) for risk-control-self-assessment-assistant.
This is a DRAFT deliverable for human review. Every section below is REQUIRED and is
enforced by scripts/validate_output.py (section keys: assessment_scope,
risk_and_control_assessment, residual_risk_summary, evidence_map, challenges_and_gaps,
remediation_plan, approvals). Do not delete sections; mark "None" where empty. Do not
record an approval as obtained unless a named human approver and date are captured.
-->

# Risk & Control Self-Assessment (RCSA) — DRAFT

> DRAFT prepared for first-line and independent human review only. No assessment sign-off,
> independent challenge, control attestation, or risk-acceptance decision has been made by
> the assistant, and nothing has been written to the GRC system of record.

## 1. Assessment scope
| Field | Value |
| ----- | ----- |
| Entity / process | `{entity}` |
| Assessment period | `{from}` – `{to}` |
| As-of date | `{as_of_date}` |
| Risk appetite (max residual) | `{risk_appetite}` |
| Scoring config version | `{config_version}` |

## 2. Risk & control assessment
For each risk: inherent score (impact × likelihood → band), mapped controls with design /
operating / overall effectiveness, and residual band after control mitigation. Every
credited (Effective / Partially Effective) control MUST cite evidence — see §4.

| Risk ID | Statement (challenged) | Inherent (I×L → band) | Key control(s) | Control effectiveness | Residual band | Within appetite |
| ------- | --------------------- | --------------------- | -------------- | --------------------- | ------------- | --------------- |
| `{risk_id}` | `{statement}` | `{impact}×{likelihood} → {inherent_band}` | `{control_id}` | `{overall_effectiveness}` | `{residual_band}` | `{yes/no}` |

## 3. Residual risk summary
- Total risks: `{total_risks}`
- Residual distribution: Low `{n}` / Medium `{n}` / High `{n}` / Critical `{n}`
- Above appetite: `{above_appetite}`
- Open remediation items: `{remediation_items}`
- Evidence gaps: `{evidence_gaps}`

## 4. Evidence map
Every credited control effectiveness conclusion traces to a dated, referenced source
(control test, KRI, loss event, attestation). Unevidenced ratings are shown as
"Unsubstantiated" in §2 and listed as gaps in §5 — they are NOT credited toward residual.

| Risk ID | Control ID | Evidence type | Reference | Date | Result |
| ------- | ---------- | ------------- | --------- | ---- | ------ |
| `{risk_id}` | `{control_id}` | `{type}` | `{ref}` | `{date}` | `{result}` |

## 5. Challenges & gaps
First-line challenges to the risk/control statements for reviewer attention (evidence gaps,
uncontrolled material risks, loss-event contradictions). These are prompts for a human, not
conclusions.
- `{risk_id}`: `{challenge}`

## 6. Remediation plan
For each residual above appetite or ineffective key control. Owner and due date are set by a
human; the draft flags "TBD" where absent. The assistant does not close or waive remediation.

| Risk ID | Residual band | Reason | Action | Owner | Due date | Status |
| ------- | ------------- | ------ | ------ | ----- | -------- | ------ |
| `{risk_id}` | `{residual_band}` | `{reason}` | `{action}` | `{owner}` | `{due_date}` | `{status}` |

## 7. Required approvals (human)
This RCSA becomes a record only after the approvals below are captured. The assistant
records them as `pending`; a human marks them obtained with name and date.

| Approval role | Status | Approver | Date |
| ------------- | ------ | -------- | ---- |
| Control / process owner (accuracy attestation) | `pending` | | |
| First-line business management (assessment sign-off) | `pending` | | |
| Second-line operational risk (independent challenge / validation) | `pending` | | |

---
*Standing note:* DRAFT RCSA for human review only — no assessment has been signed off,
challenged, attested, risk-accepted, or written to the GRC system of record by this assistant.
