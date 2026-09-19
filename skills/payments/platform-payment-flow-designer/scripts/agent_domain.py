"""Optional platform agent-commerce evidence module; core CLI unchanged."""
from agent_commerce import validate as check, analyze as review
SKILL = 'platform-payment-flow-designer'
MODE = 'platform'
def validate(data):
    return check(data, MODE)
def analyze(request):
    return review(request, MODE)
