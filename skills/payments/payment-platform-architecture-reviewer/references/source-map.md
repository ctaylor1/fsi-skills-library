# Source map

Reviewed 2026-09-18. The primary sources for an individual review are the institution's
current architecture, interface/state contracts, ledger/control design, incidents,
capacity evidence and supplied alternatives. Register them with effective/review dates.

- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html): engineering review context; the package's payment-specific schema and checks are repository conventions, not AWS certification.
- [AWS idempotent mutating operations](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_prevent_interaction_failure_idempotent.html): retry/idempotency design orientation; deployed behavior still requires testing.
- [EBA outsourcing guidelines resource](https://www.eba.europa.eu/activities/single-rulebook/regulatory-activities/internal-governance/guidelines-third-party-risk-management?version=2019): third-party governance context; check applicable dates and ICT/non-ICT scope rather than treating old cloud guidance as current.

Native rail and regional source summaries are bundled by the repository foundation;
use only the relevant profile and preserve its stated limitations. They do not prove
an institution's architecture or operational controls. Licensed provider/network
contracts and confidential diagrams remain in authorized repositories.

## Phase 3 source basis (reviewed 2026-09-18)

Native inputs are supplied operational evidence: queue snapshots, authoritative payment
outcomes, trace/release/status records, financial reconciliations, scoped test artifacts,
cost ledgers and task/model evaluation results. Prefer original versioned artifacts over
summary decks. Register source dates and review_due; preserve contradictory observations.
Offline scripts inspect supplied contents but do not authenticate identity or fetch links.

Engineering references, not payments law or certification requirements:
- [Amazon Builders Library, idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/): preserve client request identity and changed-intent boundaries.
- [Google SRE Workbook, postmortem culture](https://sre.google/workbook/postmortem-culture/): retain incident evidence, learning and accountable follow-up.

The formulas, baseline fault scenarios and AI evidence fields are library design
conventions. Reassess source versions before applying to a deployment; contractual,
scheme, security and jurisdiction requirements need their current authoritative pack.
