# Controls — nav-preparation-tie-out

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `required` — a fund accountant must review before the tie-out packet or
  any proposed resolution is delivered externally or acted on. NAV strike, price selection,
  and posting are always **separate authorized actions**, never performed by this skill.

## Prohibited (fail closed)

- **No NAV strike.** The skill never computes, strikes, finalizes, or certifies a NAV per
  share. `validate_output` rejects any `nav_per_share` / `struck_nav` / `official_nav` /
  `final_nav` / `certified_nav` field and any NAV-struck/finalized/certified language.
- **No price selection.** The skill never chooses, overrides, or fair-values a price. Every
  `price_break` **routes to `valuation-exception-packet`**; a price_break not routed fails
  closed, as does any "chose/selected/set the price" language.
- **No posting.** The skill never posts or books an accounting entry. Resolutions are
  `status: "PROPOSED"` with `chooses_value` / `strikes_nav` / `posts_entry` all false; any
  `POSTED`/`EXECUTED` status, any true flag, or any "posted/booked the entry" language fails
  closed.
- **No forced tie.** No plug, netting, or suppression of breaks. If a control total does not
  tie, surface the residual.
- **No adjudication.** The skill does not decide which source (book, custodian, administrator,
  pricing) is correct, nor approve its own resolutions.
- **No per-tie-out threshold tuning.** Tolerances, materiality, cutoff, and the
  component→verifier map come only from the versioned `config`.

## Required output screens (`scripts/validate_output.py`)

- **Tie-out:** each `(component, currency)` control total ties (`difference ==
  breaks_impact_sum`, recomputed from the break list); overall `residual == 0`;
  `out_of_tolerance_count == captured_break_count`.
- **Break taxonomy:** every break's `type` is in the fixed set {`quantity_break`,
  `price_break`, `cash_break`, `accrual_break`, `income_break`, `expense_break`,
  `shares_break`, `missing_record`, `timing_difference`} with component, key, impact, and a
  material flag.
- **Lineage:** every break cites its source rows (`book:` / `custodian:` / `administrator:` /
  `pricing:` prefix).
- **Idempotency:** `tie_out_id` is derived from `fund/share_class/as_of + input_fingerprint`
  with no timestamp/random component; `input_fingerprint` is a 64-hex content hash.
- **Proposed-only:** every resolution has `status: "PROPOSED"` and
  `chooses_value`/`strikes_nav`/`posts_entry` all false; price breaks routed to
  `valuation-exception-packet`; timing differences carry no resolution; no prohibited
  decision/action language anywhere; no forbidden struck-NAV / chosen-price field.
- **Disclaimer:** the standing no-strike/no-price/no-post disclaimer is present.

## Segregation of duties

- The skill **prepares** the tie-out and **proposes** resolutions. A different, authorized
  actor — the fund accountant (adjustments/posting), the valuation control owner (prices via
  `valuation-exception-packet`) — reviews and takes any system-of-record action. Preparation
  and the NAV strike must not be the same automated actor.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Fund holdings and NAV inputs are
  price-sensitive; minimize detail to what evidences a break. No retail customer NPI is
  required.
- Retain the tie-out packet, breaks, lineage, proposed resolutions, and `config_version` per
  records policy; log the read and any external-delivery approval.

## Reproducibility

`tie_out_id` + `input_fingerprint` bind the output to the exact inputs and config version;
re-running the same inputs reproduces the same breaks, resolutions, and tie-out.
