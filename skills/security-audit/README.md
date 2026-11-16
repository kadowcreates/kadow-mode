# security-audit

Security guidance and vulnerability review for codebases, APIs, services, CLI tools,
libraries and daemons.

The skill has two modes:

- **Guidance** (the default): for questions, focused reviews and triage. It uses only the
  relevant parts of the skill and creates no files.
- **Full audit:** only when asked for an audit, a pen test or a complete review. It runs
  reconnaissance, hunts by attack class, validates each finding, and writes a report.

Every finding must cross a real trust boundary and come with source evidence, a safe
reproduction, a priority and the smallest effective fix. Target code is never run with
network access.

The attack-class guides (`WEB-PROTOCOL-AND-AUTH.md`, `AI-AND-LLM.md`,
`SUPPLY-CHAIN-AND-RELEASE.md` and others) are loaded only when the target needs them.

**Validators** (Node.js 20+, no dependencies):

- `validate-findings.cjs`: checks a findings report against `report-schema.json`.
- `validate-coverage-ledger.cjs`: checks that the audit's coverage ledger is complete.

Run their tests with `node --test *.test.cjs`.
