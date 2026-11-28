#!/usr/bin/env python3
"""Floor check after a merge: which anchors of the archived memories are gone from the live set.

    python coverage.py MEMORY_DIR ARCHIVE_DIR
    python coverage.py --self-test

Anchors are record IDs (ABC-123456-001 style, ADR-0001, F-012) and quoted phrases of 20+
characters, matched with punctuation and case ignored. A missing anchor is a question, not a
loss: it may be stale, moved to the doc beside the work, or trimmed on purpose. This check
cannot see plain prose (a measurement, a flag value): a side-by-side read is still required.
"""
import pathlib, re, sys, tempfile

ID = re.compile(r"\b(?:[A-Z]{2,6}-\d{6}-\d{3}|ADR-\d{4}|INCIDENT-\d{8}-\d{3}|[FC]-\d{3})\b")
QUOTE = re.compile(r'"([^"\n]{20,})"')


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def body(p):
    t = p.read_text(encoding="utf-8", errors="replace")
    return t.split("---", 2)[2] if t.startswith("---") and t.count("---") >= 2 else t


def coverage(mem_dir, arch_dir):
    live = norm(" ".join(body(p) for p in pathlib.Path(mem_dir).glob("*.md")))
    report, total = {}, 0
    for p in sorted(pathlib.Path(arch_dir).glob("*.md")):
        b = body(p)
        anchors = set(ID.findall(b)) | set(QUOTE.findall(b))
        total += len(anchors)
        gone = sorted(a for a in anchors if norm(a)[:60] not in live)
        if gone:
            report[p.stem] = gone
    return total, report


def self_test():
    with tempfile.TemporaryDirectory() as t:
        d = pathlib.Path(t)
        (d / "a").mkdir()
        (d / "live.md").write_text('Kept BUG-261127-001 and "the map -- is the working item."\n')
        (d / "a" / "old.md").write_text('---\nname: old\n---\nBUG-261127-001, GOV-260101-002, '
                                        '"The map is the working item" and "a phrase that was dropped"\n')
        total, rep = coverage(d, d / "a")
        assert total == 4, total
        assert rep == {"old": ["GOV-260101-002", "a phrase that was dropped"]}, rep
    print("self-test passed")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    if len(sys.argv) != 3:
        sys.exit(__doc__.strip())
    total, rep = coverage(sys.argv[1], sys.argv[2])
    for name, gone in rep.items():
        print(f"## {name} ({len(gone)})")
        print("\n".join(f"- {g[:110]}" for g in gone))
    print(f"\n{total} anchors; {sum(map(len, rep.values()))} not in the live set. Classify each: "
          "stale, moved (say where), trimmed on purpose, or lost (restore it).")
    sys.exit(1 if rep else 0)
