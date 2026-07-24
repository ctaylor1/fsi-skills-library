# Domain Rules — engagement-history-brief

Orientation references: stewardship / active-ownership practice and applicable Stewardship
Code disclosure regimes (e.g., UK Stewardship Code reporting; SEC investment-adviser
recordkeeping for engagement records). The firm's stewardship policy and its controlled brief
template take precedence and are **versioned contracts** (`brief_version`,
`source_hierarchy_version`).

## Assembly is normalization + matching (deterministic, documented)

The brief is assembled, not judged. The engine performs only:

1. **Chronology** — engagements sorted reverse-chronologically by date; each row cited.
2. **Commitment ↔ progress matching** — each disclosed-progress record is linked to its
   commitment by `commitment_id`, across engagements (a commitment raised in one engagement
   can be progressed in a later one).
3. **Attendee roll-up** — firm-side and issuer-side attendees grouped by `(role, id)` with the
   list of engagements attended.
4. **Source-document dedup** — documents deduplicated by `doc_id`, most-recent first.
5. **Unresolved follow-ups** — follow-ups whose status is not `closed`.

## Commitment status (factual, date-based only)

| Status | Condition |
| ------ | --------- |
| `progress-disclosed` | At least one disclosed-progress record references the commitment |
| `overdue-no-disclosure` | `due < as_of_date` **and** no disclosed progress |
| `no-progress-disclosed` | No disclosed progress and `due` has not passed (or no due date) |

Status describes **what the record shows**, not whether the commitment was substantively met.
`progress-disclosed` means the issuer *disclosed and cited* something; judging adequacy is the
analyst's call. `overdue-no-disclosure` is a date observation, not a finding of failure.

## Hard boundaries (fail closed)

- No **engagement objective** chosen — `engagement_objective.selected` stays `null`.
- No **firm position / view** represented — `firm_position.represented` stays `false`.
- No **vote** cast, proposed, or recommended.
- No **substance judgment** ("met" / "failed") — status is factual and date-based.
- No **system-of-record write**, follow-up closure, or non-draft status.
- No **uncited** assembled row.

## Engagement objective & firm position — deliberately unset

The template carries both sections as placeholders with a recorded reason. The engine emits:

- `engagement_objective`: `{"selected": null, "note": "…human stewardship decision; route per
  handoffs"}`
- `firm_position`: `{"represented": false, "note": "…evidence-only; states no view"}`

Open follow-ups and source conflicts may be surfaced as **candidate discussion points for the
human**, phrased as facts drawn from the record — never as a chosen objective or a firm view.

## Brief — required contents

Durable `brief_id`; issuer profile with `as_of_date`; reverse-chronological engagement
chronology; commitments matched to disclosed progress with factual status; attendee roll-up by
role; deduplicated source documents; unresolved follow-ups; unset engagement objective and
unrepresented firm position (with reasons); citations for every item; `brief_version` and
`source_hierarchy_version`; the standing note.
