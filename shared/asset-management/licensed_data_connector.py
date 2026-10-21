"""Read-only HTTPS client for an institution-approved data gateway (MIT).

The separately controlled deployment policy identifies the trusted gateway and
principal. TLS and a fresh, request-bound gateway permission check establish a
bounded runtime observation. They do not authenticate underlying vendor data or
independently interpret a license. Offline planners never promote saved receipts
to current authorization. No tokens are written to output or error messages.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import ssl
import urllib.error
import urllib.parse
import urllib.request

VERSION = 'investment-data-gateway/1.0'
MAX_BYTES = 2_000_000


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def moment(value):
    if not isinstance(value, str):
        raise ValueError('UTC timestamp required')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError('UTC timestamp required')
    return parsed


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('gateway redirects are forbidden')


class TransientError(Exception):
    pass


def https_get(url, token, timeout, max_bytes):
    # Disable environment proxies: deployment must explicitly approve the TLS
    # gateway, not silently send bearer credentials to an inherited proxy.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
                                        urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    request = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token,
                                                  'Accept': 'application/json'}, method='GET')
    try:
        with opener.open(request, timeout=timeout) as response:
            if response.status != 200 or response.headers.get_content_type() != 'application/json':
                raise ValueError('gateway returned unsupported status or content type')
            raw = response.read(max_bytes + 1)
    except urllib.error.HTTPError as exc:
        if exc.code in {429, 502, 503, 504}:
            raise TransientError('transient gateway failure') from None
        raise ValueError('gateway request denied or failed') from None
    except (urllib.error.URLError, TimeoutError):
        raise TransientError('gateway unavailable') from None
    if len(raw) > max_bytes:
        raise ValueError('gateway response exceeds byte limit')
    try:
        return json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    except (ValueError, UnicodeError):
        raise ValueError('gateway response must be finite UTF-8 JSON') from None


def validate_request(request, policy):
    if not isinstance(request, dict) or not isinstance(policy, dict):
        raise ValueError('request and independently administered policy must be objects')
    keys = {'request_id', 'dataset', 'object_id', 'as_of', 'knowledge_cutoff', 'purpose', 'audience'}
    if set(request) != keys or any(not isinstance(v, str) or not v.strip() or len(v) > 256 for v in request.values()):
        raise ValueError('request requires exactly the documented nonempty string fields')
    for key in ('as_of', 'knowledge_cutoff'):
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', request[key]):
            raise ValueError('request dates must be YYYY-MM-DD')
        datetime.strptime(request[key], '%Y-%m-%d')
    if policy.get('schema_version') != VERSION:
        raise ValueError('unsupported deployment policy version')
    url = urllib.parse.urlsplit(policy.get('base_url', ''))
    if (url.scheme != 'https' or not url.hostname or url.username or url.password
            or url.path not in {'', '/'} or url.query or url.fragment):
        raise ValueError('policy base_url must be an HTTPS origin without credentials/path/query')
    if (not isinstance(policy.get('approved_origins'), list)
            or any(not isinstance(v, str) or not v for v in policy['approved_origins'])
            or policy['base_url'].rstrip('/') not in policy['approved_origins']):
        raise ValueError('gateway origin is not approved')
    for key in ('policy_id', 'version', 'principal', 'token_env', 'approval_reference'):
        if not isinstance(policy.get(key), str) or not policy[key].strip():
            raise ValueError('deployment policy lacks ' + key)
    if not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', policy['token_env']):
        raise ValueError('invalid token environment variable name')
    datasets = policy.get('datasets')
    if not isinstance(datasets, dict):
        raise ValueError('deployment datasets must be an object')
    allowed = datasets.get(request['dataset'])
    if (not isinstance(allowed, dict)
            or any(not isinstance(allowed.get(k), list) or not allowed[k]
                   or any(not isinstance(v, str) or not v.strip() for v in allowed[k])
                   or len(set(allowed[k])) != len(allowed[k]) for k in ('purposes', 'audiences'))
            or request['purpose'] not in allowed['purposes'] or request['audience'] not in allowed['audiences']):
        raise ValueError('dataset/purpose/audience is not allowed by deployment policy')
    for key, maximum in [('timeout_seconds', 30), ('max_attempts', 3), ('max_bytes', MAX_BYTES), ('receipt_max_age_seconds', 300)]:
        value = policy.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
            raise ValueError('policy ' + key + ' outside bounded range')


def read_snapshot(request, policy, *, environment=None, transport=None, clock=None, nonce_factory=None):
    """Perform only two fixed GET operations; injected transport is always synthetic."""
    validate_request(request, policy)
    environment = os.environ if environment is None else environment
    token = environment.get(policy['token_env'])
    if not isinstance(token, str) or not token or any(c.isspace() for c in token):
        raise ValueError('gateway credential missing or invalid')
    synthetic = transport is not None
    get = https_get if transport is None else transport
    clock = clock or (lambda: datetime.now(timezone.utc))
    nonce = (nonce_factory or (lambda: secrets.token_hex(24)))()
    request_hash = digest(request)
    query = dict(request, request_sha256=request_hash, nonce=nonce)
    attempts = []

    def contains_credential(value):
        if isinstance(value, str):
            return token in value
        if isinstance(value, dict):
            return any(contains_credential(k) or contains_credential(v) for k, v in value.items())
        if isinstance(value, list):
            return any(contains_credential(v) for v in value)
        return False

    def fetch(path):
        url = policy['base_url'].rstrip('/') + path + '?' + urllib.parse.urlencode(query)
        for attempt in range(1, policy['max_attempts'] + 1):
            try:
                value = get(url, token, policy['timeout_seconds'], policy['max_bytes'])
                if not isinstance(value, dict):
                    raise ValueError('gateway response must be an object')
                if contains_credential(value):
                    raise ValueError('gateway response reflects credential material')
                attempts.append({'operation': path, 'attempt': attempt, 'status': 'received'})
                return value
            except TransientError:
                attempts.append({'operation': path, 'attempt': attempt, 'status': 'transient-failure'})
        raise ValueError('gateway retry limit reached; no snapshot delivered')

    permission = fetch('/v1/permissions')
    binding = dict(request, request_sha256=request_hash, nonce=nonce, principal=policy['principal'])
    if any(permission.get(k) != v for k, v in binding.items()):
        raise ValueError('permission receipt is not bound to the request and principal')
    if permission.get('schema_version') != VERSION or permission.get('allowed') is not True or permission.get('operation') != 'read':
        raise ValueError('gateway did not authorize this read')
    if not isinstance(permission.get('license_version'), str) or not permission['license_version'].strip():
        raise ValueError('gateway license version missing')
    checked, expiry = moment(permission.get('checked_at')), moment(permission.get('expires_at'))

    def fresh():
        now = clock()
        if now.tzinfo is None or not checked <= now < expiry or (now - checked).total_seconds() > policy['receipt_max_age_seconds']:
            raise ValueError('permission receipt is future-dated, expired or stale')
        for key in ('as_of', 'knowledge_cutoff'):
            if datetime.strptime(request[key], '%Y-%m-%d').date() > now.date():
                raise ValueError('historical read cannot request future dates')

    fresh()
    snapshot = fetch('/v1/snapshots')
    fresh()
    if any(snapshot.get(k) != v for k, v in binding.items()):
        raise ValueError('snapshot is not bound to the authorized request/principal')
    if snapshot.get('schema_version') != VERSION or not isinstance(snapshot.get('snapshot_id'), str) or not snapshot['snapshot_id'].strip():
        raise ValueError('versioned snapshot identity missing')
    records = snapshot.get('records')
    if not isinstance(records, list) or len(records) > 100000 or any(not isinstance(row, dict) for row in records):
        raise ValueError('snapshot requires bounded object records')
    payload_hash = digest(records)
    if snapshot.get('records_sha256') != payload_hash:
        raise ValueError('snapshot records digest mismatch')
    received = clock().isoformat()
    result = {'schema_version': VERSION, 'request': request, 'request_sha256': request_hash,
            'policy_id': policy['policy_id'], 'policy_version': policy['version'], 'policy_sha256': digest(policy),
            'principal': policy['principal'], 'snapshot_id': snapshot['snapshot_id'],
            'records': records, 'records_sha256': payload_hash, 'permission_receipt': permission,
            'permission_sha256': digest(permission), 'received_at': received,
            'access_observation': 'synthetic-transport' if synthetic else 'live-approved-gateway-read',
            'permission_verified_at_gateway': not synthetic, 'source_truth_authenticated': False,
            'license_interpretation': 'relies-on-approved-gateway', 'business_action_taken': False,
            'read_performed': not synthetic, 'observability': attempts,
            'limitations': ['Saved receipts are historical evidence, not authorization for future reads.',
                            'Institution must provision and approve the gateway, identity and license policy.']}
    if contains_credential(result):
        raise ValueError('output would contain credential material')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request', type=Path)
    parser.add_argument('--policy', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = read_snapshot(json.loads(args.request.read_text()), json.loads(args.policy.read_text()))
        print(json.dumps(result, indent=2, allow_nan=False))
    except (ValueError, TypeError, KeyError, OSError):
        # Do not serialize arbitrary gateway errors, request contents or secrets.
        parser.exit(1, 'Read withheld: request, policy, credential, permission or gateway validation failed.\n')


if __name__ == '__main__':
    main()
