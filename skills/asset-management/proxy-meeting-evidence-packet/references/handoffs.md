# Adjacent-Skill Handoffs — proxy-meeting-evidence-packet

Evidence **collection/packaging** (this skill), **policy-consistency review** of a human-proposed
instruction (adjacent), and the **vote decision / ballot submission** (downstream, human) are
separate control activities with different entitlements, evidence depth, and outputs. This skill
emits a durable `case_id` + evidence bundle; it must not test a proposed vote against policy
(that is the checker's job) or cast/submit the ballot (that is the committee's/vote agent's).

## Upstream (feeds this skill)

| Upstream source | When it routes here | Handoff artifact |
| --------------- | ------------------- | ---------------- |
| Meeting notice / vote-agent feed | A new shareholder meeting (AGM/EGM/special) requires an evidence packet | Meeting id + agenda items + dates |
| `engagement-history-brief` | Prior issuer engagement is relevant context/precedent for an item | Engagement summary (cited as precedent context) |

These upstreams **surface** the meeting and context; they do not decide the vote. This skill
collects the record and packages it per agenda item for adjudication.

## Adjacent / downstream (this skill routes to)

| Route to | When | Handoff artifact |
| -------- | ---- | ---------------- |
| `voting-policy-consistency-checker` | The analyst forms a **proposed** instruction and wants it tested against documented policy and analogous precedent | `case_id` + evidence bundle + the human's proposed instruction |
| **Proxy committee / stewardship (human)** | Any `packet-assembled` case needing a vote decision, and every `contested` item | `case_id` + cited evidence bundle + `recommended_next_step` |
| **Custodian / proxy operations (human)** | An `entitlement-discrepancy-flagged` case (record-date / share mismatch) | `case_id` + entitlement block (both values) — for correction, never corrected here |

The **vote decision, ballot submission, and any entitlement correction are human actions** — no
skill in the catalog casts a vote or edits entitlement, so those are human/ops handoffs, not
skill-to-skill routing. `voting-policy-consistency-checker` reviews a **human-proposed**
instruction against policy; it does not decide the vote either.

## Duplicate-execution prevention

- This skill **does not** compare a proposed vote against policy/precedent (that is
  `voting-policy-consistency-checker`); it compiles the underlying evidence.
- It **does not** cast, submit, or propose a vote, and it **does not** correct entitlement — those
  stay with the human committee, the vote agent, and the custodian.
- The checker and the committee consume this skill's `case_id`/bundle rather than re-collecting the
  record; the deterministic `case_id` (`PME-{meeting_id}-{item_id}`) prevents duplicate cases for
  the same item.
