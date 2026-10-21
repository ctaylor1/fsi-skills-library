# Adjacent-Skill Handoffs — proxy-voting-reviewer

Evidence **collection/packaging** (this mode), **policy-consistency review** of a human-proposed
instruction (adjacent), and the **vote decision / ballot submission** (downstream, human) are
separate control activities with different entitlements, evidence depth, and outputs. This mode
emits a durable `case_id` + evidence bundle; it must not test a proposed vote against policy
(that is the checker's job) or cast/submit the ballot (that is the committee's/vote agent's).

## Upstream (feeds this mode)

| Upstream source | When it routes here | Handoff artifact |
| --------------- | ------------------- | ---------------- |
| Meeting notice / vote-agent feed | A new shareholder meeting (AGM/EGM/special) requires an evidence packet | Meeting id + agenda items + dates |
| `issuer-engagement-reviewer` | Prior issuer engagement is relevant context/precedent for an item | Engagement summary (cited as precedent context) |

These upstreams **surface** the meeting and context; they do not decide the vote. This mode
collects the record and packages it per agenda item for adjudication.

## Adjacent / downstream (this mode routes to)

| Route to | When | Handoff artifact |
| -------- | ---- | ---------------- |
| `proxy-voting-reviewer` `policy` mode | The analyst forms a **proposed** instruction and wants it tested against documented policy and analogous precedent | `case_id` + evidence bundle + the human's proposed instruction |
| **Proxy committee / stewardship (human)** | Any `packet-assembled` case needing a vote decision, and every `contested` item | `case_id` + cited evidence bundle + `recommended_next_step` |
| **Custodian / proxy operations (human)** | An `entitlement-discrepancy-flagged` case (record-date / share mismatch) | `case_id` + entitlement block (both values) — for correction, never corrected here |

The **vote decision, ballot submission, and any entitlement correction are human actions** — no
skill in the catalog casts a vote or edits entitlement, so those are human/ops handoffs, not
skill-to-skill routing. `proxy-voting-reviewer` `policy` mode reviews a **human-proposed**
instruction against policy; it does not decide the vote either.

## Duplicate-execution prevention

- This mode **does not** compare a proposed vote against policy/precedent (that is
  `proxy-voting-reviewer` `policy` mode); it compiles the underlying evidence.
- It **does not** cast, submit, or propose a vote, and it **does not** correct entitlement — those
  stay with the human committee, the vote agent, and the custodian.
- The checker and the committee consume this mode's `case_id`/bundle rather than re-collecting the
  record; the deterministic `case_id` (`PME-{meeting_id}-{item_id}`) prevents duplicate cases for
  the same item.

This document is scoped to `evidence` mode. A handoff to `policy` requires a separately prepared request `{mode: "policy", input: <native request>}` with reviewed source mappings. The current output is not the other mode's input. No automatic adapter or vote execution is supplied.
