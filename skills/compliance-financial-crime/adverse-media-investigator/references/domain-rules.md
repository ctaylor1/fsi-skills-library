# Adverse Media Investigator — bounded domain rules

- Identity attribution requires supplied source-side values, evidence excerpts and references matching the hit, plus agreement with the known subject name and DOB/identifier. Merely storing a subject DOB or a match label is insufficient.
- A reliable-source identifier mismatch can be labeled a supplied namesake exclusion; conflicting positive/negative evidence or a tier-3 mismatch stays unresolved. Name-only and country-only matches stay unresolved.
- Tier-3 reports never score material alone. They remain unresolved until independent reliable records are supplied; reliable corroborating records can be assessed separately. No automatic authenticity or independence claim is made.
- Valid event and publication dates are separate, ordered event <= publication <= as_of. Missing, invalid or future dates stay unresolved; no event date is invented from publication.
- A later reliable, strongly attributed dismissal can supersede only explicitly referenced earlier hit IDs with the same matter_id and supported event order. Keep both in chronology; unrelated dismissals do not erase allegations.
- Materiality weights/thresholds and coverage freshness are explicit supplied policy. Reliable resolved records use category + assertion + source-tier + recency; dismissed/superseded records contribute zero. Source categories do not prove underlying criminal conduct.
- A scoped negative requires documented current search status, sources, queries, languages and a source reference. Missing coverage or unresolved records prevents `Not material`; it yields `Unknown` unless supported positive records already establish a scoped Watch/Material indicator.
- Sanctions proximity routes to `sanctions-match-investigator`; PEP proximity separately routes to the CDD analyst. All unresolved concerns remain in the output even when a positive specialist route takes precedence.

No live search, complete corpus certification, source authentication, alias/transliteration inference, independent identity determination or legal culpability determination is implemented. The source category describes reported allegations/findings, not proof of the named crime. Low-reliability reports require reliable independent evidence before material conclusions.

All rules apply to the supplied model/profile only. Human reviewers confirm legal applicability and policy authority; version strings and citations alone do not establish them.
