"""Current surveillance intake and strict JSON parsing; no legacy execution path."""
import json

LIVE_SCHEMA = "ir-phase2/1.0"
MIGRATION_REQUIRED = (
    "legacy surveillance migration required: supply explicit schema_version "
    "ir-phase2/1.0 with reported financial periods, source-bound quote observations, "
    "dated security/issuer mapping and an explicit current-age policy for spread comparisons; "
    "legacy packets cannot be calculated or revalidated by the live package"
)


def require_live_contract(doc):
    if not isinstance(doc, dict) or doc.get("schema_version") != LIVE_SCHEMA:
        raise ValueError(MIGRATION_REQUIRED)


def read_json(raw):
    """Reject duplicate object keys and nonfinite constants before source binding."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON object key: " + key)
            result[key] = value
        return result

    def constant(value):
        raise ValueError("non-finite JSON constant: " + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
