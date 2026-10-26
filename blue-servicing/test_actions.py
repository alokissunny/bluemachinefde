import tempfile
import unittest
from pathlib import Path
from actions import ActionExecutor, ConfirmationExpired


class ActionExecutorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.executor = ActionExecutor(Path(self.temp.name) / 'test.sqlite3')
        self.executor.initialize()
        self.session = {'customer': 'CUSTOMER-A'}

    def tearDown(self):
        self.temp.cleanup()

    def test_same_executor_accepts_two_domains_and_persists(self):
        for kind in ['Loan prepayment', 'Card dispute']:
            action = self.executor.prepare(self.session, {'kind': kind, 'amount': 1000})
            self.executor.confirm(self.session, action['token'])
        fresh = ActionExecutor(self.executor.database)
        self.assertEqual({r['kind'] for r in fresh.history('CUSTOMER-A')}, {'Loan prepayment', 'Card dispute'})
        self.assertEqual(fresh.history('CUSTOMER-B'), [])

    def test_retry_creates_only_one_request(self):
        action = self.executor.prepare(self.session, {'kind': 'Loan prepayment', 'amount': 50000})
        first = self.executor.confirm(self.session, action['token'])
        retry = self.executor.confirm(self.session, action['token'])
        self.assertEqual(first['id'], retry['id'])
        self.assertTrue(retry['duplicate'])
        self.assertEqual(len(self.executor.history('CUSTOMER-A')), 1)

    def test_token_cannot_be_used_in_another_session(self):
        action = self.executor.prepare(self.session, {'kind': 'Card dispute'})
        with self.assertRaises(ConfirmationExpired):
            self.executor.confirm({'customer': 'CUSTOMER-B'}, action['token'])
        self.assertEqual(self.executor.history('CUSTOMER-A'), [])

    def test_new_preparation_expires_previous_token(self):
        first = self.executor.prepare(self.session, {'kind': 'Loan prepayment'})
        self.executor.prepare(self.session, {'kind': 'Card dispute'})
        with self.assertRaises(ConfirmationExpired): self.executor.confirm(self.session, first['token'])

    def test_client_cannot_replace_server_owned_payload(self):
        action = self.executor.prepare(self.session, {'kind': 'Loan prepayment', 'amount': 50000})
        self.executor.confirm(self.session, action['token'])
        self.assertEqual(self.executor.history('CUSTOMER-A')[0]['payload']['amount'], 50000)
        self.assertNotIn('token', self.executor.history('CUSTOMER-A')[0]['payload'])
