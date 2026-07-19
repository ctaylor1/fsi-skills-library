# Domain Rules — privacy-impact-assessment-assistant

Orientation references: GDPR Articles 35 (DPIA) and 36 (prior consultation), Articles 6/9/10
(lawful basis and special/criminal-offence data), Chapter V (international transfers); UK GDPR
and the ICO DPIA guidance; US state privacy laws where a risk/data-protection assessment is
required (e.g., CCPA/CPRA risk assessments). The firm's privacy program standard and its
**approved output template + privacy-risk weighting** take precedence and are versioned
contracts. This skill packages evidence and recommends; it makes no regulated privacy decision.

## Required evidence sections (all eight; a missing/uncited section is a gap)

| Section | What it must evidence |
| ------- | --------------------- |
| Processing Description & Purpose | What the processing does; controller/processor roles; specified purpose(s) |
| Personal Data Inventory & Categories | Data categories, special/criminal-offence data, data subjects, scale/volume |
| Legal Basis, Necessity & Proportionality | Lawful basis (+ any Art 9 condition); necessity/proportionality; minimization |
| Data Sharing, Recipients & International Transfers | Recipients/processors; onward sharing; transfer mechanism |
| Retention & Data Minimization | Retention periods; deletion routines; pseudonymization vs. schedule |
| Security & Technical/Organizational Measures | Encryption, access control, logging, vendor assurance |
| Data Subject Rights & Transparency | Notice; access/rectification/erasure/objection/opt-out; ADM safeguards |
| Risk Mitigations & Safeguards | Safeguards reducing risk to data subjects (restriction, human review, fairness) |

## Privacy-risk indicator (deterministic, documented)

Computed from explainable factors; the mapping is configuration, not judgement, and the band is
an **indicator of risk to data subjects' rights and freedoms to inform sign-off — never a
decision on the processing or a lawful basis of record**.

| Factor | Contribution (default) |
| ------ | ---------------------- |
| Special-category (Art 9) data | +3 |
| Criminal-offence (Art 10) data | +2 |
| Children / vulnerable data subjects | +3 |
| Large-scale processing | +2 |
| Systematic monitoring / profiling | +3 |
| Automated decision-making with legal/similar effect | +3 |
| Novel technology (e.g., AI / biometric) | +2 |
| High-risk international transfer | +2 per nexus, capped +4 |
| Data matching / combining | +1 |
| Retention beyond documented policy | +1 |

Bands: **High** total ≥ 8; **Medium** 4–7; **Low** ≤ 3. When the band is High, a
`prior_consultation_indicated` flag is raised (GDPR Art 36 may apply) — advisory, for the human.

## Hard boundaries (unlawful-processing indicators → fail closed)

Any of these sets band `Unlawful-processing-proximity`, `hard_boundary=true`, and forces
`packaging_status=blocked` with a route to privacy counsel / the DPO:

- **No lawful basis** identified for the processing.
- **Special-category data with no Article 9 condition**.
- **Restricted international transfer with no valid transfer mechanism**.

Beyond the hard boundaries, this skill additionally never: approves/authorizes/clears the
processing, sets a lawful basis of record, closes a case, files or initiates prior consultation,
writes a system of record, sends/submits the assessment, or concludes a specialist's
data-flow / third-party / AI risk analysis.

## Packaging status → recommended review path (advisory)

| Status / band | `recommended_review_path` |
| ------------- | ------------------------- |
| `blocked` (hard boundary) | `hold-pending-privacy-counsel` |
| `needs-information` (any gap) | `return-for-information` |
| `ready` + High | `dpo-and-senior-review` |
| `ready` + Medium | `dpo-review` |
| `ready` + Low | `standard-privacy-sign-off` |

The review path is a **recommendation**; the human adjudicator chooses and records the actual
sign-off, any lawful basis of record, and any prior consultation.

## PIA/DPIA — required contents

Durable `assessment_id`; the eight cited evidence sections above; the assessment scope & DPIA
trigger; the privacy-risk indicator with factors; an advisory recommendation and specialist
routes; an approval ledger listing every required role with status; an aggregate
sources-and-citations list; and the standing note (draft-only / no-decision limitation).
