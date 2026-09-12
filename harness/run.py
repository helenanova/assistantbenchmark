#!/usr/bin/env python3
"""assistantbenchmark harness: record attempts and compute honest success rates.

No dependencies. Python 3.8+.

  python3 harness/run.py list [--category CAT]   show cases and run status
  python3 harness/run.py next                    cases that still need runs
  python3 harness/run.py record CASE_ID OUTCOME [--notes TEXT] [--duration SEC]
                                 [--agent NAME] [--model NAME]
  python3 harness/run.py report [--markdown]     success rates per case/category
  python3 harness/run.py agents                  head-to-head per agent/model
  python3 harness/run.py badge                   regenerate docs/badge.svg

OUTCOME is one of: pass, partial, fail, blocked.
  pass    = 1.0, partial = 0.5, fail = 0.0
  blocked = excluded from the success-rate denominator, counted separately.

Every record carries the agent and model that produced it plus a UTC
timestamp, so results from different agents stay comparable in one log.

Results are append-only in results/attempts.jsonl. Never edit history; record
a new attempt instead.
"""
import argparse, json, os, sys, datetime, collections, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_PATH = os.path.join(ROOT, "cases", "cases.json")
RESULTS_PATH = os.path.join(ROOT, "results", "attempts.jsonl")
BADGE_PATH = os.path.join(ROOT, "docs", "badge.svg")
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
        print(f"{c['id']:>9}  [{c['category']:<16}] {c['difficulty']:<6} runs {done[c['id']]}/{c['runs']:<2} {c['title']}")

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
        "agent": args.agent,
        "model": args.model,
    }
    if args.duration is not None:
        rec["duration_s"] = args.duration
    if args.notes:
        rec["notes"] = args.notes
    with open(RESULTS_PATH, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"recorded attempt {n} for {args.case_id}: {outcome} (agent={args.agent}, model={args.model})")

def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return None
    return xs[n//2] if n % 2 else (xs[n//2 - 1] + xs[n//2]) / 2

def flaky(attempts):
    """Stddev of scored outcomes; None when fewer than 2 scored attempts."""
    scores = [SCORE[a["outcome"]] for a in attempts if a["outcome"] in SCORE]
    if len(scores) < 2:
        return None
    mean = sum(scores) / len(scores)
    return math.sqrt(sum((s - mean) ** 2 for s in scores) / len(scores))

def summarize(cases, attempts):
    by_case = collections.defaultdict(list)
    for a in attempts:
        by_case[a["case_id"]].append(a)
    rows = []
    for c in cases:
        att = by_case.get(c["id"], [])
        scored = [a for a in att if a["outcome"] in SCORE]
        blocked = sum(1 for a in att if a["outcome"] == "blocked")
        fl = flaky(att)
        if scored:
            rate = sum(SCORE[a["outcome"]] for a in scored) / len(scored)
            rate_s = f"{rate * 100:.0f}%"
        else:
            rate, rate_s = None, "-"
        durs = [a["duration_s"] for a in att if isinstance(a.get("duration_s"), (int, float))]
        med = median(durs)
        rows.append({
            "id": c["id"], "category": c["category"], "difficulty": c["difficulty"],
            "dimensions": c.get("dimensions", []),
            "title": c["title"], "attempts": len(att), "scored": len(scored),
            "blocked": blocked, "required": c["runs"], "rate": rate,
            "rate_s": rate_s, "flaky": fl, "med_s": med,
            "med_s_s": "-" if med is None else f"{med:.0f}s",
            "flaky_s": "-" if fl is None else f"{fl:.2f}",
        })
    return rows

def overall(rows):
    scored = [r for r in rows if r["rate"] is not None]
    if not scored:
        return None
    return sum(r["rate"] for r in scored) / len(scored)

def cmd_report(args):
    cases, cats = load_cases()
    attempts = load_attempts()
    rows = summarize(cases, attempts)
    if args.markdown:
        print("| case | category | difficulty | title | runs | scored | blocked | success rate | flaky | median time |")
        print("|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            print(f"| {r['id']} | {r['category']} | {r['difficulty']} | {r['title']} | {r['attempts']}/{r['required']} | {r['scored']} | {r['blocked']} | {r['rate_s']} | {r['flaky_s']} | {r['med_s_s']} |")
        print()
    else:
        for r in rows:
            print(f"{r['id']:>9}  {r['difficulty']:<6} runs {r['attempts']}/{r['required']}  scored {r['scored']}  blocked {r['blocked']}  rate {r['rate_s']:>4}  flaky {r['flaky_s']:>5}  time {r['med_s_s']:>5}  {r['title']}")
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
    print("\nby difficulty:")
    for tier in ("easy", "medium", "hard"):
        rs = [r for r in rows if r["difficulty"] == tier]
        scored = [r for r in rs if r["rate"] is not None]
        avg = f"{sum(r['rate'] for r in scored) / len(scored) * 100:.0f}%" if scored else "-"
        print(f"  {tier:<8} {avg:>4}   ({len(scored)}/{len(rs)} cases scored)")
    print("\nby dimension:")
    dims = {}
    for r in rows:
        for d in r["dimensions"]:
            dims.setdefault(d, []).append(r)
    for d, rs in sorted(dims.items()):
        scored = [r for r in rs if r["rate"] is not None]
        avg = f"{sum(r['rate'] for r in scored) / len(scored) * 100:.0f}%" if scored else "-"
        print(f"  {d:<12} {avg:>4}   ({len(scored)}/{len(rs)} cases scored)")
    ov = overall(rows)
    if ov is not None:
        print(f"\noverall mean per-case success rate: {ov * 100:.0f}% over {sum(r['scored'] for r in rows)} scored attempts ({len([r for r in rows if r['rate'] is not None])} cases with results)")

BADGE_TMPL = '''<svg xmlns="http://www.w3.org/2000/svg" width="184" height="20" role="img" aria-label="pass rate: {label}">
  <linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
  <clipPath id="r"><rect width="184" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)"><rect width="67" height="20" fill="#555"/><rect x="67" width="117" height="20" fill="{color}"/><rect width="184" height="20" fill="url(#s)"/></g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,sans-serif" font-size="11">
    <text x="34.5" y="15" fill="#010101" fill-opacity=".3">pass rate</text>
    <text x="34.5" y="14">pass rate</text>
    <text x="124.5" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="124.5" y="14">{label}</text>
  </g>
</svg>
'''

def cmd_agents(args):
    attempts = load_attempts()
    if not attempts:
        print("no attempts recorded yet")
        return
    cases, cats = load_cases()
    by_agent = collections.defaultdict(list)
    for a in attempts:
        by_agent[f"{a.get('agent','?')} / {a.get('model','?')}"].append(a)
    cat_of = {c["id"]: c["category"] for c in cases}
    header_cats = list(cats)
    print("agent / model" + " " * 18 + "".join(f"{c[:12]:>13}" for c in header_cats) + f"{'OVERALL':>13}{'runs':>6}")
    for name, att in sorted(by_agent.items()):
        scored = [a for a in att if a["outcome"] in SCORE]
        per_cat = {}
        for c in header_cats:
            cs = [a for a in scored if cat_of.get(a["case_id"]) == c]
            per_cat[c] = f"{sum(SCORE[a['outcome']] for a in cs) / len(cs) * 100:.0f}%" if cs else "-"
        ov = f"{sum(SCORE[a['outcome']] for a in scored) / len(scored) * 100:.0f}%" if scored else "-"
        print(f"{name:<30}" + "".join(f"{per_cat[c]:>13}" for c in header_cats) + f"{ov:>13}{len(att):>6}")

def cmd_badge(args):
    cases, _ = load_cases()
    rows = summarize(cases, load_attempts())
    ov = overall(rows)
    if ov is None:
        label, color = "no runs yet", "#9f9f9f"
    else:
        label = f"{ov * 100:.0f}% ({sum(r['scored'] for r in rows)} runs)"
        color = "#4c1" if ov >= 0.8 else ("#a3c51c" if ov >= 0.6 else ("#fe7d37" if ov >= 0.4 else "#e05d44"))
    with open(BADGE_PATH, "w") as f:
        f.write(BADGE_TMPL.format(label=label, color=color))
    print(f"wrote {BADGE_PATH} ({label})")

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("list"); pl.add_argument("--category"); pl.set_defaults(f=cmd_list)
    pn = sub.add_parser("next"); pn.set_defaults(f=cmd_next)
    pr = sub.add_parser("record"); pr.add_argument("case_id"); pr.add_argument("outcome")
    pr.add_argument("--notes"); pr.add_argument("--duration", type=int)
    pr.add_argument("--agent", default="instinct")
    pr.add_argument("--model", default="instinct-2026-09")
    pr.set_defaults(f=cmd_record)
    pp = sub.add_parser("report"); pp.add_argument("--markdown", action="store_true"); pp.set_defaults(f=cmd_report)
    pb = sub.add_parser("badge"); pb.set_defaults(f=cmd_badge)
    pa = sub.add_parser("agents"); pa.set_defaults(f=cmd_agents)
    args = p.parse_args()
    args.f(args)

if __name__ == "__main__":
    main()
