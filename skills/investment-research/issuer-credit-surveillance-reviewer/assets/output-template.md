# Corporate issuer surveillance — draft rendering

Render only from a validated `ir-analysis/2.0` native output and its separately retained `ir-phase2/1.0` original. Do not render retired legacy packets as current validated evidence. This template does not extend method coverage, authenticate sources or grant delivery authority.

Header: request_id, subject identity, economic as_of, knowledge_cutoff, use_on, method/schema version, financial context from the retained original, status and unresolved_issues.

## Financial observations

Show `results.period_metrics` for comparable prior/current reported periods and `metric_changes`. Preserve null values and their stated coverage gaps. Gross/net leverage requires positive EBITDA; interest and fixed-charge proxy coverage require positive interest. The fixed-charge proxy is not contractual FCCR or DSCR.

## Liquidity and maturity coverage

Show `liquidity_to_known_maturity_x` with supplied unrestricted cash, available facilities, known maturities and inventory completeness context from the retained original. Do not claim full liquidity sufficiency or invent an instrument-level maturity wall; request separately validated capital-structure evidence when needed.

## Spreads

Show `spread_change_bps` only when reconciled. Retain `spread_reconciliation` with selected observations and dated security/issuer/currency mapping; preserve timestamps, basis and source bindings. For withheld comparisons report the unresolved reasons without repeating unavailable quote assertions as validated evidence.

## Reported events and alerts

Retain source-linked `reported_events` and supplied-threshold `alerts`. Ratings remain reported-only, position action none, thesis unchanged. No rating, default, covenant headroom/compliance or investment conclusion is inferred from event text.

## Evidence and review

Preserve source/cutoff/permission context, lineage, input_hash, unverified source truth, limitations and unresolved issues. Keep authored narrative and actual reviewer approval separate from immutable native evidence. `partial` may be faithfully reconstructed without becoming accepted or actionable; `complete-for-supplied-scope` is bounded software completion only.
