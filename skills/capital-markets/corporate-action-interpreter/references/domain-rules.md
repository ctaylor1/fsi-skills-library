# Domain Rules — corporate-action-interpreter

The rules, event taxonomy, date definitions, and entitlement formulas the skill applies.
These are **descriptive** rules on the stated notice terms — they never select an option,
determine a personalized tax result, or record an election.

## Event taxonomy (CAEV-style codes)

| Code | Name | Status (typical) | Entitlement basis |
| ---- | ---- | ---------------- | ----------------- |
| `SPLF` | Stock split (forward) | Mandatory | `shares_after = qty × ratio_new / ratio_old` |
| `SPLR` | Reverse stock split | Mandatory | `shares_after = qty × ratio_new / ratio_old` |
| `DVCA` | Cash dividend | Mandatory | `cash = qty × rate_per_share` |
| `DVSE` | Stock dividend | Mandatory | `additional_shares = qty × ratio_new / ratio_old` |
| `BONU` | Bonus issue | Mandatory | `additional_shares = qty × ratio_new / ratio_old` |
| `DVOP` | Dividend option (cash or stock) | Mandatory-with-options | per option (cash or shares) |
| `CAPG` | Capital gains distribution | Mandatory | `cash = qty × rate_per_share` |
| `SOFF` | Spin-off | Mandatory | per notice ratio (narrative + ratio) |
| `MRGR` | Merger | Mandatory / with-options | per consideration (cash and/or share ratio) |
| `TEND` | Tender offer | Voluntary | per option (cash consideration) |
| `EXOF` | Exchange offer | Voluntary | per option (share/cash ratio) |
| `RHTS` / `RHDI` | Rights issue / distribution | Voluntary / mandatory | per subscription ratio and price |
| `REDM` / `PCAL` | Redemption / partial call | Mandatory | `cash = qty × rate_per_share` (or pro-rata) |
| `CHAN` | Name / identifier change | Mandatory | no economic entitlement |
| `CONS` | Consent solicitation | Voluntary | no economic entitlement |

Unknown codes are interpreted narratively from the notice text and flagged; no formula is
asserted that may not apply.

## Mandatory vs. voluntary vs. mandatory-with-options

- **Mandatory** — happens to every holder; no action required; a single outcome.
- **Voluntary** — the holder must respond to participate; missing the deadline means no
  participation. An election deadline is required.
- **Mandatory-with-options** — happens to every holder, but the holder may choose among
  options; a **default** applies if no valid election is made by the deadline. An election
  deadline **and** a default option are required.

For every options event, the interpretation states the deadline **and** the default outcome
if the holder does nothing. Stating the default is a factual description of the notice, not
a recommendation.

## Key dates

| Date | Meaning |
| ---- | ------- |
| Announcement date | When the event was declared. |
| Ex-date | On/after this date the security trades without the entitlement. |
| Record date | Holders of record on this date are entitled; **entitlement is sized on this holding**. |
| Election deadline | Last date to submit a valid election (voluntary / with-options). |
| Pay date | When cash/shares are delivered. |
| Effective date | When a reorganization (split, merger, spin-off) takes effect. |

Ordering sanity: announcement ≤ record ≤ pay; the election deadline is on/before pay date.
Reversed or missing dates are flagged, not corrected.

## Entitlement computation

- **Shares** = `quantity × ratio_new / ratio_old`. Report **whole shares** and the
  **fractional remainder** separately.
- **Cash** = `quantity × rate_per_share` (per-share cash rate).
- **Fractional shares** are settled per the notice's stated method (cash-in-lieu vs. round
  down). If the notice does not state the method or the cash-in-lieu rate, **flag it** —
  never invent it.
- `scripts/calculate_or_transform.py` computes these; `scripts/validate_output.py`
  re-derives and ties out each stated entitlement.

## Tax categories (neutral, informational only)

The interpretation may **name** the tax category the notice or governing document indicates
(e.g., "ordinary dividend", "qualified dividend", "return of capital", "generally tax-free
reorganization", "cost-basis adjustment on a split/spin-off"). It must **not** state a
personalized result ("tax-free to you", "you will owe $X"), compute basis, or apply lot or
wash-sale treatment — those route to a licensed tax professional.

## Ambiguity triggers (flag for operations review)

- Missing or contradictory ratio / per-share rate / option terms.
- Unstated fractional-share treatment or cash-in-lieu rate.
- Unknown or unconfirmed event code.
- Superseded / amended notice, or vendor scrub disagreeing with the depository notice.
- Election deadline already passed, or eligible position as-of ≠ record date.
- Multiple events or securities bundled in one file.
