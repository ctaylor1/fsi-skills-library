# Construction method

Generate one candidate per supplied model. Preserve that model's cash and aggregate asset-class
targets. Within each sleeve, remove ineligible/restricted names from allocation, then distribute the
sleeve in proportion to the remaining positive model weights. Clip a name at the lower of its
universe cap and mandate position cap; redistribute its excess by the remaining model proportions.
Repeat until the sleeve is allocated or no eligible capacity remains. No name outside the model,
cross-sleeve transfer, equal-weight fallback or expected-return assumption is introduced.

Example: a 60% equity sleeve with model names A40% and B20%, A capped30%, yields A30% B30% if B's
cap permits it. Restrict A and cap B50%: B50% plus10% unallocated equity. The latter is incomplete,
not a fully invested candidate. Report the class-band breach and unallocated remainder separately.

Model weights plus cash must equal one within numerical tolerance1e-8. That tolerance is solely
floating-point reconciliation, not a policy threshold. Do not normalize invalid models. Check every
declared class band (including a mandate class absent from the model), cash band and position cap.
Any source, eligibility, approval-record or numeric gap keeps the draft unresolved. Model approval
records are caller evidence only; controlled-source access and substantive mandate review are external.

This is a constrained model adaptation, not a global portfolio optimizer. It does not estimate
expected returns, variance, correlation, tax location, transaction fees or trade increments. Report
those gaps when relevant and route the next distinct review rather than inventing economics.

Unresolved upstream issues also mark every generated candidate needs-review and appear in its local
findings. The shared mandate/scope is not treated as clean merely because the candidate fits numerical
bands. Allocation sums and cap redistribution iterate security IDs in sorted order so identical input
reconstructs identically across process hash seeds; no economic preference follows from that order.
