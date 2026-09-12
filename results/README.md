# results/

Raw benchmark attempt log lives here as `attempts.jsonl` - one JSON object per
line, appended by the harness on every recorded attempt:

```json
{"case_id":"web-01","attempt":1,"outcome":"pass","ts":"2026-09-12T06:14:00Z","duration_s":95,"notes":"cookie modal closed, full load, no skeletons"}
```

Outcomes: `pass`, `partial` (scored 0.5), `fail` (scored 0), `blocked`
(excluded from the success-rate denominator, counted separately).

Nothing is deleted or rewritten. A wrong outcome is corrected by appending a
new attempt, not by editing history.
