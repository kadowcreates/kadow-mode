# context-safe-compaction

Compacts a file that rides in every prompt (`CLAUDE.md`, `AGENTS.md`, MCP tool schemas)
without losing a rule.

A prompt-injected file is the running config of an agent's behaviour. Cutting a line is a
silent behaviour change, and a file truncated by an inject limit still looks complete on
disk. This skill:

- measures what is actually in the context window first;
- lists every rule-bearing line (IDs, "never/always/must", numbered steps) before and
  after, so a dropped rule shows up as a diff;
- shortens prose by rewriting it in controlled language (ASD-STE100), never by deleting
  content;
- proves the result: every proposition and every verbatim-critical item (an ID, a trigger
  phrase, a command) must survive, with zero tolerance for the verbatim ones.

**Scripts** (Python 3.10+, standard library):

- `probe.py suite.md before.md after.md`: scores a compaction by how many propositions a
  probe suite still finds, not by word overlap.
- `score.py before.md after.md`: reports characters saved and meaning lost, with
  verbatim-critical items scored apart from prose.
- `drift.py SKILL.md other/SKILL.md`: fails if two platform copies of the skill differ
  outside their platform blocks.

`suites-example-agents-checkpoint.md` is a worked probe suite.
