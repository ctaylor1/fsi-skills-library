---
name: iso-20022-message-interpreter
description: >-
  Parse and explain ISO 20022 payment messages (pain, pacs, camt and related families) in
  plain language: classify the message, decode field semantics and status/reason/purpose
  codes, tie out control totals (NbOfTxs, CtrlSum), validate identifiers (IBAN, BIC, UETR,
  EndToEndId), and diagnose validation, rejection, truncation, and character-set or
  status-reporting risks — every finding source-linked. Use when a payments operations or
  implementation analyst asks "what does this pacs.008 / pacs.002 / camt.05x mean", "why was
  this message rejected", "what does status RJCT or reason AC04 mean", "will this remittance
  be truncated", or wants a control-total and identifier check on a message. Read-only and
  explanatory: it never repairs, corrects, resubmits, cancels, or moves a payment, and never
  makes a fraud, sanctions, AML, compliance, or suitability determination — route those to
  the payment failure, exception, or repair workflows or a licensed specialist.
license: MIT
compatibility: Amazon Quick Desktop; requires ISO 20022 schema/message-repository, usage-guideline (CBPR+/HVPS+/SEPA/FedNow/RTP) and external code-set retrieval, a schema + business-rule validation engine, and ISO-to-MT transformation-map integrations (all read-only).
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Utility skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Explain & summarize"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Payments operations / implementation analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# ISO 20022 Message Interpreter

## Purpose and outcome
Turn a single ISO 20022 payment message — or a linked status/response — into a faithful,
plain-language explanation an analyst can act on. A successful output tells the reader what
the message **is**, what its key fields **mean**, whether its **control totals and
identifiers hold**, what any **status/reason code** signals, and where **truncation or
character-set loss** would occur on down-mapping — with every statement traceable to the
message and the governing code list. It stops at explanation: it never repairs, resubmits,
or dispositions the payment.

## Use when
- "Interpret / explain this pacs.008 (or pain.001, pacs.002, pacs.004, camt.053/054/056)."
- "What does status RJCT / ACSP / PDNG mean?" or "what does reason code AC04 / AM04 / RR03 mean?"
- "Do the control totals tie out (NbOfTxs, CtrlSum)?" or "is this IBAN / BIC / UETR valid?"
- "Will this remittance / name field be truncated when we map to MT?" or "are there
  characters that won't survive the SWIFT-x set?"
- The analyst pastes a de-identified message (or its normalized JSON) and wants a readable,
  cited breakdown of fields, identifiers, and lifecycle state.

## Do not use
- The user wants to know **why a payment failed across the whole chain** (initiation →
  routing → screening → clearing → settlement) → route to `payment-failure-diagnoser`.
- The user wants an **exception case** built (chronology, parties, cancellation/investigation
  flow) → route to `payment-exception-investigator` (R3).
- The user wants the payment **repaired, corrected, and resubmitted** → route to
  `payment-repair-assistant` (R4, approval-gated); this skill never repairs.
- The user wants a **fraud / sanctions / AML / compliance determination**, or asks whether
  funds are "safe to release" → out of scope; explain the message and route to the regulated
  function.
- The user wants an already-settled **settlement report** summarized → `settlement-report-summarizer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). In short: `payment-failure-diagnoser`
and `payment-exception-investigator` may call this skill to interpret a specific message;
this skill routes end-to-end tracing, casework, and repair **out** to those skills and to
`payment-repair-assistant`, handing off its cited interpretation object keyed by the message
identifiers (MsgId, EndToEndId, UETR). It performs none of that downstream work itself.

## Inputs and prerequisites
- **One message at a time**, as a de-identified normalized JSON view: `message_type`
  (`<family>.<NNN>.<VVV>.<NN>`), `group_header` (MsgId, CreDtTm, and NbOfTxs/CtrlSum where
  applicable), and a non-empty `transactions` list. Each transaction needs an `end_to_end_id`,
  an `amount` (value + ISO 4217 currency), and a `source` citation. See the schema in
  [scripts/validate_input.py](scripts/validate_input.py).
- The **exact schema version** and the applicable **usage guideline** (CBPR+, HVPS+, SEPA,
  FedNow, RTP). Field mandatoriness and code lists depend on both.
- Read access to the schema/message repository and external code sets; no write access to
  any payment system is required or used.

## Source hierarchy
Rank sources and cite every field meaning and coded value. See
[references/source-map.md](references/source-map.md).
1. Registered **ISO 20022 schema** for the exact message version (highest).
2. **Usage guideline / market practice** for the scheme (mandatoriness, restrictions).
3. **Validation engine** (structural + business-rule findings).
4. **External code sets** (status/reason/purpose; ISO 4217/9362/13616) and **transformation
   maps** for down-mapping/truncation.
Never let a user assertion override the registered schema or the usage guideline; on a
conflict, surface both with citations. Decode codes against the version effective on the
message's CreDtTm; treat an unlisted code as **unknown**, not guessed. Field-level rules and
code interpretations are in [references/domain-rules.md](references/domain-rules.md).

## Workflow
1. **Scope** — confirm a single message and its `message_type` and usage guideline. If the
   family is outside pain/pacs/camt, require an explicit cited guideline before interpreting.
2. **Validate input** — run [scripts/validate_input.py](scripts/validate_input.py). Structural
   problems (missing type/identifiers/citations, bad datetime) **fail closed**; data-quality
   issues (control-total, currency, truncation, character-set, missing rejection reason) are
   carried forward as items the explanation must surface.
3. **Interpret (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): classify the
   message and family; tie out NbOfTxs and CtrlSum; validate IBAN (mod-97), BIC shape, and
   UETR (UUIDv4); detect truncation and character-set risk; decode status/reason codes for
   status reports. Each finding attaches the transaction's source citation.
4. **Explain** — write the plain-language narrative: what the message is, per-transaction
   figures with citations, control-total result, identifier findings, truncation risks, and
   any status/reason meaning — as neutral observations, never as instructions to act.
5. **Route, don't act** — if the message signals a genuine failure, exception, or repair
   need, name the appropriate downstream skill (see handoffs); do not perform it.

## Validation loop
Run `validate_input` before interpreting and `validate_output` after. `validate_output`
confirms citation coverage, control-total consistency, the no-advice / prohibited-claim
screen, disclaimer presence, and rejected-status reason coverage. If a figure lacks a
citation, a rejection has no reason and no explicit missing-reason finding, or the narrative
contains advice/repair/determination language, **fix or fail closed** — do not deliver an
untied or advice-tainted interpretation.

## Human approval
None required for the analyst's own read. **Human review is required before the
interpretation is delivered externally** (to a counterparty/beneficiary bank, into a customer
communication, or written to a system of record) — `aws-fsi-human-approval: external-delivery`.
See [references/controls.md](references/controls.md).

## Failure handling
- **Structural/schema failure** (bad `message_type`, missing identifiers or citations,
  malformed datetime) → stop; report the exact defect; do not interpret partial structure.
- **Control-total break** (NbOfTxs/CtrlSum mismatch) → state it as a finding; do not
  silently correct or reconcile it.
- **Invalid identifier** (IBAN check-digit, BIC shape, UETR) → flag it; interpret the rest.
- **Unknown code** (status/reason/purpose not in the referenced version) → report as
  unknown with a pointer to the code list; never guess its meaning.
- **Missing rejection reason** on a RJCT/return → flag that the cause cannot be explained.
- **Source conflict** (schema vs. usage guideline) → present both with citations; stop for review.
- **Tool timeout / permission denial** → report partial results and the exact gap; assume no retry.

## Output contract
1. **Header** — message name and type/version, family description, usage guideline.
2. **Summary** — NbOfTxs, total amount and currencies, and whether control totals balance.
3. **Per-transaction** — EndToEndId, UETR, amount, and any status interpretation, each cited.
4. **Findings** — control-total, identifier, truncation/character-set, and status findings
   with severity and a citation; unknown codes labeled as such.
5. **Machine-readable** — the interpretation object (classification, tie-outs, findings,
   citations) keyed by message identifiers for downstream skills.
6. **Standing disclaimer** — "Interpretation and explanation only; not a payment
   instruction, repair authorization, or compliance/fraud determination."
Every stated figure and code meaning carries a citation. See
[references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII and possibly cardholder data. Mask account/IBAN and card identifiers
(show last 4) in human-facing output; keep full values only inside the approved environment.
Never place message content in URLs or external destinations. Log the source read, the
interpretation produced (input identifiers + schema version), and any external-delivery
approval (who/when); retain per records policy. See [references/controls.md](references/controls.md).

## Gotchas
- **Version matters**: element names and code lists differ across `.VVV.NN` versions —
  interpret against the message's own version, not a newer one.
- **A reason code is a claim, not a verdict**: `FRAD` or `RR03` in the data is what a party
  asserted; this skill relays and routes it, it does not adjudicate fraud or sanctions.
- **Control totals are integrity checks, not amounts to fix**: a NbOfTxs/CtrlSum mismatch is
  surfaced and routed, never silently reconciled.
- **Truncation is silent in production**: a 200-character remittance line looks fine in ISO
  but loses data at the MT `:70:` boundary — always flag > 140-char lines and non-SWIFT-x
  characters.
- **EndToEndId must survive the chain**: if it changes between the original and a status
  report, that is a finding, not a normalization to smooth over. `NOTPROVIDED` is a literal,
  not a missing value.
- **"Explain" is not "act"**: decoding RJCT/AC04 as "closed account" is in scope; telling the
  user to resubmit, release funds, or approve is out of scope and fails the output screen.
