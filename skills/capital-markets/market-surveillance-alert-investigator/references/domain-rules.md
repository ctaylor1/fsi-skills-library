# Domain Rules — market-surveillance-alert-investigator

Orientation references: market-abuse / manipulation frameworks (e.g., US securities laws and
SRO rules; EU MAR STOR concepts) and firm trade- and comms-surveillance policy. The firm's
surveillance program standard and its **thresholds/band configuration take precedence** and
are versioned contracts. Indicators below are **evidence for a human**, never a determination
of abuse.

## Indicators (deterministic, documented)

Computed for the **subject party** over the case period. Each carries its own threshold,
a breached flag, a weight, and citations to the underlying records.

| Indicator | Definition | Default threshold (breach) | Applies to |
| --------- | ---------- | -------------------------- | ---------- |
| `order_to_trade_ratio` | subject orders ÷ max(subject trades, 1) | ≥ 4.0 | all |
| `cancel_rate` | subject cancelled orders ÷ subject orders | ≥ 0.60 | all |
| `opposite_side_cancel_cluster` | cancelled orders on the side **opposite** the subject's net traded side, within `layering_proximity_sec` (default 60s) of a fill | count ≥ 3 | spoofing_layering, ramping |
| `close_window_participation` | subject traded volume ÷ market volume in the last `close_window_min` (default 5) minutes, as % | ≥ 30.0% | marking_the_close |
| `self_match` | opposing subject trades, equal qty, price within `self_match_price_tol` (0.01) and time within `self_match_time_tol_sec` (60s) | pairs ≥ 1 | wash_trade |
| `message_trade_proximity` | min seconds from a flagged message to a subsequent subject order/trade | ≤ 3600s (with a flagged message) | insider_dealing, comms_collusion |
| `flagged_prohibited_terms` | count of subject messages carrying flagged terms | ≥ 1 | insider_dealing, comms_collusion |

## Evidence-strength mapping → disposition RECOMMENDATION

`evidence_strength_score` = sum of the weights of **breached** indicators (defaults:
OTR 2, cancel-rate 2, cancel-cluster 3, close-participation 3, self-match 3,
message-proximity 3, flagged-terms 2).

| Band | Condition | Disposition **recommendation** |
| ---- | --------- | ------------------------------ |
| Strong | score ≥ `refer_min` (6) | `recommend-refer-regulatory-consideration` |
| Elevated | `escalate_min` (3) ≤ score < 6 | `recommend-escalate-to-compliance-review` |
| Within thresholds | score < 3 | `recommend-close-no-further-action` |

Precedence before scoring:

1. **needs-data** — a required evidence stream for the alert type is absent
   (spoofing⇒orders, wash⇒trades, marking-the-close⇒market+trades, insider/comms⇒messages).
   Do **not** guess to clear or escalate a case.
2. **possible-duplicate** — overlaps an open/prior case for the **same party + alert type +
   overlapping period** sharing an order/trade id ⇒ link for human confirmation.
3. Otherwise apply the strength band above.

Every band is a **recommendation**; a qualified supervisor/compliance officer adjudicates.
The score is investigative weight-of-evidence, **not** a legal conclusion.

## Hard boundaries (fail closed)

- No **autonomous case closure**, **market-abuse determination**, **exoneration**, or
  **STOR/SAR/regulator filing** (or language asserting any of these occurred).
- No **investigation of an un-escalated alert** — missing triage provenance ⇒ route to
  `surveillance-alert-triager`.
- No **auto-merge** of cases/entities; overlaps are linked as `possible-duplicate`.
- No broadcasting of **MNPI** beyond the authorized surveillance/compliance channel.

## Evidence bundle — required contents

Durable `case_id`; subject party + all parties (masked) with roles; a time-ordered
**chronology** of orders, trades, messages, and market events (each cited); amounts (traded
qty, notional, currency); the computed **indicators** with thresholds and citations; linked
prior cases; the disposition **recommendation** with a rationale referencing the breached
indicators; and the config version used.
