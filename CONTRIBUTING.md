# Contributing

Two kinds of contributions are welcome: new cases and new results.

## Submit a case

Cases come from real assistant work - tasks a person actually asked an
assistant to do, with names and private details genericized. A good case has
a prompt phrased the way a user would say it, a checkable rubric, and
explicit safety limits.

1. Add the case to `harness/gen_cases.py` (the single source of truth),
   following the existing `C(...)` entries: unique id in its category prefix,
   difficulty tier (easy / medium / hard), fixed `runs` count (1, or 3 for
   flakiness-prone work), prompt, setup, expected, rubric, safety.
2. Regenerate the data: `python3 harness/gen_cases.py` (updates
   `cases/cases.json` and `docs/CASES.md`).
3. Open a PR with the case and why it belongs (what real workflow it comes
   from).

Case rules:
- No case may require spending money, sending messages, posting publicly, or
  bypassing bot detection. Cases stop at drafts, options, and proposals.
- `runs` is set before execution and does not shrink later.

## Submit run results

Ran the benchmark against your own agent or setup? Add your attempts.

1. Record each attempt with your agent named:
   `python3 harness/run.py record web-01 pass --agent youragent --model your-model-id --notes "what actually happened"`
2. Each record lands in `results/attempts.jsonl` with a UTC timestamp, the
   agent, and the model. Records from different agents coexist in the log.
3. Regenerate `docs/RESULTS.md` (`report --markdown`) and `docs/badge.svg`
   (`badge`) and include them in the PR.

Honesty rules (the whole point of the repo):
- Never edit or delete history in `results/attempts.jsonl`. A mistake is
  corrected by appending a new record.
- `blocked` means the environment stopped you (CAPTCHA, outage, auth wall),
  not that the task was hard. Hard tasks that produced wrong output are
  `fail`.
- Notes must say what actually happened, including on passes.
