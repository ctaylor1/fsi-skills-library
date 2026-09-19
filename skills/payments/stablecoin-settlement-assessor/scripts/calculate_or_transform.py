"""Offline native analysis; no connected action."""
import domain
from payment_foundation import main

if __name__ == "__main__":
    raise SystemExit(main(domain, "calculate"))
