# Native handoffs

Use `insurance-policy-transaction-packager` to prepare a separately authorized administrative change; billing past due does not establish cancellation rights. Use `gl-reconciler` for an explicitly mapped GL control and `payment-settlement-reconciler` for source cash/settlement evidence. Preserve account/policy IDs, ledger period, currency, transaction kinds and open breaks. Match actual receiver schema; an envelope or account balance is not a posting instruction.
