<!--
Credit Surveillance Packet — controlled template (packet_version: credit-surv-packet-2026.07)
Draft & package. Fill EVERY bracketed field from a cited source only. Do not invent figures,
spreads, ratings, or covenant conclusions. Every material number and assertion must carry a
citation `{system}:{ref}@{as-of/version}` traceable to references/source-map.md. Section keys
in the HTML comments below are the canonical required sections enforced by
scripts/validate_output.py — do not rename or drop them. This packet REPORTS agency ratings
and never assigns one; it expresses no thesis and no position/trade view. A changed covenant
is FLAGGED here and its term detail is handed off to credit-terms-covenant-extractor.
-->

# Credit Surveillance Packet (DRAFT)

- **Issuer:** [name] · **Issuer ID:** [issuer_id] · **Sector:** [sector]
- **As of:** [as_of] · **Prior period:** [prior_as_of] · **Packet template:** credit-surv-packet-2026.07

> Draft credit surveillance packet for human review. It reports agency ratings but assigns
> none, forms or changes no investment thesis, recommends no position or trade, and has not
> been circulated, sent, or submitted.

## 1. Issuer summary  <!-- issuer_summary -->
[Issuer, sector, as-of/prior-as-of, and the headline metrics: reported net leverage, interest
coverage, total liquidity, and the single most notable change this period. Surveillance only —
no rating set, no position view.] `{filing}`

## 2. Leverage  <!-- leverage -->
[Gross leverage (gross debt / EBITDA) and net leverage ((gross debt − cash) / EBITDA), with the
underlying inputs. Figures must tie out to the model/computation; do not restate an unsupported
number.] `{filing}`

## 3. Coverage  <!-- coverage -->
[Interest coverage (EBITDA / interest expense) and the fixed-charge coverage proxy
((EBITDA − capex) / interest expense). Ties out to the computation.] `{filing}`

## 4. Liquidity  <!-- liquidity -->
[Total liquidity = cash + undrawn revolver, and whether it covers near-term maturities within
the configured horizon. State the coverage plainly; do not opine on adequacy.] `{filing}`

## 5. Maturity wall  <!-- maturity_wall -->
[Scheduled maturities by year and the nearest maturity (year + amount). Cite the credit
agreement / filing.] `{filing}`

## 6. Spreads  <!-- spreads -->
[Current credit spread (instrument named) vs the prior period, with the delta and direction
(widening / tightening). Market spreads must come from an APPROVED market source.] `{market}`

## 7. Ratings  <!-- ratings -->
[Reported agency ratings and outlook, with prior rating/outlook and any change. Ratings are
REPORTED from the rating-agency source — this packet never assigns, derives, or opines on a
rating level.] `{rating-agency}`

## 8. Covenant changes  <!-- covenant_changes -->
[List covenant items flagged as CHANGED vs the prior period. Flag only — do not extract full
terms or determine compliance/headroom. Route term detail and interpretation to
credit-terms-covenant-extractor and compliance determination to a human.] `{filing}`

## 9. Citations and evidence  <!-- citations_and_evidence -->
[Confirm every metric and claim ties to a cited source; external market/rating-agency inputs
are approved-source only. List any blocking data gaps.] `{filing}`

---

## Traceability appendix
| Claim / figure | Source citation | As-of / version | Approved |
| -------------- | --------------- | --------------- | -------- |
| [claim] | `{system}:{ref}` | [as-of] | [yes/no] |

## Period-over-period change log
| Metric | Prior | Current | Delta | Disclosure |
| ------ | ----- | ------- | ----- | ---------- |
| Net leverage (x) | [prior] | [current] | [delta] | [disclose if >= threshold] |
| Interest coverage (x) | [prior] | [current] | [delta] | [disclose if <= -threshold] |
| Spread (bps) | [prior] | [current] | [delta] | [disclose if widening >= threshold] |

## Approvals (recorded by humans before delivery)
| Role | Name | Status | Date |
| ---- | ---- | ------ | ---- |
| Preparer (credit research analyst) | [name] | [pending → recorded] | [date] |
| Reviewer (sector lead / desk) | [name] | [pending → recorded] | [date] |
| **Rating / thesis / position** | — | **not set here** (reported-only / unchanged / none) | — |

_Both preparer and reviewer sign-offs must be `recorded` before this draft may be delivered.
The rating, thesis, and position are never set by this skill._
