---
name: memory-review
description: "Review an agent's persistent memory folder from first principles: check every fact against the system it describes, give each memory a verdict (move or pointer first, then merge), move procedures off to their docs, plan every change and ask about the unsure ones, execute only on the owner's go on the final plan, and prove nothing live was lost. A staleness-only mode just checks the facts and links and reports. Use for 'review the memories', 'clean up memory', 'memory staleness' or 'check memories for staleness' (staleness-only), 'MEMORY.md is over budget', or after rules change and memories may now restate them."
---

# Memory review

A memory earns its place only if it makes the system work better at what it is for. Everything
else is noise the agent reads every session. The review cuts noise without losing a live fact,
and every claim it makes rests on a script's output or a file the owner can open.

The folder this assumes: one memory per `.md` file with frontmatter (`name`, `description`,
`type`), `[[name]]` links between memories, and an index `MEMORY.md`, one line per memory.

**Two modes.** **Staleness only** (the request is a staleness check, a routine check, or
`staleness`): run step 0, fix false facts and dead links, re-run, report the numbers, and stop.
No verdicts, no merges. **Full review** (everything else): steps 0 to 5. Steps 0 to 2 change
nothing; the folder is edited only in step 3, after the owner's go on the final plan.

## 0. Baseline (measure before touching anything)

    python scripts/staleness.py <memory-dir> [--budget 200] [--host NAME]

Record: memory count, index lines, fact lines read, false, unreadable, and each finding list.
A **false fact** is fixed first (in a full review, as the plan's first items): either the memory is wrong (correct it or
drop it) or the fact line is (correct the line). An **unreadable** fact is not a pass.

A fact line is an HTML comment the agent never reads, so it costs no context:
`<!-- fact: ~/repo/app.py contains "retry_limit" -->`, `buildbox:~/path lacks "TEXT"` for a
file on another machine, `~/app/config.json json:server.port "8080"` for a JSON value, or `<!-- fact: none (why) -->` for a preference with nothing to read.
A memory that names a file or a system needs one. The script is read-only and opens no network
connection: facts for another machine are listed as not checked; run it there with
`--host buildbox` to check them.

## 1. A verdict for every memory

Read each memory whole, then check what it claims against what runs. Decide in this order,
and stop at the first verdict that fits: a memory leaves the folder before it is merged.

| Order | Verdict | When |
|---|---|---|
| 1 | **drop** | Stale, wrong, or about a direction that has ended |
| 2 | **move** | A procedure or a convention for one folder or tool: it belongs in the doc beside the work (a README, a runbook); the memory keeps one link line, or goes |
| 3 | **pointer** | A system, repo, roster or doc can answer it: keep where to look and when it was checked, not a copy that drifts |
| 4 | **promote** | A rule every agent needs: draft it into the rules file; the memory keeps the incidents |
| 5 | **merge** | What is left shares a topic with others: one memory per topic (one per person, project, machine, practice) |
| 6 | **keep** | It changes what the agent does, and nothing else says it |

Lenses that decide most cases:
- **A person is two memories at most: who they are, and the work done with or for them.** The
  person memory holds role, what they decide, how to work with them. Their repos, hosts,
  accounts, access and product details are a pointer to where those live (their GitHub org,
  their docs), with the date checked, never a copy. Trigger: a memory names someone else's
  repo, host, account or product, so split it and point.
- **A how-to is a move**, even when it is one paragraph: the next reader of that folder or tool
  needs it, and an agent finds it there without memory.
- **A rule already written elsewhere gets a pointer**, never a second copy.
- **Practices of one kind are one topic**: five memories about how to verify work are one
  memory with five parts, not five memories.
- **Is it recurring?** A failure that recurs gets a gate (a hook, a test); otherwise a fix and
  a regression test, and the memory labels itself guidance.
- **Keep the why.** A merged memory keeps each incident's date and ID, and the owner's own
  words where they decided something.
- **A thin memory is not junk on thinness alone**: it may be a deliberate test or a held
  decision. Check before dropping.

Write the verdicts as a table (memory, verdict, target, why, evidence, confidence). Unlisted
means keep. **Confidence** is `sure` or `unsure`. Mark a verdict unsure when two lenses
disagree, when it depends on whether something is still live and you could not check, or when
memories might share a topic but you are not certain. Never resolve an unsure verdict by
guessing: it becomes a question in step 2.

## 2. Plan, ask, and get the go (nothing changes yet)

Write the plan in one file, in the order it will run:
1. false-fact fixes from step 0;
2. drops;
3. moves and pointers: each memory, its target, and the doc text to write there;
4. promotions: the rule draft and where it goes;
5. merges: each survivor's name, what it absorbs, and an outline of its **contents** (sections
   and the facts each keeps), not just file names;
6. the expected after numbers: memory count, index lines.

**Then ask the unsure verdicts, one question at a time.** Each question shows the memories
involved (a short quote of each), the choices (merge into X, keep apart, pointer to Y), what
each choice would cost or lose, and your recommendation first. A possible merge you noticed
but did not plan is a question too. Record each answer and update the plan before asking the
next.

**Then show the final plan and ask for the go on it as a whole.** Changes the owner asks for
update the plan and it is shown again. Execute only after an explicit go on the final plan;
anything not in it waits for another plan. Without an owner to ask, stop here: the plan and the
questions are the deliverable.

## 3. Execute the approved plan

Run it in the plan's order. Do not add to it: a new finding goes into the report as a proposal.

**Moves and pointers first.** Write the procedure into its target doc, then cut the memory to
one line naming where it went (or archive it with `merge.py` into the memory that keeps the
link). A target the reviewer cannot write (another machine, another repo, outside its reach):
the plan carries the doc text ready to paste; the memory stays until the owner pastes it. Never
merge the procedure into a memory instead.

**Then merges**, on what is left:

1. `python scripts/merge.py <memory-dir> <survivor> <absorbed>...` first. It moves each
   absorbed file to `archive-YYMMDD/`, repoints links to the survivor, drops their index
   lines, removes duplicate and self links from link lists, and prints dead links. Without
   git it copies an existing survivor's old text to `archive-YYMMDD/<survivor>.pre-merge.md`.
   A drop with no survivor: `merge.py <memory-dir> - <name>`; fix the dead links it prints.
2. Then write the survivor fresh, from the archived files: frontmatter, a first line naming
   what it absorbed, then the kept facts in its own words, one section per absorbed concern,
   fact lines and `[[links]]`. Never paste absorbed bodies whole: a merge that cuts no words
   has only renamed the files. Aim for the survivor to be shorter than the files it absorbed,
   without losing a fact.
3. Add the survivor's index line. Fix any dead link it printed.
4. In a git folder, commit one topic per commit, naming what merged. Without git, the archive
   and the `.pre-merge` copies are the undo; list each topic in the report instead.

## 4. Prove nothing live was lost

    python scripts/coverage.py <memory-dir> <memory-dir>/archive-YYMMDD

It lists record IDs and quoted phrases from the archived files that the live set no longer
holds. Classify each: **stale** (the record is closed: say how you checked), **moved** (name
where), **trimmed on purpose**, or **lost** (restore it). This is a floor: it cannot see plain
prose such as a measurement or a flag value. So also read each absorbed file side by side with
its survivor and list every live statement the survivor dropped. Restore the lost ones.

Then run `staleness.py` again: false facts must be 0, and the index under budget.

## 5. Report

Before and after: memory count, index lines, fact lines (true / false / unreadable), findings
per list, anchors absent and how each was classified. Name what is held for the owner (a
verdict that is a taste call, a rule draft waiting on review).

## Rules for the reviewer

- Never delete a memory file: archive it. The archive is the undo.
- Never edit another agent's or project's memory folder.
- A memory is a lead, not a fact: re-check before repeating it.
- Personal or private content never goes into a shared or public repo, including this skill.
