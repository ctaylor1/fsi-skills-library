# Domain Rules — phishing-and-bec-investigator

Orientation references: email authentication (SPF/DKIM/DMARC, RFC 7208/6376/7489), BEC and
invoice/vendor-impersonation fraud typologies (FBI IC3 BEC advisories), and MITRE ATT&CK
phishing techniques. The firm's email-security standard and its **scoring + watchlist
config** take precedence and are versioned contracts. Scoring is a triage rank for a human
adjudicator, not a determination.

## Indicator scoring (deterministic, documented)

Risk is computed from explainable inputs; the mapping is configuration, not judgment.

| Indicator | Contribution (default) |
| --------- | ---------------------- |
| SPF result | fail +2, softfail +1, none +1 |
| DKIM result | fail +2, none +1 |
| DMARC result | fail +3 |
| Lookalike sender domain (homoglyph or edit-distance ≤ 2 vs a known domain) | +4 |
| Reply-to domain ≠ From domain | +2 |
| Display-name impersonation (watchlisted party from a non-corporate domain) | +2 |
| Malicious link (display≠href host, lookalike host, or raw-IP host) | +3 each, capped +6 |
| Suspicious attachment (`.html/.htm/.hta/.js/.vbs/.exe/.scr/.iso/.lnk`) | +3 |
| BEC payment request present | +3 |
| Beneficiary/vendor bank change (beneficiary not in approved registry) | +4 |
| Urgency / secrecy / first external contact | +1 each |

Bands: **Critical** ≥ 12, **High** ≥ 8, **Medium** ≥ 4, **Low** ≤ 3. The band ties out to
the score and is checked by `validate_output`.

## Disposition recommendations (the ONLY dispositions permitted — all recommendations)

Evaluated in order; the first match wins:

1. `needs-data` — missing `from_addr` or missing SPF/DKIM/DMARC results (never guessed).
2. `possible-duplicate` — same `from_addr` + `subject` as an open case → **linked** to that
   parent case, not re-investigated or closed.
3. `recommend-bec-fraud` — payment request with a beneficiary/vendor bank change **and** a
   sender anomaly (auth failure or impersonation). Routes to `payment-fraud-case-investigator`.
4. `recommend-credential-phishing` — malicious link **and** a sender anomaly. Routes to
   `identity-access-reviewer` (credential exposure).
5. `recommend-malware-phishing` — suspicious attachment **and** a sender anomaly. Routes to
   `cyber-incident-response-coordinator`.
6. `recommend-suspicious` — score ≥ 4 with sender/behavioral anomalies but no confirmed
   payload; analyst review (routes to incident response when High/Critical).
7. `recommend-benign` — authentication passes, known sender domain, no payload or payment.

## Hard boundaries (fail closed)

- No **final determination** ("confirmed phishing/BEC") and no **case closure**.
- No **executed containment** (block, quarantine, credential reset, endpoint isolation).
- No **payment recall/hold/reversal** and no **filing** with any authority or network.
- No **guessing** of missing authentication/header evidence.
- No **auto-merge / auto-close**; dedup **links** for human confirmation.

## Evidence bundle — required contents

Durable `case_id`; chronology of the reported activity (received → payment request →
reported); parties (sender/reply-to/recipients/reported-by, masked) and impersonated party;
indicators (IOCs) with per-item citations; amounts and beneficiary for any payment request;
recommended disposition with reason; recommended containment / fraud-coordination steps
(each marked as requiring approval); citations for every item.
