# Native handoffs

- `claim-settlement-authority-request-builder` receives separately reviewed settlement request and source evidence.
- `claim-payment-closure-reviewer` receives approved payment request with native authority and gate evidence.

These are candidate human-reviewed transfers, not automatic adapters. Construct the receiver's native input, preserve source references, unresolved issues and upstream artifact, then run its input validator. A common envelope proves neither compatibility nor decision authority.
