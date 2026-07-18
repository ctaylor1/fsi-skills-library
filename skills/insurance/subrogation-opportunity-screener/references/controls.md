# Controls — subrogation-opportunity-screener

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the referral goes to a recovery
  specialist / counsel or is written to the claim system of record.

## Prohibited (fail closed)

- No **subrogation determination** — never decide that recovery will/should be pursued as a
  binding outcome; produce a screening band and evidence only.
- No **liability determination** — never state or imply that a third party **is liable** or **at
  fault**; describe the recorded liability indicators factually and attribute the finding to the
  human specialist / counsel.
- No **limitation (time-bar) determination** — never assert a claim **is** or **is not**
  time-barred; report the diaried date and days remaining and route limitation questions to
  counsel. A missing limitation date is a data gap, not a basis to conclude anything.
- No **recovery action or recommendation to act**: issuing/sending a demand, filing suit,
  placing a lien, negotiating, releasing the third party, or **waiving/closing** the recovery.
- No **threshold tuning to the individual claim**; use only the versioned config floors/factors.
- No **opaque scoring** presented as decisive; signals are explainable and individually evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every fired signal has ≥1 cited evidence row.
- `screening_band` equals the deterministic mapping from `fired_signals` (+ `time_critical`);
  see [domain-rules.md](domain-rules.md).
- No determination/action language (regex screen: "third party is liable", "is time-barred",
  "file suit", "issue the demand", "waive subrogation", "close the recovery", "we will recover",
  "deny the claim", etc.).
- Standing disclaimer present: "Screening evidence only; not a subrogation, liability, or
  limitation determination. No demand, filing, waiver, or recovery action has been taken."
- `consider_prompts` (counter-considerations) included whenever the band is not `No-Action`.

## Time-critical safeguard

When the diaried limitation date is at or inside the urgent buffer (or already past), the pack
sets `time_critical` and the screen forces at least a `Review` band whenever liability is
indicated and recovery is available — so a live recovery right is never allowed to lapse
silently. The skill still does **not** decide whether the claim is time-barred.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask claimant/party identifiers where not needed
  to evidence a signal; minimize third-party PII to what supports the referral.
- Retain screening + citations + config version per records policy; log the read and any
  external-delivery approval. Never exfiltrate claim or third-party data.

## Reproducibility

`screening_id` binds the output to the exact claim inputs, the diaried limitation date, and the
**config version**; re-running with the same inputs and config reproduces the signals, the
referral economics, and the band.
