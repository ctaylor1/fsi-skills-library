# Domain Rules — enhanced-due-diligence-packager

Orientation references: FATF Recommendation 10 (CDD) and Recommendation 12 (PEPs);
US BSA/FinCEN CDD rule and beneficial-ownership requirements; the firm's EDD program standard.
The firm's standard and its **approved output template + residual-risk weighting** take
precedence and are versioned contracts. This skill packages evidence and recommends; it makes
no regulated decision.

## Required evidence sections (all nine; a missing/uncited section is a gap)

| Section | What it must evidence |
| ------- | --------------------- |
| Case & Customer Overview | Identity verification, customer type, occupation/role |
| Source of Funds (SoF) | Origin of the specific funds, corroborated by documents |
| Source of Wealth (SoW) | Origin of overall wealth, independently documented |
| Ownership & Control (UBO) | UBO traced; nominee/opacity assessed |
| Geographic Exposure | Residence/funding/business nexus vs. high-risk lists |
| Adverse Media | Search results, severity, charge/conviction status |
| PEP & Sanctions Screening | PEP status; sanctions result (true-match ⇒ hard boundary) |
| Expected Activity & Rationale | Expected volumes/patterns consistent with SoF/SoW |
| Ongoing Monitoring & Controls | Enhanced monitoring plan, cadence, escalation path |

## Residual-risk indicator (deterministic, documented)

Computed from explainable factors; the mapping is configuration, not judgement, and the band
is an **indicator to inform adjudication — never a rating of record or a decision**.

| Factor | Contribution (default) |
| ------ | ---------------------- |
| PEP status | primary +4, associate/family +2, none 0 |
| High-risk-geography nexus | +3 per nexus, capped +6 |
| Adverse-media severity | severe +4, moderate +2, low +1, none 0 |
| Ownership opacity | nominee/opaque +3, layered +2, transparent 0 |
| Cash-intensive | +2 |
| Product/channel risk | non-face-to-face / correspondent / private-banking +2, standard 0 |
| SoF/SoW inconsistency | +3 |

Bands: **High** total ≥ 10; **Medium** 5–9; **Low** ≤ 4. **Hard boundary:** a sanctions
true-match sets band `Prohibited-proximity`, `hard_boundary=true`, and forces
`packaging_status=blocked` with a route to `sanctions-match-adjudicator`.

## Packaging status → recommended review path (advisory)

| Status / band | `recommended_review_path` |
| ------------- | ------------------------- |
| `blocked` (hard boundary) | `hold-pending-specialist` |
| `needs-evidence` (any gap) | `return-for-evidence` |
| `ready` + High | `senior-management-adjudication` |
| `ready` + Medium | `edd-committee-adjudication` |
| `ready` + Low | `standard-adjudication` |

The review path is a **recommendation**; the human adjudicator chooses and records the actual
disposition and any approvals.

## Hard boundaries (fail closed)

- No **onboarding/retention/exit decision**, and no communication of one.
- No **risk-rating change of record** (the band informs; it does not rate).
- No **case closure**, **SAR/CTR/STR drafting or filing**, or regulatory submission.
- No **system-of-record write** and no **send/submit** of the package (draft-only).
- No **sanctions/UBO/adverse-media conclusion** — route to the specialist.
- No **tipping-off**: never reveal monitoring/SAR activity to the customer.

## EDD package — required contents

Durable `case_id`; the nine cited evidence sections above; EDD trigger & scope; the residual-
risk indicator with factors; an advisory recommendation and specialist routes; an approval
ledger listing every required role with status; an aggregate sources-and-citations list; and
the standing note (draft-only / no-decision limitation).
