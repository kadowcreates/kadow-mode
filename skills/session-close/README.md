# session-close

Closes out an agent session so nothing it knows lives only in its transcript. A session
can close when everything it learned is in a pushed commit, a record, a memory, or a
handoff file.

The skill works through the session's own transcript and the repos it touched:

1. **Inventory:** repos, branches, records, artifacts, background jobs.
2. **Nothing unbacked:** push your own work; remove only clean worktrees.
3. **Promises:** every "I'll check" or "after deploy" is either done or recorded.
4. **Records match reality:** each record touched is re-read against what shipped.
5. **Decisions have build items:** each decision has an open item or is marked Proposed.
6. **Inferred items:** sibling bugs, caveats said in chat, side observations.

It ends with a short report: closable or not, what was fixed, and what waits on the owner.
Reversible fixes are made on the spot; deploys, deletes and messages are listed, not done.
