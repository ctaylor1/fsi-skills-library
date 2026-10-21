"""Gateway protocol controls with independent synthetic transport; no live access claim."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest
from urllib.parse import parse_qs, urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'shared/asset-management'))
import licensed_data_connector as gateway


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.request = dict(request_id='READ-1', dataset='licensed-prices', object_id='FUND-1', as_of='2026-09-30',
                            knowledge_cutoff='2026-10-01', purpose='internal-risk', audience='risk-team')
        self.policy = dict(schema_version=gateway.VERSION, policy_id='TEST', version='1', approval_reference='SYNTHETIC',
                           base_url='https://gateway.example', approved_origins=['https://gateway.example'], principal='service-principal',
                           token_env='FSI_AM_TEST_TOKEN', datasets={'licensed-prices': {'purposes': ['internal-risk'], 'audiences': ['risk-team']}},
                           timeout_seconds=3, max_attempts=2, max_bytes=5000, receipt_max_age_seconds=60)
        self.calls = []
        self.change_permission = lambda x: None
        self.change_snapshot = lambda x: None
    def transport(self, url, token, timeout, max_bytes):
        self.calls.append(urlsplit(url).path)
        self.assertEqual(token, 'synthetic-token')
        self.assertEqual(timeout, 3)
        self.assertEqual(max_bytes, 5000)
        fields = {k: v[0] for k,v in parse_qs(urlsplit(url).query).items()}
        output = dict(fields, principal='service-principal', schema_version=gateway.VERSION)
        if urlsplit(url).path == '/v1/permissions':
            output.update(allowed=True, operation='read', license_version='licensed-v1', checked_at='2026-10-04T12:00:00Z', expires_at='2026-10-04T12:01:00Z')
            self.change_permission(output)
        else:
            records = [{'security': 'TEST-SECURITY', 'price': '101.75', 'currency': 'USD'}]
            output.update(snapshot_id='snapshot-1', records=records, records_sha256=gateway.digest(records))
            self.change_snapshot(output)
        return output
    def run_read(self, **kwargs):
        return gateway.read_snapshot(self.request, self.policy, environment={'FSI_AM_TEST_TOKEN': 'synthetic-token'},
                                     transport=kwargs.pop('transport', self.transport),
                                     clock=kwargs.pop('clock', lambda: datetime(2026,10,4,12,0,10,tzinfo=timezone.utc)),
                                     nonce_factory=lambda: 'fresh-synthetic-nonce', **kwargs)
    def test_bound_read_and_no_false_live_claim(self):
        out = self.run_read()
        self.assertEqual(self.calls, ['/v1/permissions', '/v1/snapshots'])
        self.assertEqual(out['records'][0]['price'], '101.75')
        self.assertEqual(out['access_observation'], 'synthetic-transport')
        self.assertFalse(out['permission_verified_at_gateway'])
        self.assertFalse(out['business_action_taken'])
        self.assertNotIn('synthetic-token', json.dumps(out))
    def test_denial_prevents_data_access(self):
        self.change_permission = lambda p: p.update(allowed=False)
        with self.assertRaises(ValueError): self.run_read()
        self.assertEqual(self.calls, ['/v1/permissions'])
    def test_all_permission_binding_fields(self):
        for field in list(self.request) + ['principal', 'nonce', 'request_sha256']:
            with self.subTest(field=field):
                self.change_permission = lambda p: p.update({field: 'forged'})
                with self.assertRaises(ValueError): self.run_read()
    def test_snapshot_binding(self):
        for field in list(self.request) + ['principal', 'nonce', 'request_sha256']:
            with self.subTest(field=field):
                self.change_snapshot = lambda p: p.update({field: 'forged'})
                with self.assertRaises(ValueError): self.run_read()
    def test_expired_future_and_stale_permission(self):
        for fields in [dict(expires_at='2026-10-04T12:00:09Z'), dict(checked_at='2026-10-04T12:00:11Z'), dict(checked_at='2026-10-04T11:00:00Z')]:
            self.change_permission = lambda p: p.update(fields)
            with self.assertRaises(ValueError): self.run_read()
    def test_permission_expires_during_read(self):
        times = iter([datetime(2026,10,4,12,0,10,tzinfo=timezone.utc), datetime(2026,10,4,12,1,0,tzinfo=timezone.utc)])
        with self.assertRaises(ValueError): self.run_read(clock=lambda: next(times))
    def test_digest_mismatch(self):
        self.change_snapshot = lambda p: p.update(records_sha256='0'*64)
        with self.assertRaises(ValueError): self.run_read()
    def test_reflected_credentials_are_never_returned(self):
        self.change_permission = lambda p: p.update(debug_authorization='Bearer synthetic-token')
        with self.assertRaises(ValueError): self.run_read()
        self.assertEqual(self.calls, ['/v1/permissions'])
        self.change_permission = lambda p: None
        self.change_snapshot = lambda p: p['records'][0].update(debug={'value': 'synthetic-token'})
        with self.assertRaises(ValueError): self.run_read()
    def test_unlicensed_purpose(self):
        self.request['purpose'] = 'redistribution'
        with self.assertRaises(ValueError): self.run_read()
        self.assertEqual(self.calls, [])
    def test_malformed_policy_strings_cannot_grant_substring_access(self):
        self.policy['datasets']['licensed-prices']['purposes'] = 'not-internal-risk'
        with self.assertRaises(ValueError): self.run_read()
        self.policy['datasets']['licensed-prices']['purposes'] = ['internal-risk']
        self.policy['datasets']['licensed-prices']['audiences'] = 'not-risk-team'
        with self.assertRaises(ValueError): self.run_read()
        self.assertEqual(self.calls, [])
    def test_unapproved_insecure_or_redirect_origins(self):
        for url in ['http://gateway.example', 'https://evil.example', 'https://token@gateway.example', 'https://gateway.example/orders']:
            self.policy['base_url'] = url
            with self.assertRaises(ValueError): self.run_read()
    def test_bounded_retries(self):
        calls = []
        def unavailable(*args):
            calls.append(1)
            raise gateway.TransientError('timeout')
        with self.assertRaises(ValueError): self.run_read(transport=unavailable)
        self.assertEqual(len(calls), 2)
    def test_transient_recovery(self):
        attempts = []
        def once(*args):
            attempts.append(1)
            if len(attempts) == 1: raise gateway.TransientError('temporary')
            return self.transport(*args)
        out = self.run_read(transport=once)
        self.assertEqual([r['status'] for r in out['observability']], ['transient-failure', 'received', 'received'])
    def test_boolean_limits_and_extra_operations_rejected(self):
        self.policy['max_attempts'] = True
        with self.assertRaises(ValueError): self.run_read()
        self.policy['max_attempts'] = 2
        self.request['operation'] = 'place-order'
        with self.assertRaises(ValueError): self.run_read()
    def test_missing_credential_and_timezone(self):
        with self.assertRaises(ValueError): gateway.read_snapshot(self.request, self.policy, environment={})
        self.change_permission = lambda p: p.update(checked_at='2026-10-04T12:00:00')
        with self.assertRaises(ValueError): self.run_read()


if __name__ == '__main__': unittest.main()
