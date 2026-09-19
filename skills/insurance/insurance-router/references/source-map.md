# Structured routing input and output

The input is a JSON object with explicit `intent` from routes.json, or a recognized
`legacy_skill` plus any required disambiguation. Optional `participant`,
`line_of_business`, `jurisdiction`, `requested_action` and `available_skills` retain
request context. `requested_action` is analyze or draft; other values remain visible
as action-unavailable. Line values are routing families: pc, life, annuity,
disability, long-term-care, health. Preserve the precise product/coverage/cause in
the actual target input instead of treating these broad families as claim codes.

The caller supplies deployment inventory as a list of installed skill names.
Without it, an existing catalog route has unverified installation status. A missing
supporting skill is reported separately from an unavailable lead. An intent for a
later-phase job returns its planned capability and no lead skill; evidence options
do not complete the missing job and their installation also needs verification.

Output retains the request, its content hash, registry version, selected owner,
missing context/support, limitations, target validation requirement and explicit
no-authority state. Revalidation recomputes from the retained request and current
registry; this detects accidental alteration but cannot authenticate the user,
source, legal applicability or execution authority.

Source information used for routing is user-supplied context. Read the selected
target's source map for actual operational evidence. Never invent policy/claim
identifiers, jurisdiction applicability, source permission or connector availability.
