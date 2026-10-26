"""Exercise a running local demo; creates synthetic service requests and evidence."""
import http.cookiejar
import json
import math
import os
import platform
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = os.environ.get('BASE_URL', 'http://localhost:8080')


def client():
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def call(connection, path, body=None):
    request = urllib.request.Request(BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Content-Type': 'application/json'})
    with connection.open(request, timeout=15) as response:
        return json.load(response)


def expect_status(connection, path, body, status):
    try:
        call(connection, path, body)
    except urllib.error.HTTPError as error:
        assert error.code == status, (error.code, status)
    else:
        raise AssertionError(f'{path} accepted a request that should return {status}')


def summarize(samples):
    result = {'sample_count': len(samples)}
    for key in ['server_ms', 'round_trip_ms']:
        values = sorted(sample[key] for sample in samples)
        for percentile in [50, 95]:
            result[f'{key}_p{percentile}'] = values[max(0, math.ceil(len(values)*percentile/100)-1)]
    return result


def main():
    connection = client()
    call(connection, '/api/bootstrap')
    phases = {}
    queries = ['Why did my EMI increase?', 'What if I prepay 50000?',
               'What about 20000 instead?', 'Check my last payment']
    for phase, turns, switches in [
        ('normal', queries*3, {}),
        ('slow', queries, {'slow': True}),
        ('payments_failure', ['show failed payments']*4, {'fail': True}),
    ]:
        samples = []
        for text in turns:
            start = time.perf_counter()
            result = call(connection, '/api/chat', {'text': text, **switches})
            samples.append({'query': text, 'server_ms': result['trace']['ms'],
                'round_trip_ms': round((time.perf_counter()-start)*1000), 'ok': result['trace']['ok']})
            if phase == 'payments_failure':
                assert not result['trace']['ok'] and result['action'] is None and result['sources'] == []
        phases[phase] = {**summarize(samples), 'samples': samples}

    action = call(connection, '/api/chat', {'text': 'prepay 50000'})['action']
    other = client()
    call(other, '/api/bootstrap')
    expect_status(other, '/api/confirm', {'token': action['token']}, 409)
    first = call(connection, '/api/confirm', {'token': action['token']})
    retry = call(connection, '/api/confirm', {'token': action['token']})
    assert first['id'] == retry['id'] and retry['duplicate']
    stale = call(connection, '/api/chat', {'text': 'prepay 20000'})['action']
    call(connection, '/api/chat', {'text': 'next EMI'})
    expect_status(connection, '/api/confirm', {'token': stale['token']}, 409)
    card = call(connection, '/api/chat', {'text': 'Dispute transaction', 'workflow': 'cards'})
    assert card['action']['kind'] == 'Card dispute'
    card_request = call(connection, '/api/confirm', {'token': card['action']['token']})
    ids = {request['id'] for request in call(connection, '/api/bootstrap')['requests']}
    assert first['id'] in ids and card_request['id'] in ids
    expect_status(connection, '/api/chat', {'text': 123}, 400)
    expect_status(connection, '/api/chat', [], 400)
    expect_status(connection, '/api/telemetry', {'metric': 'unsupported', 'value': 3}, 400)
    # Do not fabricate browser or voice timings: the API is checked with an invalid metric only.
    report = {
        'captured_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'environment': {'target': BASE, 'python': platform.python_version(), 'platform': platform.system(),
            'engine': 'deterministic router (AI environment variables disabled for benchmark)',
            'services': 'in-process synthetic adapters; 60–180 ms random delay, 5x in slow mode',
            'execution': 'sequential requests; nearest-rank p50/p95; not a concurrency benchmark'},
        'phases': phases,
        'checks': {'cross_session_token_rejected': True, 'duplicate_submission_idempotent': True,
            'stale_confirmation_rejected': True, 'payments_failure_safe': True, 'card_action_persisted': True,
            'request_history_persisted': True, 'malformed_inputs_rejected': True},
        'voice_measurements': {'status': 'not recorded', 'reason': 'Requires a real microphone and speech-capable browser; no synthetic timings substituted.'},
    }
    Path(__file__).with_name('performance.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({name: {key:value for key,value in phase.items() if key!='samples'} for name,phase in phases.items()}, indent=2))
    print('All HTTP contract, action and failure checks passed.')


if __name__ == '__main__':
    main()
