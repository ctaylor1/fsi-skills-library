# Domain Rules — bank-product-feature-comparator

How the skill turns a set of **approved** product records into a neutral, cited side-by-side
comparison, and when it **fails closed**. All product terms are versioned content owned by the
product/marketing-compliance function — never hard-coded here and never inferred. The
authoritative computation is `scripts/calculate_or_transform.py`; this file documents its
contract.

## Comparison dimensions

The comparison is organized into three attribute families plus disclosures and effective
dates. Attribute names are taken verbatim from the approved records (order preserved on first
appearance across the compared products):

| Family | Examples |
| ------ | -------- |
| `eligibility` | min age, residency, minimum opening deposit, relationship/balance requirements |
| `fees` | monthly maintenance, maintenance waiver conditions, overdraft item, out-of-network ATM, paper statement |
| `features` | mobile deposit, overdraft protection, debit card, interest/APY |
| disclosures | Truth in Savings, fee schedules — id, title, effective date, citation |
| effective dates | per product: version, effective date, expiry date |

Where a product's approved sheet does not specify an attribute another product has, the cell
is marked **`present: false`** ("not specified on this product's approved sheet") and a
**data gap** is logged. The skill never fills the gap by inference.

## Neutrality rule (hard boundary)

The comparison is **factual and symmetric**. It lists each product's cited value side by
side. It must **never**:

- assess or characterize the customer's **needs**, goals, risk tolerance, or situation;
- state or imply a product is **suitable / appropriate / a good fit** (a suitability call);
- **recommend, suggest, prefer, rank**, pick a "best"/"better" product, or declare a winner;
- editorialize on a value ("cheap", "expensive", "only", "unbeatable").

Differences may be stated factually ("Essential monthly maintenance 5.00 USD/month; Premier
18.00 USD/month") but never framed as an advantage for a customer.

## Version / effective-date rules (fail closed)

A requested product is **usable** only if all hold as of `as_of`:

1. `approval_status == "approved"` (not draft, pending, retired, withdrawn);
2. `effective_date <= as_of` (not yet effective → blocked);
3. `expiry_date` absent OR `expiry_date >= as_of` (expired → blocked);
4. no `superseded_by` (a newer version exists → this record is stale → blocked).

If **any** requested product is not usable, the whole comparison **fails closed**
(`status: "fail_closed"`): no comparison is emitted, `block_reasons` lists each blocked
product and reason, and `required_action` tells the banker to refresh/approve the content or
remove the product. Rationale: a comparison is only trustworthy if every side is current,
approved content — a stale fee or lapsed disclosure would mislead.

## Missing discovery questions

The pack surfaces the **outstanding factual questions** the banker still needs to confirm
with the customer (union of each approved product's `discovery_questions`, de-duplicated).
These are **fact-gathering prompts** ("Confirm the customer's combined qualifying balances to
determine the fee waiver"), never suitability judgments. Answering them is the human's job;
scoring the answers is out of scope.

## Source hierarchy

See `references/source-map.md`. The controlled product catalog is the position of record;
disclosures and entity resolution support it; the freshness service confirms currency. Cite
every value to a versioned record + effective date.

## Durable identifiers

- `request_id` — durable job ID binding the pack to the requested products, `as_of`, and
  `approved_catalog_version`; makes the comparison reproducible and is the handoff key.
- `approved_catalog_version` — the versioned catalog snapshot used.

## Reproducibility

Given the same requested products, `as_of`, and catalog version, the engine deterministically
reproduces the comparison rows, the citation index, the discovery questions, and any
fail-closed block reasons.
