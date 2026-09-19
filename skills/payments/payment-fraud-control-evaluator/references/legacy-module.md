# Legacy single-predicate module

Retained from payment-fraud-rule-impact-analyzer v0.2.0 for reproduction of old fixtures. This is a separate input/output contract and is not wrapped by the new foundation. Run from the package root:

```sh
python scripts/legacy/validate_input.py evals/files/sample_example.json
python scripts/legacy/calculate_or_transform.py evals/files/sample_example.json
python scripts/legacy/validate_output.py evals/files/estimate_example.json
```

Schema: rule_change with rule_id, current/proposed field/op/threshold, optional version fields; sample with transactions {txn_id, numeric rule field, label fraud/legit or unlabeled}. It compares two predicates, counts blocks and labeled confusion shifts, and emits a standing disclaimer. Original fixtures and four executable evaluations remain.

Legacy limitations: no source-bound recomputation, label-maturity test, control-portfolio interaction, economic value/friction, causal analysis or authenticated sources. Its basic input/output validation does not establish current native completeness. Use reviewed finite numeric values, unique transaction identifiers and trusted labels for historical reproduction; never route a current portfolio into this schema by dropping fields. Prefer the current root CLIs for new work. Neither mode deploys rules or makes live decisions.
