"""Local declared-intent engine; no discovery or execution side effects."""
import json
from pathlib import Path
from research_runtime import route, validate_router
ROOT = Path(__file__).resolve().parents[1]
def registries():
    return tuple(json.loads((ROOT/"references"/name).read_text()) for name in ("routes.json","capabilities.json"))
def validate_document(doc):
    routes, _ = registries()
    return validate_router(doc, routes)
def compute(doc):
    routes, capabilities = registries()
    return route(doc, routes, capabilities)
