# Follow-up sources

The documented meeting is authoritative for what was discussed/agreed. Planning supplies goals,
portfolio/OMS supplies positions/drift, product sources supply product facts, and controlled
libraries supply disclosure/template/communication policy. Cite the actual source for each item.
Do not use a meeting pre-read as proof that the client agreed to an action.

Every material item and policy citation resolves to the owned source inventory. Its dates must
cover the request as-of date; template/disclosure versions also resolve to current records.
Missing or stale validity rejects the request. An agent may not invent source validity.

Proposed deployment reads: crm.meeting.read, crm.profile.read, planning.objectives.read,
oms.holdings.read, product.reference.read, register.disclosures.get, template.followup.get.
No integrations are shipped: the bundled scripts consume normalized JSON, emit stdout and never
write CRM, send messages, schedule, trade or file records.

Keep the source snapshot and artifact/hash/request lineage within approved privacy/retention
boundaries. Hashes prove input identity, not source truth, legal applicability or authorization.
Human readback must confirm the cited source supports each claim and any required approval.
