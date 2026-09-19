# Transaction reconciliation handoffs

Settlement/batch records always route to payment-settlement-reconciler, even if their
amounts agree. Preserve partition, reference and supplied evidence; the target must map
records to its own schema and validate independently. Do not run both packages over the
same transaction group as competing owners.

Unresolved transaction issues route to bank-payment-exception-investigator with case ID,
issue IDs, partition and source references. GL account analysis belongs to gl-reconciler;
the discrepancy is evidence for investigation, not a debit/credit instruction.

Machine-readable packets use the bundled payment contract: contract_version, handoff_id,
source_skill, target_skill, case_id, lead_owner, requested_output, action_mode=read-only,
source_refs, unresolved_issues, target_input, target_validation=required and
authority_granted=false. The envelope is transport metadata. It does not make target_input
a valid target schema and does not substitute for authenticated runtime permissions.

Phase 1 handoff: retain case/participant/rail/jurisdiction, original source references and unresolved issues using payment-contract.md. Validate the target native input independently; renamed skills are not assumed input-compatible. Local IDs and hashes grant no authority and do not persist or accept a case. Only invoke installed capabilities within the requested scope.
