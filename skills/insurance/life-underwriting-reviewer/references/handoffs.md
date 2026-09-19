# Native handoffs

Receive application preparation from insurance-submission-preparer only after explicitly mapping application/applicant identities. Hand evidence defects to insurance-data-reconciler, and policy explanation to policy-document-explainer. Hand medical or financial interpretation and risk classification to the licensed/authorized life underwriting function, not to P&C underwriting or a health-benefit appeal workflow.

Carry case_id, source_document, artifact, context, unresolved_issues, material dates/currencies/bases and requested output. A source artifact is not the receiver input: map the receiver schema explicitly and run its actual validate_input.py before proceeding. Preserve role and object transitions, with reviewed identity mappings. Do not announce an unavailable target as installed. No handoff grants access, approval or execution permission.
