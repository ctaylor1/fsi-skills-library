# Source Map — customer-interaction-summarizer

Every item in the summary must cite one of the sources below, ranked. See the shared
platform services in [`docs/SHARED-SERVICES.md`](../../../../docs/SHARED-SERVICES.md).

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Contact-center (CCaaS) **recording/transcript of record** | Calls, chats, IVR — the literal segments spoken/typed | Read-only |
| 2 | **CRM / case-management** interaction log & email system of record | Email threads, agent notes, case history, prior contacts | Read-only |
| 3 | **Complaint-management system** | Logged complaints, recorded commitments, disclosure logs | Read-only |
| 4 | **Approved knowledge / product terms** | Only to explain a term used in the interaction — never to add new facts | Read-only |
| 5 | User-provided transcript/file | Only when 1–4 unavailable; must be labeled as unverified | Read-only |

Never let a user assertion override the transcript of record. If sources conflict, present
both with citations and stop for human review.

## Citation format

Each extracted item (key point, commitment, disclosure, open action) carries a citation of
the form `{system}:{ref}` pointing at a specific segment — e.g.
`ccaas:call=INT-7741;seg=4` or `crm:case=C-9021;email=3` or `complaints:cmp=CMP-55;line=2`.
The machine-readable output stores the citation per item; the narrative references the same
segments inline where an item is stated.

## Freshness / effective dates

- Every interaction carries an **interaction date**; the summary states a single date and a
  single channel. Do not merge interactions across dates or channels.
- **ASR / transcription confidence** matters: segments flagged inaudible, `[redacted]`, or
  low-confidence are excluded from the recap and listed under Data gaps.
- A **partial or truncated** transcript is summarized as partial and labeled — never
  extrapolated to a full call.

## Least-privilege operations (deployment)

- `interactions.read(interaction_id)` → interaction header + ordered segments (bounded page
  size).
- `transcript.read(interaction_id)` → transcript segments with speaker, timestamp, and
  citable `ref`.
- `case.read(case_id)` → linked case/complaint context for cross-referencing commitments.
All read-only, deterministic schemas, durable `summary_id`, below the fixed timeout.
