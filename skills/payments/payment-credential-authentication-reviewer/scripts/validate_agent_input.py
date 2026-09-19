"""Optional agent-commerce CLI; offline supplied evidence only."""
import agent_domain as domain
from payment_foundation import main
if __name__ == "__main__":
    raise SystemExit(main(domain, 'input'))
