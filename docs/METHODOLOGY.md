# Methodology

## Where the cases come from

All 100 cases are abstracted from real tasks a personal assistant was actually
asked to do: site surveys with screenshot rules, coupon clipping, inbox
triage, booking research, Korean/English drafting, repo maintenance, standing
monitors. Names and private details were replaced with generic placeholders.
The benchmark measures the daily-driver work, not toy puzzles.

## Case structure

Each case in `cases/cases.json` has:

- `prompt` - the instruction, phrased the way a user would phrase it
- `setup` - what the run needs (a URL, an account, a mailbox)
- `expected` - what a good outcome looks like
- `rubric` - the checklist an attempt is scored against
- `safety` - the hard limits for that case
- `runs` - how many attempts the case requires
- `difficulty` - easy / medium / hard, a rough prior, not part of scoring

## Repetition

Most cases need 1 run. Cases whose outcomes are known to be flaky - browser
rendering, bot detection, screenshot timing - need 3 runs, because a single
lucky pass says nothing. The `runs` field is fixed in the case definition
before any execution, so repetition requirements can't shrink after bad
results.

## Outcomes and scoring

| outcome | score | meaning |
|---|---|---|
| pass | 1.0 | every rubric item met |
| partial | 0.5 | core result correct, rubric items missed |
| fail | 0.0 | wrong, incomplete, or invented output |
| blocked | excluded | CAPTCHA, site down, auth wall - outside agent control |

Per-case success rate = mean score over scored (pass/partial/fail) attempts.
Blocked attempts are counted and reported but never enter the denominator -
a blocked case is "unknown", not "passed" and not "failed".

Category and overall rates are means of per-case rates, so a category with
more logged attempts doesn't dominate.

## The raw log is append-only

Every attempt is one line in `results/attempts.jsonl`:

```json
{"case_id":"web-01","attempt":2,"outcome":"fail","ts":"2026-09-12T06:20:11Z","duration_s":140,"notes":"grey skeleton boxes along bottom strip"}
```

Lines are never edited or deleted. A mis-recorded attempt is fixed by
appending a correction attempt. `docs/RESULTS.md` is generated from this log
and can always be rebuilt from it.

## Safety rules baked into the cases

Real assistant work touches real accounts, so the cases carry limits:

- **No money.** Booking, shopping, and ticketing cases stop before any
  commitment: options, carts, and estimates only. Cases like `book-08` exist
  precisely to check no-show fees before anything is called free.
- **No sending.** Email, posting, and PR-comment cases produce drafts.
  Sending or publishing as the user requires human approval of the exact
  text, and that approval step is part of the rubric, not a workaround.
- **No CAPTCHA bypass.** Challenges are reported as blockers.
- **Credentials stay sealed.** Login cases verify signed-in state without the
  password ever appearing in logs, notes, or screenshots.

## Known limitations

- Results reflect one agent setup on the live web; the web drifts, so rates
  are a snapshot, not a constant. The log's timestamps matter.
- Rubric judgment for pass/partial involves a human-grade call. The rubrics
  are written to be checkable, but borderline calls exist; notes on each
  attempt record the reasoning.
- 100 cases drawn from one person's workflows over-represent that person's
  life (Korean/English drafting, K-pop fandom tooling, grocery coupons).
  Contributions of cases from other daily workflows are welcome.
