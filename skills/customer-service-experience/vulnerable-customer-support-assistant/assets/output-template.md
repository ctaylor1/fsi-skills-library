# Support-needs assessment (DRAFT) — for human review

> Draft support-needs suggestions for human review only; this is not a diagnosis and not a
> determination about the customer, it applies no vulnerability marker or accommodation to any
> system of record and sends nothing to the customer, and every suggestion is drawn from the
> approved catalog and must be confirmed with the customer and an authorized colleague before
> anything is applied.

Fill every `{{placeholder}}` from the computed assessment and the cited interaction only. Do not
add any statement that is not backed by a cited signal. Do not diagnose, do not determine
capacity, do not limit service, do not advise. Mask the customer identifier to the last 4. Keep
all seven section headings below (they are enforced by `validate_output`).

## Support-needs assessment (DRAFT) — {{customer_ref}}

- **Reference:** {{assessment_id}}   **Channel:** {{channel}}
- **Signals:** {{signal_count}}   **Readiness:** {{readiness}}

## Observed signals
For each signal, quote what the customer actually said and cite the transcript/chat line. State
the driver category as *current context, not a diagnosis*.
- **[{{signal_id}}]** "{{quote}}" — {{driver}} ({{signal_type}}) — {{citation}}

## Possible support needs
List the driver categories evidenced, framed as possibilities the customer signalled — never as a
label or condition.
- {{driver}}: signalled by {{supporting_signal_ids}}

## Suggested accommodations
Only items from the approved catalog, each traced to the signal(s) that support it. Mark any that
need the customer's consent as `pending_consent`.
- {{accommodation_code}} — {{accommodation_label}} (supports: {{supporting_signal_ids}}) {{pending_consent_flag}}

## Suggested referral
State the primary approved route and any additional approved routes, with the reason and the
supporting signals. If none, say accommodations may suffice and the human decides.
- Primary route: {{referral_route}} — {{referral_reason}} (supports: {{supporting_signal_ids}})
- Additional routes: {{additional_routes}}

## Consent and approvals
- Special-category data involved: {{special_category}}; consent status: {{consent_status}}
- Human review required before anything is shared, recorded, or referred: {{human_review_required}}
- System-of-record change: {{record_mode}} (applied: {{record_applied}})

## What this is not
- Not a diagnosis, not a mental-capacity determination, not financial/medical/legal advice, and
  not a decision to limit service. A human reviews and an authorized colleague acts.

---

<!-- Standing note (leave verbatim):
Draft support-needs suggestions for human review only; this is not a diagnosis and not a
determination about the customer, it applies no vulnerability marker or accommodation to any
system of record and sends nothing to the customer, and every suggestion is drawn from the
approved catalog and must be confirmed with the customer and an authorized colleague before
anything is applied. -->
