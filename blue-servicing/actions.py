"""Reusable confirmation and persistence boundary, independent of conversation domain."""
import json
import secrets
import sqlite3
from datetime import datetime, timezone


class ConfirmationExpired(ValueError):
    pass


class ActionExecutor:
    def __init__(self, database):
        self.database = database

    def initialize(self):
        with sqlite3.connect(self.database) as db:
            db.execute('CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, customer TEXT, kind TEXT, payload TEXT, created TEXT, idem TEXT UNIQUE)')

    def prepare(self, session, payload):
        """Only server-owned domain code can supply the executable payload."""
        action = dict(payload, token=secrets.token_urlsafe(24))
        session['pending'] = action
        return action

    def confirm(self, session, token):
        if not isinstance(token, str) or not token:
            raise ConfirmationExpired('A confirmation token is required.')
        with sqlite3.connect(self.database) as db:
            prior = db.execute('SELECT id FROM requests WHERE idem=? AND customer=?', (token, session['customer'])).fetchone()
            if prior:
                return {'id': prior[0], 'duplicate': True}
            pending = session.get('pending')
            if not pending or not secrets.compare_digest(pending['token'], token):
                raise ConfirmationExpired('This confirmation expired. Request a fresh quote.')
            request_id = 'SR-' + secrets.token_hex(6).upper()
            payload = {key: value for key, value in pending.items() if key != 'token'}
            db.execute('INSERT INTO requests VALUES (?,?,?,?,?,?)', (
                request_id, session['customer'], pending['kind'], json.dumps(payload),
                datetime.now(timezone.utc).isoformat(timespec='seconds'), token))
        session.pop('pending', None)
        return {'id': request_id, 'status': 'Submitted for review'}

    def history(self, customer):
        with sqlite3.connect(self.database) as db:
            rows = db.execute('SELECT id,kind,payload,created FROM requests WHERE customer=? ORDER BY rowid DESC', (customer,)).fetchall()
        return [{'id': row[0], 'kind': row[1], 'payload': json.loads(row[2]), 'created': row[3]} for row in rows]
