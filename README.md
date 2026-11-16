# kadow-mode

Agent skills by kadowcreates, for Claude Code and any harness that reads `SKILL.md`
folders (Grok loads them through its Claude compatibility).

| Skill | What it does |
|---|---|
| [debloat](skills/debloat) | Measured simplification pass: baseline, delete what nothing uses, census state machines, a proven comment-only comment pass, stop with numbers. |
| [session-close](skills/session-close) | Close a session so nothing lives only in its transcript: unpushed work, promises made in chat, records that disagree with what shipped. |
| [context-safe-compaction](skills/context-safe-compaction) | Compact a file that rides in every prompt without losing a rule, with probes that prove it. |
| [security-audit](skills/security-audit) | Security guidance, focused reviews and full audits, with validators for the findings report. |
| [humanizer](skills/humanizer) | Find AI writing tells and rewrite in a natural voice without dropping coverage. |
| [meeting-intelligence](skills/meeting-intelligence) | Conservative, actionable summaries of engineering and operations transcripts. |
| [content-intelligence](skills/content-intelligence) | Structured insight summaries from talks, training and recordings. |

## Install

Copy a skill folder into your skills directory:

```
git clone https://github.com/kadowcreates/kadow-mode
cp -r kadow-mode/skills/debloat ~/.claude/skills/
```

debloat links four principle skills (`principle-subtract-before-you-add`,
`principle-model-the-domain`, `principle-laziness-protocol`, `principle-prove-it-works`)
from [pstack](https://github.com/cursor/plugins/tree/main/pstack); it runs without them.

## License

MIT, see [LICENSE](LICENSE). debloat adapts goal-sloc (MIT, Maxim Saplin); its
[NOTICE](skills/debloat/NOTICE) carries that license.
