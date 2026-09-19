# Practitioner response — insurance-premium-audit-reviewer

Synthetic evaluation case; not a live insurance engagement.

Case `insurance-premium-audit-reviewer-forward-01` | Harbor Mutual (synthetic) | Premium auditor | object `POL-AUD-41` | SYNTHETIC-STATE / commercial-package | as of 2026-09-18.

Using the supplied reviewed classes and full-period manual, warehouse premium is $625,000.25 / 100 × $1.37 × 0.92 = $7,877.503151. Office premium is $123,456.78 / 100 × $0.19 × 0.92 = $215.80245144. The distinct PAY-W and PAY-O payroll records sum to unrounded manual premium $8,093.30560244 (manual §1; payroll §1).

Adding the supplied $37.50 fixed charge yields $8,130.80560244, above the $8,000 minimum. Rounding only then, half-up to cents, produces audited premium $8,130.81. Less the $7,900 deposit, the audit adjustment is $230.81. Calculated premium exceeds the reported $8,130.80 by $0.01 (manual §2; control §1).

The cent difference is a known reconciliation exception. Row rounding could be one explanation, but the evidence does not prove the report’s rounding method; finance should inspect its computation before accepting or correcting the result. Classification specialist review and audited inclusions/exclusions were supplied assertions, not newly adjudicated here. This draft does not authorize billing or change coverage.

Evaluation chronology: the initial native mapping omitted a newly explicit source-record identity field and safely withheld aggregate money. A separately retained mapping supplement adds basis_record_id PAY-W/PAY-O from the unchanged raw payroll record identifiers. Replay then produced the complete arithmetic above and needs-review status. The original input/output remain available for audit.

Native disposition: **needs-review**, completeness **complete**, evaluability **evaluable**. Retained native artifact: [mapping-replay/result.json](mapping-replay/result.json). Raw source register and exact section mapping: [mapping.json](mapping.json). All evidence is supplied synthetic v1, unauthenticated. Human review remains required; approval not requested and execution not performed.
