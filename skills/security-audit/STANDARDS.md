# Standards: references and crosswalk

Every check in this audit is anchored to a published standard or a widely used industry practice. This file lists them with the version the audit was written against, and says which kind of reference each one is. The crosswalk from each control objective to ISO/IEC 27001, ISO/IEC 42001 and NIST CSF 2.0 lives beside the objective in `CONTROLS.md`; Part C uses it to fill the Statement of Applicability without collecting anything twice.

**Two kinds of reference** (`METHOD.md` § Criteria). *Criteria* state requirements a finding is graded against: the ISO standards, ASVS, CIS Benchmarks, SLSA, SSDF, PCI DSS, the law. *Classifications* name what kind of weakness a finding is: the OWASP Top 10 lists, CWE, MITRE ATLAS, STRIDE. A finding is never graded "nonconforming to the OWASP Top 10"; it is graded against a criterion and labelled with a category.

**Pin versions.** Record in the report the version of each standard you audited against. Versions were checked in October 2026; anything marked *draft* may since have been finalised.

## References

### Management systems and audit

| Standard | Version | Role here |
|---|---|---|
| ISO 19011 | 2018 | How the audit is run: principles (incl. risk-based approach), plan, evidence, sampling, findings, report |
| IIA Global Internal Audit Standards | 2024 (effective Jan 2025) | Working-paper review and supervision: the independent verifier and the closing meeting |
| ISO/IEC 27035-1 | 2023 | Information security incident management |
| ISO/IEC 27005 | 2022 | The risk model: likelihood × impact risk level, inherent and residual, acceptance criteria |
| IEC 60812 | 2018 | FMEA: severity, occurrence, detection; augments the 27005 model with detection |
| AIAG-VDA FMEA Handbook | 1st ed. 2019 | Action priority in place of RPN; the 1–5 AP table here is modelled on it, not copied |
| ISO 31000 | 2018 | Risk management vocabulary for Phase 1: likelihood, impact, inherent and residual risk |
| ISO/IEC 27001 | 2022 + Amd 1:2024 | Information security management: clauses 4–10, Annex A (93 controls) |
| ISO/IEC 27002 | 2022 | Guidance for each 27001 Annex A control |
| ISO/IEC 42001 | 2023 | AI management system: clauses 4–10, Annex A (38 controls) |
| ISO/IEC 23894 | 2023 | AI risk management guidance |
| ISO/IEC 42005 | 2025 | AI system impact assessment |
| ISO/IEC 42006 | 2025 | Requirements for bodies certifying 42001, which says what a certification auditor will check |
| ISO/IEC 27701 | current edition | Privacy information management |
| ISO 22301 | 2019 | Business continuity |
| ISO/IEC 20000-1 | 2018 | Service management (incident, problem, change, release) |
| ISO/IEC 17021-1 / 27006-1 | current | Certification bodies: why this audit is not certification |

### Security and AI frameworks

| Framework | Version | Role here |
|---|---|---|
| NIST Cybersecurity Framework (CSF) | 2.0 (2024) | Outcome taxonomy: Govern, Identify, Protect, Detect, Respond, Recover |
| NIST AI Risk Management Framework | 1.0 (2023) | Govern, Map, Measure, Manage for AI systems |
| NIST AI 600-1 | 2024 | Generative AI profile of the AI RMF |
| NIST IR 8596, Cyber AI Profile | *preliminary draft*, Dec 2025 | CSF 2.0 profile for AI |
| NIST SP 800-53 | Rev. 5, Release 5.2.0 (Aug 2025) | Control catalogue, if a customer asks for a federal mapping |
| NIST SP 800-218 (SSDF) | 1.1; 1.2 is *draft* (Dec 2025) | Secure software development practices |
| NIST SP 800-63B-4 | 2025 | Criterion: authenticator assurance; phishing-resistant MFA for privileged accounts |
| NIST SP 800-61 | Rev. 3 (2025) | Criterion: incident response, aligned to CSF 2.0 |
| NIST SP 800-171 | Rev. 3 | Protecting CUI, which flows down to defense suppliers (CMMC) |
| CIS Critical Security Controls | v8.1 (2024) | Prioritised safeguards |
| CIS Benchmarks | per OS and service | Criterion: host and service hardening |
| AICPA Trust Services Criteria (SOC 2) | 2017, revised points of focus 2022 | What US business buyers ask for; source of design vs operating effectiveness testing (Type I / Type II) |
| PCI DSS | v4.0.1 | If card data is in scope |

### Application, supply chain and AI security

| Reference | Version | Role here |
|---|---|---|
| OWASP Top 10 | 2025 | Classification: web application risk categories (A01–A10) |
| OWASP ASVS | 5.0 (2025) | Criterion: verifiable application security requirements, levels 1–3 |
| OWASP Top 10 for LLM Applications | 2025 | Classification: LLM01–LLM10 |
| OWASP Top 10 for Agentic Applications | 2026 (Dec 2025) | Classification: ASI01–ASI10 |
| MITRE ATLAS | current | Classification: adversarial ML and agent attack techniques |
| MITRE CWE | current | Classification: weakness IDs for every code finding |
| STRIDE | — | Classification: threat categories per trust boundary |
| SLSA | v1.2 (build and source tracks) | Criterion: supply chain integrity levels |
| OpenSSF Scorecard | current | Repo security posture checks |
| CycloneDX / SPDX | current | SBOM formats; SPDX licence identifiers |
| MITRE ATT&CK | current | Classification: adversary techniques outside ML (e.g. valid accounts) |
| SPF, DKIM, DMARC | RFC 7208, RFC 6376, RFC 7489 (check for the DMARCbis successor) | Criterion: sending-domain authentication |

### Operations

| Practice | Source | Role here |
|---|---|---|
| SLIs, SLOs, error budgets, golden signals, postmortems | Google SRE books (sre.google) | Production reliability baseline |
| DORA measures | dora.dev | Change health from git and deploy history |
| ITIL 4 practices | AXELOS / PeopleCert | Names for incident, problem, change, release |
| 3-2-1 backup, RPO/RTO | ISO 22301 terms, CIS Control 11 | Recoverability |
| 8D / 5 whys | Manufacturing quality practice | Root cause and corrective action effectiveness |

## Crosswalk

Control objectives to ISO/IEC 27001, ISO/IEC 42001 and NIST CSF 2.0: `CONTROLS.md`, one row per objective.

The generic failure tests (`METHOD.md` § 3.3), and the standards that require each guard:

| Test | Standards that require the guard |
|---|---|
| Enforced? | 27001 5.36, 5.37; clause 9.1 |
| Fails closed? | 27001 8.27 (secure architecture: fail secure) |
| Independent alarm? | 27001 8.16; CSF DE.CM |
| True green? | Clause 9.1 (valid results); 42001 A.6 |
| Consistent? | Clause 7.5 (control of documented information) |
| Sticks? | Clause 10.2 (effectiveness of corrective action) |
| Graduated? | Clause 6.2 (objectives with owner and date); 8.32 |
| Beyond one human? | 27001 5.3; clauses 7.1, 9.3 |
