# Domain Rules — senior-investor-protection-screener

Explainable senior-investor **concern signals** and how they map to a suggested **review
disposition band**. Thresholds are configuration (versioned, owned by the wealth-management
compliance / senior-protection team), not hard-coded judgments, and never tuned to an
individual. Orientation references: **FINRA Rule 2165** (Financial Exploitation of Specified
Adults), **FINRA Rule 4512** (Trusted Contact Person), the **Senior Safe Act**, and the
**NASAA Model Act** — the firm's senior/vulnerable-investor standard takes precedence.

A "specified adult" is (per Rule 2165) a client **age >= 65**, or a client the firm reasonably
believes has a mental or physical impairment that impairs financial self-protection
(`impairment_flag`). Specified-adult status is **context** — it decides which protections
apply — and is **not** itself a concern signal or a negative inference about the client.

## Signal taxonomy

| Signal | Fires when (default config) | Evidence attached | High severity |
| ------ | --------------------------- | ----------------- | ------------- |
| `unusual_disbursement` | Focal disbursement > baseline mean + `amount_k`·stdev (default k=3) of same-direction debit history | Focal txn + baseline stats + window | |
| `new_external_payee` | First-seen counterparty receiving a disbursement >= `new_payee_amount` (default 5,000) | Payee first-seen + amount | |
| `rapid_liquidation` | Debit outflow within `cluster_days` (default 30) >= `liquidation_amount` (default 25,000) | The debit rows in the window | ✓ |
| `account_or_beneficiary_change` | A beneficiary/registration/address change within `change_window_days` (default 90) coincident with a disbursement | The change record(s) + focal txn | |
| `trusted_contact_gap` | No trusted contact on file, or last confirmation > `tc_stale_days` (default 365) — a Rule 4512 gap | Trusted-contact status | |
| `third_party_influence` | Observed `third_party_present` or `new_caregiver_or_poa` | The set observation flags + observation ref | ✓ |
| `capacity_concern_indicators` | Observed `confusion_observed`, `cannot_recall_transaction`, or `repeated_questions` — **indicators only, not a diagnosis** | The set observation flags | |
| `communication_red_flags` | Observed `unusual_urgency`, `requests_secrecy`, `refuses_family_involvement`, or `scam_narrative_flag` | The set observation flags | ✓ |

Signals are **additive and independent**; the output reports each that fired with its own
evidence. There is no opaque composite "exploitation score". Behavioral signals
(`third_party_influence`, `capacity_concern_indicators`, `communication_red_flags`) are
computed only from **structured observation flags supplied by a trained human** — the skill
does not infer them from free text or diagnose the client.

## Disposition mapping (deterministic, documented)

Let `fired` be the set of fired concern signals and `HIGH` = {`rapid_liquidation`,
`third_party_influence`, `communication_red_flags`}.

| Suggested band | Rule |
| -------------- | ---- |
| **Monitor** | 0 signals fired |
| **Review** | 1–2 signals fired and none is high-severity |
| **Escalate** | >= 3 signals fired, OR any high-severity signal fired |

Disposition is a **triage suggestion for a human adjudicator**. It is not a determination that
exploitation or diminished capacity occurred, and it never triggers a hold, a filing, a
trusted-contact contact, or a case closure. `scripts/validate_output.py` re-derives the band
from `fired` and fails closed on any mismatch.

## Hard boundaries (fail closed)

- Never state or imply that exploitation/abuse **has occurred**, or that the client **lacks
  capacity / is incapacitated** — surface indicators and attribute conclusions to the human.
- Never recommend as an executed action, or take, a **Rule 2165 hold**, freeze, filing
  (SAR / APS), trusted-contact outreach, or **case closure**.
- Never tune thresholds to the individual or infer "what's normal for this person" beyond the
  computed baseline.
- `capacity_concern_indicators` are **observed indicators**, never a clinical determination.

## Benign-explanation prompts (always include when relevant)

A legitimate large purchase (home, vehicle, medical / long-term care); planned gifting to
family or charity; estate, tax, or RMD/Roth-conversion planning; a genuine new professional or
caregiver the client engaged; a relocation to assisted living; a real, client-directed
personal relationship or new payee. The pack must invite the adjudicator to weigh these before
reaching any conclusion.
