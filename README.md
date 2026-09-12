# assistantbenchmark

![pass rate](docs/badge.svg)

500 real personal-assistant tasks, run for real, scored honestly.

Most agent benchmarks test coding puzzles or sandboxed web navigation. This one
tests the stuff a personal AI assistant actually gets asked to do all day:
screenshot a site without the skeleton loaders, clip the right coupons, find
the free slots on a calendar, draft a Korean post that doesn't read like a
translation, check a booking's no-show fee before calling it free.

Every case comes from real daily use of an assistant over email, calendar,
docs, sheets, the browser, and GitHub. Cases are run against a live agent on
the live web, multiple times where flakiness matters, and every attempt -
pass, partial, fail, blocked - is appended to `results/attempts.jsonl`.
Failures are published, not rounded up.

## Status

Repo, case list, and harness are up. Results land batch by batch as cases are
executed; the results table in `docs/RESULTS.md` is regenerated from the raw
log each time. No results are claimed before they exist.

## The 500 cases

| category | cases | examples |
|---|---|---|
| Web research & site surveys | 12 | screenshot mid-scroll fully loaded, login-method survey, pricing extraction |
| Accounts & login | 8 | vault login without exposing the password, 2FA handoff, CAPTCHA honesty |
| Bookings & reservations | 8 | restaurant slots, flight options, cancellation/no-show terms |
| Shopping, deals & coupons | 10 | coupon clipping, unit prices, is this deal real |
| Email | 10 | triage, receipt totals, phishing verdict, draft-only replies |
| Calendar & scheduling | 8 | free-slot finder, timezone conversion, conflict detection |
| Docs, Sheets & Drive | 8 | formatted sheets, append without breaking, folder conventions |
| Writing, translation & drafts | 8 | Korean posts, Show HN, proofreading register |
| Code & GitHub | 8 | issues, releases, CI, tests |
| Research reports | 6 | feasibility with honest downsides, market comparisons |
| Monitoring & standing checks | 6 | weekly deal checks, reply watching, clean monitor retirement |
| Data extraction & QA | 8 | screenshot quality gate, schema validation, fact-check before publish |

Full text of every case, with setup, expected outcome, rubric, and safety
limits: [docs/CASES.md](docs/CASES.md). Machine-readable source:
[cases/cases.json](cases/cases.json).

## How a run works

```sh
python3 harness/run.py list                 # all 500 cases and their run status
python3 harness/run.py next                 # what still needs runs
python3 harness/run.py record web-01 pass --notes "clean load, no skeletons"
python3 harness/run.py report               # per-case and per-category rates
```

Each case defines how many runs it needs (1 for deterministic work, 3 for
flakiness-prone work like browser rendering). An attempt ends in one of four
outcomes:

- **pass** (1.0) - every rubric item met
- **partial** (0.5) - the core result is right but rubric items were missed
- **fail** (0.0) - wrong, incomplete, or invented output
- **blocked** - outside the agent's control (CAPTCHA, down site, auth wall);
  counted separately, not hidden inside the success rate

Every recorded attempt carries the agent name, the model identifier, and a
UTC timestamp, so runs from different agents can share one log. The report
also shows a per-case **flaky** column (stddev of scored attempts - how much
a case's outcome swings between runs), a **median duration** column (speed is
part of assistant quality), and breakdowns by **difficulty tier** and by
**capability dimension** (online-task, multi-step, restraint, memory, speed,
proactive) - so "where does it fail" is as visible as "how often". The badge
above is regenerated from the raw log with `python3 harness/run.py badge`.

Because every record names its agent and model, results from different
assistants coexist in one log and can be compared head-to-head:

```sh
python3 harness/run.py agents    # per-agent rates by category + overall
```

## How this differs from assistantbenchmark.com

The site assistantbenchmark.com is an editorial scoreboard: reviewers rate
assistant products 1-10 across dimensions after using them. This repo is the
complement, not a copy: 500 executable case definitions, an append-only raw
log of every real attempt (including failures), and numbers that anyone can
recompute from the log. Editorial scores say what a reviewer felt; this log
shows what actually happened, run by run.

Per-case success rate = mean score over scored attempts. The methodology,
including the safety rules baked into every case (no spending money, no
sending messages, drafts only until a human approves), is in
[docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## Repo layout

```
cases/cases.json      the 500 cases, single source of truth
docs/CASES.md         human-readable case list (generated)
docs/METHODOLOGY.md   scoring, repetition, safety, limitations
docs/RESULTS.md       latest results table (generated from the log)
harness/run.py        record attempts, compute rates
harness/gen_cases.py  regenerates cases.json + CASES.md
results/attempts.jsonl  append-only raw log, one JSON object per attempt
```

## Contributing

Cases from other people's real workflows and results from other agents are
welcome - see [CONTRIBUTING.md](CONTRIBUTING.md).

## CI

Every push and PR runs the case-schema validator
(`harness/validate.py`: 500 cases, unique ids, required fields, valid
categories/dimensions/run counts), checks that generated docs are in sync
with the case definitions, and validates the results log as JSONL.

## Honesty policy

The point of the repo is the failure column. Results are append-only: a wrong
verdict is corrected by recording a new attempt, never by editing history.
Roundups, cherry-picked retries, and silent re-scoring are exactly what this
benchmark exists to avoid.

## License

MIT - see [LICENSE](LICENSE).
