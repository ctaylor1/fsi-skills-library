# Domain Rules — actuarial-model-run-assistant

The documented assumption config governs (versioned). Method implemented: **volume-weighted
chain-ladder** on a cumulative triangle.

## Computation (deterministic)
| Step | Definition |
| ---- | ---------- |
| Age-to-age factor `LDF[j]` | `Σ_i cum[i][j+1] / Σ_i cum[i][j]` over origins `i` with both cells filled |
| Cumulative dev factor `CDF[j]` | `tail_factor × Π_{k≥j} LDF[k]`; `CDF[last] = tail_factor` |
| Latest diagonal | Per origin, the most recent filled `(age, value)` — never read across a null |
| Ultimate | `latest_value × CDF[latest_age_index]` |
| IBNR | `ultimate − latest_value` |
| Totals | `Σ ultimate`, `Σ IBNR` |

Assumptions (`method`, `tail_factor`) are a **versioned contract**; the run records the version.
A factor with a zero/empty denominator is reported as **not-computable**, never forced.

## Reporting (indication only)
- The run reports factors, per-origin ultimate/IBNR, and totals as an **indication for review**.
- It does not select a method for the actuary, weight multiple methods, or book a number.

## Hard boundaries (fail closed)
- Never book/set a reserve; never certify adequacy; never invent a tail factor or method.
- Ragged/non-monotone triangles are flagged, not silently repaired.
