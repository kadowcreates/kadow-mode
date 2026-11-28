# memory-review

Reviews an agent's persistent memory folder: checks every fact against the system it
describes, gives each memory a verdict, merges one topic at a time with the owner's go, and
proves nothing live was lost.

1. **Baseline:** `scripts/staleness.py` reads every fact line (`<!-- fact: PATH contains "X" -->`,
   on the machine it runs on; read-only, no network) and reports false facts, missing paths, dead links, index drift
   and budget.
2. **Verdicts:** keep, merge, pointer, move, promote, drop, with the lenses that decide them.
3. **Merge:** `scripts/merge.py` archives absorbed files, repoints links and tidies the index.
4. **Prove:** `scripts/coverage.py` lists IDs and quotes the merge dropped; a side-by-side read
   covers the rest.

Python 3.10 or later, standard library only. Each script has `--self-test`.
