#!/usr/bin/env python3
"""Score a compaction: how much was saved, and how much meaning was lost.

    python3 score.py before.md after.md

TWO classes, because averaging them hides the dangerous failure. Verbatim-critical
items are DATA -- a channel id, a Task-ID, an exact trigger phrase, a command the agent
runs. Paraphrasing one breaks it outright, so its tolerance is ZERO. Prose propositions
degrade gracefully, so they get the 2-3% band. One blended number would let you drop a
channel id and still report 98%.
"""
import re
import sys

TOLERANCE = 3.0          # percent of prose content the operator accepts losing

# Verbatim-critical: ids, quoted trigger strings, backticked code/paths/endpoints.
CRITICAL = re.compile(
    r'\b[A-Z]{2,4}-\d{6,8}-\d{3}\b'      # GOV-260809-002
    r'|\bADR-\d{4}\b'
    r'|\b\d{17,20}\b'                    # discord snowflake
    r'|`[^`]+`'                          # code, paths, endpoints
    r'|"[^"]{3,}"'                       # exact trigger phrases
)

STOP = set("""a an the and or but if then than that this these those of to in on at by for with from as is
are was were be been being it its it's do does did not no nor so such very can could should would will
shall may might must you your we our they their he she i me my mine us them there here when where which
who whom what how why all any both each few more most other some only own same too s t just don now""".split())


def _flatten(t):
    """Collapse newlines first. A trigger phrase wrapped across two lines is not a
    dropped trigger, and a checker that says it is teaches you to ignore it."""
    return re.sub(r"\s+", " ", t)


def critical(t):
    return {m.group(0).strip().lower() for m in CRITICAL.finditer(_flatten(t))}


def content(t):
    t = CRITICAL.sub(" ", t.lower())                 # scored separately; don't double count
    t = re.sub(r"[^a-z0-9\s-]", " ", t)
    return {w for w in t.split() if w not in STOP and len(w) > 2}


def score(before, after):
    cb, ca = critical(before), critical(after)
    pb, pa = content(before), content(after)
    lost_c, lost_p = sorted(cb - ca), sorted(pb - pa)
    crit = 100.0 * len(cb & ca) / len(cb) if cb else 100.0
    prose = 100.0 * len(pb & pa) / len(pb) if pb else 100.0
    saved = len(before) - len(after)
    return {
        "chars_before": len(before), "chars_after": len(after),
        "saved": saved, "saved_pct": 100.0 * saved / len(before) if before else 0.0,
        "critical_retention": crit, "critical_lost": lost_c,
        "prose_retention": prose, "prose_lost": lost_p,
        "pass": crit == 100.0 and prose >= 100.0 - TOLERANCE,
    }


def main():
    b = open(sys.argv[1], encoding="utf-8").read()
    a = open(sys.argv[2], encoding="utf-8").read()
    r = score(b, a)
    print(f"size      {r['chars_before']:,} -> {r['chars_after']:,}  "
          f"saved {r['saved']:,} ({r['saved_pct']:.1f}%)")
    print(f"critical  {r['critical_retention']:.1f}%  (tolerance 0 - ids, triggers, commands are data)")
    if r["critical_lost"]:
        print("   LOST:", ", ".join(r["critical_lost"]))
    print(f"prose     {r['prose_retention']:.1f}%  (tolerance {TOLERANCE}%)")
    if r["prose_lost"]:
        print("   dropped:", ", ".join(r["prose_lost"][:25]),
              f"... (+{len(r['prose_lost'])-25})" if len(r["prose_lost"]) > 25 else "")
    print("\nVERDICT:", "PASS" if r["pass"] else "FAIL - review every dropped item above")
    return 0 if r["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
