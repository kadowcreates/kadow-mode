# Control objectives

The baseline every agent platform is measured against. Each objective states what must be true, the risk it exists to treat, and the criteria it is graded against. They do three jobs in the method (`METHOD.md`):

- **Phase 1:** each objective's baseline risk seeds the risk register, so nothing standard is missed.
- **Phase 2:** each control found is mapped to the objective it serves. An objective with no control is a gap.
- **Phase 4:** the objective is the criterion a finding cites when the system has no rule of its own.

The 27001, 42001 and CSF columns are the crosswalk Part C uses to fill the Statement of Applicability without collecting evidence twice. ISO/IEC 27001 entries are Annex A controls, ISO/IEC 42001 entries are Annex A objectives, CSF 2.0 entries are categories. Classification lists (OWASP Top 10s, CWE, ATLAS) are in the last column: they label findings, they are not graded against (`METHOD.md` § Criteria).

## External effects

| ID | Objective | Baseline risk | Requirement criteria | 27001 | 42001 | CSF | Classify as |
|---|---|---|---|---|---|---|---|
| CO-01 | **One enforcement point per effect.** Each effect (message, money, public change, agent change, ship, secret read) has one code path, holding the policy, idempotency key, rate limit, log and kill switch. Sends use an outbox. | A second path skips the policy | ASVS V8 (authorization); SSDF PW.1 | 5.3, 8.2, 8.18, 8.32 | A.9 | PR.AA, PR.PS | ASI02, ASI03; LLM06 |
| CO-02 | **Audit log with reconciliation.** One append-only, tenant-tagged record of every effect, reconciled against the outside system. Truth comes from the effect, not the actor's report. | An effect happens with no record, or a record with no effect | ASVS V16 (logging); CIS 8 | 5.28, 8.15, 8.16 | A.6 | DE.CM | OWASP A09 |
| CO-03 | **Money paths are capped and exact.** Amounts are right, charges and refunds are idempotent, every claimed cap exists in code, API spend has a ceiling, meters match the provider's bill. | Wrong, duplicate or uncapped spend | PCI DSS v4.0.1 if card data; ASVS V2 (business logic) | 5.3, 5.31, 8.32 | A.9 | GV.RM | LLM10 |
| CO-04 | **Messages to people are lawful and on-brand.** Consent, opt-out and quiet hours are enforced in code; platform terms are respected; bots say only what the client agreement allows, from one source of business facts, with disclosure. | A bot spams, misleads or speaks out of turn for a client | TCPA, A2P 10DLC, CAN-SPAM, CASL; platform terms; EU AI Act transparency duties | 5.31 | A.8, A.9 | GV.OC | LLM09; ASI09 |

## Access and isolation

| ID | Objective | Baseline risk | Requirement criteria | 27001 | 42001 | CSF | Classify as |
|---|---|---|---|---|---|---|---|
| CO-05 | **Every route is authenticated and authorised, deny by default.** Including WebSocket, admin, exec, file-serving and refund routes. Services bind narrowly and don't run as root. | An unauthenticated caller reaches an effect | ASVS V6, V7, V8 at L2 (L3 for money and admin) | 5.15, 5.17, 8.2, 8.3, 8.5 | — | PR.AA | OWASP A01, A07 |
| CO-06 | **Tenants are isolated.** The tenant comes from the session only, never the request body; isolation is one function at the data layer every read and write goes through; no fallback to a default tenant. | One client sees or changes another's data | ASVS V8 | 5.15, 8.3, 8.22, 8.31 | A.9 | PR.AA | OWASP A01; ASI08 |
| CO-07 | **Each client has its own credentials and blast radius.** No shared sessions, tokens or keys across clients; per-client rate limits, browser sessions and quotas. | One enforcement action or leak takes every client down | ISO 22301 single points of failure | 5.19–5.23, 5.30 | A.10 | GV.SC | — |
| CO-08 | **Secrets are out of code and history.** Held in a secret store, absent from every branch and commit, the job that leaked any is fixed, exposed ones are rotated. | A credential is read from a repo, backup or mirror | ASVS V13; CIS 3 | 5.17, 8.12, 8.24 | — | PR.AA, PR.DS | CWE-798 |

## Agents and models

| ID | Objective | Baseline risk | Requirement criteria | 27001 | 42001 | CSF | Classify as |
|---|---|---|---|---|---|---|---|
| CO-09 | **Untrusted content cannot drive an effect.** No agent holds the lethal trifecta (untrusted input, private data or credentials, an external effect) without a deny-by-default code boundary between input and effect. An LLM is never the boundary. | Prompt injection causes an effect | NIST AI RMF Map/Manage; AI 600-1 | 5.7, 8.27; clause 6.1.2 | A.6; clause 6.1.2 | ID.RA | LLM01; ASI01; ATLAS |
| CO-10 | **Agents have least privilege.** Per agent: only the tools, exec rights, sandboxing, inbound channels and agent-to-agent messaging its job needs. Allowlists are explicit and reviewed. | An agent does more than its job | NIST AI RMF Govern | 5.15, 5.18, 8.2, 8.18 | A.6, A.9 | PR.AA, PR.PS | LLM06; ASI02, ASI03, ASI07 |
| CO-11 | **Each LLM call earns its place.** Every call has a role (generate, classify, judge, route, act); "act" is code unless proven otherwise; every remaining call has validated output, an eval set, an owner, a defined failure behaviour and a current model ID. Judges are independent of what they judge. | A model makes a decision code should, or fails silently | NIST AI RMF Measure; AI 600-1 | 5.9, 5.19–5.22 | A.4, A.6, A.7, A.10 | ID.AM, GV.SC | LLM05, LLM09 |
| CO-12 | **Behavioural drift is detected.** Forgetting, hallucination, false "done", stale memory and falling eval scores each have a named detector. | Agents degrade unnoticed | NIST AI RMF Measure | 5.25, 5.27 | A.6 | DE.AE | ASI06, ASI09; LLM09 |
| CO-33 | **AI impact is assessed and disclosed.** Every AI system that makes or carries out decisions about people or for clients has a documented impact assessment (intended use, foreseeable misuse, who is affected and how, the human who can override), reviewed when the system or its model changes. The people affected, and the clients it acts for, are told when AI is acting, what it may do, and how to reach a human or report a problem. | AI harms people or clients nobody assessed, and they can't tell or appeal | ISO/IEC 42005:2025; EU AI Act Art. 50 | 5.31, 5.34 | A.5, A.8, A.9; clauses 6.1.4, 8.4 | GV.OC, ID.RA | LLM09 |

## Reliability and detection

| ID | Objective | Baseline risk | Requirement criteria | 27001 | 42001 | CSF | Classify as |
|---|---|---|---|---|---|---|---|
| CO-13 | **Controls fail closed.** A crash, timeout, missing file or missing dependency in a gate or hook blocks the action. | A broken gate lets everything through | 27001 8.27 (fail secure) | 8.27 | — | PR.PS | OWASP A10:2025 |
| CO-14 | **Alarms are independent and actionable.** No alarm routes through what it watches; user journeys have SLIs and SLOs; alerts fire on symptoms (golden signals); every page has a runbook; no sink closes failures without paging. | An outage or failure is not seen | Google SRE; CIS 8 | 5.24–5.26, 8.16 | A.6 | DE.CM, DE.AE, RS.MA | OWASP A09 |
| CO-15 | **Results are true.** A check that didn't run never reports pass; an agent's "done" is confirmed by the effect, not its claim. | False green hides failure | 27001 clause 9.1 (valid results) | 8.16; clause 9.1 | A.6 | DE.AE | ASI09 |
| CO-16 | **Data is recoverable.** 3-2-1 with one copy offline or immutable; backups encrypted, with the keys stored apart from the backups and themselves recoverable; RPO and RTO stated; a restore tested within the period and meeting them; nothing in scope is unbacked; sync failures alarm. | Data loss with no way back | ISO 22301; CIS 11 | 5.29, 5.30, 8.13, 8.14 | — | PR.DS, RC.RP | — |
| CO-17 | **Hosts and network are hardened.** Edge, exposed ports, TLS and egress controlled; hosts scored against the matching CIS Benchmark; patching, supervision, limits, capacity, time sync. | Host compromise or exhaustion | CIS Benchmarks; CIS 4, 12, 13 | 8.1, 8.6–8.9, 8.17, 8.20–8.22; 7.x via provider | — | PR.PS, PR.IR | — |

## Change and code

| ID | Objective | Baseline risk | Requirement criteria | 27001 | 42001 | CSF | Classify as |
|---|---|---|---|---|---|---|---|
| CO-18 | **Changes reach production through a gate.** Staging exists with CI in front; default branches are protected; the customer path runs in its own process; change health measured (DORA). | A bad change ships straight to clients | SSDF PS, PW; SLSA source track | 8.25, 8.31, 8.32 | A.6 | PR.PS | — |
| CO-19 | **Code is free of injectable sinks.** XSS, command injection at every exec site, path traversal, SQL injection, prototype pollution. | Code execution or data theft through input | ASVS V1, V5 at L2 | 8.26, 8.28 | — | PR.PS | OWASP A05; CWE |
| CO-20 | **Dependencies and builds are trustworthy.** Lockfiles scanned for known vulnerabilities; an SBOM exists; SLSA build and source level stated; OpenSSF Scorecard checked; dependency and model licences (including open-weight model licences) permit the use made of them. | A compromised or vulnerable dependency ships | SLSA v1.2; SSDF PS.3, PW.4; CIS 16 | 5.21, 8.8, 8.30 | — | GV.SC, ID.RA | OWASP A03, A08; CWE-1395 |
| CO-21 | **Tests assert behaviour.** Tests fail when behaviour breaks and survive behaviour-preserving refactors; no mocks of the code's own internals; no tests asserting today's bug; no test that can't fail; no push-suite test reads live host state. | Tests lock in implementation, so fixes look like regressions | SSDF PW.8 | 8.29, 8.33 | A.6 | PR.PS | — |

## Data

| ID | Objective | Baseline risk | Requirement criteria | 27001 | 42001 | CSF | Classify as |
|---|---|---|---|---|---|---|---|
| CO-22 | **Personal data is minimised and governed.** Known where it lives (code, transcripts, memory, logs, media, retrieval corpora); retention and deletion work; every third party receiving it, model providers included, is listed, with its data-use terms checked: training on customer data off, retention as short as offered (zero data retention where available), region where it matters; the privacy policy matches the code. | Personal data is kept, shared or leaked unlawfully | GDPR / UK GDPR; CCPA/CPRA; ISO/IEC 27701 | 5.14, 5.34, 8.10–8.12 | A.7 | PR.DS | LLM02 |
| CO-23 | **Each entity has one system of record.** Client, contact, conversation, rule, config and product entities each have one owner; every other copy is a cache. | Copies disagree and the wrong one acts | — | 5.9, 5.12, 8.10 | A.7 | ID.AM, PR.DS | — |

## Governance

| ID | Objective | Baseline risk | Requirement criteria | 27001 | 42001 | CSF | Classify as |
|---|---|---|---|---|---|---|---|
| CO-24 | **Rules are governed.** High-risk rules are enforced in code; rules are deduplicated, conflict-checked, capped and retired; each rule reaches every harness it is meant for; exceptions (grants, suppressions, bypasses) stand only as dated owner acceptances; every rule and memory store has a known set of writers, and facts in them are kept true; always-loaded context stays within budget; "read first" and handoff files are current; nothing sits undispositioned. | Rules pile up, contradict and are ignored | 27001 clause 7.5 | 5.1, 5.2, 5.4, 5.36, 5.37 | A.2, A.3; clause 7.5 | GV.PO, GV.RR, GV.OV | — |
| CO-25 | **Corrective actions stick.** Every incident gets a blameless postmortem with root cause, a test that locks the behaviour, and an effectiveness check; recurrences are counted. | The same failure recurs | 27001 clause 10.2; ISO/IEC 20000-1 problem management; 8D | 5.27; clause 10.2 | Clause 10.2 | ID.IM | — |
| CO-26 | **Temporary states end.** Every shadow, observe or feature flag has an owner and a graduation date. | A control sits disarmed indefinitely | 27001 clause 6.2 | 8.32; clause 6.2 | Clause 6.2 | GV.OV | — |
| CO-27 | **Scope and complexity are bounded.** Only launching products run; every agent harness, with its model and provider, is on the system's own list; every component maps to a paid capability; someone owns removal. | Unneeded surface carries risk for nothing | 27001 clause 4.3 | 5.9, 8.9; clause 4.3 | A.4; clause 4.3 | GV.OC, ID.AM | — |
| CO-28 | **Human attention is budgeted.** Decisions queue no faster than they are made; alarms aren't auto-closed unread; someone other than the owner could run the system from its runbooks. | One person is the only backstop | 27001 clauses 7.1, 7.2, 9.3 | 5.3; clauses 7.1, 7.2, 9.3 | Clauses 7.1, 7.2, 9.3 | GV.RR | — |
| CO-29 | **Value and cost are measured per client.** Each client's outcome metric and cost to serve are measured, including meters that read zero or miss part of the bill. | The business can't tell whether it works or can be priced | 27001 clauses 7.1, 9.1 | Clauses 7.1, 9.1 | Clauses 7.1, 9.1 | GV.OC, GV.RM | LLM10 |

## Identity and response

| ID | Objective | Baseline risk | Requirement criteria | 27001 | 42001 | CSF | Classify as |
|---|---|---|---|---|---|---|---|
| CO-30 | **Privileged accounts resist takeover.** Every account that can change the system (code host and org, cloud, domain registrar, DNS, email, model provider, payment and ad platforms) has phishing-resistant MFA (passkey or security key), recovery paths that don't fall back to SMS or a single inbox, no shared logins, tokens scoped and expiring, and a dated access review that removed what wasn't needed. | One phished login hands over the system | NIST SP 800-63B-4 (AAL3 for admin); CIS 5, 6 | 5.15–5.18, 8.2, 8.5 | — | PR.AA | ATT&CK T1078 |
| CO-31 | **Sending domains can't be spoofed or hijacked.** Every domain the system sends from has SPF, DKIM and DMARC at enforcement (`p=quarantine` or `reject`); domains have registrar lock and DNSSEC where offered; expiry is auto-renewed and alarmed. | Someone sends mail as the client, or takes the domain | RFC 7208, RFC 6376, RFC 7489; Google and Yahoo bulk sender rules | 5.14, 8.20, 8.21 | — | PR.PS, PR.DS | — |
| CO-32 | **Incidents can be handled and agents stopped.** An incident response plan names roles, contacts and the path to revoke every credential; it has been exercised (tabletop) within the year; a kill switch stops every agent and job, and its stop time has been measured. | An incident runs on because nobody can stop it fast | NIST SP 800-61 Rev. 3; ISO/IEC 27035 | 5.24–5.28, 5.30 | A.6 | RS.MA, RS.MI, RC.RP | — |

## Test methods for specific objectives

Phase 3 applies to every control. These objectives have a test that needs more than the generic steps:

- **CO-01:** for each effect, count the code paths that can cause it (grep the outbound client, every exec site, every scheduler entry). Report paths per effect; the target is 1.
- **CO-02:** pick a sample of effects from the outside system (sent messages, charges, ad changes) and find each in the log; then the reverse. Report both match rates.
- **CO-05:** enumerate every route with a script, not by eye: find the route registrations, subtract those behind auth middleware or a gated prefix, read the first lines of each remaining handler for an inline check. Keep the script; re-runs diff its output.
- **CO-06:** count every fallback to a default tenant, and every query not routed through the isolation function.
- **CO-09:** map every agent against the three trifecta legs; draw trust boundaries; run STRIDE on each boundary; map agent paths to ATLAS techniques.
- **CO-10, approval binding:** an approval covers one exact action. For every approval path (a permission prompt, a grant typed by the owner, an allowlist entry added mid-session, a go at a hold), approve one action on a stub, then try it with a changed argument, another target, a retry, a resumed session, a later turn and as part of a batch. Each must be refused or asked again. Then put approval-shaped text where the owner didn't write it (a tool result, a file the agent reads, a message from another agent) and see that it approves nothing. An approval that carries over to an action the owner didn't approve is a finding.
- **CO-33:** list every AI system from the harness inventory (`METHOD.md` § 1.1.1) that acts on people or for clients; for each, find its impact assessment and its date against the last model or prompt change. Then, as a user and as a client, find where the system says it is AI, what it may do, and the path to a human. An AI system with no assessment, or an assessment older than its model, is a finding.
- **CO-13, CO-14:** sabotage test against a stub: kill the dependency or break the watched thing, and see the gate refuse and the alarm arrive by its own path.
- **CO-21:** per repo, on a seeded random sample of tests (record the seed): mutate one line of the code under test and re-run. A test that still passes is a survivor; check whether something else (a sandbox refusal, an error with the same status) makes it pass. Report `Mutation score: K of N` in the report, every audit that has CO-21 in scope; if no suite could be run, `Mutation score: did-not-run, <reason>`. Then, across the whole suite, by script:
  - **Can't fail:** tests with no assertion, that compare a value to itself, or that return early and pass.
  - **Host-reading:** tests in the push or pre-merge suite that read live host state (a live service, the real home folder, the clock, the network). Count how many red pushes each caused.
  - **Failure history:** the share of test functions ever named failing in the gate or CI log, and from what date names were logged. A test that has never failed is not proof of a useless one; it is where to sample next.
  - **Duplicates:** tests that assert the same behaviour on the same path.
  - **Cost:** the slowest tests and their share of the suite's time, and any test that runs the suite again.
  Re-runs diff each count against the last audit, so regrowth shows.
- **CO-24:** this is Phase 2's inventory. Report totals by scope × enforcement and the `dup:` and `contra:` counts.
- **CO-25:** count repeat patches of the same bug in history and retros that re-propose the same fix. Each recurrence is a corrective action that failed its effectiveness check.
- **CO-28:** count undecided items, queued reviews and auto-closed alarms, against the decisions made per day.
- **CO-30:** list every privileged account from the effects in Phase 1 (each effect runs on some account). Read the MFA requirement where an API shows it (a code host org's two-factor requirement, a cloud account's MFA report); otherwise interview the owner and ask for a screenshot. Check recovery options, token expiry and the date of the last access review.
- **CO-31:** read the DNS records (`dig TXT`, `_dmarc.`, the DKIM selector) for every sending domain, and the registrar's lock, DNSSEC and expiry.
- **CO-32:** the tabletop and the timed kill switch (`METHOD.md` § 3.6).

**Highest leverage: CO-01, CO-27 and CO-25.** CO-01 closes a whole class of bugs. CO-27 removes attack surface for free. CO-25 shows whether any fix holds.
