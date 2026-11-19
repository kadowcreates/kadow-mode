# Evidence guide

Where to look, and how. The method (`METHOD.md`) decides what is examined and how hard; this file says where the evidence lives in an agent platform and which techniques collect it. The 15 areas are the split for the survey pass: one subagent per area, or two small areas together. The test pass comes back to them per risk (`METHOD.md` § Passes and holds).

An area is not a report section. Each area's working file (`out/<area>.md`) records what it read and what it found, and every finding it raises is filed against a risk and a control (`REPORTING.md` § 2).

## Sources and snapshots

Before any area reads code, establish what you are reading, and give every subagent the same answer:

- **Find the real code.** List every copy: default branch, live branches, deploy directories, backups, scratch copies. The newest full copy wins. Say which one you used and its date. A backup missing the main entry file is a finding, not a source.
- **Default branch is not live.** Check every branch with `git ls-remote`. Live work often sits on a non-default branch, and a reader of `main` sees a stale system.
- **History counts.** Secrets and personal data that were deleted are still in history. A blob-size-limited bare clone of every repo (`--filter=blob:limit=2m`) covers every commit on every branch cheaply.
- **Compare by hash, not by reading.** Drift between copies is cheapest found by comparing blob SHAs from `git/trees?recursive=1`, without downloading content.
- **Mine the system's own records** for readings you can't take directly: agents' command logs, transcripts, ops notes, scheduler history.

## Areas

Each area lists where to look, the techniques that collect the evidence, and the control objectives (`CONTROLS.md`) it mainly feeds. Every area also feeds Phase 1 (effects it finds) and Phase 2 (controls it finds).

| # | Area | Feeds |
|---|---|---|
| 1 | Product code and routes | CO-01, CO-05 |
| 2 | Secrets | CO-08 |
| 3 | Agent runtime | CO-09, CO-10 |
| 4 | Ops, alarms and change health | CO-13–CO-15, CO-18 |
| 5 | Models and delegation | CO-11, CO-22, CO-29, CO-33 |
| 6 | External services | CO-01, CO-02, CO-04, CO-07 |
| 7 | Governance records and accounts | CO-24–CO-28, CO-30, CO-32 |
| 8 | Backups and repo hygiene | CO-16, CO-18 |
| 9 | Tenancy and orchestration | CO-06, CO-07 |
| 10 | Privacy | CO-22, CO-23 |
| 11 | Infrastructure and domains | CO-17, CO-31 |
| 12 | Money paths | CO-03 |
| 13 | Application security and supply chain | CO-19, CO-20, CO-09 |
| 14 | Behaviour and incidents | CO-12, CO-25, CO-32 |
| 15 | Gap closure | all |

### 1. Product code and routes
- Every HTTP and WebSocket route in every service, enumerated by script (`CONTROLS.md` CO-05 test). Keep the script and its output.
- Per service: bind address, user it runs as, restart history.
- Every route or job that executes commands, serves files, refunds, sends or deletes: read it whole.
- Every outbound API client and exec site: these are the effect paths CO-01 counts.

### 2. Secrets
- Filename pass (auth, env, token, key, cookie, credential stores, browser profiles), then a content sweep, across all branches and history.
- Hold content in memory, redact before anything is written, print type and path only. The same applies to `evidence/`.
- Separate live-looking credentials from placeholders, and say how you told them apart.
- Find the job that put them there (sync, backup, mirror). Fixing files without fixing the job re-leaks them.
- Run a scanner (gitleaks or similar) and check what its patterns miss for the providers this system uses.

### 3. Agent runtime
- Runtime version against the registry's current release channels; its config file, and whether the live copy is backed up.
- Per agent: tools, exec permissions, sandboxing, hooks, allowlists, which agents it can message, which inbound channels reach it and what policy decides.
- Session and context size, fallback models, state databases and whether their backups are complete (a backup of only the `-wal` file is not a backup).
- The trifecta map for CO-09 starts here.

### 4. Ops, alarms and change health
- Every alarm, watchdog, dead-man switch, scheduler and gate. For each alarm, trace the delivery path end to end.
- Sinks that close failures without paging; gates that skip silently when their script is missing; security gates forced to exit 0.
- SLIs and SLOs per user journey; alert rules (symptom or cause); runbooks per paging alert; error budget policy.
- DORA measures from git and deploy history: deployment frequency, lead time, change failure rate, time to restore, rework rate.
- CI configuration and whether staging exists.

### 5. Models and delegation
- Every model ID in use, counted per call site; retired or deprecated IDs.
- Router and failover order, timeouts, caching.
- Which calls judge others, and whether the judge is a different model and prompt.
- Cost meters against the provider's bill for the same period.
- Each provider's data-use settings and terms: training on your data, retention, zero-data-retention status, region (CO-22).
- The LLM call inventory for CO-11: role per call.

### 6. External services
- Every daemon, cron, bot and script that acts externally.
- Per service: idempotency, rate and volume caps, opt-out and quiet-hours handling, kill switch, platform terms risk.
- Shared accounts, sessions and keys across clients (CO-07).
- Where a guard claims to block, the bypass test runs against a stub.

### 7. Governance records and accounts
- The sources of Phase 2's control inventory: contributor and process rules, workflow gates, every agent instruction file, coding-agent config and memory, permission rules and allowlists, hooks (and in which host each blocks), server-side gates.
- The harness inventory (`METHOD.md` § 1.1.1): every harness, its context sources, and which rules, memories and hooks each one loads.
- Exceptions in rules and memory: grants, suppressions ("never flag", "expected"), bypass instructions, standing grants; and for each, the owner's dated acceptance or "none".
- Who can write each rule and memory store, and whether a write is reviewed. Facts stated in rules and memory, sampled and checked against their source.
- Always-loaded context size; stale or contradictory "read first" files; handoff and state files that drift from the truth.
- Undispositioned piles: proposals, retros, drafts nobody decided.
- Policies, ADRs, risk register, tickets, incident records, review records: whatever exists, with dates.
- Shadow and observe flags with their owner and date (CO-26); launch scope and component list (CO-27); decision queues and alarm closures (CO-28).
- Every privileged account behind an effect: MFA type, recovery options, shared logins, token scopes and expiry, last access review (CO-30).
- The incident response plan, its contacts and credential-revocation steps, and the date of its last exercise (CO-32).

### 8. Backups and repo hygiene
- Backup jobs, copies, locations and which is offline or immutable; restore test records; stated RPO and RTO.
- What in scope is not backed up at all; silent sync failures.
- Repo inventory: count, classes, size, churn, abandoned repos.
- Shortcut markers, by script per repo: `git grep -nE '(#|//|/[*]) ?(shortcut|ponytail|HACK|noqa|eslint-disable|type: ?ignore)'`. One `exception` row each (`METHOD.md` § Phase 2) with the limit and trigger it names; count the ones with no trigger. Re-runs diff the counts.
- Branch protection and org settings (visibility rights, member permissions, base permission), read as whatever role you have.

### 9. Tenancy and orchestration
- Every route and query that touches tenant data: where the tenant comes from, every fallback to a default tenant (count them), every query outside the isolation function.
- How work is dispatched to agents and handed between them; loop guards; kill switches.
- Client-authored rules: count, cap, conflict check, and whether any judge reads only part of them.

### 10. Privacy
- Personal data in code, transcripts, memory, ledgers, logs, media and any retrieval corpus.
- A **count-only scanner**: match by regex, hash in memory, print counts. Sample large archives on a fixed stride and say what the sample was.
- Retention and deletion paths; which third parties (model providers included) receive what; privacy policy and terms against the code.
- The system of record per entity (CO-23).

### 11. Infrastructure and domains
- Network edge (tunnels, VPNs, exposed ports, TLS), what listens on which interface, egress control.
- Host hardening scored against the matching CIS Benchmark with a read-only assessor (Lynis or CIS-CAT); ssh, sudoers, firewall, MAC, patch level, auto-updates.
- Process supervision and limits, disk growth, capacity at launch, single points of failure, time sync, cron timezone correctness.
- Every sending and serving domain: SPF, DKIM, DMARC policy, registrar lock, DNSSEC, expiry and renewal (CO-31).
- Physical controls point at the host or hosting provider: say which, and whether its assurance (SOC 2 report, ISO certificate) was seen.

### 12. Money paths
- Billing, payments, refunds, ad spend, trading, API spend ceilings.
- Every claimed cap, located in code. Amount calculations, currency and rounding, duplicate protection.
- What breaks at any spend tolerance: wrong amounts, duplicate charges or refunds, missing caps, platform bans.

### 13. Application security and supply chain
- Every HTML sink (`innerHTML`, `insertAdjacentHTML`, server templates using request data), enumerated by script and checked against the escape helpers.
- Every exec site, file path built from input, SQL built from strings, object merge from input.
- Static analysis (Semgrep or CodeQL) over the real code copy, plus the sink and exec inventory where the scanner is blind.
- Agents with tools, walked against OWASP LLM and Agentic Top 10 categories for coverage: injection paths, memory poisoning, tool misuse, inter-agent trust. These classify findings for CO-09 and CO-10.
- Licences: dependency licences from the SBOM, and the licence of every open-weight model in use, against how the system uses them (CO-20).
- Supply chain: ecosystem audit tools and `osv-scanner` against **lockfiles only**, no install, no scripts; SBOM (CycloneDX or SPDX); IaC and container image scans if any exist; OpenSSF Scorecard per repo; SLSA level reached.
- Dynamic testing (DAST, fuzzing) only against staging and only with the owner's go.
- Test suites, sampled for CO-21.

### 14. Behaviour and incidents
- Agents forgetting or hallucinating, false "done" claims, stale memory, eval scores over time. For each, the detector, or "none".
- Incident records: postmortem, root cause, action items, and whether the items closed.
- The tabletop exercise and the timed kill switch (`METHOD.md` § 3.6), run in the test pass.
- History of repeat patches of the same bug, and retros that re-propose the same fix (CO-25).

### 15. Gap closure
Every "Not covered" line from areas 1–14: read it now, or write a read-only collection script for it. Report closed, partial, scripted and not scriptable, with counts. What stays uncovered becomes did-not-run in the coverage table, never pass.

## Working file per area

`out/<area>.md`, five sections:

1. **Coverage:** what was read, with exact counts (files, routes, commits, days of logs). A sample says population, size and how chosen.
2. **Effects and controls found:** rows for `risks.csv` and `controls.csv`.
3. **Defects seen in passing:** each with its evidence, for grading in Phase 4.
4. **Tests run** (test pass only): each with pass, fail or did-not-run, the evidence, and the risk and control IDs.
5. **Not covered:** what wasn't read and why. Area 15 takes these.
