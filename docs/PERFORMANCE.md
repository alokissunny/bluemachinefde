# Performance evidence

Measured on 2026-10-26T08:05:27+00:00. Raw samples: [performance.json](../blue-servicing/performance.json).

## Recorded HTTP latency

| Scenario | Samples | Server p50 | Server p95 | HTTP round-trip p50 | HTTP round-trip p95 |
| --- | --- | --- | --- | --- | --- |
| normal | 12 | 148 ms | 177 ms | 151 ms | 179 ms |
| slow | 4 | 879 ms | 888 ms | 881 ms | 892 ms |
| payments failure | 4 | 178 ms | 180 ms | 182 ms | 183 ms |

## Method and limits

Python 3.9.6 on Darwin. Requests ran sequentially against localhost. Domain adapters inject random 60–180 ms delays; slow mode multiplies them by five. The optional AI provider was not active. Percentiles use nearest-rank calculation; small sample counts are illustrative, not stable capacity estimates.

Server latency includes routing, adapter calls, rules and response preparation. HTTP round trip additionally includes loopback HTTP and client processing. Parallel adapter calls keep a multi-service query closer to the slowest adapter than to the sum of all adapter delays. Failure samples deliberately return an unavailable Payments source with no action prepared.

## Functional checks

The HTTP run verified cross-session confirmation rejection, duplicate-submission idempotency, stale-token rejection, safe payment failures, persisted loan and card requests, request history and malformed-input rejection. Thirteen unit tests cover the calculator, conversational context and shared action executor.

## Browser and voice evidence

A typed EMI question was verified in the browser observability view: 149 ms text round trip, with one recorded sample. This is a single manual observation, not a statistically meaningful browser benchmark. The dashboard records and exports actual browser samples.

Real microphone latency and audible interruption timing have not been measured in this submission. The app instruments final-transcript-to-first-audio on the synthesis start event and cancellation-call dispatch on speech start. Cancellation dispatch measures an API call, not the time until sound stops. No synthetic voice result is presented as a real measurement.

## Reproduce

```sh
cd blue-servicing
python3 server.py
# In a second terminal:
python3 verify_http.py
```

The verifier creates synthetic requests and overwrites the raw report. Open System observability to examine traces or download browser evidence. Results vary with host scheduling and simulated random delays. No throughput, 1,000-conversation, external provider or production network performance claim is made.
