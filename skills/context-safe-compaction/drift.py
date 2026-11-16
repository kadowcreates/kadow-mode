#!/usr/bin/env python3
"""Fail if the two copies of this skill have drifted outside their platform blocks.

    python3 drift.py SKILL.md /path/to/other/SKILL.md

Two copies of a document is the shape that produced FIND-260804-008 and a duplicate deep
dive deleted the same week. A skill about not losing content silently must not itself
drift silently. Platform blocks are expected to differ; nothing else is.
"""
import re
import sys

STRIP = re.compile(r"<!-- PLATFORM:.*?-->.*?<!-- /PLATFORM -->", re.S)


def method(path):
    t = open(path, encoding="utf-8").read()
    t = STRIP.sub("", t)
    t = re.sub(r"^description:.*$", "", t, flags=re.M)   # descriptions are platform-worded
    return [l.rstrip() for l in t.splitlines() if l.strip()]


a, b = method(sys.argv[1]), method(sys.argv[2])
if a == b:
    print(f"in sync — {len(a)} shared method lines")
    sys.exit(0)
import difflib
print(chr(10).join(list(difflib.unified_diff(a, b, "A", "B", lineterm=""))[:40]))
sys.exit(1)
