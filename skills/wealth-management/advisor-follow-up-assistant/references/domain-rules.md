# Follow-up request v0.2

## Request and source contract
Required: request_id, followup_id, author_id, as_of_date, config_version, template_version,
disclosures_version, engagement, communication_policy, client, meeting, discussion_points[],
recommendations[], action_items[], client_communication, disclosures[], crm_update, next_meeting,
source_inventory[] and approvals[]. Arrays contain objects; no malformed shape is inferred.

Engagement specifies advisory/brokerage/private-bank/trust and jurisdiction US. The approved
communication_policy records matching version/capacity, classification (correspondence/retail/
institutional/internal), owner, approved_by, citation and unique required_roles including Advisor.
This supplied policy governs review roles; there is no universal principal-preapproval assumption.

Source inventory rows contain unique citation, owner, as_of, valid_until; require
source.as_of <= request.as_of_date <= source.valid_until. Template/disclosure version strings
must resolve to this registry. Registry validity is governed configuration, not an agent override.

## Substantive domain records
- client: household_id, name_masked, boolean senior_or_vulnerable, citation.
- meeting: meeting_id, ISO date no later than as_of_date, channel, nonempty attendee roster, citation.
- discussion_points: topic, summary, citation per point.
- recommendations: unique id, summary, citation, explicit boolean requires_disclosure and
  requires_suitability_review. Missing reviewed flags never default to false.
- action_items: unique id, owner, description, ISO due_date, citation.
- client_communication: channel email/letter/portal, subject, citation, nonempty key_points[] of
  `{text, citation}`. The deterministic body joins only these supplied texts; it invents no prose.
- disclosures: unique id, existing covers_recommendation, ref, citation. Every flagged
  recommendation needs a corresponding disclosure and recommendation-evidence review route.
- crm_update.fields: field, substantive proposed_value, citation per field.
- next_meeting: target_timeframe, purpose, citation. This is not a calendar invitation.
- approvals: any supplied status must be pending. Output records configured roles as pending.

Empty action-items, CRM-update or next-meeting content requires `not_applicable[section-key]`
with a substantive reason and a valid citation. No required disclosure is reported as none when
a recommendation flag says otherwise.

## Validation and outputs
Each missing/unknown item citation or substantive field becomes needs-data; another item's
citation cannot satisfy it. Invalid structure, registry, versions or applicability stops assembly.
The seven output sections carry actual content, not only present flags. The complete result also
retains household/attendees, communication body, source inventory/map, input snapshot/hash,
request/artifact/prior-artifact lineage, draft flags, approvals and handoff routes.

Output validation reconstructs the result from its snapshot and screens actual content. It
rejects incomplete drafts at the readiness gate. These checks establish supplied-data consistency,
not semantic grounding, legal compliance or human acceptance.
