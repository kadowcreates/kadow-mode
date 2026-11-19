# Reporting

Every audit is reported to **ISO 19011:2018** § 6.5 (audit report content), whether or not Part C runs. The method, criteria, evidence labels and grading are in `METHOD.md`; this file is the report and its files.

The report reads the way the audit ran: **risk → control → test → grade**. A reader starting from any risk sees which controls treat it, how each was tested, what the test showed and the grade that follows.

## 1. Report sections

In this order. Save the report as `report.html` (or `report.md`) in the output folder. Its numbers come from the CSVs, never from a hand count: run `python validate.py --summary <output folder>` and quote its lines verbatim in Conclusions and Control inventory.

1. **Cover:** title, system audited, owner, auditor, reviewer type (human or agent), the clean-room line (`METHOD.md` § Independence) with the harness each audit role ran in, the audit scope line (`Audit scope: full`, or `Audit scope: delta, <CO IDs>` with the objectives left out, `METHOD.md` § Delta audits), audit dates, report date and version, **classification, distribution list and retention** (`METHOD.md` § Phase 0: report handling).
2. **Audit plan:** objectives, scope in and out, mode, criteria with versions, the evidence period, sources used, sampling, methods, limitations (what couldn't be seen, whether the auditor is independent), the owner's three go decisions with who and when (`METHOD.md` § Passes and holds), the auditor's access and when it was revoked, and the budget against what was spent.
3. **Conclusions:** the degree to which the criteria are met, in one paragraph; the **systemic findings** first, each with the findings it closes; the top residual risks; counts by grade and by severity; **stop-ship items** (every major nonconformity and every Critical finding that must close before launch), with any owner's-call item among them listed apart, never as stop-ship. If Part C ran: whether the system is certification-ready.
4. **Risk register:** every risk, ranked by residual AP then residual score, with inherent score, residual detection and AP, treating controls and the depth tested; accepted risks marked with who accepted them and until when. A heat map (likelihood × impact) before and after controls.
5. **Control inventory:** totals by scope × enforcement × type; the share that is blocking; how many blocking controls were seen refusing at the consumer; `dup:` and `contra:` counts; the harnesses, and the rules each one is meant to load but doesn't; the exceptions, each with its acceptance or finding; control objectives with no control; controls that treat no risk. The full inventory as a sortable, searchable table.
6. **Findings, by risk:** one section per risk with a finding, highest residual first. Each section: the risk statement and rating; each treating control with its design and operating result and the evidence; the findings, each nonconformity in the three-part write-up (`METHOD.md` § Grading) with its corrective action request.
7. **Generic failure tests:** the `METHOD.md` § 3.3 tests as a table, one row per test: controls that fail it, controls that pass, controls not tested. This is where the eight recurring failure modes are answered.
8. **Part C, if it ran:** clauses 4–10, Statement of Applicability summary, regulatory screen, certification readiness (`COMPLIANCE.md`).
9. **Nonconformity register:** every nonconformity in one table: ID, grade, severity, risk, control, systemic group, criterion, evidence reference, statement, corrective action request, verifier result, due date, proposed owner.
10. **Needs validation:** every needs-validation finding, apart from the graded ones: its risk, the exact fact not seen, and the check that settles it. None is a pass.
11. **Good practice:** conformities worth keeping, with evidence.
12. **Ranked proposals:** each with grade, severity, effort, and the findings it closes. Proposals that close many findings (one enforcement point, deleting unlaunched scope) rank first.
13. **Coverage:** per evidence area: what ran, what didn't, and why, with exact counts. Did-not-run is its own column, never a pass. Then the coverage critic's gaps line, quoted from `coverage-critic.md`, and the gaps left did-not-run or out of scope. With CO-21 in scope: the `Mutation score:` line and the five test-value counts (`CONTROLS.md` § CO-21), each beside the last audit's.
14. **Calibration:** the `--summary` calibration lines, the rejected findings with the verifier's reasons, the grade changes at hold 3 with reasons, and the row added to the owner's calibration log (`CALIBRATION.md` gives its format).
15. **Unresolved points:** where auditor and owner disagree after the closing meeting, or evidence conflicts, and what would settle it.

## 2. Files

The report is built from these files. `validate.py` checks them; a report whose files fail validation is not finished.

Cells holding several IDs separate them with `;`. Enumerated values are lower case, exactly as listed.

### `risks.csv` (Phase 1, updated in Phase 4)

| Field | Values |
|---|---|
| `risk_id` | `R-01`, `R-02`, … |
| `statement` | *If [source] causes [event] through [path], then [consequence] for [party].* |
| `effect` | message / money / public / agent / ship / disclose / outage |
| `source` | attacker / content / agent / operator / supplier / environment |
| `likelihood`, `impact` | 1–5 (`METHOD.md` § 1.5); `impact` as confirmed at hold 2 |
| `impact_proposed` | 1–5, the auditor's rating before hold 2 (`METHOD.md` § Calibration) |
| `impact_source` | owner / record cited by the agent reviewer |
| `inherent_score` | likelihood × impact |
| `depth` | full / sample / design (`METHOD.md` § 1.6, from inherent score) |
| `control_ids` | the controls that treat it, or empty |
| `residual_likelihood` | 1–5, with effective preventive controls in place |
| `residual_score` | residual_likelihood × impact |
| `residual_detection` | 1–5, from detective controls proven effective |
| `residual_action_priority` | high / medium / low, from impact, residual likelihood and residual detection |
| `accepted_by`, `accepted_until` | who accepted the residual risk and until when (`YYYY-MM-DD`), or both empty (`METHOD.md` § 4.6) |

### `controls.csv` (Phase 2, tested in Phase 3)

| Field | Values |
|---|---|
| `control_id` | `C-001`, `C-002`, … |
| `control` | short paraphrase, plus the system's own ID if it has one |
| `objective` | the `CONTROLS.md` ID it serves (`CO-01` …), or empty |
| `risk_ids` | the risks it treats, or empty (a deletion candidate) |
| `scope` | system / client / agent |
| `type` | preventive / detective / corrective / exception (weakens a control or raises a risk, `METHOD.md` § Phase 2) |
| `enforcement` | blocking / advisory / llm / prose |
| `stated_at` | `host:path:line` |
| `enforced_at` | `host:path:line`, or empty |
| `intended_for` | harness IDs the rule, memory or hook is meant for, `all`, or empty when it isn't an agent's context |
| `loaded_by` | harness IDs that actually load or enforce it, or empty |
| `topic` | 1–3 word slug, for joining duplicates |
| `conflicts` | `dup:C-…` / `contra:C-…`, or empty |
| `design` | effective / deficient / not-tested |
| `operation` | effective / deficient / not-tested / did-not-run |
| `operation_evidence` | re-performance / sabotage / records / inspection, with reference |
| `refused_at_consumer` | yes / no: seen refusing at the host, not only a log line |

### `harnesses.csv` (Phase 1)

| Field | Values |
|---|---|
| `harness_id` | `H-01`, `H-02`, … |
| `harness` | what it is, e.g. "coding agent CLI", "self-hosted agent runtime" |
| `version` | the installed version |
| `model`, `provider` | the model it runs and who serves it |
| `role` | what the system uses it for |
| `context_sources` | every instruction file, memory store, hook, skill, MCP server and settings file it loads, as paths |
| `on_system_list` | yes / no: whether the system's own inventory lists it |

### `findings.csv` (Phase 4)

| Field | Values |
|---|---|
| `finding_id` | `F-001`, `F-002`, … |
| `title` | one line |
| `risk_id`, `control_id`, `objective` | what it is filed against; at least one is set |
| `grade` | major / minor / ofi / observation / conformity / needs-validation / rejected |
| `severity` | critical / high / medium / low (from the risk's impact when `risk_id` is set); empty for needs-validation and rejected |
| `evidence` | verified / confirmed / inferred |
| `reference` | `path:line`, or the command run |
| `criterion` | the requirement graded against, with its ID; empty only for observations and rejected |
| `blocker`, `validation_plan` | needs-validation only: the exact fact not seen, and the bounded local test or owner check that settles it |
| `reason` | rejected only: why the verifier overturned it |
| `classification` | CWE, OWASP, ATLAS or STRIDE labels, or empty |
| `requirement`, `statement` | the nonconformity write-up (evidence is `reference`) |
| `failure_case` | major, minor and ofi: one concrete case, this input or situation through this path leads to this harm (`METHOD.md` § Grading) |
| `correction`, `root_cause`, `corrective_action`, `effectiveness_check` | the corrective action request; required for nonconformities |
| `systemic_id` | `S-01` … when it shares a root cause with others (`METHOD.md` § 4.5), or empty |
| `verifier` | upheld / overturned / not-run (`METHOD.md` § 3.5); required upheld for a nonconformity or Critical finding |
| `due` | `YYYY-MM-DD`; required for a nonconformity (`METHOD.md` § 4.4) |
| `proposal` | the fix proposed |
| `owners_call` | yes / no: a deliberate owner choice, noted but never must-fix |

### `coverage-critic.md` (Phase 3)

One row per gap the coverage critic named (`METHOD.md` § 3.7): the gap, the record it cites, and its disposition (tested with reference / did-not-run with reason / out of scope with reason). Last line: `Gaps: N named, T tested, D did-not-run, O out of scope`.

### `evidence/manifest.csv`

| Field | Values |
|---|---|
| `file` | path under `evidence/` |
| `sha256` | of the file as saved |
| `command` | what produced it |
| `tool_version` | tool and version, e.g. `semgrep 1.90.0` |
| `source_commit` | commit SHA of the code it ran against, or empty for live readings |
| `captured_at` | ISO 8601 timestamp |

### `soa.csv` (Part C only)

As in `COMPLIANCE.md` § 3.

### `out/<area>.md`

One working file per evidence area, as in `EVIDENCE.md` § Working file per area.

## 3. What `validate.py` checks

```
python validate.py <output folder>      # exit 0 clean, 1 with every problem listed
python validate.py --summary <folder>   # the lines the report must quote
```

A clean run writes `validation.txt` to the output folder: the date, the method commit, and the SHA-256 of every file it checked. The report links to it; a reader re-runs `validate.py` and compares.

```
python validate.py --self-test
```

- Every enumerated field holds an allowed value; IDs are unique; every cross-reference resolves.
- Scores are the products they claim to be; depth matches the inherent score; the residual action priority matches § 1.5.1.
- Every nonconformity rests on Verified or Confirmed evidence, names a criterion and carries a full corrective action request.
- Every finding except an observation or a rejected one names a criterion.
- Every nonconformity and OFI states its failure case.
- A needs-validation finding names its blocker and validation plan, and a rejected one the verifier's reason; neither carries a severity, and a rejected finding covers no risk, control or objective.
- Every `evidence/` citation in a finding's `reference` names a real file, and its cited lines exist.
- Every file under the output folder is a top-level CSV, note or report, or a row in `evidence/manifest.csv`.
- A finding filed against a risk has the severity that risk's impact sets.
- An operating-effective control has operating evidence that isn't inspection alone.
- Every risk with a residual score of 8 or more, or a residual AP of High, has a finding (`METHOD.md` § 4.2).
- The report states `Audit scope: full` or `Audit scope: delta, <CO IDs>`. Every objective in scope has a control mapped to it or a finding citing it; a delta's report names every objective it left out.
- Every `contra:` conflict has a finding filed against one of its two controls.
- Every harness ID resolves to `harnesses.csv`; a rule meant for a harness that doesn't load it has a finding; a harness missing from the system's own list has a CO-27 finding.
- Every exception names the risks it raises, and each is accepted with a date or has a finding filed against it; exceptions don't count towards objective coverage.
- A report that says "Clean room: yes" has `cleanroom.py` output saying yes, for every role, in `evidence/`.
- Every nonconformity and Critical finding was upheld by the verifier; every nonconformity has a due date; acceptances name both who and until when.
- With CO-21 in scope, the report states `Mutation score: K of N` (K ≤ N, N > 0) or `Mutation score: did-not-run, <reason>`.
- The coverage critic's output is in `evidence/coverage-critic.txt`; `coverage-critic.md` gives every gap a disposition, its counts add up, and the report quotes its gaps line.
- Every file in `evidence/manifest.csv` exists and matches its SHA-256.
- The report exists, quotes every `--summary` line verbatim (tags and spacing ignored), and names every nonconformity, every OFI, every needs-validation finding, every systemic finding and every risk with a residual score of 8 or more by ID.
