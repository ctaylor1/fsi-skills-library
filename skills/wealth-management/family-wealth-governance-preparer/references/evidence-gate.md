# Detached structured-assertion evidence gate

This standard-library component addresses the P4 gap between a structurally valid
input and the raw evidence supporting its fields. It does **not** read natural
language for entailment. A separate reviewer records that judgment. Hashes, exact
quotes, names and an independence flag do not authenticate that reviewer or turn
their judgment into professional certification.

Use it before a native wealth workflow and retain all four detached inputs. It
does not replace native schema/calculation validation, audience permission review,
source authentication or institution-specific professional acceptance. Receipt and
inventory content can reveal restricted facts; keep both in the private review
workspace. They are not client deliverables.

## API and command line

`make_inventory(candidate, packet, producer_id)` returns a deterministic inventory.
`check(candidate, packet, inventory, review)` returns a receipt.
`validate_receipt(receipt, candidate, packet, inventory, review)` returns errors by
full reconstruction. Invalid JSON types/oversized inputs raise `ValueError` in the
API. Structural review or support failures produce a blocked receipt.

```sh
python3 evidence_gate.py inventory --candidate candidate.json --sources packet.json --producer extractor-A > inventory.json
# A separate reviewer reads the raw packet and candidate and supplies review.json.
python3 evidence_gate.py check --candidate candidate.json --sources packet.json --inventory inventory.json --review review.json > receipt.json
python3 evidence_gate.py validate --candidate candidate.json --sources packet.json --inventory inventory.json --review review.json --receipt receipt.json
```

`check` exits 0 for `reviewed-for-draft`, 1 for blocked, 2 for invalid file/JSON
input. `validate` checks receipt integrity, so a faithfully reconstructed **blocked**
receipt can validate successfully; consumers must also inspect its status.
All commands support `--help`, accept explicit local paths, and emit JSON to stdout.
They perform no network or business-system operation. JSON duplicate object keys,
nonfinite numbers and inputs over 8 MB are rejected. Limits are engineering bounds,
not financial or regulatory thresholds.

## Detached source packet

```json
{
  "schema_version": "wealth-source-packet-v1",
  "packet_id": "raw-7",
  "recipients": [{"recipient_id": "advisor-A", "kind": "person"}],
  "sources": [{
    "source_id": "S1",
    "reference": "Custody extract; record owner; dated reference",
    "content": "Account IRA-N is described only as a spouse IRA.",
    "data": {"account_id": "IRA-N"},
    "access": {
      "allowed_recipient_ids": ["advisor-A"],
      "effective_date": "2026-10-04",
      "valid_until": "2026-10-31"
    }
  }]
}
```

Source IDs are unique; reference/content remain untouched nonempty strings.
Optional `data` must be genuinely supplied raw structured data, not a model-created
extraction relabeled as authoritative evidence. The entire packet, including
audience/access metadata and any additional fields, is hashed. This component
does not interpret permission grants; the audience gate does that separately.
Changing any source text, metadata or permission invalidates the detached review.

## Inventory and reviewer decision contract

Candidate is a nonempty JSON object. Inventory covers **every scalar leaf, null
and empty list/object**, not a model-selected subset. JSON Pointers are claim IDs:
`/accounts/0/account_id`, `/upstream_issues`, `/engagement/capacity`. Escapes use
RFC 6901 `~0` and `~1`. Inventory fields contain `claim_id` and `value_sha256`;
its producer identity, candidate/source hashes and full ordered field inventory
are bound by `inventory_sha256` (hash of the inventory excluding that digest key).
An empty issue list is an assertion needing support, not an automatic exemption.

Review schema:

```json
{
  "schema_version": "wealth-evidence-review-v1",
  "candidate_sha256": "copy from inventory",
  "source_packet_sha256": "copy from inventory",
  "inventory_sha256": "copy from inventory",
  "reviewer": {
    "reviewer_id": "reviewer-B",
    "kind": "human",
    "independent_from_producer": true
  },
  "reviewed_at": "2026-10-04T12:00:00Z",
  "review_reference": "separately-retained-review-record",
  "decisions": [{
    "claim_id": "/account_id",
    "classification": "supported",
    "verdict": "supported",
    "subject_check": "matched",
    "field_check": "matched",
    "rationale": "Specific account identity matches the raw custody record.",
    "evidence": [],
    "value_binding": {"source_id": "S1", "pointer": "/data/account_id"}
  }]
}
```

One decision per inventoried field, with no duplicates or extra paths, is required.
The reviewer ID must differ from the producer, and declared independence must be
true. This detects explicit self-review; aliases, dishonest declarations,
qualifications and institutional authority remain unauthenticated. The timestamp
is a supplied timezone-aware review-record timestamp, not an independent time attestation.

- `classification`: `supported`, `derived`, `unknown`, or `local-label`.
- `verdict`: only `supported` clears a field. `unsupported`, `unreviewed`, absent or
  any other verdict blocks it. For unknowns, supported means the null/uncertainty
  representation is appropriate, not that a missing fact was established.
- `field_check` must be `matched`; `subject_check` must be `matched` for supported
  or derived facts. Unknown/local labels may use `not-applicable`. Mismatch or
  unreviewed alignment blocks. These are the reviewer's judgments, not NLP results.
- `evidence` is always a list. Each exact citation has `source_id`,
  `field: content|reference`, `start`, `end`, `quote`. Indices are zero-based Unicode
  character offsets, end-exclusive. Quotes must match the detached source exactly.
- Optional `value_binding` compares exact JSON type and value at a raw source
  pointer. `true` is not `1`, and string `"100"` is not number `100`. This checks
  equality, not that the selected source field means the intended candidate field.

Supported claims require citations or a typed value binding. A generic IRA sentence
does not establish tax-deferred treatment; the semantic reviewer must reject that
claim. If a reviewer falsely marks the inference supported, exact-span software
cannot detect the false semantic judgment. The regression suite demonstrates this
limit explicitly; this component alone does not close behavioral Q0 acceptance.

Unknown requires the candidate's actual JSON `null`; no conversion from
`none-recorded`, empty list, false, zero or guessed classification is performed.
Unknowns may cite the inspected context. Local labels are limited to string-valued
`schema_version`, `request_id`, `mode`, `goal_id`, `objective_id`, `item_id`,
`row_id`, `draft_id`, and `label` fields. They do not become source IDs, actual
account/household identities, priorities, review attribution or approval records.
Native validation still checks schema versions/modes. A reviewer must also detect
misuse of a permitted label to smuggle an authoritative statement.

Fields named `artifact_id`, `origin_artifact_id`, `upstream_artifact_id`, or
`input_hash` require an exact standalone identifier/hash span or exact typed raw
source value. A broad paragraph citation does not allow an invented origin.
Those values and `priority` cannot be derived. A mentioned upstream ID is attributed
source evidence only; it is not proof the original artifact exists or was validated.

## Derived values and safe projection

```json
{"operation":"difference","operands":["/gross_proceeds","/fee"],"unit":"USD"}
```

A derived decision adds `derivation` with that shape. Operations are `sum`,
`difference` (two operands), `product`, `ratio` (two, nonzero denominator) and
`round` (one operand, explicit integer `places` 0–8, ROUND_HALF_UP). No code,
arbitrary expression, unbound literal assumption or implicit rounding is executed.
All operands must be already-supported/derived claims; cycles and unknown/local/
blocked dependencies fail. Decimal arithmetic uses 60-digit working precision.
Operands and target results are bounded to 60 coefficient digits, absolute value
at most 1e30 and stored decimal exponent -30 through 30. These are engineering
bounds. Except explicit `round`, any Inexact/Rounded/Underflow/Overflow arithmetic
signal blocks the claim. A nonterminating ratio is therefore blocked; this gate
does not invent a display tolerance or accept an approximate ratio as exact.
The reviewer remains responsible for the formula, compatible units and economic
meaning. Transitive source IDs accompany each derived claim in the receipt.

Receipt status is `reviewed-for-draft` only if bindings, complete inventory and
every field decision qualify. It retains `claim_reviews` (claim_id, classification,
status, source_ids, findings), safe `reviewed_fields`, `withheld_claim_ids`, reviewer
declarations, limitations and a full content digest. `projected_input` equals the
unchanged candidate only when all fields qualify; otherwise it is null. Partial
reviewed fields are diagnostic evidence, not a schema-valid executable input.
Do not drop array entries or fabricate nulls to force a native schema to pass.
Amend the candidate from raw evidence and obtain a newly bound review instead.

Release composition must reconstruct the receipt from its detached originals,
require overall `reviewed-for-draft`, resolve every block claim ID to a reviewed
row, and include **all** its transitive source IDs in the block's source dependencies.
Missingness statements and labels still require audience assessment in context.

## Executable worked example

`example()` returns `(candidate, packet, inventory, review)` for a small **synthetic**
account with a supplied value and unknown tax treatment. It is for local integration
tests and schema learning; it is not a factory for real reviewer approvals.

```python
import evidence_gate
candidate, packet, inventory, review = evidence_gate.example()
receipt = evidence_gate.check(candidate, packet, inventory, review)
assert receipt["status"] == "reviewed-for-draft"
assert receipt["projected_input"]["tax_treatment"] is None
assert not receipt["identity_authenticated"]
```

Tests: `python3 -B tools/test_wealth_p5_evidence.py` from the repository root.
