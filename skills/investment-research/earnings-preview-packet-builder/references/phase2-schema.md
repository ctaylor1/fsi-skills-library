# Native schema

All Phase 2 inputs carry schema_version=ir-phase2/1.0, request_id,purpose=internal-research,audience=internal-review,subject{type,id,issuer_id for security},as_of,use_on,aware knowledge_cutoff,information_barrier,sources[],top-level evidence_refs[],unresolved_issues[]. Every row citation must be nonempty, registered and also declared at top level for source permission/time gating. Supplied future or ineligible evidence withholds the result projection. The example is synthetic; no entitlement or authenticity is asserted.

`release_at` is an aware timestamp strictly after knowledge_cutoff. `metrics[]` has unique metric_id,direction=higher-is-better/lower-is-better,baselines[]. Baselines have unique kind=consensus/whisper/guidance/model; currency,unit,accounting_basis,consolidation_scope,period{start,end,fiscal_calendar_id},known_at,evidence_refs; nullable value or guidance-only low/high. Frozen known_at must precede release and be no later than preview cutoff.

See the paired JSON fixtures under evals/files; the separately retained original is mandatory for output reconstruction.

Each cited source known_at must be a timezone-aware timestamp no later than its row known_at. Both the frozen baseline row and its cited source must be strictly before release_at; date-only source knowledge is insufficient for this intraday proof. Reported actual known_at must be at or after release_at and no later than cutoff; preannounced results require a separate unsupported mode. Contradictory temporal assertions are invalid input and are not converted into an eligible comparison.
