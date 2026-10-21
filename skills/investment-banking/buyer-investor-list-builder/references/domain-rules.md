# Domain Rules — buyer-investor-list-builder

Orientation: standard sell-side / capital-raise buyer-universe construction. The firm's
engagement standard, its information-barrier policy, and its **restricted / conflicts list**
take precedence and are versioned contracts. This skill produces an internal draft only; it
makes no binding decision and gives no advice.

## Fit scoring (deterministic, documented)

The fit score is computed from explainable inputs; the mapping is configuration, not judgment.
Buyer types considered: `strategic`, `sponsor` (financial/PE), `lender`, `investor`.

| Input | Contribution (default) |
| ----- | ---------------------- |
| Sector / strategic fit | strong +3, moderate +1, weak 0 |
| Size / financial capacity fit (can write the cheque for the deal-size band) | high +3, medium +2, low +1 |
| Geographic fit | +2 if aligned |
| Mandate / thesis alignment (sponsors/investors) | +2 if aligned |
| Precedent activity (comparable deals in sector recently) | +2 if present |
| Relationship strength (coverage / prior contact) | strong +2, some +1, none 0 |

Maximum score is 14. Outreach waves:

- **wave-1-priority** — total ≥ 8 (highest-conviction targets, contacted first).
- **wave-2-standard** — total 4–7.
- **wave-3-broaden** — total ≤ 3 (breadth / optionality).

A wave is an **outreach sequencing plan for a human**, not a decision to contact anyone.

## Screening and exclusions (order applied per candidate)

1. **needs-data** — missing/invalid `buyer_type`, `sector_fit`, or `size_fit`: cannot be
   scored; excluded and listed for follow-up. Never guessed to place a candidate.
2. **needs-source** — no rationale claim resolves to a document in the source index (all
   claims unsupported): excluded from waves; the dropped source refs are recorded.
3. **hold-conflicts-review** — candidate is on the restricted list (`restricted` true or
   `entity_id` in `restricted_list`) or carries an unresolved conflict (`conflict_flag`): held
   and routed to conflicts clearance; **never** placed in an active wave, regardless of fit.
4. **duplicate** — `entity_id` matches a prior outreach-list entry: linked to that entry for
   human confirmation; not re-listed in a wave.
5. Otherwise the candidate is placed into the wave for its fit score.

## Hard boundaries (fail closed)

- No **sending, delivering, or sharing** the list; no **contacting/soliciting** any buyer.
- No **restricted/conflicted candidate in an active wave**.
- No **unsupported assertion** — every rationale/relationship claim cites an indexed source.
- No **investment recommendation, buy/sell advice, or valuation opinion**.
- No **filing or system-of-record write**; external delivery is a gated human action.

## Buyer list — required contents

Durable `list_id`; the documented fit criteria; the source index; per-candidate fit score with
reason, disposition, cited rationale, and relationship context; the tiered outreach waves; the
conflicts-hold list (with reason and route); the gaps lists (needs-data, needs-source,
duplicates); the approvals ledger; the standing note.
