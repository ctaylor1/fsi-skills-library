# Handoffs

- `wealth-onboarding-packager`: Prepare new relationship/account opening evidence.
- `estate-wealth-transfer-reviewer`: Reconcile estate intentions before drafting beneficiary or authority service requests.
- `trust-administration-reviewer`: Obtain the specific trust’s governing-clause, fiduciary authority, distribution evidence and unresolved accounting context for a separately requested trust service. A reviewed evidence packet does not approve the operation.
- `household-wealth-data-reconciler`: Resolve cash, holding and account-ownership conflicts.
- `kyc-customer-due-diligence-screener`: Route independently required identity/CDD reviews under the applicable policy.
- `advisor-follow-up-assistant`: Draft a cited client follow-up after operations review; no send.

Transmit artifact ID, household/request IDs, engagement capacity, policy version, source registry, substantive result and unresolved findings. These are draft evidence handoffs, not API calls or authority to act. Counsel, licensed professionals and custody operations own their respective decisions.

Trust-scoped artifacts must map to the actual service account and reviewed client/beneficiary identity. Preserve trust_id, originating artifact/issue IDs and exact authority evidence; never substitute trust:<trust_id> for an authenticated client or account identifier.
