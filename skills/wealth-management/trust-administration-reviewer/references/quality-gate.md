# Source and recipient quality gate

These controls supplement the native calculator and output validator. They require
detached original evidence, a complete candidate field inventory, separate review
decisions and a single exact recipient set. They never authorize delivery or advice.

## Working sequence

1. Keep the operator-supplied `wealth-source-packet-v1` source packet unchanged in
   a restricted work area. The permission registry names individual recipients,
   including each internal colleague. An omitted, expired or group-only permission
   is insufficient. Do not extract or expand permissions yourself to make a gate pass.
2. Build the native candidate JSON faithfully. Keep missing classifications,
   priorities, account membership and review facts null. Never use a source owner's
   name or applicability review date as evidence of a different performed review.
   Local tracking IDs must not masquerade as supplied upstream artifacts.
3. Run `python scripts/evidence_gate.py inventory --candidate candidate.json
   --sources source-packet.json --producer PRODUCER-ID > inventory.json`.
   Read [evidence-gate.md](evidence-gate.md) for the exact field review contract.
   A separate reviewer checks every leaf and empty container. The generating agent
   must not invent another identity, review record or approval. If review is absent,
   retain the candidate and inventory as pending; never claim quality clearance.
4. After complete field review, run native input, calculation and output validation
   on the exact reviewed input. A native validator pass alone says nothing about
   source truth. If native schema cannot express an unknown, withhold that analysis
   and supply a conditional, source-backed working note rather than fill a guess.
5. Build a content plan and exact audience request using
   [audience-gate.md](audience-gate.md). Every text block, including headings,
   references candidate JSON Pointer `claim_ids` plus every supporting source and
   upstream block dependency. Include restrictions inherited by derived facts.
   Each client, advisor, service manager, facilitator and trust officer needs an
   explicitly permitted projection. Never attach the full packet to a wider draft.
6. Run the audience builder to obtain a pending preview. A separate reviewer reads
   the actual preview, original evidence and whole plan, checking source support,
   complete semantic dependencies and exact recipients. Keyword scans and hashes
   cannot supply this judgment. The same separate reviewer may do field and draft
   review; that reviewer must be distinct from the producer.
7. Compose the gates with `quality_gate.py` below. With no draft review it returns
   `pending-draft-review` and records the exact required bindings in its restricted
   receipt; it emits no reviewed recipient file. Pass a completed separate review
   to a **new** output pair. Run `--verify` on the actual final file before handoff.

```sh
python scripts/quality_gate.py --candidate candidate.json --sources source-packet.json \
  --inventory inventory.json --field-review field-review.json \
  --request advisor-request.json --plan content-plan.json \
  --draft-review advisor-review.json --receipt internal-advisor-receipt.json \
  --rendered advisor-draft.md
```

Use the same arguments plus `--verify` to reconstruct and compare existing files.
Inputs, receipt and rendered file must have distinct paths. Prior outputs are not
overwritten. Newly created receipt and recipient files use owner-only permissions
(0600, subject to any stricter process umask), with exclusive creation. This is
local file protection, not recipient authentication or access enforcement by a
delivery system. Only the recipient file belongs in that audience's delivery area;
all other files remain restricted operator evidence. Missing review is a useful
staged result, not a reason to stop gathering supported facts or preparing a draft.

## Separate draft review contract

`schema_version` is `wealth-draft-review-v1`. Copy the `bindings` from the pending
combined receipt's `review_request` only after inspecting its exact inputs and
the rendered audience preview. Supply `reviewer` with `reviewer_id`, `kind`
(`human` or `model`), `independent_from_producer: true`; an ISO timestamp with
timezone in `reviewed_at`; and a retained `review_reference`.

`checks` has exactly three entries with `criterion`, `status` (`pass`, `fail` or
`not-assessed`) and a substantive `rationale`:

- `content-supported`: each actual heading, statement and source reference is
  faithful to reviewed evidence, uncertainty and calculation limits.
- `dependencies-complete`: the plan lists every semantic source dependency,
  including indirect references and restricted facts inferred from other blocks.
- `recipient-scope-correct`: the exact named recipients may receive all included
  text and source metadata; no restricted fact, identifier, label or omission count
  is disclosed through this draft or its accompanying files.

All must pass to emit `reviewed-draft`. Changed source text, field review, plan,
recipients or rendered bytes requires a newly bound review. A failed or absent
review cannot be replaced by the producer's claim that it checked its own work.

## Boundaries

The controls verify declarations and recorded assessments; they do not authenticate
sources, permissions, reviewer identity or independence, and cannot prove semantic
truth. Runtime isolation, signed identity, access enforcement, retention policy and
qualified professional approval belong to deployment. Native tools remain usable
for backward compatibility and can bypass this workflow; do not label their output
P5-reviewed. The operational instructions require this gate for model-created
inputs and audience drafts in this package.
