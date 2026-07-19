# Domain Rules — third-party-cyber-risk-reviewer

Explainable third-party cyber **findings** and how they map to a **suggested residual-risk
tier**. Thresholds are configuration (versioned, owned by the third-party-risk / CISO
function), not hard-coded judgments, and are never tuned to a single supplier to reach a
desired outcome. Orientation references: the firm's third-party risk-management standard,
NIST SP 800-161 (supply-chain risk) and the applicable operational-resilience/outsourcing
rules take precedence. The suggested tier is **decision support for a human risk owner**, not
an approval, risk acceptance, or onboarding decision.

## Finding taxonomy

| Finding | Fires when (default config) | Default severity | Evidence attached |
| ------- | --------------------------- | ---------------- | ----------------- |
| `control_gap` | More than `control_gap_max_partial_missing` (1) mandatory-domain controls missing/partial, OR any mandatory control `missing` | high if any missing, else medium | The gap control rows + status |
| `stale_or_missing_attestation` | No in-scope, in-date independent attestation (SOC 2 Type 2 / ISO 27001) covering the service | high | The attestation rows + `valid_until` |
| `open_critical_vulnerabilities` | `critical_open` > 0, OR `high_open` > `high_vuln_max` (3), OR any SLA breach, OR `oldest_open_days` > `vuln_oldest_open_max_days` (30) | critical if any critical open, else high | Posture counts + scan ref |
| `unresolved_material_incident` | An incident that `affected_our_data` is unresolved, OR disclosed later than `incident_disclosure_max_days` (3) after it occurred | critical if unresolved, else high | Incident row + disclosure gap |
| `fourth_party_data_exposure` | A subcontractor `processes_our_data` in a region not in `fourth_party_approved_regions`, or without evidence | high | The subcontractor rows |
| `contractual_gap` | Breach-notification SLA absent or > `breach_notification_max_hours` (72), OR no right-to-audit, OR no data return/deletion | medium | Contract term flags |
| `resilience_gap` | Important/critical service with untested BCP, or RTO worse than the required RTO | high if critical, else medium | BCP/RTO evidence |
| `overdue_remediation` | A committed remediation item is past its committed date and not closed | high if the item is high/critical, else medium | The overdue item rows |

Findings are **additive and independent**; the review reports each that fired with its own
cited evidence. There is no opaque composite "vendor score". Controls whose status is
`unknown` are listed under `not_evaluable` — never silently treated as pass or fail.

## Residual-tier mapping (deterministic, documented)

Bands: `Low` < `Moderate` < `High` < `Critical`. Computed in
`scripts/calculate_or_transform.py` and re-derived independently in
`scripts/validate_output.py`:

1. **Base band** from the highest fired-finding severity: critical → `High`, high →
   `Moderate`, medium/low → `Low`. No fired findings → `Low`.
2. **+1 band** if 4 or more findings fired.
3. **+1 band** if the engagement is *amplified*: `criticality == critical`, OR
   `hosts_regulated_data`, OR `data_classification` in {Highly Confidential, Restricted}.
4. Bounded at `Critical`.

The tier is a **triage suggestion for a human risk owner**. It is not a decision and it
never onboards, approves, rejects, risk-accepts, or closes the assessment.

## Hard boundaries (fail closed)

- Never **approve, reject, onboard, clear, or risk-accept** a supplier; never **sign off**,
  **close** an assessment, **file/attest**, or state a **final determination** — those are
  the human risk owner's decisions (see `references/controls.md`).
- Never write a system of record (GRC/TPRM register, contract, exception log).
- Never tune thresholds to a single supplier to reach a desired tier; use only the versioned
  config and record `config_version`.
- Where an internal system of record contradicts a supplier attestation, surface both; do
  not resolve in the supplier's favor.

## Considerations to surface (always include when findings fired)

Compensating controls not captured in the intake (segmentation, monitoring), attestation
scope and exception dispositions, whether open items already have an accepted remediation
plan and named owner, whether classification/criticality are current, and supplier
concentration/substitutability (route per `references/handoffs.md`). The review must invite
the risk owner to weigh these before adjudicating.
