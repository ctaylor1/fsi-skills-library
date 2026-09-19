# Domain rules and limits

## Calculation contract
Open invoice = original amount - linked credits - settled allocations. Remaining before proposed = open invoice - pending allocations. Proposed allocations are compared to this remainder and do not close the invoice. Each payment allocation sum must equal its stated amount; allocations must have the same supplier, buyer and currency as their payment and invoice. There is no cross-currency conversion or credit transfer between invoices without explicit upstream allocation.

The dataset must cover full prior/pending history. A reused ERP import ID is caught structurally; a reused business invoice number is independently flagged. The input uses native business documents but is not a vendor-specific ERP import/export connector. Dates are due-date evidence, not a computed legal payment deadline. No early-payment discount, tax, FX, credit eligibility or bank mandate is inferred. Invoice approval and a current policy are workflow evidence only.
