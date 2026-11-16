#!/usr/bin/env python3
"""Score a compaction by PROPOSITION recall, not word overlap.

    python3 probe.py suite.md candidate.md          # score one candidate
    python3 probe.py suite.md before.md after.md    # score both and compare

Word overlap cannot tell "dropped the word *glance*" from "dropped the fact that nine
days of ideas were lost" — it weights them the same, which is why a defensible 39% cut
scored 51.3% and read as a catastrophe. A 2-3% tolerance is only meaningful over
PROPOSITIONS: things the file asserts that a reader must be able to recover.

A suite is a markdown list. Each probe is one line:

    - [critical] 1528223315037261997          # the #ideas channel id
    - [critical] "wrap up"                    # an exact trigger phrase
    - [rule] NO_REPLY is never valid for a #ideas message | NO_REPLY
    - [rule] a commit that changes state refreshes NOW.md | PAT-260717-001, same edit

Class `critical` is DATA — ids, endpoints, commands, exact quoted triggers. Tolerance 0:
one loss fails the run, because paraphrasing a trigger breaks it outright.

Class `rule` is a proposition. After the `|` is a comma-separated list of ANCHORS: the
distinctive fragments that must survive for the proposition to be recoverable. A rule
counts as retained when EVERY anchor is present. Anchors are matched case-insensitively
against the file with whitespace collapsed, so a line wrap is not a loss — that bug cost
a real run two false failures.

Exit 0 if critical retention is 100% and rule retention >= 100 - TOLERANCE.
"""
import re
import sys

TOLERANCE = 3.0


def norm(t: str) -> str:
    """Lowercase, whitespace collapsed. A trigger split across a line wrap is not a
    dropped trigger, and a checker that says it is teaches you to ignore it."""
    return re.sub(r"\s+", " ", t.lower())


def load_suite(path: str):
    probes = []
    for raw in open(path, encoding="utf-8"):
        line = raw.strip()
        m = re.match(r"^-\s*\[(critical|rule)\]\s*(.+)$", line)
        if not m:
            continue
        kind, body = m.group(1), m.group(2).strip()
        if "|" in body:
            claim, anchors = body.split("|", 1)
            anchor_list = [a.strip() for a in anchors.split(",") if a.strip()]
        else:
            claim, anchor_list = body, [body.strip()]
        probes.append({"kind": kind, "claim": claim.strip(), "anchors": anchor_list})
    if not probes:
        raise SystemExit(f"{path}: no probes found — a suite that asserts nothing "
                         f"cannot fail, which is the truncation it was meant to catch")
    return probes


def score(probes, text: str):
    hay = norm(text)
    results = []
    for p in probes:
        missing = [a for a in p["anchors"] if norm(a).strip('"') not in hay]
        results.append({**p, "retained": not missing, "missing": missing})
    crit = [r for r in results if r["kind"] == "critical"]
    rule = [r for r in results if r["kind"] == "rule"]
    pct = lambda xs: 100.0 * sum(1 for x in xs if x["retained"]) / len(xs) if xs else 100.0
    return {
        "results": results,
        "critical_total": len(crit), "critical_retained": sum(1 for r in crit if r["retained"]),
        "critical_pct": pct(crit),
        "rule_total": len(rule), "rule_retained": sum(1 for r in rule if r["retained"]),
        "rule_pct": pct(rule),
        "chars": len(text),
        "pass": pct(crit) == 100.0 and pct(rule) >= 100.0 - TOLERANCE,
    }


def report(label, s):
    print(f"\n{label}  ({s['chars']:,} chars)")
    print(f"  critical  {s['critical_retained']}/{s['critical_total']}  "
          f"{s['critical_pct']:.1f}%   (tolerance 0)")
    print(f"  rules     {s['rule_retained']}/{s['rule_total']}  "
          f"{s['rule_pct']:.1f}%   (tolerance {TOLERANCE}%)")
    for r in s["results"]:
        if not r["retained"]:
            print(f"    LOST [{r['kind']}] {r['claim'][:70]}"
                  f"  — missing: {', '.join(r['missing'][:3])}")
    print(f"  VERDICT: {'PASS' if s['pass'] else 'FAIL'}")


def main(argv):
    if len(argv) < 3:
        raise SystemExit(__doc__)
    probes = load_suite(argv[1])
    scores = [(p, score(probes, open(p, encoding="utf-8").read())) for p in argv[2:]]
    for path, s in scores:
        report(path, s)
    # A suite written AFTER the rewrite encodes the rewrite's wording and scores it
    # high by construction. Observed exactly that on the first real run: the original
    # scored 80% and the rewrite 100%, which is not a result, it is a mirror. The
    # baseline must score 100% or the ANCHORS are wrong, not the file.
    if len(scores) == 2:
        base = scores[0][1]
        if base["critical_pct"] < 100.0 or base["rule_pct"] < 100.0:
            print("")
            print("!! SUITE MISCALIBRATED: baseline " + scores[0][0] + " scores below 100%.")
            print("   The anchors are matching the candidate's phrasing, not the claim.")
            print("   Fix them against the BASELINE until it passes, then score the cut.")
            return 2
    if len(scores) == 2:
        (bp, b), (ap, a) = scores
        saved = b["chars"] - a["chars"]
        print(f"\nsaved {saved:,} chars ({100.0 * saved / b['chars']:.1f}%) "
              f"for {b['rule_pct'] - a['rule_pct']:.1f}pp of rule recall")
    return 0 if scores[-1][1]["pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
