# Review method and limits

Establish the requested review scope and inventories before inspecting the packet.
Carry inherited issues forward. Review is blocked by an explicitly incomplete
inventory, absent claims, missing requested sections/claims/checks/risks/disclosures,
unsupported claims, numerical breaks, incompatible bases or unresolved contradictions.
A supplied contradiction resolution remains pending adjudication, with its original
resolution evidence retained in the detached input. This method cannot close it.

For claim review, compare each subject with the requested subject or its issuer;
compare cited source subjects with the actual claim. Compare claim knowledge time
with the cutoff and cited source time with claim knowledge time. Mixed date and
timestamp precision does not imply a chronological ordering. A numeric fact's
period end cannot exceed analysis date. A forecast requires explicit horizon and
assumptions, and its horizon cannot precede its numeric period. Every judgment
requires rationale and creates a human-assessment finding: text entailment and
conclusion validity are not inferred from a citation's existence.

Arithmetic uses supplied numeric claim values and recomputes each declared operation:

- Sum: sum of operands using compensated summation.
- Difference: first operand minus second.
- Ratio: first operand divided by second.
- Percent change: `(first / second - 1) * 100`; first is current, second is base.

Arithmetic operand dimensions must match exactly: period, currency, units,
accounting basis and consolidation scope. Sum/difference result dimensions must
also match. Measure names remain distinct so a declared debt minus cash identity
can produce net debt; declaring arithmetic never proves its economic meaning.
Percent change instead permits an earlier base period, requires the same measure,
and reports the current period. Ratio outputs use currency `not-applicable`, units `ratio` or `percent`,
and the same period/accounting/scope as the operands. Zero denominator, missing
value and nonfinite result are unavailable findings; null is never zero. A supplied
absolute tolerance bounds the difference between reported and recomputed value.
Comparability groups independently report differing or absent numeric bases.
No currency translation, period normalization or share-class inference is supplied.

A high or critical finding blocks readiness; a human-assessment finding requires
review. A result without findings is complete only for the declared supplied scope.
The packet may omit undisclosed evidence, semantic contradictions, arithmetic
relationships, economic assumptions or required institution controls. Even the
presence of a risk/disclosure row proves only structural coverage: a reviewer must
judge whether its cited text actually covers the required item. Checks do not ingest
workbooks, assess market predictions, prove research truth, authenticate sources,
clear conflicts, or authorize publication, model changes or trades.

For a producer handoff, retain its original input and computed native result. Use a
reviewed adapter that validates both before constructing this packet; a producer
name, hash or caller-provided pass flag is insufficient. This method does not execute
producer packages or elevate their supplied results into professional approval.
