# Adjacent work and handoff artifact

- Ordinary refund/return/cancel proposal: `payment-servicing-planner`; provide the
  original transaction, intended operation, finality, eligibility and authority
  evidence. A lifecycle output cannot substitute for a servicing profile.
- Consumer error/dispute: `issuer-payment-dispute-reviewer`; provide the card and
  payment timeline and asserted error. Do not apply merchant representment clocks.
- One payment's finality or mixed-rail state: `payment-lifecycle-diagnoser`.
- Token lifecycle, account updater or authentication scope:
  `payment-credential-authentication-reviewer`; provide opaque credential identities,
  domain restrictions, current state, consent and exact payment/authentication binding.
- Transaction matching or monetary breaks: `payment-transaction-reconciler`.
- Confirmed bank payment defects: `bank-payment-exception-investigator` before
  `payment-repair-planner`; ordinary card servicing cannot borrow repair authority.

The case stays with its accountable owner. Any handoff must retain original source
links, unknowns, card/account/token identities and requested deliverable. Validate
the target's native input and installation separately. No handoff grants authority.
