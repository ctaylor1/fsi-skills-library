# Scope and handoffs

This workflow owns family discussion preparation, not trust administration, estate
planning or household implementation. Preserve the distinction between a family
discussion role and legal powers in every packet.

| Need | Receiving workflow | Required evidence |
| --- | --- | --- |
| Legal trust role, distribution or administration question | trust-administration-reviewer | Actual trust scope and instruments, specific unresolved authority question, attributed source records. |
| Estate intent, titling or beneficiary coordination | estate-wealth-transfer-reviewer | Actual household, stated intent, relevant instrument references and unresolved legal question. |
| Household cash goals or planning after a family discussion | household-financial-planning-assistant | Actual household ID, supported client objectives and explicit unresolved issues; no family vote substitutes for client authority. |
| A household review meeting is needed | client-review-preparer | Actual household, permitted evidence, proposed topics and open issues. |
| Individual meeting actions need follow-up drafting | advisor-follow-up-assistant | Actual meeting evidence, attributed owner/acceptance and disclosure restrictions; this proposal is not proof a meeting occurred. |
| Documented exploitation observations | senior-investor-protection-screener | Exact sourced observations, without age/competence inference or a legal hold decision. |

The family_subject and handoff_context preserve scope_type, family_id, collection
marker and member-to-actual-household mapping. Create a new recipient request with
the appropriate actual household/trust subject and the recipient's exact schema;
never pass `family:<family_id>` as a real client. Do not select a household for a
family-wide issue without attributed scope evidence.

Keep the originating family artifact ID and relevant topic/follow-up IDs. Preserve
the upstream issue's artifact_id, code, message, status and source_ids. For a schema
requiring unresolved_issues, explicitly map without dropping origin or resolution
evidence. An empty inventory is supplied after review, not inferred from omission.

Select only records permitted for the recipient and purpose. The full internal
snapshot is not an outward handoff by default. Do not copy hidden audience records
because their IDs occur in a shared discussion. No downstream status or digest grants
permission to disclose, change legal authority or perform a transaction.
