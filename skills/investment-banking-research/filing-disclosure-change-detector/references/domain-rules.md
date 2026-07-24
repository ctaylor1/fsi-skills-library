# Domain Rules — filing-disclosure-change-detector

Deterministic, cited **change findings** across two versions of a filing/disclosure, and how
the detected change **types** map to human review lanes. Markers, prefixes, and thresholds
are configuration (versioned, owned by the research-supervision / disclosure-controls
function), not hard-coded judgments. Nothing here determines materiality, legal
significance, or investment implication — those are human determinations.

## Finding taxonomy

| Finding type | Fires when | Evidence attached |
| ------------ | ---------- | ----------------- |
| `changed_language` | A section present in both filings has different whitespace-normalized, case-folded text | Added/removed sentence spans, each cited to its version; `similarity_ratio`, word counts |
| `section_added` | A non-risk section present in current but not prior | Bounded snippet of the new section (current cite) |
| `section_removed` | A non-risk section present in prior but not current | Bounded snippet of the removed section (prior cite) |
| `new_risk_factor` | A **risk-factor** section (kind `risk_factor` or `section_id` under a `risk_section_prefixes` item, default `1a`) present in current but not prior | New risk-factor snippet (current cite) |
| `removed_risk_factor` | A risk-factor section present in prior but not current | Removed risk-factor snippet (prior cite) |
| `restatement_language` | A section present in the **current** filing contains any configured restatement/non-reliance marker | Verbatim excerpt + `markers_detected` list (current cite) |
| `exhibit_added` / `exhibit_removed` | An exhibit (by `exhibit_no`) present on only one side | Exhibit description + cite; `material_contract` flag |
| `exhibit_changed` | An exhibit present on both sides with a different content `hash` or description | Current + prior descriptions, both cited; `material_contract` flag |

Findings are **factual and independent**; each is reported with its own citation and
evidence. There is no composite "importance score".

### Default restatement / non-reliance markers (configurable)

`restate`, `restated`, `restatement`, `revised previously issued`, `should no longer be
relied upon`, `non-reliance`, `item 4.02`, `prior period adjustment`. Detection is literal
substring matching on normalized text — it flags that the **wording is present** and quotes
it. It does **not** conclude that a restatement occurred, that prior statements are
unreliable, or that the matter is material; a qualified human makes that call. (`material
weakness` may be added per deployment, but note it is an ICFR concept, not by itself a
restatement.)

### "Material" exhibit note

An exhibit whose number begins with a `material_contract_prefixes` value (default `10`,
i.e. Item 601(b)(10)) is flagged `material_contract: true`. This is the **filer's own
exhibit-index categorization** (a material contract under the SEC exhibit rules), surfaced
as a neutral routing attribute. It is **not** this skill judging that the exhibit or its
change is material to investors.

## Review-lane routing (deterministic fan-out, NOT a ranking)

Detected change **types** map to which human functions should look. This is a notification
fan-out so the right reviewer sees the change — it does not rank or grade importance.

| Detected type present | Review lane added |
| --------------------- | ----------------- |
| any `changed_language` / `section_added` / `section_removed` | Covering analyst |
| any `new_risk_factor` / `removed_risk_factor` | Research supervisory analyst |
| any `restatement_language` | Financial-reporting / disclosure-controls reviewer |
| any `exhibit_*` with `material_contract: true` | Legal / contracts reviewer |

Lanes are sorted and de-duplicated. `validate_output` recomputes both the `change_summary`
counts and the `review_routing` list from the findings and fails closed on any mismatch.

## Hard boundaries (fail closed)

- Never state or imply that a change **is material / immaterial**, "material to investors",
  or that materiality is established — describe the change factually and route to a human.
- Never assert **legal significance**: no "violation", "breach", "unlawful", "legally
  significant", "misrepresentation", "fraudulent".
- Never assert an **investment implication**: no rating/target/estimate change, no
  buy/sell/hold/upgrade/downgrade, no bullish/bearish/thesis/valuation call.
- Never conclude that a **restatement occurred** or that prior statements are unreliable;
  detect and quote the wording only.
- Never treat a non-filed source (press release, transcript, draft) as the position of
  record over the as-filed text.

## Data-quality handling

- Missing exhibit list on a side → `exhibit_*` reported in `not_evaluable`; do not fabricate
  exhibit changes.
- No overlapping `section_id` → `changed_language` not evaluable; `validate_input` warns to
  confirm alignment.
- Renumbered items → align `section_id`s before running; otherwise expect spurious
  add/remove findings (a `changed_language` mis-reported as add+remove).
