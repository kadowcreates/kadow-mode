# Part C: the conformity audit (optional)

Part C grades the system, and the organisation that runs it, against ISO management-system requirements. It runs only when the prompt says yes. It runs after Phase 4, reuses the evidence Phases 1–4 collected, and uses the same method and grading (`METHOD.md`) and report (`REPORTING.md`); what it adds is the ISO standards as criteria, clauses 4–10, a Statement of Applicability, a regulatory screen and a certification-readiness list.

**What this is, and isn't.** This is a first-party **internal audit** (ISO/IEC 27001 and ISO/IEC 42001 clause 9.2) and gap assessment. It tells you where you stand and what a certification body would ask for. It is not certification: only an accredited certification body can certify, under ISO/IEC 17021-1 with ISO/IEC 27006-1 (information security) or ISO/IEC 42006 (AI management systems). This repository quotes no standard text; it cites clause and control numbers. Buy the standards you are audited against.

## 1. Audit criteria

State them at the top of the report. Default set:

| Criterion | Use |
|---|---|
| **ISO/IEC 27001:2022** (+ Amd 1:2024) clauses 4–10 and Annex A (93 controls) | Information security management. The baseline for any system that holds credentials, customer data or money. |
| **ISO/IEC 42001:2023** clauses 4–10 and Annex A (38 controls, objectives A.2–A.10) | AI management. Applies whenever agents or models make or carry out decisions. |
| **ISO/IEC 27002:2022** | Implementation guidance for each 27001 Annex A control: what "implemented" looks like. |
| **ISO/IEC 23894:2023** and **ISO/IEC 42005:2025** | AI risk management, and AI system impact assessment (42001 clause 6.1.4). |
| **ISO/IEC 27701** | Privacy information management, if the system processes personal data at scale. |
| **ISO 22301:2019** | Business continuity, if uptime is sold. |
| **ISO/IEC 20000-1:2018** | Service management (incident, problem, change, release), if the system is run as a service. Pairs with ITIL 4 practice names. |

Add or drop criteria in the prompt. Grade every finding as `METHOD.md` § Grading says.

## 2. Management-system clauses 4–10

ISO's Harmonized Structure gives 27001, 42001, 9001, 20000-1 and 22301 the same clauses 4–10. Audit them once and grade against each standard in scope. For each clause, find the documented information or record that shows the requirement is met, and say where it lives.

| Clause | What to look for in an agent platform |
|---|---|
| **4 Context** | Internal and external issues; interested parties and their requirements (customers, model providers, platforms whose terms you depend on, regulators); the scope statement, which names hosts, repos, products and agents in and out of scope; the inventory of AI systems (42001). |
| **5 Leadership** | A security policy and an AI policy; who holds which role and authority, including what each agent is authorised to do and who answers for it. |
| **6 Planning** | A risk assessment method and a current risk register, the system's own (the audit's Phase 1 register is the auditor's, and doesn't count as the organisation's); a risk treatment plan; a **Statement of Applicability**; an AI system impact assessment (42001 6.1.4); measurable objectives with owners and dates; planned changes. |
| **7 Support** | Resources and competence, including the competence of agents (evals); awareness; communication; **documented information control**: versioned, reviewed, findable, retired when superseded. Instruction files, memory and ADRs are documented information, so stale or contradictory ones are a 7.5 finding. |
| **8 Operation** | Operational planning and control; risk assessments and treatment actually carried out on schedule; AI system impact assessments done before deployment; control of externally provided processes (model APIs, SaaS, agent runtimes). |
| **9 Performance evaluation** | What is monitored and measured, by whom, how often, and with what result (SLOs, DORA, gate pass rates, eval scores); internal audit (this audit is one, so is there a programme?); **management review**: is there a record that the owner reviewed the results and decided? |
| **10 Improvement** | Nonconformity and corrective action: correction, root cause, action, **effectiveness check**, record. Reuse CO-25: each recurrence is a corrective action that failed its effectiveness check. Continual improvement shown by trend, not claim. |

A one-person system can conform. The standards scale to the organisation: management review can be a dated note of decisions; a policy can be one page. What can't be skipped is the record.

## 3. Statement of Applicability

Produce `soa.csv`, one row per control:

| Field | Values |
|---|---|
| Standard | 27001 or 42001 |
| Control | number and short title |
| Applicable | yes / no |
| Justification | why it applies, or why it is excluded (every exclusion needs one) |
| Implemented | yes / partial / no |
| Evidence | control and finding IDs, or `path:line`, or command |
| Grade | conformity / ofi / minor / major / observation (`METHOD.md` § Grading) |
| Owner | who answers for it |

Rows: all 93 ISO/IEC 27001:2022 Annex A controls (5.1–5.37 organizational, 6.1–6.8 people, 7.1–7.14 physical, 8.1–8.34 technological) and all 38 ISO/IEC 42001:2023 Annex A controls (A.2–A.10). Physical controls usually point at the host or hosting provider: say which, and whether its assurance (a provider SOC 2 or ISO certificate) was seen.

Fill the rows from the control inventory and findings through the crosswalk in `CONTROLS.md`: an Annex A control takes the worst grade among the objectives mapped to it, with their evidence. Collect new evidence only for organisational controls no objective maps to. Don't re-collect.

## 4. Regulatory and contractual screen

For each item, say whether it applies, why, and what the system does about it. This is a screen for legal review, not legal advice.

- **Privacy:** GDPR / UK GDPR (lawful basis, records of processing, data-subject rights, processors and transfers, DPIA for high-risk processing), CCPA/CPRA, other state laws where users live.
- **AI regulation:** the EU AI Act risk tier of each AI system (prohibited, high-risk, limited-risk transparency, minimal). Check the current application dates before reporting them: the high-risk dates were being moved by the 2026 Digital Omnibus.
- **Messaging and marketing:** TCPA and A2P 10DLC for SMS and calls, CAN-SPAM and CASL for email, platform rules (Meta, Google, marketplaces) for anything automated.
- **Payments:** PCI DSS v4.0.1 scope if card data touches the system, even through an iframe.
- **Customer flow-down:** what customers will require. Business buyers ask for SOC 2 (AICPA Trust Services Criteria) or ISO/IEC 27001. US defense manufacturers flow down CMMC and NIST SP 800-171 for controlled unclassified information. Healthcare flows down HIPAA.
- **Terms of service** of every provider the system depends on: model APIs, agent runtimes, ad platforms, scraping targets.

## 5. Certification readiness

End Part C with the list an external auditor would ask for on day one, and whether each exists:

scope statement · information security policy · AI policy · risk assessment method · risk register · risk treatment plan · Statement of Applicability · AI system impact assessments · asset and AI system inventory · supplier list with assessments · access review records · change records · incident records with root cause · backup and restore test records · business continuity test · internal audit programme and reports · management review records · corrective action log with effectiveness checks · competence and awareness records · document control (versions, owners, review dates).

Give each a status (exists and current / exists but stale / missing) and the effort to close it. That list, ranked, is the certification roadmap.
