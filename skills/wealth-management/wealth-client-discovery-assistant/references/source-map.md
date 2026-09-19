# Discovery sources and provenance

1. Firm-controlled engagement record: documented scope, capacity, relationship status.
2. Current approved client documents/CRM facts: documented observations with exact locators.
3. Dated interview or signed client questionnaire: client-reported facts and goals.

Authority is field-specific. An interview does not override a custody balance or prove account
ownership. Preserve both and flag conflicts rather than claiming verification. A source ID lookup
validates provenance metadata, not whether source text entails a claim; the author and human
reviewer must inspect the underlying material.

Proposed deployment reads: `crm.household.read`, `crm.interview.read`,
`documents.client.read`, `engagement.read`. These are integration contracts to implement and
approve, not connectors shipped with this package. No network, write, retry, or delivery occurs.

The source registry records owner, reference and validity interval. Reject stale/future evidence.
Source `valid_until` must come from approved freshness policy; an agent may not extend it to make
an input pass. The artifact includes the registry and full normalized input snapshot for review.
