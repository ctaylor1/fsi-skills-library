"""Offline source-bound review. No connected action."""
import commercial_card_domain as domain
from payment_foundation import main

if __name__ == "__main__":
    raise SystemExit(main(domain, "calculate"))
