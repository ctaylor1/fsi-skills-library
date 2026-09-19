# P4 handoff scenarios and test-only adapters

The executable companion is `tools/test_wealth_p4_handoffs.py`. It invokes the real
package calculation and output-validation CLIs in separate subprocesses. Every
upstream artifact is produced during the test, validated, and then consumed by the
next adapter. It does not substitute independently prepared downstream results.
Nothing is sent, approved, opened, reassigned, traded, borrowed or written to a CRM.

Run from the repository root with an available Python 3 runtime:

```sh
PYTHONDONTWRITEBYTECODE=1 python -B tools/test_wealth_p4_handoffs.py
```

The test module is safe to import and uses standard-library modules only. Temporary
requests and outputs live in system temporary directories and are removed afterward.
There are 20 substantive test methods, five primary chains and 14 distinct skills.
They are deterministic integration evidence, **not real-model behavioral evidence**.
The separate P4 model-response experiment must be assessed independently.

## Five actual chains

| Chain | Generated data consumed downstream | Independent expected facts |
| --- | --- | --- |
| Discovery → household reconciliation → risk → IPS | Discovery assets/debt/goal plus a separately sourced account mapping create reconciliation records; reconciled account amounts and discovery goal populate risk dimensions; risk facts and originating concerns populate the draft mandate. | Assets 720,000; debt 90,000; net worth 630,000; liquid cash 25,000 versus dated need 90,000 gives shortfall 65,000. Willingness 25% implies 180,000 versus a separately human-assessed loss capacity of 72,000/10%. No risk score or effective IPS is created. |
| Generated IPS → client review → follow-up | Actual IPS identity and unresolved issues become cited planning items, open actions and questions; reconciled account values and discovery goals form the review packet. The resulting packet feeds the follow-up actions and communication body. | Review reports 720,000 supplied account value, preserves every concern's original code/message/artifact, and retains owners, due dates and citations into the follow-up. All approval entries remain pending; delivery and CRM writing remain disabled. |
| Family → trust → account service | A generated family legal-authority question and discussion text accompany an explicitly reviewed family-member/beneficiary mapping. Trust output's cash and remaining requested amount populate a service packet. | Trust opening cash 50,000 + receipt 2,000 − settled payment 3,000 = 49,000. Requested 8,000 − prior payment 1,000 − current payment 3,000 = 4,000 only when evidence qualifies. An unresolved family authority question makes the qualified remaining amount unknown; null stays null in service preparation. Separately cited professional resolution can clear that evidence gap, but never grants payment approval. |
| Private market → lending/liquidity | The generated account-specific cash schedule, original issue identities and source registry populate a funding request. | Cash 22,000 less reserve 4,000 = 18,000. Other obligation 4,000 plus outstanding calls/fees 22,000 produces a known-obligation deficit of 8,000; incremental forecast produces 15,000. The adapter requests the 8,000 known-obligation amount by the first deficit date, 2026-09-24. It does not reuse source-account cash, treat unsettled distributions as cash, or include forecast calls in the committed need. Separate sale scenario nets 10,000 −100 −1,200 = 8,700; no option is selected. |
| Construction → comparison → recommendation evidence | Generated model weights, cash and sizing amounts populate proposals; separately supplied security costs/exposures and proposal fees complete the comparison. Its exact costs and concerns populate permitted recommendation evidence items and per-check unresolved issues. | On 400,000, growth EQ-A caps at 35%/140,000 and EQ-B becomes 30%. Annual costs are 80 and 68 bps; first-year amounts are 3,400 and 3,020, right-minus-left −380. Known issuer exposure is 65%, above the supplied 60% limit. Model-review and cost/concentration concerns persist; missing client evidence remains missing. No candidate, proposal or recommendation is selected. |

## Input fixtures and additional evidence

These are synthetic records, not observed clients, authenticated approvals or legal
opinions. Package examples and earlier independent scenarios were consulted for
schema shape. Household identities, principal scenario facts, cash amounts, costs,
model allocations and expected arithmetic were authored for these chains. No golden
output files supply the expected results.

- `discovery.json`, `account-mapping.json`, `risk-assessments.json` and
  `ips-policy.json`: source collection, explicit registration mapping, independent
  human assessment and substantive draft mandate policy. The separate mapping splits
  assets into investment 695,000 and cash 25,000; no account is inferred from prose.
- `review-policy.json` and `followup-meeting.json`: synthetic controlled template/
  disclosure policy and separately asserted meeting facts. A prepared review does
  **not** prove a meeting occurred. The meeting fixture explicitly supports discussion
  of carried actions; a production adapter would have to verify actual meeting notes.
- `family.json`, `subject-map.json`, `trust.json`, `service-policy.json`: family
  discussion records, an internal-purpose permission/identity mapping, separately
  reviewed trust instruments and cash ledger, and a service checklist.
- `private.json`, `lending-policy.json`: since-inception private-position ledger,
  account-specific cash, known obligations, forecasts and separate liquidity options.
- `construction.json`, `comparison-economics.json`, `recommendation-policy.json`:
  models/constraints, separately sourced fee and exposure assumptions, and a supplied
  advisory evidence-review profile. General recommendation evidence is intentionally
  incomplete; the adapter never manufactures client-profile or disclosure delivery.

Some fixtures are **adapter ingredients**, not standalone complete package requests.
The harness fills dependent fields exclusively from freshly generated upstream output
and explicitly supplied additional source facts. Replaying a downstream ingredient
by itself is not an end-to-end test and may correctly reject or return needs-data.

## Contract-specific mappings and limits

1. Common source IDs are preserved exactly. A same-ID/different-record collision
   rejects instead of overwriting. An additional generated-artifact source records
   the exact artifact ID and input hash; it supplements original source records.
   Hash binding establishes content identity, not legal authority or source truth.
2. P1–P3 issue records carry original artifact/code/message/status/source IDs.
   For P0 findings lacking item-level citations, this bounded adapter cites the
   originating artifact and its complete source set. It does not invent fine-grained
   attribution. Context such as account, date and balance is retained in origin context.
3. Discovery/reconciliation/risk do not themselves enforce the newer generic upstream
   issue contract. Test-only metadata preserves origin records in their bound inputs;
   the adapter withholds unconfirmed account totals from quantitative risk inputs and
   explicitly forwards all concerns to the IPS. An omitted unknown numeric field is
   used where the risk schema requires omission rather than JSON null. This is a
   declared compatibility adapter, not a claim that native P0 issue semantics changed.
4. The trust schema rejects extra top-level adapter fields. Its registry carries the
   generated family artifact ID/hash and the reviewed mapping source. Family text
   enters an existing request-packet description. The harness checks member/actual
   household/beneficiary/trust links before construction, and checks them again across
   the edge. It does not add a family charter to the governing-instrument register.
5. Collection markers are never actual households. `family:P4-COUNCIL` maps through
   member A and an attributed permission record to beneficiary `P4-HH-BEN` in
   `trust:P4-TRUST`; service context uses that actual beneficiary household. The trust
   account remains owned by the separately supplied trust entity, not by the beneficiary.
   Family source transfer is limited to the documented internal specialist purpose;
   this does not authorize client delivery, other audiences or real legal authority.
6. Review sources map common `{source_id,reference,as_of,...}` to the legacy
   `{source_id,system,ref,date,...}` format. Follow-up maps them to exact rendered
   citations and source inventory. Open concerns remain in visible actions/discussion/
   communication content, not only a hidden issue register. A draft-ready legacy
   response describes preparation completeness, not resolution of those concerns.
7. Recommendation evidence maps generic unresolved issues into the appropriate check
   (`costs` or `strategy_review`) with origin `upstream-artifact` and the original
   skill/artifact/input hash. Costs are copied from generated comparison metrics,
   including explicit nulls. No undocumented personal alignment or delivery record
   is synthesized. Unknown future tax effects remain outside the calculation.
8. USD-only numerical examples and their specific source/identity rules are bounded
   test adapters. They are not production ETL, an authority resolver, a portfolio
   optimizer, a universal legal-policy mapping or a universal permission model.

## Adverse controls

Tests exercise missing account confirmation, missing private-ledger coverage, missing
expense data, unsupported resolution labels, resolution without citations, wrong
household and collection markers, conflicting source IDs and disclosure scope.
A source-data change must change downstream numbers, proving they were consumed.

Cross-artifact negative controls deliberately reconstruct a locally valid downstream
artifact after dropping an issue, removing an original source, rebinding the household,
or removing visible follow-up actions while retaining a hidden issue register. The
cross-artifact assertions must reject each. Standalone reconstruction cannot discover
facts omitted before input construction; this is why the harness holds the external
upstream artifacts and compares them independently.

Separate output-tamper controls reject changes to issues, household identity, source
reference, funding amount and action status against the bound input. These controls
prove the stated boundaries for these records; they do not establish general agent
reasoning quality or freedom from all integration defects.
