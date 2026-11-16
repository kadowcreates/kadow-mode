---
name: session-close
description: "Close out a session so nothing lives only in its transcript: find unpushed work, promises made in chat, records that disagree with what was built, decisions with no build item, and inferred items nobody wrote down; fix or record each, then report whether the session can close. Use for /session-close, or when the owner asks what is left, whether anything is undocumented, or says he is closing or merging sessions."
---

# Session close

A session is closable when everything it knows lives somewhere a fresh agent will find:
a pushed commit, a ledger record, a memory, or a line in a live handoff. The transcript
is not one of those places. Work the list below against this session's own transcript
and the trees it touched; read, don't recall.

## 1. Inventory

List what this session touched: repos and worktrees, branches, ledger records (created
or updated), ADRs, artifacts, memories, background jobs, browser tabs, scratch files.
Search the transcript for tool calls; don't reconstruct from memory.

## 2. Nothing unbacked

For each repo and worktree touched: `git status -sb`, ahead count, stashes, branches
named for this session. Push what is yours. Remove a worktree only when it is clean and
has nothing ahead of main. Stop background jobs you started. Close browser tabs you
opened. Anything another session owns is reported, not touched.

## 3. Promises

Find every sentence in your own replies that points at the future: "after deploy",
"I'll check", "once X runs", "pending", "follow-up", "later", "until built". Each one is
done now, or it sits in a record as Plan or Blocker (Needs Validation), or in a handoff.
A promise only in chat is lost when the session closes.

## 4. Records match reality

For each record touched, re-read it against what shipped: title, description, acceptance
criteria, Status. A design that changed mid-build (a different library, a narrower
scope) gets a Progress line saying what and why. A residual the fix can't reach
(history it can't correct, a case it skips) is written into the record.

## 5. Decisions have build items

Every decision made or accepted this session (an ADR edit, an owner call in chat)
either has an open item to build it or is explicitly Proposed and waiting. An Accepted
decision with no item is the most common gap. File the item; don't build it.

## 6. Inferred items

The things nobody asked about:
- Siblings of a fix: other callers or startup paths with the same flaw (close the
  bypass). Check them; record or fix.
- Caveats said in chat ("board power only", "days X to Y stay wrong").
- `ponytail:` ceilings and known limits added this session.
- Side observations: a red test, an alert in push output, an odd process, noise you
  stepped past. One line each: filed, or named in the report as not looked into.
- The owner's feedback or praise in this session: is it in memory?

## 7. Report

Open with the session id. Keep it short and grouped:
- **Closable: yes / no** (and what blocks it).
- **Fixed or recorded now:** each gap and where it went (record id, commit).
- **Checked clean:** what you looked at and found nothing, in one line each.
- **Waiting on the owner:** decisions and buttons only they can press.
- **Handoff:** any check another session must run, and the record that holds its Plan.

Fixing gaps is two-way-door work: do it, then report. Deploys, controls behind an approval
gate, sends and deletes of others' work stay one-way: list them, don't do them.
