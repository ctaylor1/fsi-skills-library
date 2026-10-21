# Controls and stopping rules

- Fail malformed/duplicate native identities, reversed periods, changed native case context,
  unsupported data fields and source/audience/classification violations before output.
- Resolve consequential fields from exact source/fact values. Future, expired, missing or
  inconsistent source support withholds dependent conclusions; null is not a favorable result.
- Keep unknown/untested observations separate. No filled-in reviewer, dates, legal profile,
  case disposition, criteria or sampling evidence. Names and role labels do not authenticate.
- SAR-restricted sources require sar_restricted output and authorized_fiu recipient; a broadly
  permitted audience list is insufficient to bypass that boundary. No redaction projection or
  mixed MNPI/legal/SAR adapter is bundled. Refuse invalid audience intake without echoing evidence.
- Counts are unique native cases or explicit case/criterion observations. Publish denominators,
  partial IDs and sampling rationale. No convenience sample population inference. Exact decimal
  threshold only; keep failures even when tolerance is met.
- Preserve concerns, contradictions and counterevidence with explicit reviewed-ID mappings.
  A linked rationale cannot prove semantic adequacy; qualified human assessment remains required.
- Require versioned tool/copilot factual content and named human source-faithfulness review.
  No legal privilege, reputation score, automated regulated decision or model-validity inference.
- Validate exact detached native reconstruction before handoff. Human narrative remains a
  separate unverified draft and needs its own source-faithfulness and recipient review.
- No case closure, reportability/SAR filing, customer contact, access change, list modification,
  assurance opinion, external disclosure or system-of-record write. Owner accepts/rejects findings.
