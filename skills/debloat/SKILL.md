---
name: debloat
description: "Run a measured simplification pass on a codebase: baseline, delete what nothing uses, census state machines, encode constraint comments, and stop with numbers when only restructuring or scope cuts remain. Use for 'debloat', 'cut SLOC', 'reduce/simplify the codebase', 'dead code', 'find implicit state machines', or a line-count target."
---

# Debloat

Lines of code are the proxy. The goal is a system that is simpler and still correct. Every
deletion is a claim: the system is better or equal, and still works. Adapted from goal-sloc
(MIT, see NOTICE); the principles it leans on are already skills and are linked, not copied:
**principle-subtract-before-you-add**, **principle-model-the-domain**,
**principle-laziness-protocol**, **principle-prove-it-works**.

## 0. Preflight: nothing is cut before every line here is answered

- **Where:** a worktree on a branch named for the session, never the canonical tree. One
  commit per verified milestone, with a pathspec. Push through the pre-push gates; a deploy
  stays the owner's.
- **Metric:** one counter, written down and used for both ends: non-blank lines that are not
  comment-only, per area (server, scripts, web, tests). Measuring the end with a different
  filter than the start is a fake delta.
- **Feedback loop:** full suite green at baseline (name the known failures), typecheck, and a
  way to run the real thing. No loop on an area means no cuts in it.
- **Target:** the owner's number, or "until the structural well is dry". Do the floor
  arithmetic before promising a number.
- **Tools** go in a throwaway venv or `npx`, never the project: vulture, pylint
  (duplicate-code), radon (complexity) for Python; knip for TS/JS.

## 1. Order of work, safest first

1. **Dead code.** A tool hit is a candidate; `git grep -w` across the repo (code, tests, web,
   docs excluded) confirms it. These look dead and are not: routes and middleware
   (decorators), enum and vocabulary members (iterated), fixtures, entry points, names used
   by string (`getattr`, registries, templates). **Scripts and config entries also have
   consumers outside the repo:** grep systemd units (user and system), crontabs and timers
   for the file name before calling a script dead.
2. **A dead constant can hide an unenforced rule.** If an unused name encodes a policy (a
   deny list, a limit, a role default), find what enforces that policy now and the test that
   covers it. Enforced elsewhere: delete. Enforced nowhere: it is a bug; file it, do not delete.
3. **Placeholder subsystems:** plumbed features that do nothing (a hard-coded "unavailable",
   a logged no-op). Delete.
4. **Misplaced code:** dev or test scaffolding in shipping paths moves to its home.
   **Dated one-shot scripts are records**: they move to `docs/archive/` on
   the owner's word, never deleted.
5. **Duplication:** merge only real duplication. Test fixtures that differ on purpose stay.
   Merging ~10-line blocks is SLOC-neutral; do it for clarity or not at all.
6. **State machines:** run `scripts/state_machines.py`. It reports:
   - **declared** vocabulary or enum classes;
   - **implicit** ones: a status-like key branched on 3 or more string literals, with
     transitions guarded by inline `if status != "proposed"`;
   - **bypassed** ones: a raw literal compared where a declared member exists, which a rename
     will not catch.
   Read each hit. A classification (a bench verdict) or a state read from outside (systemd's
   ActiveState) is not a lifecycle. Promote real lifecycles to the project's declared pattern
   with their allowed transitions (**principle-model-the-domain**). This is quality work and
   is usually SLOC-neutral; say so.
7. **Comments, a pass of their own over the whole tree.** The counter skips comment-only
   lines, so this pass cannot inflate the number; that is what keeps it honest, not a narrow
   scope. Rank files by comment-only lines, run **/no-comments** on them heaviest first, and
   apply our rules on top of its verdicts:
   - **Keep** records: an owner's quoted approval, a dated owner decision, an incident or item ID, and
     "not X, because Y". Those are the why.
   - **History** ("used to", "was", "no longer") is the session's story: rewrite it as the
     present-tense why, or delete it.
   - **A constraint comment** ("do not remove", "must stay") gets a test that fails if the
     thing changes, then the comment can go (a guarding comment earns a test).
   - **A workaround comment** names a root cause: fix it or file an item and cite the ID.
   - **A comment the code contradicts:** the code wins; fix the comment.
   Before committing, run `scripts/comment_verify.py <repo> <node_modules>`: it proves the
   code is unchanged with comments stripped and lists every record ID a file lost. Agents
   drop IDs while tightening (31 in one 360-file pass); restore each one.
   Two more traps, both hit on that pass:
   - **Comments can be load-bearing.** Tests anchor on section banners (`# --- uplink`) or
     grep for a word in a comment. The full suite catches these; restore the line.
   - **Installed and pinned copies** (units, scripts copied under `/usr/local`, hash-pinned
     files) differ from the repo after a comment edit. Hold them back as a patch and name
     them for the owner; they land with a reinstall or a pin update.
   Commit per file or small group. Report comment lines before and after per area, and the
   count per verdict, apart from the code delta.

8. **Restructuring** of the biggest modules (radon hotspots) is the last lever and rarely a
   SLOC win. Do not start one you cannot finish and verify this session; file it instead.

## 2. Gaming, refused

Editing the counter's scope, packing lines, reformatting, deleting features or records to move
the number. A scope cut is the owner's decision: escalate with the floor arithmetic.

## 3. Verify and stop

After each milestone: suite, typecheck, web tests; re-measure with the same counter; commit.
Stop when consecutive milestones yield little, or every remaining lever is restructuring or
scope. Stopping early with honest numbers is a finding, not a failure.

## 4. Report

- Baseline and end, per area, from the same counter. Lines deleted.
- **Self-audit:** share of the cut that was structural (dead, placeholder, relocate, dedup)
  versus cheap (formatting, line packing). Cheap dominating means stop. The comment pass
  is reported on its own line, never folded into the code delta.
- State machine census: declared, implicit, bypassed, each with file and states.
- Candidates rejected and why (false positives teach the next run).
- Owner calls: archive moves, scope cuts, restructuring items to file.
- Clean up: worktree removed, temp venv deleted.
