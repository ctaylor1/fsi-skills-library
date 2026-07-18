# Adjacent-Skill Handoffs — reinsurance-treaty-interpreter

This skill produces a **plain-language interpretation of one reinsurance treaty** (plus an
optional illustrative ceded-recovery calculation) and stops. It does not determine
recoverability, reserve, bill, dispute, or advise. Downstream skills consume its normalized
interpretation object via the durable `interpretation_id`.

## Downstream (this skill hands off to)

| Downstream skill | When to route | Handoff artifact |
| ---------------- | ------------- | ---------------- |
| `policy-wording-comparator` | The user wants a form/version/wording comparison of the treaty against a prior version, filed form, or the placed slip | `interpretation_id` + the clauses to compare |
| `reserving-analysis-assistant` | The question is about ceded reserve development, severity/frequency, IBNR, or uncertainty | `interpretation_id` + layer terms |
| `catastrophe-exposure-monitor` | The question is about event footprints, accumulations, or modeled loss ranges against the treaty | `interpretation_id` + exposure context |
| `claims-file-reviewer` | A specific ceded-claim file needs review for coverage evidence, chronology, or reserve support | `interpretation_id` + claim reference |
| `policy-document-explainer` | The user pivots from the treaty to interpreting the **underlying direct policy** wording | policy identifier |

For a **binding recoverability determination**, collection, commutation, dispute, or the
legal interpretation of contested wording, there is **no in-scope skill** — those belong to the
authorized ceded reinsurance claims function and, for contested wording, to reinsurance
counsel. Decline and direct the user to that human specialist; do not answer it here.

## Upstream (may call this skill)

Ceded-claims and treaty-administration workflows may request a plain-language treaty
interpretation, or an illustrative recovery under the layer terms, rather than reading the
wording by hand.

## Duplicate-execution prevention

- This skill **only interprets and illustrates**; it must not compare wordings, reserve, review
  a claim file, monitor accumulations, or determine recoverability — those belong to the skills
  and functions above.
- Downstream skills must **not** re-normalize the treaty clauses or re-derive the illustration
  when a valid `interpretation_id` for the same treaty and period already exists; they reuse it.
