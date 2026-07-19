# Domain Rules — payment-fraud-case-investigator

Orientation references: card-network fraud rules and dispute frameworks; ISO 20022
(pacs/pain) message structure; scheme/RTP push-payment risk guidance; BSA/FinCEN
recordkeeping (SAR filing is downstream and human-performed). The firm's fraud-operations
standard and its **scoring config** take precedence and are **versioned contracts**.

## Evidence categories (the six evidence pillars)

Each case is investigated across six pillars; each pillar contributes documented,
explainable signals — no black-box conclusion.

| Pillar | Example signals |
| ------ | --------------- |
| **Device** | new device, device-id change, IP/geo mismatch, emulator flag |
| **Identity** | recent credential reset, recent contact change, KYC unverified |
| **Behavior** | velocity spike, off-pattern amount, unusual hour |
| **Transaction** | high-risk MCC, cross-border, structuring pattern |
| **Beneficiary** | new beneficiary, mule-watchlist proximity, beneficiary < 30 days old |
| **Network** | shared-device ring, linked prior fraud cases |

## Fraud-risk scoring (deterministic, documented)

Score is the sum of the signal weights below plus flag/linkage contributions. It is a
triage-of-evidence rank for a human adjudicator — **not** a fraud determination.

| Signal | Weight (default) |
| ------ | ---------------- |
| device.new_device / device_id_changed / ip_geo_mismatch / emulator_flag | +2 / +1 / +2 / +3 |
| identity.credential_reset_recent / contact_change_recent / kyc_unverified | +3 / +2 / +2 |
| behavior.velocity_spike / off_pattern_amount / unusual_hour | +2 / +2 / +1 |
| transaction.high_risk_mcc / cross_border / structuring_pattern | +2 / +1 / +3 |
| beneficiary.new_beneficiary / mule_watchlist_hit / beneficiary_new_30d | +1 / +4 / +2 |
| network.shared_device_ring | +3 |
| sanctions/adverse-media proximity flag | +4 (also forces route to specialist) |
| linked fraud cases | +2 each, capped +4 |
| prior fraud cases in 180d (velocity) | +1 each, capped +3 |

**Bands:** **High** total ≥ 8; **Low** ≤ 3; **Elevated** 4–7.

## Disposition mapping (recommendation only; precedence top-down)

1. **sanctions/adverse-media flag** → `route-specialist` → `sanctions-match-adjudicator`.
2. **APP scam / BEC indicator** → `route-specialist` → `phishing-and-bec-investigator`.
3. **Incomplete required evidence** and band ≠ High → `needs-evidence` (never clear/confirm
   by guessing over gaps).
4. **High band** → `recommend-fraud` (recommend a fraud adjudicator review and action).
5. **Low band** with complete evidence → `recommend-legitimate` (recommend releasing the
   hold pending human review — a recommendation, not a clearance).
6. **Elevated band** with complete evidence → `recommend-elevated-monitoring`.

Required evidence for completeness: `device`, `identity`, `behavior`, `transaction`,
`beneficiary` present and non-empty (`network` optional).

## Hard boundaries (fail closed)

- No **fraud determination**, **exoneration**, or **case closure**.
- No **block / freeze / reversal / return** of a payment or account.
- No **SAR drafting/filing** or reporting to authorities.
- No **sanctions-match adjudication** or **APP/BEC** investigation (route to specialists).
- No bundle without a **durable `case_id`**; no **uncited** evidence item.

## Evidence bundle — required contents

Durable `case_id`; masked parties with roles; time-ordered **chronology** (case-open,
transactions, dated identity/timeline events); **evidence items** per pillar, each cited;
**network links** to prior cases (cited); amounts/instruments/channel; `risk_score` +
`risk_band` + score reasons; evidence-completeness status; the recommended disposition with
rationale; and citations for every item.
