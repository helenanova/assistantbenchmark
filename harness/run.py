#!/usr/bin/env python3
"""assistantbenchmark harness: record attempts and compute honest success rates.

No dependencies. Python 3.8+.

  python3 harness/run.py list [--category CAT]   show cases and run status
  python3 harness/run.py next                    cases that still need runs
  python3 harness/run.py record CASE_ID OUTCOME [--notes TEXT] [--duration SEC]
  python3 harness/run.py report [--markdown]     success rates per case/category

OUTCOME is one of: pass, partial, fail, blocked.
  pass    = 1.0, partial = 0.5, fail = 0.0
  blocked = excluded from the success-rate denominator, counted separately.

Results are append-only in results/attempts.jsonl. Never edit history; record
a new attempt instead.
"""
import argparse, json, os, sys, datetime, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_PATH = os.path.join(ROOT, "cases", "cases.json")
RESULTS_PATH = os.path.join(ROOT, "results", "attempts.jsonl")
SCORE = {"pass": 1.0, "partial": 0.5, "fail": 0.0}

def load_cases():
    with open(CASES_PATH) as f:
        data = json.load(f)
    return data["cases"], data["categories"]

def load_attempts():
    if not os.path.exists(RESULTS_PATH):
        return []
    out = []
    with open(RESULTS_PATH) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                sys.exit(f"corrupt results line {i}: fix or remove it (append-only log)")
    return out

def cmd_list(args):
    cases, cats = load_cases()
    attempts = load_attempts()
    done = collections.Counter(a["case_id"] for a in attempts)
    for c in cases:
        if args.category and c["category"] != args.category:
            continue
        print(f"{c['id']:>9}  [{c['category']:<16}] runs {done[c['id']]}/{c['runs']:<2} {c['title']}")

def cmd_next(args):
    cases, _ = load_cases()
    attempts = load_attempts()
    done = collections.Counter(a["case_id"] for a in attempts)
    pending = [c for c in cases if done[c["id"]] < c["runs"]]
    if not pending:
        print("all cases have completed their required runs")
        return
    for c in pending:
        print(f"{c['id']:>9}  needs {c['runs'] - done[c['id']]} more run(s)  {c['title']}")
    print(f"\n{len(pending)} case(s) pending")

def cmd_record(args):
    cases, _ = load_cases()
    known = {c["id"]: c for c in cases}
    if args.case_id not in known:
        sys.exit(f"unknown case id {args.case_id!r} (see `list`)")
    outcome = args.outcome.lower()
    if outcome not in ("pass", "partial", "fail", "blocked"):
        sys.exit("outcome must be pass, partial, fail, or blocked")
    attempts = load_attempts()
    n = sum(1 for a in attempts if a["case_id"] == args.case_id) + 1
    rec = {
        "case_id": args.case_id,
        "attempt": n,
        "outcome": outcome,
        "ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if args.duration is not None:
        rec["duration_s"] = args.duration
    if args.notes:
        rec["notes"] = args.notes
    with open(RESULTS_PATH, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"recorded attempt {n} for {args.case_id}: {outcome}")

def summarize(cases, attempts):
    by_case = collections.defaultdict(list)
    for a in attempts:
        by_case[a["case_id"]].append(a)
    rows = []
    for c in cases:
        att = by_case.get(c["id"], [])
        scored = [a for a in att if a["outcome"] in SCORE]
        blocked = sum(1 for a in att if a["outcome"] == "blocked")
        if scored:
            rate = sum(SCORE[a["outcome"]] for a in scored) / len(scored)
            rate_s = f"{rate * 100:.0f}%"
        else:
            rate, rate_s = None, "-"
        rows.append({
            "id": c["id"], "category": c["category"], "title": c["title"],
            "attempts": len(att), "scored": len(scored), "blocked": blocked,
            "required": c["runs"], "rate": rate, "rate_s": rate_s,
        })
    return rows

def cmd_report(args):
    cases, cats = load_cases()
    attempts = load_attempts()
    rows = summarize(cases, attempts)
    if args.markdown:
        print("| case | category | title | runs | scored | blocked | success rate |")
        print("|---|---|---|---|---|---|---|")
        for r in rows:
            print(f"| {r['id']} | {r['category']} | {r['title']} | {r['attempts']}/{r['required']} | {r['scored']} | {r['blocked']} | {r['rate_s']} |")
        print()
    else:
        for r in rows:
            print(f"{r['id']:>9}  runs {r['attempts']}/{r['required']}  scored {r['scored']}  blocked {r['blocked']}  rate {r['rate_s']:>4}  {r['title']}")
    print()
    by_cat = collections.defaultdict(list)
    for r in rows:
        by_cat[r["category"]].append(r)
    print("by category:")
    for cat, name in cats.items():
        rs = by_cat.get(cat, [])
        scored = [r for r in rs if r["rate"] is not None]
        avg = f"{sum(r['rate'] for r in scored) / len(scored) * 100:.0f}%" if scored else "-"
        ran = sum(r["attempts"] for r in rs)
        req = sum(r["required"] for r in rs)
        print(f"  {name:<32} {avg:>4}   ({ran}/{req} runs logged)")
    scored_all = [r for r in rows if r["rate"] is not None]
    if scored_all:
        overall = sum(r["rate"] for r in scored_all) / len(scored_all)
        print(f"\noverall mean per-case success rate: {overall * 100:.0f}% over {sum(r['scored'] for r in rows)} scored attempts ({len(scored_all)} cases with results)")

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("list"); pl.add_argument("--category"); pl.set_defaults(f=cmd_list)
    pn = sub.add_parser("next"); pn.set_defaults(f=cmd_next)
    pr = sub.add_parser("record"); pr.add_argument("case_id"); pr.add_argument("outcome")
    pr.add_argument("--notes"); pr.add_argument("--duration", type=int); pr.set_defaults(f=cmd_record)
    pp = sub.add_parser("report"); pp.add_argument("--markdown", action="store_true"); pp.set_defaults(f=cmd_report)
    args = p.parse_args()
    args.f(args)

if __name__ == "__main__":
    main()
