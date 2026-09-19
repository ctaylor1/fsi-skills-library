# Native handoffs

Receive normalized notice from claim-intake-preparer with a reviewed mapping of notice/policy/insured/case identifiers. Use this life-specific review rather than generic P&C liability analysis. Contract-service requests go to life-annuity-contract-service-reviewer; suspected wrongdoing only goes to insurance-fraud-referral-reviewer with supporting and contrary evidence, never because contestability applies. Beneficiary/legal disputes and pay/deny decisions remain with authorized human specialists.

Carry case_id, source_document, artifact, context, unresolved_issues, material dates/currencies/bases and requested output. A source artifact is not the receiver input: map the receiver schema explicitly and run its actual validate_input.py before proceeding. Preserve role and object transitions, with reviewed identity mappings. Do not announce an unavailable target as installed. No handoff grants access, approval or execution permission.
