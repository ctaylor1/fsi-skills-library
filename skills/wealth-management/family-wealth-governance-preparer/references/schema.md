# Exact schema — version 0.1.0

Use `evals/files/request.json` as a synthetic shape example, not policy. All arrays
are explicit, contain at most 1,000 objects, and use unique nonempty row IDs. Dates
are exact `YYYY-MM-DD`. Numeric minutes/quorums/sequences accept integer JSON numbers
or decimal strings representing integers; booleans are invalid. Unlisted top-level
properties reject. Nested descriptive metadata is retained internally but never adds
calculation, permissions or legal powers.

## Common envelope and family scope
Required: `schema_version: wealth-p0-v1`, request_id, as_of, `scope_type: family-group`,
family_id and household_id exactly `family:<family_id>`. The latter is a collection
marker. Required engagement is `{capacity: advisory|brokerage|private-bank|trust,
jurisdiction: US, source_ids}`. One capacity per run. Required source registry rows
are `{source_id, reference, owner, as_of, valid_until}` with unique IDs and nonempty
text, and `source.as_of <= request.as_of <= valid_until`. `scope_source_ids` cite the
family and member inventory. Invalid registry entries reject; missing item citations
produce findings rather than unsupported qualified conclusions.

Required `upstream_issues` is an explicit list of `{artifact_id, code, message,
status: unresolved|resolved, source_ids}`. Resolved items additionally require
`resolution: {owner, reference, as_of, source_ids}` with nonfuture date. A status
alone cannot clear an issue. Top-level unresolved_issues must first be explicitly mapped.

## Source and access objects
Every material row has `source_ids`, a nonempty unique list of registry IDs. Rows
in policy, decision_rules, succession_criteria, members, roles, topics, responses,
succession, criteria_evidence, education, followups and completion_evidence also have:

`access: {allowed_member_ids: [member_id, ...], source_ids: [...]}`

Allowed IDs must be unique and declared; an explicit empty list authorizes no
family audience. Missing/null access is valid incomplete evidence and withholds
disclosure. Malformed access rejects. Access citations are required independently
of fact citations. Every requested audience member must be allowed by every
contributing record. A row being cited does not authenticate the permission statement.

`audience` requires member_ids (nonempty unique declared IDs), a nonempty purpose,
and source_ids. This is the requested recipient set and purpose, not proof of delivery
permission. The purpose text itself is prepared for that recipient set. The full
internal snapshot is never an audience artifact.

## Policy
`policy` requires version, owner, capacity/jurisdiction matching engagement,
effective_date <= as_of <= valid_until, source_ids and access. Date and ownership
metadata are attribution, not institutional approval. Additionally:

- `decision_rules`: nonempty unique rule_id rows with description, method
  unanimity|majority-of-all-eligible|discussion-only, quorum_min integer 1..1000,
  source_ids and access. No default majority or quorum is invented.
- `succession_criteria`: explicit unique criterion_id rows with description,
  source_ids and access. Every listed criterion is required for every supplied
  succession review; nonempty when succession records are supplied, otherwise [] is
  permitted. Use an appropriate scoped policy, not a universal readiness scale.

## Members and roles
`members` is nonempty. Rows: member_id, label, kind family-member|professional,
household_id, participation_status willing|declined|unknown, participation_as_of
(nonfuture date or null), source_ids and access. A family-member requires an actual
household ID with no family:/book:/trust: prefix. Professional household_id is null.
Participation describes the person's attributed willingness for the proposed meeting,
not legal competence or assent to a topic.

`roles` rows: role_id, member_id (declared member or null), label, scope_description,
authority_type family-discussion-role|legal-role-assertion|unknown, basis_reference
(nonempty text or null), reviewer_member_id (declared or null), review_date
(nonfuture date or null), review_by (date no earlier than review_date or null),
source_ids and access. A current sourced role is a documented assertion only.
Legal authority remains not-determined for every role, including legal-role-assertion.

## Topics and attributed positions
`topics` is nonempty. Rows: topic_id, title, question, proposed_decision (substantive
nonempty text), decision_class discussion|family-discussion-agreement|legal-authority-question,
sequence (unique integer 1..1000), minutes (integer 1..1440 or null), eligible_member_ids
(nonempty unique declared members), role_ids (unique declared roles; [] allowed),
rule_id, responses, source_ids and access.

`responses` is explicit, with at most one row for each eligible member; missing rows
remain unrecorded. Rows: member_id, position support|oppose|abstain|not-recorded,
participation in-person|written|not-participating|unknown, statement (attributed text),
recorded_on (nonfuture date or null), source_ids and access. A position of support,
oppose or abstain requires in-person or written participation. Absent/uncited/undated
positions never enter support counts. The literal record remains in the internal view.

The evaluator requires all eligible positions supported to qualify a threshold
observation. The denominator for majority is **all eligible members**, never only
votes cast. Recorded participation and quorum are separate. A threshold observation
does not adopt a decision, fabricate consensus or establish legal power.

## Succession review
`succession` rows: succession_id, topic_id, role_id (also listed in that topic's
role_ids), candidate_member_id (declared or null), candidate_interest
confirmed|declined|unknown, interest_as_of (nonfuture or null), target_date
(date >= as_of or null), criteria_evidence, source_ids and access.

`criteria_evidence` rows reference unique policy criterion_id and contain status
documented|incomplete|unknown|not-applicable, observation, reviewer_member_id
(declared or null), review_date (nonfuture or null), review_by (not before review_date
or null), source_ids and access. Missing criterion, not-applicable label, unknown
reviewer, stale review or missing source prevents evidence-complete qualification.
Candidate interest is attributed and dated. No age, wealth or psychological inference
is made. Legal-role succession always requires separate legal review; no appointment.

## Education, meeting and follow-ups
`education` rows: education_id, topic_id, participant_member_ids (nonempty declared
IDs), facilitator_member_id (declared or null), learning_need_basis, learning_objective,
proposed_activity (nonempty substantive text), minutes (integer 1..1440 or null),
source_ids and access. Activities belong to this meeting agenda; participant IDs must
be proposed meeting attendees for a documented proposal. Willingness and learning
need must be supplied, not inferred from generation or age.

`meeting` requires participant_member_ids (nonempty declared IDs), facilitator_member_id
(declared or null), proposed_date (as_of through policy.valid_until or null),
available_minutes (integer 1..1440 or null), and source_ids. Each attendee needs
attributed dated willingness. No availability lookup or calendar booking occurs.
Topics run in supplied sequence; linked education follows each topic. Unknown duration
is not zero. Known effort exceeding the meeting budget is an explicit finding.

`followups` rows: followup_id, topic_id, owner_member_id (declared or null), description,
due_on (any ISO date or null), status proposed|agreed|completed|unknown,
owner_acceptance confirmed|declined|unknown, completion_evidence (object or null),
source_ids and access. A completed row requires current supplied completion evidence
`{reviewer_member_id, reference, as_of, source_ids, access}` with nonfuture as_of.
No missing owner is assigned automatically. An attributed completion is a record for
human review, not proof that this tool performed the action.

## Output and CLI
All CLIs accept one JSON path or --selftest, read locally and print JSON without
writing files. Validators return `{"errors": []}`/exit 0 for valid content, exit 1
for errors. Valid needs-data reports are successful calculations.

The canonical envelope contains identity/hash, context, sources, findings/status,
human_review_required true, action_taken false and delivery_status not-delivered.
`result` preserves full input_snapshot, policy, upstream_issues, handoff_context
and scope. It adds family_subject (family and actual member-household mapping),
classification internal-review-only, role_register, decision_register, succession_register,
education_register, followup_register, meeting_plan and boundaries. Handoff context
explicitly includes scope_type, family_id and member_household_mapping.

`audience_draft` is a separate projection: allowed topics and attributed statements,
succession observations with the permitted role label/scope/type and transition target,
education proposals with intended participants, and follow-ups, plus readable draft_markdown.
It excludes raw input/access lists, registry locators, internal findings, hidden item
counts and hidden titles/IDs. It remains a candidate requiring human confidentiality
review and is never delivered. Do not distribute the enclosing full output. Output
validation reconstructs the entire object and rejects changes or omissions; a hash
cannot authenticate a false replacement input or establish permission.
