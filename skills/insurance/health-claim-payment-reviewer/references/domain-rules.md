# Method and applicability

The payer payment-integrity/coding analyst reviews supplied coded claim lines.
The method is a source-bound comparison, not an adjudication engine. A current code
set, exact quarterly/replacement edit file, payer adoption and permitted-use basis
must be supplied. Opaque synthetic tokens in this package have no clinical or billing
meaning. No licensed CPT/UB content or actual edit tables are bundled.

Preserve original/replacement/void history. Only the unique attested terminal of a
connected, nonbranching, date-consistent chain can support amounts. Claim_id/line_id
is the economic duplicate key; replacement must retain full provider/product/service
line identity, while code/version/modifier changes require exact matching terminal
profiles and contracts. A void's remaining ledger amount is an investigation fact.

Maximum-unit and exact incompatible-pair checks produce coding flags. They never
produce a medical necessity conclusion or prior authorization determination. An edit
flag withholds conditional amounts instead of turning them into zero or a denial.
All distinct active lines must be resolved before evaluating pair dependencies.

Calculate exact rate × units only under the declared supported contract method.
Preserve independently supplied allocation components and validate their identity.
Other payment methodologies, bundled/per-diem rates, lesser-of rules, rounding,
sequestration, taxes and inferred patient responsibility need a separately reviewed
method and are unsupported here. The analyst owns investigation of variances and any
subsequent decision. Valid software output does not authenticate contract, code rights,
benefit allocation or recorded ledger data.

CMS describes NCCI as coding edits, separate from medical necessity and prior
authorization. Private payer adoption varies. CMS updates edit files quarterly and
may issue replacement files between updates; quarter label alone is insufficient.
AMA's CPT licensing FAQ was updated July 14, 2026 and addresses permitted CPT use,
including AI-related terms. Access to a website does not establish licensing rights.
See [primary sources](source-map.md).
