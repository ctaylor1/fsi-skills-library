"""Optional credential agent-commerce evidence module; core CLI unchanged."""
from agent_commerce import validate as check, analyze as review
SKILL = 'payment-credential-authentication-reviewer'
MODE = 'credential'
def validate(data):
    return check(data, MODE)
def analyze(request):
    return review(request, MODE)
