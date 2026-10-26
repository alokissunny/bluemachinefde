# Technical review demo

## Before the review

Run `python3 server.py` from `blue-servicing/`, open localhost:8080 in Chrome, and check microphone permission and headphone audio. Do not assume speech recognition works in every embedded browser. Run the verification commands in the root README. If demonstrating AI interpretation, configure the provider first and verify the engine label changes; otherwise identify the deterministic demo mode clearly.

## Six-minute product walkthrough

| Step | Customer interaction | Evidence to show |
| --- | --- | --- |
| 1. Explain a change | “Why did my EMI increase this month?” | Prior/current EMI, rate reset, notice and policy identifiers |
| 2. Explore a decision | “What if I prepay ₹50,000?” | Calculated savings, term reduction, reduced-EMI alternative and assumptions |
| 3. Follow up | “What about ₹20,000 instead?” | Retained prepayment context, recalculated result |
| 4. Act | Review the prepayment and confirm | Exact request details, persisted ID, visible request history; no money movement |
| 5. Investigate | “Show failed payments in the last six months” | Failure reasons, subsequent resolution, optional payment review request |
| 6. Reuse | Select Credit card; ask about an unrecognized transaction; confirm dispute | A second domain using the same ActionExecutor and history |
| 7. Degrade safely | Enable Payments failure in observability; return to chat and ask about payments | Explicit inability to verify, failed trace and no prepared action |
| 8. Inspect performance | Open observability and download evidence | Server traces, browser timings, clear sample counts and conditions |

## Voice validation checklist

These are manual checks to perform on the actual demonstration machine. They are not marked as already passed.

- [ ] Start the microphone and ask “What is my next EMI?”
- [ ] Hear a reply and inspect a final-transcript-to-first-audio timing sample.
- [ ] Follow up with “Actually, check my last payment first.”
- [ ] While a reply plays, begin speaking; observe playback cancellation.
- [ ] Ask “What if I prepay twenty thousand?” In demo-router mode, use digits in text if browser transcription spells out the amount; model interpretation can handle broader language when configured.
- [ ] Enable slow services and verify immediate progress feedback.
- [ ] Confirm the documented behavior when a new utterance arrives during an active query: it remains in the composer for submission.
- [ ] Disable microphone permission and verify that typing remains usable.

## Suggested review discussion

Show `actions.py` and its domain-independent tests. Explain why the model only selects intent, why calculations are deterministic, and why a confirmed request is distinct from moving funds. Show the architecture diagram and the raw performance report. State the limitations of the fixed identity, mock adapters, seeded policy text, browser voice implementation and concurrency evidence.

For a surprise requirement, keep scope within the existing seams: add a domain payload type, an alternate calculation strategy, another mock service field or another policy case. Run the relevant tests and demonstrate the change through the same conversation and confirmation path.
