---
name: memory-review
description: "Review an agent's persistent memory folder from first principles: check every fact against the system it describes, give each memory a verdict (keep, merge, pointer, move, promote, drop), merge one topic at a time with the owner's go, and prove nothing live was lost. A staleness-only mode just checks the facts and links and reports. Use for 'review the memories', 'clean up memory', 'memory staleness' or 'check memories for staleness' (staleness-only), 'MEMORY.md is over budget', or after rules change and memories may now restate them."
---

# Memory review

A memory earns its place only if it makes the system work better at what it is for. Everything
else is noise the agent reads every session. The review cuts noise without losing a live fact,
and every claim it makes rests on a script's output or a file the owner can open.

The folder this assumes: one memory per `.md` file with frontmatter (`name`, `description`,
`type`), `[[name]]` links between memories, and an index `MEMORY.md`, one line per memory.

**Two modes.** **Staleness only** (the request is a staleness check, a routine check, or
`staleness`): run step 0, fix false facts and dead links, re-run, report the numbers, and stop.
No verdicts, no merges. **Full review** (everything else): steps 0 to 4.

## 0. Baseline (measure before touching anything)

    python scripts/staleness.py <memory-dir> [--budget 200] [--host NAME]

Record: memory count, index lines, fact lines read, false, unreadable, and each finding list.
A **false fact** is fixed first, before any merge: either the memory is wrong (correct it or
drop it) or the fact line is (correct the line). An **unreadable** fact is not a pass.

A fact line is an HTML comment the agent never reads, so it costs no context:
`<!-- fact: ~/repo/app.py contains "retry_limit" -->`, `buildbox:~/path lacks "TEXT"` for a
file on another machine, or `<!-- fact: none (why) -->` for a preference with nothing to read.
A memory that names a file or a system needs one. The script is read-only and opens no network
connection: facts for another machine are listed as not checked; run it there with
`--host buildbox` to check them.

## 1. A verdict for every memory

Read each memory whole, then check what it claims against what runs. Verdicts:

| Verdict | When |
|---|---|
| **keep** | It changes what the agent does, and nothing else says it |
| **merge** | Same topic as others: one memory per topic (one per person, project, machine, practice) |
| **pointer** | A system, repo or doc can answer it: keep where to look, not a copy that drifts |
| **move** | A procedure: it belongs in the doc beside the work (a README, a runbook), not in memory |
| **promote** | It is a rule every agent needs: draft it into the rules file; the memory keeps the incidents |
| **drop** | Stale, wrong, or about a direction that has ended |

Lenses that decide most cases:
- **Facts readable from a system get a pointer.** A version number, a config value, a team
  roster: the memory says where to read it and when it was last checked.
- **A rule already written elsewhere gets a pointer**, never a second copy.
- **Is it recurring?** A failure that recurs gets a gate (a hook, a test); otherwise a fix and
  a regression test, and the memory labels itself guidance.
- **Keep the why.** A merged memory keeps each incident's date and ID, and the owner's own
  words where they decided something.
- **A thin memory is not junk on thinness alone**: it may be a deliberate test or a held
  decision. Check before dropping.

Write the verdicts as a table (memory, verdict, why, evidence). Unlisted means keep.

## 2. Merge one topic at a time, with the owner's go

Show the owner the proposed survivor's **contents**, not file names, one topic per round.
Merge only on the owner's go. Then:

1. Write the survivor: frontmatter, a first line naming what it absorbed, the kept content,
   fact lines, `[[links]]`.
2. `python scripts/merge.py <memory-dir> <survivor> <absorbed>...` moves each absorbed file
   to `archive-YYMMDD/` (history kept), repoints links, drops their index lines, removes
   duplicate and self links, and prints dead links.
3. Add the survivor's index line. Fix any dead link it printed.
4. Commit, one topic per commit, naming what merged.

## 3. Prove nothing live was lost

    python scripts/coverage.py <memory-dir> <memory-dir>/archive-YYMMDD

It lists record IDs and quoted phrases from the archived files that the live set no longer
holds. Classify each: **stale** (the record is closed: say how you checked), **moved** (name
where), **trimmed on purpose**, or **lost** (restore it). This is a floor: it cannot see plain
prose such as a measurement or a flag value. So also read each absorbed file side by side with
its survivor and list every live statement the survivor dropped. Restore the lost ones.

Then run `staleness.py` again: false facts must be 0, and the index under budget.

## 4. Report

Before and after: memory count, index lines, fact lines (true / false / unreadable), findings
per list, anchors absent and how each was classified. Name what is held for the owner (a
verdict that is a taste call, a rule draft waiting on review).

## Rules for the reviewer

- Never delete a memory file: archive it. The archive is the undo.
- Never edit another agent's or project's memory folder.
- A memory is a lead, not a fact: re-check before repeating it.
- Personal or private content never goes into a shared or public repo, including this skill.
