"""Native offline corridor_domain entrypoint."""
import corridor_domain
from payment_foundation import main

if __name__ == "__main__":
    raise SystemExit(main(corridor_domain, "calculate"))
