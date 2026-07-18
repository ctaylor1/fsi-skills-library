# Domain Rules — ai-use-case-intake-classifier

Explainable intake **risk factors** and how they map to a **governance tier** and a **recommended
governance path**. Thresholds are configuration (versioned, owned by AI/Model Risk Governance), not
hard-coded judgments, and never invented per submission. The firm's AI-governance standard and the
applicable jurisdiction packs take precedence; this map is an orientation reference.

## Factor taxonomy

| Factor | Fires when (default config) | Evidence field(s) |
| ------ | --------------------------- | ----------------- |
| `regulated_decision` | `decision_effect == "regulated-decision"` (credit, insurance, suitability, employment, benefits, etc.) | `decision_effect` |
| `autonomous_action` | `autonomy == "autonomous-action"` (acts without a human in the loop) | `autonomy` |
| `customer_or_public_facing` | `user_populations` includes `customer` or `public` | `user_populations` |
| `special_category_data` | `data.special_category == true` (biometric, health, protected attributes) | `data.special_category` |
| `personal_data_at_scale` | `data.personal_data == true` AND `data.affected_individuals >= personal_data_scale_threshold` (default 10,000) | `data.personal_data`, `data.affected_individuals` |
| `high_materiality` | `materiality.financial_exposure_usd >= high_materiality_exposure_usd` (default 1,000,000) OR `materiality.affected_individuals >= high_materiality_individuals` (default 100,000) | `materiality.*` |
| `cross_border` | `len(jurisdictions) > 1` OR any jurisdiction in the configured `restricted_jurisdictions` | `jurisdictions` |
| `third_party_model` | `external_provider == true` | `external_provider` |
| `genai_or_agentic` | `model_type in {"genai-llm", "agentic"}` | `model_type` |
| `prohibited_practice_flag` | `prohibited_practice_indicators` is non-empty (matches a documented prohibited-practice list) | `prohibited_practice_indicators` |

Factors are **additive and independent**; the output reports each that fired with its own evidence.
There is no opaque composite "AI risk score". A factor whose inputs are missing is reported
`not_evaluable` (e.g., `high_materiality` with no materiality block), never silently treated as fired
or not-fired.

## Governance tier mapping (deterministic, documented)

Let `F` = the set of fired factors.

| Tier | Rule (first match wins) |
| ---- | ----------------------- |
| **Prohibited** | `prohibited_practice_flag` ∈ `F` |
| **High** | any of {`regulated_decision`, `autonomous_action`, `special_category_data`, `high_materiality`} ∈ `F`, OR `len(F) >= 3` |
| **Limited** | `1 <= len(F) <= 2` and none of the High triggers |
| **Minimal** | `F` is empty |

## Recommended governance path (from tier)

| Tier | Recommended governance path |
| ---- | --------------------------- |
| **Prohibited** | Prohibited-practice escalation — route to Legal/Ethics; do not proceed pending human adjudication |
| **High** | Full governance review |
| **Limited** | Standard governance review |
| **Minimal** | Lightweight review (register and attest) |

## Required reviews (from fired factors)

Each fired factor contributes review gate(s); the set is de-duplicated and sorted.

| Fired factor | Required review gate(s) |
| ------------ | ----------------------- |
| `regulated_decision` | Legal/Compliance regulated-decision review; Model risk validation |
| `autonomous_action` | Agent permission-scope and human-in-the-loop review |
| `customer_or_public_facing` | Fairness and conduct review |
| `special_category_data` | Privacy / DPIA review |
| `personal_data_at_scale` | Privacy / DPIA review |
| `high_materiality` | Senior management approval gate |
| `cross_border` | Cross-jurisdiction legal review |
| `third_party_model` | Third-party AI due diligence |
| `genai_or_agentic` | Prompt and agent risk review; Evaluation benchmark |
| `prohibited_practice_flag` | Legal/Ethics prohibited-practice escalation |
| *(none fired — Minimal)* | Register in AI inventory and owner attestation |

The tier and path are a **triage recommendation for a human governance body**. They are not a
governance decision, an approval, an exemption, or an intake closure.

## Hard boundaries (fail closed)

- Never state or imply that a use case **is approved**, cleared, greenlit, exempt, waived, fit for
  production, or that the intake is closed — attribute the decision to the human governance body.
- Never adjudicate the **legality** of a prohibited-practice indicator; escalate it.
- Never **down-tier** on a self-declared attribute that conflicts with the authoritative catalog;
  take the more conservative value.
- Never invent thresholds or tune them to a specific submission; use only the versioned ruleset.

## Open-question prompts (include when relevant)

Missing materiality data, data class not corroborated by the catalog, model type unconfirmed in the
registry, jurisdiction pack not configured, or human-in-the-loop design unspecified for an
autonomous use case. The record must surface these so the reviewer can complete the picture before
adjudicating.
