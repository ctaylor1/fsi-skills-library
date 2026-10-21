# Execution and human oversight controls

This package performs local supplied-record analysis only. It does not retrieve live records, write a system of record, approve or decline customers, set ratings, authorize an override, confirm identity/legal status, clear a hit, close cases, contact a customer, send a package or make a filing.

The accountable owner function is Negative-news screening and investigation owner. A deployment must assign actual owners, reviewer roles, data access, audience and applicable confidentiality controls. The package metadata is not an appointment or authorization. Apply segregation of duties where the institution's policy requires it; this code does not enforce identity or role separation.

Protected SAR/STR information, investigations, personal data and ordinary CDD records may require different handling. Classify the supplied case and use least necessary disclosure. Do not reveal protected filings or investigations. Ordinary missing-document remediation is not inherently a prohibited disclosure; any communication must be separately authorized and performed outside this package.

The complete native result must pass exact detached-input reconstruction. Missing original input, changed source data, embedded raw input, source-authentication claims and added native narrative are rejected. Never treat a rehashed self-consistent fabrication as authenticated evidence. The separate workflow envelope and downstream producer/receiver checks remain distinct.

A supplied `approved` policy flag or approval reference is evidence metadata for a reviewer, not technical authentication of that approval. The scripts cannot certify legal applicability, source truth, effective AML/CTF/CPF controls, fairness or production readiness. Domain-owner acceptance and live operational integration remain pending.

Read [evidence contract](evidence-contract.md) and [source governance](source-governance.md).
