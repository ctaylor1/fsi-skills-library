# Practitioner response — insurance-fraud-pattern-analyzer

Synthetic evaluation case; not a live insurance engagement.

Case `insurance-fraud-pattern-analyzer-forward-01` | Harbor Mutual (synthetic) | Fraud analytics analyst | object `SIU-SCREEN` | SYNTHETIC-STATE / commercial-package | as of 2026-09-18.

The exact-token screen identifies bank token B-7 shared by C1, C2 and C4, and email token E-2 shared by C2 and C4. Bank-linked claimed amount is $5,000; email-linked amount is $4,200. Because the signals overlap, the union is three claims and $5,000 of claimed amount—not $9,200 and not an estimate of fraud loss (claims §2–3).

R-COMMON is excluded on the supplied vendor-master rationale that it represents a regional repair network used by unrelated customers. This exclusion does not remove the bank or email links and does not clear any claim (outcomes §2). Shared tokens may reflect a household, authorized representative, shared service, data quality issue or misconduct; token linkage does not resolve identity or intent.

May has three claims across 1,000 location-months: 0.003 per exposure and 3/31 = 0.096774 claims per day. June also has three, across 1,200: 0.0025 per exposure and 3/30 = 0.1 per day. The flagged fractions are 2/3 and 1/3; independently, flagged rates per exposure are 0.002 and 0.000833333. The unequal calendar lengths explain why per-day and exposure-based comparisons differ (claims §1).

Among the three flagged claims, one supplied disposition is confirmed, one cleared and one pending. Confirmed share is 1/2 = 50% among mature outcomes, excluding pending C4 (outcomes §1). Links were discovered across both windows at review time; this is not historical alert precision or predictive validation. SIU should verify underlying links and legitimate alternatives before case selection. No fraud determination, referral or adverse action occurred.

Native disposition: **ready-for-review**, completeness **complete**, evaluability **evaluable**. Retained native artifact: [initial/result.json](initial/result.json). Raw source register and exact section mapping: [mapping.json](mapping.json). All evidence is supplied synthetic v1, unauthenticated. Human review remains required; approval not requested and execution not performed.
