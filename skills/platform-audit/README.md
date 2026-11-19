# Agent Platform Audit

A complete, read-only, risk-based audit for production systems where AI agents speak, spend money or ship code on someone's behalf. It is run by a coding agent (Claude Code or similar) with shell access and subagents. It produces an evidence-backed report, a risk register, a control inventory, a findings register with corrective action requests, and a ranked list of fixes.

**Every audit is run and reported to ISO 19011**, the international guideline for auditing management systems: an audit plan, stated criteria, objective evidence, findings graded as nonconformities, opportunities for improvement or observations, and conclusions against the criteria.

## How it works

The audit follows ISO 19011's risk-based approach. It starts from what the system can do to the world, not from a list of files to read:

| Phase | Question | Output |
|---|---|---|
| 0. Plan | What must the audit conclude, about what, against which criteria? | Audit plan |
| 1. Risk assessment | What can the system do outside itself, who is harmed if it goes wrong, and how likely is it? | Ranked risk register |
| 2. Control inventory | What rules, gates, hooks, permissions, alarms and processes are meant to stop each risk? Are they enforced in code or only written down? | Control inventory |
| 3. Control testing | Would each control work as built (design), and did it actually work across the period (operation)? Proven at the consumer, with sabotage and bypass tests. | Tested controls |
| 4. Gaps and grading | Which risks have no working control? | Findings, graded the ISO way |
| 5. Part C, optional | Would the organisation around the system pass an ISO/IEC 27001 or 42001 audit? | Statement of Applicability, certification readiness |

The depth of testing follows the risk: high risks get every path tested across the whole period, low risks get a design review. The report reads the same way the audit ran: **risk → control → test → grade**.

Design and operating effectiveness come from SOC 2 Type I and Type II testing. Risk rating follows ISO/IEC 27005 (likelihood × impact), augmented with FMEA's detection axis and AIAG-VDA action priority, because agent failures are often asynchronous and indirect: the question is not only how likely and how bad, but whether anyone would notice before a client does. The 32 baseline control objectives in `CONTROLS.md` make sure nothing standard is missed, and each one is crosswalked to ISO/IEC 27001, ISO/IEC 42001 and NIST CSF 2.0.

## Why it exists

Agent platforms fail in ways a normal security review misses, because most of the system's behaviour lives in prose instructions that nothing enforces, and the only backstop is one person's attention. This audit was built from real audits of real agent platforms. Every control in scope is put through eight tests, one for each failure mode that kept recurring:

1. Prose rules nothing enforces.
2. Hooks that fail open.
3. Alarms routed through the process they watch.
4. Agents reporting "done" or "green" for work that wasn't.
5. Rules piling up and contradicting each other.
6. Fixes that don't stick: the same bug patched again and again.
7. Shadow-mode flags that never graduate.
8. One human as the only backstop.

Every one of them looks fine from the inside. The audit finds them from evidence, not from the system's own reports about itself.

## What it covers

**Control objectives** (`CONTROLS.md`, 33): one enforcement point per external effect, an audit log reconciled against the outside world, capped and exact money paths, lawful messaging, authenticated routes, tenant isolation, per-client blast radius, secrets, prompt injection and the lethal trifecta, agent least privilege, LLM call discipline, behavioural drift, fail-closed controls, independent alarms, true results, recoverability, hardening, change control, injectable sinks, supply chain, behavioural tests, privacy, systems of record, rule governance, corrective actions that stick, temporary states that end, bounded scope, the human attention budget, value and cost per client, phishing-resistant MFA on privileged accounts, unspoofable sending domains, incident readiness proven by drills, and AI impact assessed and disclosed (ISO/IEC 42001 A.5, A.8).

**Evidence areas** (`EVIDENCE.md`, 15): where to look and how, from route enumeration and secret sweeps to CIS Benchmark scoring, lockfile scanning and count-only privacy scans. They are also the natural split for subagents.

**Part C (optional):** management-system clauses 4–10 · a Statement of Applicability over all 93 ISO/IEC 27001 and 38 ISO/IEC 42001 Annex A controls · a regulatory and contractual screen (GDPR, EU AI Act, TCPA, PCI DSS, SOC 2, CMMC flow-down and more) · a certification-readiness list.

## How to run it

### What you need

- **Python 3.11 or newer**, and **git**.
- **Claude Code** (`claude`) or **Grok** (`grok`) on your PATH, and an account to log in with. Your own account is fine: the clean room keeps its settings, skills and plugins out of the audit.
- **A read-only copy of the system** to audit, kept outside the folder below (`EVIDENCE.md` § Sources and snapshots).
- **A scoped read-only token** for the audit, for any live host or repo the auditor must reach. Never give the audit your own login to the system.

### Start an audit

```
cd skills/platform-audit           # in this plugin, or wherever the skill is installed
python audit.py                     # the auditor runs in Claude Code
python audit.py --harness grok      # or in Grok
```

`audit.py` then does five things, in this order:

1. **Asks the questions.** First the four decisions: Part C, who reviews at holds 2 and 3, clean room, full or delta. Then the plan: whose system it is, the objective, the evidence period, budget, access, report handling, a previous audit, the hosts, users today, where the system's rules live, and owner's-call exemptions. A menu takes a number; Enter takes the default shown.
2. **Writes the prompt** to `C:\audit-cr\work\PROMPT-<YYMMDD>.md` (`~/audit-cr/work/...` on macOS and Linux). Keep it: you restart, or start the reviewer, from it.
3. **Builds the clean room** in `C:\audit-cr`:
   - `config\`: an empty Claude Code config folder. Claude Code starts with `--safe-mode`, which keeps your login and loads none of your account's skills, plugins, hooks, MCP servers or settings.
   - `home-grok\`: an empty home folder for Grok. A separate config folder isn't enough for Grok, because it also loads `~/.claude` and `~/.cursor`.
   - `work\`: a copy of this folder as `agent-platform-audit\` (with a `VERSION` file naming the commit it came from), the prompt, and `out\`, where the report and every file it rests on go.
4. **Checks it** with `cleanroom.py`. "Clean room: yes" goes on. "Clean room: no" lists every leak and stops (see below).
5. **Starts the agent** in `work\` with the prompt. The first time, it asks you to log in to the audit's config before the session opens, then the audit starts by itself; you type nothing until hold 1.

**What you'll be asked.** In Claude Code the auditor and the agent reviewer read anything under your home folder without asking, since the audit reads the system by path. Everything else asks you. Allow commands that only read, such as `git log`, `ls`, `schtasks /query` or `grep`. Allow writes only inside `C:\audit-cr\work`. Deny any write elsewhere, `ssh` or network calls to a host out of scope, and anything that starts a harness with your own config. Grok asks for everything.

The agent's first act is to run `cleanroom.py` again, from inside the session, and save the output as `out/evidence/cleanroom-auditor.txt`. Then it writes the audit plan and stops at the first hold for your go.

### Other commands

| Command | What it does |
|---|---|
| `python audit.py --prompt C:\audit-cr\work\PROMPT-<YYMMDD>.md` | Restart from a prompt already written, skipping the questions |
| `python audit.py --prompt <same prompt> --role reviewer` | Start the agent reviewer by hand. Add `--harness grok` for Grok |
| `python audit.py --prompt <same prompt> --role reviewer --hold 2` | What the auditor runs itself at holds 2 and 3: a headless, read-only reviewer whose verdict for each run lands in `out/review-hold2-run<K>.md` (Claude Code only) |
| `python audit.py --check` | Build and check the clean room, but don't start the session |
| `python audit.py --root D:\somewhere` | Put the clean room somewhere else. Keep it outside the audited system's folders and outside any git repo |
| `python audit.py --self-test`, `python cleanroom.py --self-test`, `python validate.py --self-test` | Check the tools themselves |

### If it says "Clean room: no"

Each line names what leaked in and where.

| Line | Fix |
|---|---|
| `CLAUDE.md`, `AGENTS.md` or `.claude` in a parent of the working folder, or "project config at the git root" | The clean room sits inside a folder or repo with agent instructions. Use `--root` somewhere outside it |
| A skill, an installed plugin, hooks or MCP servers in `config\` or `home-grok\` | Something was added to the audit's own config. Delete that folder and run again; you log in once more |
| `grok inspect: ...` | Grok still loads something besides its bundled parts. The line names the file; remove it |
| `git global core.hooksPath` | Your git config runs hooks in every repo. Run the audit as a separate OS user, or clear the setting for the run |
| `BASH_ENV`, `NODE_OPTIONS` and the like | `audit.py` removes these for the session. If you see this, `cleanroom.py` ran from your own shell |

Lines that start with `note` don't fail the check. Copy them into the plan as limitations: credentials in the environment, managed settings, files on disk that safe mode doesn't load.

For another harness, such as Codex, or for the strongest clean room (a separate OS user), set it up by hand as `METHOD.md` § Independence says, then run `python cleanroom.py --harness <name>` from the working folder before you start.

### Or fill in the prompt by hand

Fill in `PROMPT.md` and paste it into a fresh session. It asks the same four decisions first, then the plan. Leave any decision blank and the agent asks before it does anything else.

### During and after the run

1. **Give three go decisions.** The agent holds and waits for your explicit go after the audit plan, after ranking the risks, and at the closing meeting. None can be waived, and silence is not a go. Each is sized for you, not for the code: at the second you confirm a short impact sheet (what would actually hurt, and whom); at the closing meeting you get the stop-ship list, the systemic findings and the questions about intent, and may formally accept a risk. The first two are the cheapest points to correct the audit, because the ranking sets how hard everything is tested.
2. **Expect a long run.** A survey pass of about 15 subagents maps the system for breadth; after your second go, a test pass of one subagent per high risk goes deep. A full audit fans out to roughly 15–25 subagents and takes hours on a real system. Heavy jobs are announced before they start.
3. **Read the report and decide.** It is `out/report.html`, with the CSVs and `evidence/` beside it. Findings come back as proposals. Nothing is changed, filed or committed by the audit.
4. **Close the access.** Revoke the scoped token, and delete the clean-room folder when the report is final.

To re-audit later, give the prompt the previous report and CSVs, and choose full or delta (`METHOD.md` § Delta audits). `METHOD.md` § Re-runs seeds the risks and controls from last time, re-tests every control fresh, then diffs: fixed, still open, regressed, new.

## What you get

- **Audit report** (HTML page or document) in ISO 19011 order: cover, plan, conclusions led by systemic findings and stop-ship items, risk register with heat maps, control inventory, findings by risk, the eight failure tests, the nonconformity register with corrective action requests, good practice, ranked proposals, coverage, unresolved points.
- **`risks.csv`**, **`controls.csv`**, **`findings.csv`**, **`harnesses.csv`**: the registers the report is built from, including every agent harness, which rules each one actually loads, and every exception (grant, suppression, bypass) with its acceptance or finding.
- **`soa.csv`** (Part C only): the Statement of Applicability, filled from the evidence.
- **`out/<area>.md`**: the working file for each evidence area, including what it didn't cover.
- **`evidence/`**: every raw output a finding relies on, with a manifest of SHA-256 hashes, commands, tool versions and source commits, so the audit can be reproduced.

`validate.py` checks the CSVs before the report counts as finished: every grade is an allowed value, every nonconformity rests on Verified or Confirmed evidence with a criterion and a full corrective action request, scores add up, every medium or high residual risk has a finding, and every control objective is accounted for. It also checks the report against the CSVs: the report must quote the validator's summary counts verbatim and name every nonconformity and open risk by ID, so the report can't drift from its data. Run `python validate.py --self-test` to check the checker.

## How findings are labelled

- **Grade:** major nonconformity, minor nonconformity, opportunity for improvement, observation, conformity. Two more are kept ungraded: needs validation (the deciding fact couldn't be seen; the finding names it and the check that settles it) and rejected (the verifier disproved it; kept so the next audit doesn't repeat it). Each nonconformity is written as requirement / evidence / statement, with a corrective action request: correction, root cause, corrective action, effectiveness check.
- **Severity:** Critical, High, Medium, Low, set by the impact of the risk. Grade says whether a criterion is met; severity says how bad it is if the risk occurs.
- **Evidence:** Verified (the check ran and its output is pasted), Confirmed (read in code or data, `path:line` cited), Inferred. Only Verified and Confirmed can support a nonconformity.
- **Criterion:** every graded finding names one: ASVS, a CIS Benchmark, SLSA, a control objective, the system's own rule, or an ISO control. The OWASP Top 10 lists, CWE and MITRE ATLAS classify findings; they are not graded against.
- **Three states for every test:** pass, fail, did-not-run. A test that didn't run is never counted as a pass.

## Safety

The audit is read-only by design. It changes nothing, restarts nothing and files nothing; scanners run on local copies; tests are traced before they run so they never reach real hardware, send a message, spend money or load a large model; secrets are reported by type and path, never by value; dynamic testing happens only against staging and only with the owner's go. Auditing someone else's system adds stricter rules: no live host contact, no client names, personal data as counts only.

The auditor treats everything it reads in the audited system as data, never as instructions, so planted text can't steer it. It uses a scoped read-only token made for the audit and revoked afterwards, works within a stated budget, and the report carries a classification, a distribution list and a retention period, because it is a map of the system's weak points.

## Limits

- **Not certification.** This is an internal audit and gap assessment (ISO clause 9.2), with or without Part C. Only an accredited certification body can certify (ISO/IEC 17021-1 with 27006-1 or 42006).
- **Not legal advice.** The regulatory screen flags what needs a lawyer's view.
- **No standard text included.** This repo cites clause and control numbers only. ISO standards are copyrighted; buy the ones you audit against.
- **Versions move.** `STANDARDS.md` records the version of each standard the audit was written against. Check for newer editions, and record the ones you used in the report.
- **The auditor is an agent.** It overclaims. A separate verifier subagent tries to disprove every nonconformity and Critical finding, and the closing meeting puts the draft in front of the owner, but the owner should still spot-check the stop-ship list before acting on it.

## Files

| File | Contents |
|---|---|
| `PROMPT.md` | The prompt to fill in and paste |
| `METHOD.md` | The phases, modes, criteria, evidence, sampling, grading, safety and re-runs. It governs. |
| `CONTROLS.md` | The 33 control objectives, their baseline risks, criteria, and crosswalk to ISO/IEC 27001, 42001 and NIST CSF |
| `EVIDENCE.md` | Sources and snapshots, and the 15 evidence areas: where to look and how |
| `REPORTING.md` | The report's sections and the CSV formats |
| `validate.py` | The gate: checks the CSVs against the method |
| `audit.py` | The guided start: asks the questions, writes the prompt, sets up and checks the clean room, starts the session |
| `cleanroom.py` | The clean-room check each audit session runs first: no system context in its harness config, folders or environment |
| `COMPLIANCE.md` | Part C (optional): ISO criteria, clauses 4–10, Statement of Applicability, regulatory screen, certification readiness |
| `CALIBRATION.md` | The format of your own calibration log, kept outside this repo, and the method changes calibration has made |
| `STANDARDS.md` | Every referenced standard with its version and whether it is a criterion or a classification |
