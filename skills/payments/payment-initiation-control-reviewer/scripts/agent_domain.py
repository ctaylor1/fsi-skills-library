"""Optional initiation agent-commerce evidence module; core CLI unchanged."""
from agent_commerce import validate as check, analyze as review
SKILL = 'payment-initiation-control-reviewer'
MODE = 'initiation'
def validate(data):
    return check(data, MODE)
def analyze(request):
    return review(request, MODE)
