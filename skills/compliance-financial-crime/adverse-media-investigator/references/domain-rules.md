# Domain Rules — adverse-media-investigator

Orientation references: FATF guidance on adverse-media / negative-news screening,
BSA/FinCEN CDD and recordkeeping, Wolfsberg guidance on name screening and adverse media.
The firm's screening standard and its **versioned scoring config** take precedence and are
the authoritative contract. Everything below is deterministic and documented — it is
decision *support*, not judgment.

## 1. Entity resolution (is the hit actually about the subject?)

Each candidate hit carries an `entity_match` with fields `name`, `dob`, `nationality`,
`location`, `identifier` (values `exact/partial/none` for name; `match/mismatch/unknown`
otherwise). Score (defaults):

| Field | match | partial | mismatch | unknown |
| ----- | ----- | ------- | -------- | ------- |
| name | exact +3 | partial +1 | (n/a) | none -> discard |
| dob | +3 | — | **hard-discard** | 0 |
| nationality | +1 | — | -2 | 0 |
| location | +1 | — | -1 | 0 |
| identifier (LEI/passport/registry) | +4 | — | **hard-discard** | 0 |

- **name = none**, or a **DOB or identifier mismatch**, is a *hard disambiguator* → the hit
  is **namesake-discarded** regardless of anything else, and contributes **0** to materiality.
- Otherwise: score `>= 6` → **strong**; `>= 3` → **weak**; below → namesake-discarded.
- Discarded namesakes are **recorded** with their disambiguator (transparency), never
  silently dropped.

## 2. Assertion type (allegation vs. finding vs. resolved)

- **finding** — adjudicated: conviction, regulatory enforcement, court judgment, official
  designation. Highest assertion weight.
- **allegation** — accusation, ongoing probe, "alleged", reported but not adjudicated.
- **resolved-dismissed** — acquitted, charges dropped/withdrawn, dismissed. **Mitigating**:
  contributes **0** materiality (it is exculpatory context, still recorded in the chronology).

## 3. Materiality (deterministic, per matched hit)

`relevance = category_weight + assertion_addend + source_tier_addend + recency_addend`,
computed **only** for strong/weak matched hits (namesake-discarded and resolved-dismissed → 0).

| Input | Contribution (default) |
| ----- | ---------------------- |
| Category | money_laundering / terrorist_financing / sanctions_evasion / sanctions_designation +4; fraud / corruption / bribery / tax_evasion / market_abuse / pep_exposure +3; financial_crime_other / regulatory_breach +2; litigation_civil / adverse_other +1 |
| Assertion | finding +3; allegation +1; resolved-dismissed 0 |
| Source tier | Tier 1 +3; Tier 2 +1; Tier 3 +0 |
| Recency (vs `as_of_date`) | <=2y +2; <=5y +1; older +0 |

**Case materiality score** = the maximum hit relevance across matched hits. Bands:

- **Material** — score `>= 9`
- **Watch** — score `5..8`
- **Not material** — score `<= 4`

## 4. Disposition (recommendation only — evaluated in order)

1. Any matched (non-discarded) hit with `list_type` in {sanctions, pep} →
   **`recommend-route-sanctions-pep`** (route to `sanctions-match-adjudicator`; identity and
   status are **not** adjudicated here).
2. Subject has **no** DOB, nationality, or identifier **and** a name-matched hit exists →
   **`needs-data`** (do not attribute adverse media on a name alone).
3. Band = Material → **`recommend-escalate-edd`**.
4. Band = Watch → **`recommend-monitor`**.
5. Otherwise → **`recommend-no-material-adverse-media`**.

Every path is a recommendation for a human adjudicator. None closes, clears, determines, or
files.

## 5. Hard boundaries (fail closed)

- No **case closure**, **customer clearance**, **exoneration**, or **final determination**
  (including confirming a sanctions/PEP true match).
- No **SAR drafting/filing**, and no assertion that a SAR was or will be filed.
- No **attribution on a name alone** — unresolved subjects are `needs-data`.
- No **sanctions/PEP adjudication** or **risk-rating recalculation** (route out).
- No **tipping-off**: never produce customer-facing text revealing screening/monitoring/SAR.

## 6. Evidence bundle — required contents

Durable `case_id`; masked subject; **chronology** (dated matched events, each cited);
**parties** (as named in cited sources); **amounts** (with context + citation); matched hits
with entity-match basis, source tier, assertion type, and relevance basis; discarded
namesakes with disambiguators; reviewed-source citations; recommended disposition + reason.
Every item is cited; the screening baseline is cited as `screening:{config_version}@{as_of}`.
