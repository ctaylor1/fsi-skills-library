# Domain Rules — sanctions-match-adjudicator

Orientation references: OFAC's *Framework for Compliance Commitments* and the **50% Rule**
(an entity owned 50%+ by one or more blocked persons is itself blocked), EU/UN/HMT-OFSI
consolidated lists, and the firm's sanctions program standard. The firm's program standard and
its **match-factor / band configuration** take precedence and are versioned contracts.

## Match factors (deterministic, documented)

Each factor is computed by comparing the subject to the matched listed entity. Corroborators add
weight; discriminators subtract. Only fired factors appear in the bundle, each with citations.

| Factor | Kind | Weight (default) | Fires when |
| ------ | ---- | ---------------- | ---------- |
| `name_primary_match` | corroborator | +3 | subject name == listed primary name (normalized) |
| `alias_match` | corroborator | +2 | a subject name/alias matches a listed name/AKA (and primary did not) |
| `dob_match` | corroborator | +3 | DOB present on both and equal |
| `strong_id_match` | corroborator | +5 | a strong identifier (passport, national_id, registration_number, tax_id, lei) matches by type+value |
| `nationality_match` | corroborator | +1 | nationality present on both and equal |
| `place_of_birth_match` | corroborator | +1 | place of birth present on both and equal |
| `address_country_match` | corroborator | +1 | a subject address country matches a listed address country |
| `ownership_nexus` | corroborator | +6 | subject owned ≥ `ownership_threshold_pct` (default 50%) by a listed party (50% Rule) |
| `transaction_jurisdiction_nexus` | corroborator | +2 | a payment country matches the listed entity's nationality/address country |
| `program_asset_freeze` | corroborator | +1 | the listing is on an asset-freeze program (OFAC-SDN/SSI, EU-CFSP, UN, HMT-OFSI) |
| `dob_mismatch` | discriminator | −3 | DOB present on both and differs |
| `strong_id_mismatch` | discriminator | −4 | same-type strong identifier present on both but values differ (no match) |
| `nationality_mismatch` | discriminator | −2 | nationality present on both and differs |
| `entity_type_mismatch` | discriminator | −4 | subject entity type differs from the listed entity type |

`match_score` = sum of all fired factor weights.

## Disposition logic (a RECOMMENDATION only)

Evaluated in order; the first that applies wins, and the reason is recorded as `disposition_basis`:

1. **`needs-data`** — the subject carries a name only (no DOB, identifier, nationality, place of
   birth, address, ownership, or transaction context). A name-alone hit cannot be confirmed or
   discounted. `disposition_basis = needs-data`.
2. **`possible-duplicate`** — a prior/open case exists for the same `subject_id` + `list_ref`.
   Link for human confirmation; do not re-adjudicate. `disposition_basis = possible-duplicate`.
3. **`recommend-true-match-escalate` (ownership override)** — an `ownership_nexus` fired (50%
   Rule). Recommended even if the entity type differs from the listed owner's.
   `disposition_basis = ownership-override`.
4. **`recommend-true-match-escalate` (strong-id override)** — a `strong_id_match` fired together
   with a `name_primary_match` or `alias_match` (identity corroborated).
   `disposition_basis = strong-id-override`.
5. **`recommend-potential-match-l2-review` (conflict guard)** — a strong corroborator pair
   (name/alias + DOB or nationality match) and a strong discriminator (identifier or DOB
   mismatch) disagree, and the numeric score is below the review band. Never auto-discount;
   route to L2. `disposition_basis = conflict-guard`.
6. **Score bands** (`disposition_basis = score-band`):
   - `match_score ≥ true_match_min` (default **6**) → `recommend-true-match-escalate`
   - `match_score ≥ review_min` (default **2**) → `recommend-potential-match-l2-review`
   - otherwise → `recommend-false-positive-discount`

The score bands are triage of the *evidence*, not a determination. Overrides and the conflict
guard exist because a numeric score alone must never confirm identity or clear a genuine-looking
hit.

## Evidence bundle — required contents

Durable `case_id` (`SANC-<alert_id>`); `subject_id`, `list_ref`, `list_program`,
`screening_context`; parties (subject, matched listed entity, listed owners, transaction
parties) with roles and citations; a time-ordered chronology (list entry/update, transaction,
prior cases, screening hit) with a citation on every event; amounts (payment amount/currency, or
null for non-payment screening); the fired match factors with weights and citations;
`match_score`; linked cases; and a de-duplicated citation list.

## Hard boundaries (fail closed)

- No **confirmation/discount**, **block/reject/release**, **unblock**, **filing**, or **closure**.
- No **adjudication without screening provenance**.
- No **clearing on name alone**, and no **auto-discount of conflicting strong signals**.
- No **auto-merge** of duplicates; dedup **links** for human confirmation.
- No **tipping-off**: never produce customer-facing text revealing screening/blocking/SAR activity.
