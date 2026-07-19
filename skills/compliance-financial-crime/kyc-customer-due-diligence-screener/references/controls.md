# Controls — kyc-customer-due-diligence-screener

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only
  analysis.
- **Human approval:** `required` — a qualified analyst must adjudicate before any regulated
  decision, customer commitment, risk-rating write, case closure, or filing. The skill
  itself decides nothing and writes nothing.

## Prohibited (fail closed)

- No **CDD/KYC decision**: never approve, reject, onboard, exit/off-board, or state/imply
  the outcome is decided.
- No **sanctions/PEP disposition**: never clear, confirm, or dispose of a potential match —
  route it to the specialist adjudicator and a human.
- No **determination language**: never assert a customer **is** a criminal, sanctioned
  party, terrorist, or money launderer; indicators are potential matches/allegations.
- No **customer risk rating** set/updated and no **system-of-record write**.
- No **filing** (SAR/regulatory report) and no **case closure**.
- No **threshold/list tuning to the individual**; use only the versioned config.
- No **opaque scoring** presented as decisive; signals are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every fired signal has ≥ 1 cited evidence row.
- `recommended_track` equals the deterministic mapping from `fired_signals`
  (`references/domain-rules.md`).
- `adjudication_required` is present and `true`.
- No prohibited decision/closure/filing/disposition language in narrative, notes, or signal
  reasons (regex screen: "approve the customer", "close the case", "clear the sanctions
  hit", "confirmed match", "file a SAR", "the customer is a criminal", "update the risk
  rating", etc.).
- Standing disclaimer present: the `DISCLAIMER` text (recommendation only; not a decision;
  nothing onboarded, rated, closed, or filed; analyst must adjudicate).
- `recommended_next_steps` (human/specialist routing) present when any elevated-risk or
  sanctions signal fired.

## Fairness / conduct

- Do not use protected-class attributes or proxies as risk signals. Higher-risk
  jurisdiction/industry lists are program configuration, applied uniformly.
- Describe indicators and allegations factually; avoid stigmatizing language and never treat
  an allegation as a finding.

## Data classification, privacy, records (tipping-off aware)

- **Restricted (AML/BSA — SAR confidentiality; tipping-off controls).** The existence and
  content of any potential SAR-related concern must not be disclosed to the customer.
- Minimize customer PII to what evidences a fired signal; mask identifiers where feasible.
- Retain screening + citations + `config_version` per records policy; log the read and any
  downstream adjudication/approval. Never exfiltrate customer or screening data.

## Reproducibility

`screening_id` binds the output to the exact inputs, `as_of`, and **config version**;
re-running with the same inputs and config reproduces the signals and the recommended track.
