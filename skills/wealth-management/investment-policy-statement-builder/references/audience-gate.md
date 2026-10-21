# Declared-recipient audience projection, v1

`audience_gate.py` produces one draft for an exact set of people. It is a pure,
standard-library component with a small local CLI. It neither delivers a draft
nor grants access to a system. It does not accept a generic “internal” audience,
an all-audiences output bundle, a model-authored permission policy, or a raw
Markdown replacement for its controlled rendering.

This gate addresses declared audience separation. It must be composed with the
evidence gate and independent semantic review before any claim-release decision.
Passing it alone means **pending human review**, not approved for distribution.

## Detached inputs

All inputs are JSON. IDs are case-sensitive concrete identifiers (1–128 ASCII
letters, digits, or `_.:@/-`, beginning with a letter or digit). Reserved generic
identifiers such as `internal`, `public`, `reviewers`, `all`, and `*` are rejected.
Calling an actual group `person` does not make it a verified individual: the
registry is an operator assertion, not an authentication mechanism.

The request has exactly these keys:

```json
{
  "schema_version": "wealth-audience-request-v1",
  "request_id": "review-heath",
  "as_of": "2026-10-04",
  "recipient_ids": ["H-A", "H-B"]
}
```

The source packet is supplied separately from generated content. The unchanged
raw `content` and `reference` strings are the evidence gate's citation targets.
Additional top-level and source-row metadata, including genuinely supplied typed
source values, is permitted and included in the private input hash. It is never
automatically included in recipient output.

```json
{
  "schema_version": "wealth-source-packet-v1",
  "packet_id": "source-heath",
  "recipients": [
    {"recipient_id": "H-A", "kind": "person"},
    {"recipient_id": "H-B", "kind": "person"},
    {"recipient_id": "Mira", "kind": "person"}
  ],
  "sources": [
    {
      "source_id": "MEETING",
      "reference": "Meeting minutes, October 3, 2026",
      "content": "No portfolio decision was made.",
      "access": {
        "allowed_recipient_ids": ["H-A", "H-B", "Mira"],
        "effective_date": "2026-10-01",
        "valid_until": "2026-10-31"
      }
    }
  ]
}
```

Recipient rows have exactly `recipient_id` and `kind: "person"`. Every source
requires `source_id`, `reference`, `content`, and `access`. The access object has
exactly `allowed_recipient_ids`, `effective_date`, and `valid_until`. An empty
grant list explicitly denies everyone. Dates are real ISO calendar dates and the
interval is inclusive. Access applies to the whole source, including its ID and
reference; a finer-grained permission requires separately scoped source records.

Every listed recipient must exist in the detached registry. Unknown requested
people, unknown people in grants, duplicate IDs, missing permission metadata,
invalid dates, or ambiguous shapes stop projection, including when the malformed
source is unused. An explicit expired or future grant is valid metadata but does
not authorize the source on the requested day. Source ownership, professional
role, public availability, and possession of a document never imply permission.

The generated content plan has exactly `schema_version` and `blocks`. Every block
has exactly the six keys below. `source_ids` and `claim_ids` must be nonempty;
`depends_on_block_ids` may be empty. Lists have no duplicate IDs.

```json
{
  "schema_version": "wealth-audience-plan-v1",
  "blocks": [
    {
      "block_id": "meeting-outcome",
      "heading": "Meeting outcome",
      "text": "No portfolio decision was made.",
      "source_ids": ["MEETING"],
      "depends_on_block_ids": [],
      "claim_ids": ["/meeting/outcome"]
    }
  ]
}
```

`claim_ids` are JSON Pointer strings into the separately reviewed candidate.
Escaped segments `~0` and `~1` are supported. This component checks pointer syntax,
not resolution or claim coverage. The composing gate must require evidence claims
for all rendered assertions and verify that each claim's evidence sources are a
subset of the block's explicit/transitive sources. A text block, its heading, and
any derived summary/count must declare **all** contributing dependencies.
Omitting a semantic dependency is not detectable from graph structure alone.

## Projection and artifacts

For each block, the gate computes all transitive source dependencies. A block is
included only when every requested person has a current grant on every source in
that closure. Cycles, missing dependencies, and unknown sources stop projection.
An entirely excluded plan returns a generic failure, not an empty approved draft.
An iterative graph walk supports long chains without a recursion-depth failure.

The safe `projection` has `schema_version: "wealth-audience-projection-v1"`, sorted
`recipient_ids`, original-order included `blocks`, and sorted `sources`. A public
block contains only `heading`, `text`, and the used transitive `source_ids`. The
used-source registry contains only `source_id` and `reference`. It contains no
unused sources or grants. It never adds excluded topic labels, block IDs, claim
pointers, hidden counts, hidden-source IDs, input hashes, or the raw source packet.

The rendered Markdown has a fixed draft heading and human-review notice, the
exact recipient IDs, the included text, citations, and the used-source registry.
Author-supplied HTML, Markdown links, images, and comments render as literal text.
This prevents markup injection; it does not make unsupported plain text true.

For otherwise valid inputs, adding, changing, or removing inaccessible sources
and their inaccessible blocks leaves both public projection and rendered bytes
unchanged, provided the permitted content and its declared dependencies are
unchanged. The private receipt changes because the full input hashes change. A
new malformed record fails closed rather than being silently ignored.

The separate **operator-only receipt** binds canonical SHA-256 hashes of the full
request, detached packet, content plan, and public projection, plus the SHA-256 of
the exact rendered UTF-8 bytes. It also carries included block IDs and claim
pointers for composition. Never append this receipt to recipient drafts or use it
as a recipient-facing sidecar. It discloses internal metadata and input-change
signals. Its status is `declared-audience-projection-checked`; it explicitly says
permission authentication, semantic dependency completeness, and deployment
access enforcement are `not-established`.

## APIs and CLI

- `project(request, source_packet, content_plan)` returns
  `{projection, rendered_markdown, receipt}` or raises `GateError`.
- `validate_projection(request, source_packet, content_plan, bundle)` returns a
  list of internal errors. It reconstructs and compares the entire bundle.
- `validate_rendered(request, source_packet, content_plan, rendered_bytes, receipt)`
  returns internal errors. It reconstructs the actual expected bytes and receipt;
  copying a receipt or recalculating only a sidecar hash cannot bless edited text.
- `GateError.errors` and exception details are operator-only.
  `GateError.public_message` is always the generic failure message.

`tools/test_wealth_p5_audience.py:inputs()` returns a runnable `(request, packet,
plan)` example with household recipients, two advisors, a private source, and a
derived block that inherits the private dependency. Importing the test module
does not execute its checks or alter `sys.path`.

```sh
python3 -B shared/wealth-quality/audience_gate.py render \
  --request request.json --source-packet source-packet.json --plan plan.json \
  --rendered household-draft.md --receipt operator-only-receipt.json

python3 -B shared/wealth-quality/audience_gate.py validate \
  --request request.json --source-packet source-packet.json --plan plan.json \
  --rendered household-draft.md --receipt operator-only-receipt.json

python3 -B tools/test_wealth_p5_audience.py
```

The CLI refuses aliases among its inputs and two output files, including symbolic
and hard links, and never overwrites existing output. Exclusive creation protects
against substitution during file creation; local output mode is `0600`. Permission
denial happens before output creation. A filesystem failure can leave an empty or
partial local file, which cannot pass reconstruction validation. Caller-controlled
directories, secure retention, identities, source-grant authenticity, transport,
and recipient delivery controls remain deployment responsibilities. The CLI emits
only a generic failure message, never internal source details. No external action
or communication is performed.
