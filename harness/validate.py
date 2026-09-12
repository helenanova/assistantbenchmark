#!/usr/bin/env python3
"""Validate cases/cases.json structure. Exits non-zero on any violation.

Run: python3 harness/validate.py
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "cases", "cases.json")
REQUIRED = ["id", "category", "title", "difficulty", "runs", "prompt",
            "setup", "expected", "rubric", "safety", "dimensions"]
OUTCOMES_RUNS = {1, 3}

def main():
    errors = []
    try:
        data = json.load(open(PATH))
    except Exception as e:
        sys.exit(f"cases.json is not valid JSON: {e}")
    cases = data.get("cases", [])
    cats = data.get("categories", {})
    dims = data.get("dimensions", {})
    if len(cases) != 500:
        errors.append(f"expected 500 cases, found {len(cases)}")
    ids = [c.get("id") for c in cases]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        errors.append(f"duplicate ids: {sorted(dupes)}")
    for c in cases:
        cid = c.get("id", "?")
        for k in REQUIRED:
            if k not in c:
                errors.append(f"{cid}: missing field {k}")
        if c.get("difficulty") not in ("easy", "medium", "hard"):
            errors.append(f"{cid}: bad difficulty {c.get('difficulty')!r}")
        if c.get("runs") not in OUTCOMES_RUNS:
            errors.append(f"{cid}: runs must be one of {sorted(OUTCOMES_RUNS)}, got {c.get('runs')}")
        if c.get("category") not in cats:
            errors.append(f"{cid}: unknown category {c.get('category')!r}")
        if not isinstance(c.get("rubric"), list) or not c.get("rubric"):
            errors.append(f"{cid}: rubric must be a non-empty list")
        for d in c.get("dimensions", []):
            if d not in dims:
                errors.append(f"{cid}: unknown dimension {d!r}")
    if errors:
        print(f"INVALID - {len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"OK: {len(cases)} cases, {len(cats)} categories, {len(dims)} dimensions, schema v{data.get('version')}")

if __name__ == "__main__":
    main()
