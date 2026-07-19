# Controls — conflicts-of-interest-reviewer

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a qualified human adjudicator (compliance officer, legal,
  or the conflicts/ethics committee) must decide any clearance, waiver, restriction,
  escalation, closure, or filing. This skill decides nothing.

## Prohibited (fail closed)

- No **clearance / approval / waiver** of a conflict, and no statement that a matter **is
  cleared, approved, or waived**.
- No **closure** of the matter and no "no further action required" / "final disposition".
- No **filing or submission** of a disclosure, U4/U5, attestation, or regulatory form.
- No binding **"there is no conflict"** determination — report that no indicator fired and
  leave the determination to the adjudicator.
- No assertion of **insider dealing, MNPI misuse, or intent** — route to surveillance.
- No **threshold tuning to the individual**; use only the versioned config.
- No **opaque scoring** presented as decisive; indicators are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every fired finding has ≥ 1 cited evidence row.
- Each finding's `open_gap` and `residual_risk` are **recomputed** from its own
  `inherent_severity` + disclosure/control/approval status and must tie out (anti-tamper: a pack
  cannot under-state an unmitigated conflict by self-reporting a softer gap/residual band).
- `matter_residual_risk` equals the deterministic max across the **recomputed** residuals.
- `recommended_review_path` equals the deterministic mapping from the recomputed residual + open
  gaps.
- No clearance/approval/waiver/closure/filing/determination language (regex screen: "conflict
  cleared", "waiver granted", "we approve", "approved to proceed", "case closed", "no further
  action required", "final disposition", "file a disclosure", "there is no conflict", "insider
  trading", "clear to trade", etc.).
- Standing disclaimer present: "Conflicts review and recommendations only; not a compliance
  determination, clearance, waiver, or approval. A qualified human adjudicator must decide. No
  matter has been closed and no filing has been made."
- Mitigation prompts present when any indicator fired or any open gap exists.

## Fairness / conduct

- Do not use protected-class attributes or proxies as conflict indicators.
- Describe relationships and interests factually; avoid stigmatizing or accusatory language
  about the subject or counterparties.

## Data classification, privacy, records

- **Restricted** (employee PII, MNPI, AML/BSA-adjacent facts). Mask subject/employee and
  account identifiers to last 4.
- Minimize personal data in output to what evidences a fired indicator.
- Observe **tipping-off / SAR-confidentiality**: never reveal the existence of a
  suspicious-activity referral to the subject or in externally shared output.
- Retain review + citations + config version per records policy; log the read and the
  adjudication hand-off.

## Reproducibility

`review_id` binds the output to the exact inputs, `as_of` date, and **config version**;
re-running with the same inputs and config reproduces the findings, residual risk, and
recommended review path.
