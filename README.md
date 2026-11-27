# kadow-mode

[![check](https://github.com/kadowcreates/kadow-mode/actions/workflows/check.yml/badge.svg)](https://github.com/kadowcreates/kadow-mode/actions/workflows/check.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Agent skills for engineering and operations work. Each one is a folder with a `SKILL.md`,
so it loads in Claude Code, in Grok (through its Claude compatibility), and in any harness
that reads the same format.

The skills share one habit: **measure, then claim.** A skill here stops with numbers, a
proof, or a named gap. It does not stop with "looks done."

## The skills

### Engineering

| Skill | Use it when | What you get |
|---|---|---|
| [debloat](skills/debloat) | "Cut the SLOC", "find dead code", "simplify this codebase" | A measured reduction pass: same counter at both ends, a state-machine census, a comment pass proven comment-only, and a stop when only restructuring is left. |
| [platform-audit](skills/platform-audit) | An audit of a system where AI agents send messages, spend money or ship code | A read-only, risk-based audit run to ISO 19011: risk register, tested controls, graded findings and a ranked fix list, with optional ISO/IEC 27001 and 42001 conformity. Validators check every output. |
| [context-safe-compaction](skills/context-safe-compaction) | `CLAUDE.md` or a tool schema is over its inject limit, or a rule stopped being followed | A smaller prompt file with every rule kept, proven by probe and score scripts. |
| [session-close](skills/session-close) | You are ending or merging agent sessions | A check that nothing lives only in the transcript: unpushed work, promises made in chat, records that disagree with what shipped. |

### Writing and summaries

| Skill | Use it when | What you get |
|---|---|---|
| [humanizer](skills/humanizer) | A draft reads like AI wrote it | A rewrite in a natural voice that keeps every point, with a score and a short review. |
| [meeting-intelligence](skills/meeting-intelligence) | You have a meeting transcript | A conservative summary of decisions, actions, owners and risks. |
| [content-intelligence](skills/content-intelligence) | You have a talk, a training session or a recording | Structured insights and takeaways that keep the technical depth. |

## Install

### Claude Code: as a plugin

```
/plugin install kadow-mode --marketplace kadowcreates/kadow-mode
```

On Claude Code before 2.1.275, add the marketplace first:

```
/plugin marketplace add kadowcreates/kadow-mode
/plugin install kadow-mode@kadow-mode
```

Claude Code picks a skill up from its `description`, or you can call it by name:
`/kadow-mode:debloat`. Each version is a [release](https://github.com/kadowcreates/kadow-mode/releases); update with
`/plugin marketplace update kadow-mode`, then `/plugin update kadow-mode@kadow-mode`.

### Grok, or single skills by copy

Clone once, then copy the skills you want into the harness's skills folder.

```bash
git clone https://github.com/kadowcreates/kadow-mode.git

cp -r kadow-mode/skills/humanizer ~/.grok/skills/     # Grok
cp -r kadow-mode/skills/debloat ~/.claude/skills/     # Claude Code, one skill: /debloat
```

To update, `git pull` and copy again.

### Requirements

The skills are Markdown. A few ship helper scripts:

- **debloat**, **context-safe-compaction**: Python 3.10 or later, standard library only.
- **platform-audit**: Python 3.11 or later, git, and Claude Code or Grok to run the auditor.

## Layout

```
.claude-plugin/
  plugin.json       the Claude Code plugin manifest
  marketplace.json  lets this repo serve as its own marketplace
skills/
  <name>/
    SKILL.md      the skill: frontmatter (name, description) and instructions
    README.md     what it is for, for people browsing the repo
    ...           optional scripts and reference files the skill points to
scripts/
  check-skills.py checks every skill's frontmatter, line endings and scripts (CI runs it)
```

## Related

debloat links four principle skills from
[pstack](https://github.com/cursor/plugins/tree/main/pstack):
`principle-subtract-before-you-add`, `principle-model-the-domain`,
`principle-laziness-protocol` and `principle-prove-it-works`. It works without them.

## Contributing

Issues and pull requests are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## License

[MIT](LICENSE). debloat adapts [goal-sloc](https://github.com/maxim-saplin/goal-sloc)
(MIT, Maxim Saplin); its [NOTICE](skills/debloat/NOTICE) carries that license.
