# Source Map — iso-20022-message-interpreter

Every field semantic, code meaning, and validation rule in an interpretation must cite one
of the authoritative sources below, ranked. Shared platform services are described in
[`docs/SHARED-SERVICES.md`](../../../../docs/SHARED-SERVICES.md); this skill references them
rather than reimplementing them.

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **ISO 20022 message repository** — the registered schema (XSD) and message-definition report for the exact `<family>.<NNN>.<VVV>.<NN>` version | Element names, cardinality, data types, code lists | Read-only |
| 2 | **Usage-guideline / market-practice book** — CBPR+, HVPS+ (Fedwire ISO, CHIPS, TARGET2/T2, CHAPS), SEPA (EPC), FedNow, RTP (TCH) | Which elements are mandatory/restricted for a given scheme and version | Read-only |
| 3 | **Validation engine** — schema + business-rule validator for the scheme | Structural validity, control-total tie-outs, identifier and code-list checks | Read-only, deterministic |
| 4 | **External code sets** — ISO 20022 External Code Lists (status, reason, purpose, category-purpose), ISO 4217 currencies, ISO 9362 BIC, ISO 13616 IBAN | Decoding coded values; identifier format/check-digit validation | Read-only |
| 5 | **Transformation maps** — ISO 20022 ⇄ legacy MT (CBPR+ translation portal), scheme field maps | Detecting truncation and character-set loss on down-mapping | Read-only |
| 6 | **Payment status data** — status reports (pacs.002/pain.002), returns (pacs.004), investigations (camt.029/056) tied to the original message by identifiers | Explaining lifecycle state and status/reason chronology | Read-only |

Never substitute a user assertion for the registered schema or the applicable usage
guideline. If two sources disagree (e.g., base schema permits a field the scheme forbids),
surface the conflict and cite both; do not silently pick one.

## Message families in scope

- **pain** — Payments Initiation (customer-to-bank): pain.001, pain.002, pain.007, pain.008.
- **pacs** — Payments Clearing and Settlement (FI-to-FI): pacs.002/003/004/007/008/009/028.
- **camt** — Cash Management (reporting, notification, exception): camt.029/052/053/054/055/056/060/087.
- "Related messages" outside these families are interpreted only with an explicit,
  cited usage guideline.

## Citation format

Each interpreted figure or coded value carries a citation of the form
`{system}:{ref}` drawn from the message's `source` object — e.g.
`payment-gateway:batch=BAT-77;msg=MSGID-20260715-0001;tx=1`. Code meanings additionally
reference the code list and version they were decoded against (e.g. External Status Reason
code set). The machine-readable interpretation stores the citation per transaction and per
finding; the narrative references them inline where a figure or status is stated.

## Freshness / effective dates

- The **schema version** (`.VVV.NN`) is load-bearing: element names and code lists change
  across versions. Interpret against the version in `message_type`, not a newer one.
- **Usage guidelines and external code lists are versioned contracts** with effective
  dates; decode codes against the version effective on the message's `cre_dt_tm`.
- Flag any code not present in the referenced code-list version as **unknown** rather than
  guessing its meaning.

## Least-privilege operations (deployment)

- `schema.describe(message_type)` → element list, cardinality, data types.
- `codeset.decode(list_id, code, version)` → plain-language meaning + version.
- `validate.message(message, usage_guideline)` → structural + business-rule findings.
- `translate.map(message, target_format)` → down-mapping preview for truncation detection.

All read-only, deterministic schemas, bounded payloads, below the fixed timeout. No skill
operation initiates, modifies, repairs, cancels, or resubmits a payment.
