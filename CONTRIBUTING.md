# Contributing

Thanks for helping. This repo holds agent skills, so a change to one is a change to how an
agent behaves. The bar is: the skill still does what its description promises, and you can
show it.

## Ways to help

- **Report a skill misfiring.** Open an issue with the skill name, the prompt, what the
  agent did, and what you expected. A transcript excerpt beats a summary.
- **Fix or sharpen a skill.** Small, focused pull requests are easiest to review.
- **Propose a new skill.** Open an issue first, so we agree it belongs here before you
  write it.

## A skill's shape

```
skills/<name>/
  SKILL.md     required
  README.md    required: two or three paragraphs for people browsing GitHub
  ...          optional scripts or reference files that SKILL.md points to
```

`SKILL.md` starts with YAML frontmatter:

```yaml
---
name: <name>            # must match the folder name
description: "<what it does>. Use when <the triggers>."
---
```

The `description` is how an agent decides to load the skill, and it rides in every prompt.
Keep it under 1,024 characters. Say what the skill does and name the phrases or situations
that should trigger it.

## Writing a good skill

- **Instructions, not essays.** Each line should change what the agent does. Cut
  background the agent doesn't need to act.
- **Say when to stop.** A skill that never says "done" runs forever or stops at random.
- **Name what not to do** when an agent is likely to get it wrong, with the reason.
- **Prove it.** If the skill claims a result (fewer lines, no lost rules, a valid report),
  give the agent a way to check it, ideally a script in the skill folder.
- **No private data.** No names, hostnames, home paths, internal record IDs that point at
  a private system, or tokens. Write "the owner", not a person's name.

## Scripts

- Python: 3.10 or later, standard library only, so a skill installs with a copy.
- Node: 20 or later, no dependencies.
- If a script has logic worth breaking, it has a test or a self-check next to it.
- LF line endings only. `.gitattributes` enforces it.

## Before you open a pull request

```bash
python scripts/check-skills.py              # frontmatter, line endings, scripts compile
node --test skills/security-audit/*.test.cjs  # if you touched security-audit
```

CI runs the same checks on every push and pull request.

In the pull request, say:

1. which skill changed and why;
2. how you checked it: a test, a script run, or a before-and-after transcript.

## Versioning

Skills are versioned by the repo history. A skill that keeps its own `version` field
(humanizer) bumps it in the same pull request and notes the change in its README.

## License

By contributing, you agree your contribution is licensed under the [MIT License](LICENSE).
