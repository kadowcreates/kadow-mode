"""Check an audit's CSVs against METHOD.md, and its report against the CSVs (REPORTING.md § 3).

    python validate.py <output folder>    exit 0 clean, 1 with every problem listed
    python validate.py --summary <folder> print the summary lines the report must quote
    python validate.py --self-test
"""
import hashlib
import html
import csv
import re
import subprocess
import sys
from datetime import datetime, timezone
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

RISK_ENUMS = {
    "effect": {"message", "money", "public", "agent", "ship", "disclose", "outage"},
    "source": {"attacker", "content", "agent", "operator", "supplier", "environment"},
    "depth": {"full", "sample", "design"},
    "residual_action_priority": {"high", "medium", "low"},
}
CONTROL_ENUMS = {
    "scope": {"system", "client", "agent"},
    "type": {"preventive", "detective", "corrective", "exception"},
    "enforcement": {"blocking", "advisory", "llm", "prose"},
    "design": {"effective", "deficient", "not-tested"},
    "operation": {"effective", "deficient", "not-tested", "did-not-run"},
    "refused_at_consumer": {"yes", "no"},
}
HARNESS_ENUMS = {"on_system_list": {"yes", "no"}}
FINDING_ENUMS = {
    "grade": {"major", "minor", "ofi", "observation", "conformity", "needs-validation", "rejected"},
    "severity": {"critical", "high", "medium", "low", ""},
    "evidence": {"verified", "confirmed", "inferred"},
    "owners_call": {"yes", "no"},
    "verifier": {"upheld", "overturned", "not-run"},
}
NC = {"major", "minor"}
UNGRADED = {"needs-validation", "rejected"}  # no severity: the fact is unseen, or the claim was disproved
CAR = ("requirement", "statement", "correction", "root_cause", "corrective_action", "effectiveness_check")
DATE = re.compile(r"\d{4}-\d\d-\d\d$")
GAPS = re.compile(r"Gaps: (\d+) named, (\d+) tested, (\d+) did-not-run, (\d+) out of scope")
SEVERITY_BY_IMPACT = {5: "critical", 4: "high", 3: "medium", 2: "low", 1: "low"}


def objectives():
    return set(re.findall(r"^\| (CO-\d\d) \|", (HERE / "CONTROLS.md").read_text(encoding="utf-8"), re.M))


def method_commit():
    """The commit this method folder came from: git when it sits in a checkout, else the VERSION
    file audit.py writes beside the copy it makes in the working folder."""
    if (HERE / "VERSION").is_file():
        return (HERE / "VERSION").read_text(encoding="utf-8").strip()
    try:
        out = subprocess.run(["git", "-C", str(HERE), "rev-parse", "--short=12", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        dirty = subprocess.run(["git", "-C", str(HERE), "status", "--porcelain", "--untracked-files=no", "--", "."],
                               capture_output=True, text=True, timeout=10).stdout.strip()
        return out.stdout.strip() + ("-modified" if dirty else "") if out.returncode == 0 else "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def ids(cell):
    return [x.strip() for x in (cell or "").split(";") if x.strip()]


def depth_for(score):
    return "full" if score >= 15 else "sample" if score >= 8 else "design"


def action_priority(s, o, d):
    """METHOD.md § 1.5.1: severity first, then occurrence, then detection."""
    if s >= 4 and o >= 4 or (s == 5 and d == 5):
        return "high"
    if s >= 4 or (s == 3 and (o >= 3 or d >= 4)):
        return "medium"
    return "low"


def needs_finding(r):
    res = r.get("residual_score", "")
    return (res.isdigit() and int(res) >= 8) or r.get("residual_action_priority") == "high"


def read(folder, name, errors):
    path = Path(folder) / name
    if not path.exists():
        errors.append(f"{name}: missing")
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def check_enums(name, row_id, row, enums, errors):
    for field, allowed in enums.items():
        if row.get(field, "") not in allowed:
            errors.append(f"{name} {row_id}: {field}={row.get(field, '')!r} not in {sorted(allowed)}")


def check_unique(name, rows, key, errors):
    seen = set()
    for r in rows:
        if r.get(key) in seen:
            errors.append(f"{name}: duplicate {key} {r.get(key)}")
        seen.add(r.get(key))


def as_int(name, row_id, row, field, errors):
    try:
        v = int(row.get(field, ""))
    except ValueError:
        errors.append(f"{name} {row_id}: {field}={row.get(field, '')!r} is not a number")
        return None
    if field != "inherent_score" and field != "residual_score" and not 1 <= v <= 5:
        errors.append(f"{name} {row_id}: {field}={v} not in 1-5")
    return v


def validate(folder):
    errors = []
    risks = read(folder, "risks.csv", errors)
    controls = read(folder, "controls.csv", errors)
    findings = read(folder, "findings.csv", errors)
    harnesses = read(folder, "harnesses.csv", errors)
    objs = objectives()
    check_unique("risks.csv", risks, "risk_id", errors)
    check_unique("controls.csv", controls, "control_id", errors)
    check_unique("findings.csv", findings, "finding_id", errors)
    check_unique("harnesses.csv", harnesses, "harness_id", errors)
    harness_ids = {h.get("harness_id") for h in harnesses}
    if not harnesses and (Path(folder) / "harnesses.csv").exists():
        errors.append("harnesses.csv: no harness listed (METHOD.md § 1.1.1)")
    for h in harnesses:
        check_enums("harnesses.csv", h.get("harness_id"), h, HARNESS_ENUMS, errors)
        if not h.get("context_sources"):
            errors.append(f"harnesses.csv {h.get('harness_id')}: context_sources is empty")
    if any(h.get("on_system_list") == "no" for h in harnesses) and not any(
            f.get("objective") == "CO-27" and f.get("grade") not in ("observation", "conformity", "rejected")
            for f in findings):
        errors.append("harnesses.csv: a harness is missing from the system's own list, but no finding cites CO-27")
    risk_by_id = {r["risk_id"]: r for r in risks}
    control_ids = {c["control_id"] for c in controls}
    live = [f for f in findings if f.get("grade") != "rejected"]  # a disproved claim covers nothing

    for r in risks:
        rid = r.get("risk_id")
        check_enums("risks.csv", rid, r, RISK_ENUMS, errors)
        lik, imp, inh = (as_int("risks.csv", rid, r, f, errors) for f in ("likelihood", "impact", "inherent_score"))
        res_lik, res = (as_int("risks.csv", rid, r, f, errors) for f in ("residual_likelihood", "residual_score"))
        res_det = as_int("risks.csv", rid, r, "residual_detection", errors)
        as_int("risks.csv", rid, r, "impact_proposed", errors)
        if not r.get("impact_source"):
            errors.append(f"risks.csv {rid}: impact_source is empty (owner, or a record the agent reviewer cited)")
        elif r["impact_source"] == "unconfirmed":
            errors.append(f"risks.csv {rid}: impact is unconfirmed; the owner signs the impact sheet at hold 2 "
                          "(METHOD.md § Passes and holds)")
        if None not in (lik, imp, inh) and inh != lik * imp:
            errors.append(f"risks.csv {rid}: inherent_score {inh} != {lik}x{imp}")
        if None not in (imp, res_lik, res_det):
            want = action_priority(imp, res_lik, res_det)
            if r.get("residual_action_priority") != want:
                errors.append(f"risks.csv {rid}: residual_action_priority {r.get('residual_action_priority')!r} "
                              f"should be {want!r} for S{imp} O{res_lik} D{res_det}")
        if inh is not None and r.get("depth") != depth_for(inh):
            errors.append(f"risks.csv {rid}: depth {r.get('depth')!r} should be {depth_for(inh)!r} for score {inh}")
        if None not in (res_lik, imp, res) and res != res_lik * imp:
            errors.append(f"risks.csv {rid}: residual_score {res} != {res_lik}x{imp}")
        for c in ids(r.get("control_ids")):
            if c not in control_ids:
                errors.append(f"risks.csv {rid}: control {c} not in controls.csv")
        by, until = r.get("accepted_by", ""), r.get("accepted_until", "")
        if bool(by) != bool(until) or (until and not DATE.match(until)):
            errors.append(f"risks.csv {rid}: acceptance needs both accepted_by and accepted_until (YYYY-MM-DD)")

    for c in controls:
        cid = c.get("control_id")
        check_enums("controls.csv", cid, c, CONTROL_ENUMS, errors)
        if c.get("objective") and c["objective"] not in objs:
            errors.append(f"controls.csv {cid}: objective {c['objective']} not in CONTROLS.md")
        for r in ids(c.get("risk_ids")):
            if r not in risk_by_id:
                errors.append(f"controls.csv {cid}: risk {r} not in risks.csv")
        for field in ("intended_for", "loaded_by"):
            for h in ids(c.get(field)):
                if h != "all" and h not in harness_ids:
                    errors.append(f"controls.csv {cid}: {field} {h} not in harnesses.csv")
        if c.get("type") == "exception" and not ids(c.get("risk_ids")):
            errors.append(f"controls.csv {cid}: an exception names no risk it raises")
        if c.get("operation") == "effective":
            ev = c.get("operation_evidence", "").lower()
            if not ev or ev.startswith("inspection"):
                errors.append(f"controls.csv {cid}: operation effective needs re-performance, sabotage or records evidence")

    for f in findings:
        fid = f.get("finding_id")
        check_enums("findings.csv", fid, f, FINDING_ENUMS, errors)
        grade = f.get("grade")
        if not (f.get("risk_id") or f.get("control_id") or f.get("objective")):
            errors.append(f"findings.csv {fid}: names no risk, control or objective")
        if f.get("risk_id") and f["risk_id"] not in risk_by_id:
            errors.append(f"findings.csv {fid}: risk {f['risk_id']} not in risks.csv")
        if f.get("control_id") and f["control_id"] not in control_ids:
            errors.append(f"findings.csv {fid}: control {f['control_id']} not in controls.csv")
        if f.get("objective") and f["objective"] not in objs:
            errors.append(f"findings.csv {fid}: objective {f['objective']} not in CONTROLS.md")
        if grade not in ("observation", "rejected") and not f.get("criterion"):
            errors.append(f"findings.csv {fid}: {grade} names no criterion")
        if grade in UNGRADED and f.get("severity"):
            errors.append(f"findings.csv {fid}: {grade} carries no severity (METHOD.md § Grading)")
        elif grade not in UNGRADED and not f.get("severity"):
            errors.append(f"findings.csv {fid}: severity is empty")
        if grade in NC | {"ofi"} and not f.get("failure_case"):
            errors.append(f"findings.csv {fid}: {grade} states no failure_case; no case, no finding (METHOD.md § Grading)")
        if grade == "needs-validation":
            for field in ("blocker", "validation_plan"):
                if not f.get(field):
                    errors.append(f"findings.csv {fid}: needs-validation has no {field} (METHOD.md § Grading)")
        if grade == "rejected" and (f.get("verifier") != "overturned" or not f.get("reason")):
            errors.append(f"findings.csv {fid}: rejected needs verifier overturned and the reason (METHOD.md § 3.5)")
        if grade in NC:
            if f.get("evidence") not in ("verified", "confirmed"):
                errors.append(f"findings.csv {fid}: nonconformity on {f.get('evidence')!r} evidence")
            if not f.get("reference"):
                errors.append(f"findings.csv {fid}: nonconformity has no reference")
            for field in CAR:
                if not f.get(field):
                    errors.append(f"findings.csv {fid}: nonconformity missing {field}")
            if not DATE.match(f.get("due", "")):
                errors.append(f"findings.csv {fid}: nonconformity has no due date (YYYY-MM-DD)")
        if (grade in NC or f.get("severity") == "critical") and grade != "conformity" and f.get("verifier") != "upheld":
            errors.append(f"findings.csv {fid}: verifier is {f.get('verifier')!r}; a nonconformity or Critical finding must be upheld")
        if f.get("systemic_id") and not re.match(r"S-\d+$", f["systemic_id"]):
            errors.append(f"findings.csv {fid}: systemic_id {f['systemic_id']!r} is not S-<n>")
        for item in f.get("reference", "").split(";"):
            m = re.match(r"\s*(?:out/)?(evidence/[^:\s]*)(?::([\d,\-]+))?", item)
            if not m:
                continue  # a host:path citation, or a command
            cited = Path(folder) / m.group(1)
            if not cited.is_file():
                errors.append(f"findings.csv {fid}: reference {item.strip()!r} names no file in out/")
            elif m.group(2):
                last = max(int(n) for n in re.findall(r"\d+", m.group(2)))
                lines = len(cited.read_text(encoding="utf-8", errors="replace").splitlines())
                if last > lines:
                    errors.append(f"findings.csv {fid}: reference {m.group(1)}:{m.group(2)} is past the file's {lines} lines")
        risk = risk_by_id.get(f.get("risk_id"))
        if risk and risk.get("impact", "").isdigit() and grade not in UNGRADED:
            want = SEVERITY_BY_IMPACT.get(int(risk["impact"]))
            if want and f.get("severity") != want:
                errors.append(f"findings.csv {fid}: severity {f.get('severity')!r} should be {want!r} (risk impact {risk['impact']})")

    controls_with_findings = {f.get("control_id") for f in live}
    for c in controls:
        cid = c.get("control_id")
        if cid in controls_with_findings:
            continue
        missing = sorted(set(harness_ids if "all" in ids(c.get("intended_for")) else ids(c.get("intended_for")))
                         - set(ids(c.get("loaded_by"))))
        if missing:
            errors.append(f"controls.csv {cid}: meant for {', '.join(missing)}, which don't load it, and no finding is filed against it")
        unaccepted = [r for r in ids(c.get("risk_ids")) if not risk_by_id.get(r, {}).get("accepted_by")]
        if c.get("type") == "exception" and unaccepted:
            errors.append(f"controls.csv {cid}: exception raises {', '.join(unaccepted)} with no recorded acceptance "
                          "and no finding filed against it (METHOD.md § Phase 2)")
    for c in controls:
        for other in re.findall(r"contra:\s*(C-\d+)", c.get("conflicts", "")):
            if not {c.get("control_id"), other} & controls_with_findings:
                errors.append(f"controls.csv {c.get('control_id')}: contradicts {other} but no finding is filed against either")

    risks_with_findings = {f.get("risk_id") for f in live}
    for r in risks:
        if needs_finding(r) and r["risk_id"] not in risks_with_findings:
            errors.append(f"risks.csv {r['risk_id']}: residual score {r.get('residual_score')}, "
                          f"AP {r.get('residual_action_priority')} has no finding")

    report = report_text(folder)
    scope = re.search(r"Audit scope: (full\b|delta\b[\s,;:]*((CO-\d\d[\s,;]*)+))", report or "")
    in_scope = set(re.findall(r"CO-\d\d", scope.group(2))) if scope and scope.group(2) else objs
    if report is not None and not scope:
        errors.append("report does not state 'Audit scope: full' or 'Audit scope: delta, <CO IDs>' (METHOD.md § Delta audits)")
    for o in sorted(in_scope - objs):
        errors.append(f"audit scope names {o}, which is not in CONTROLS.md")
    covered = {c.get("objective") for c in controls if c.get("type") != "exception"} | {f.get("objective") for f in live}
    for o in sorted(in_scope & objs - covered):
        errors.append(f"{o}: no control mapped and no finding cites it")

    manifest = Path(folder) / "evidence" / "manifest.csv"
    cleanroom = []
    listed = {manifest}
    if not manifest.exists():
        errors.append("evidence/manifest.csv: missing")
    else:
        for row in read(manifest.parent, "manifest.csv", errors):
            listed.add(manifest.parent / row.get("file", ""))
            if Path(row.get("file", "")).name.startswith("cleanroom") and (manifest.parent / row["file"]).is_file():
                cleanroom.append((manifest.parent / row["file"]).read_text(encoding="utf-8"))
            path = manifest.parent / row.get("file", "")
            if not row.get("file") or not path.is_file():
                errors.append(f"evidence {row.get('file')!r}: file missing")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != row.get("sha256", "").lower():
                errors.append(f"evidence {row['file']}: sha256 does not match")

    critic = Path(folder) / "coverage-critic.md"
    gaps = GAPS.search(critic.read_text(encoding="utf-8")) if critic.is_file() else None
    if not (Path(folder) / "evidence" / "coverage-critic.txt").is_file():
        errors.append("evidence/coverage-critic.txt: missing; save the coverage critic's output (METHOD.md § 3.7)")
    if not gaps:
        errors.append("coverage-critic.md: missing, or has no 'Gaps: N named, T tested, D did-not-run, O out of scope' line")
    elif int(gaps[1]) != sum(int(g) for g in gaps.groups()[1:]):
        errors.append(f"coverage-critic.md: {gaps[0]!r}; every gap named is tested, did-not-run or out of scope")

    for q in sorted(stray_files(folder, listed)):
        errors.append(f"{q.relative_to(folder).as_posix()}: not an audit output and not in evidence/manifest.csv")

    if report is None:
        errors.append("report.html or report.md: missing")
    else:
        for line in summary(risks, controls, findings):
            if norm(line) not in report:
                errors.append(f"report does not quote: {line}")
        must_name = [f["finding_id"] for f in findings if f.get("grade") in NC | {"ofi", "needs-validation"}]
        must_name += sorted({f["systemic_id"] for f in findings if f.get("systemic_id")})
        must_name += [r["risk_id"] for r in risks if needs_finding(r)]
        must_name += sorted(objs - in_scope)  # a delta names what it left out
        for i in must_name:
            if not re.search(rf"\b{re.escape(i)}\b", report):
                errors.append(f"report does not name {i}")
        if gaps and norm(gaps[0]) not in report:
            errors.append(f"report does not quote: {gaps[0]}")
        mut = re.search(r"Mutation score: (?:(\d+) of (\d+)\b|did-not-run\b[\s,;:.–—-]+(\w+\W+){1,}\w)", report)
        if "CO-21" in in_scope and (not mut or (mut[2] and not 0 < int(mut[2]) >= int(mut[1]))):
            errors.append("CO-21 in scope: report does not state 'Mutation score: K of N' (K <= N) or "
                          "'Mutation score: did-not-run, <reason>' (CONTROLS.md § CO-21)")
        if not re.search(r"Clean room: (yes\b|no\b[\s,;:.–—-]+(\w+\W+){2,}\w)", report):
            errors.append("report does not state 'Clean room: yes', or 'Clean room: no, <what leaked in and why>' "
                          "(METHOD.md § Independence)")
        if "Clean room: yes" in report and (not cleanroom or any("Clean room: yes" not in c for c in cleanroom)):
            errors.append("report says 'Clean room: yes' but evidence/ has no cleanroom.py output saying so for every role")
    return errors


def stray_files(folder, listed):
    """Files under out/ that are neither a top-level CSV, report or note, nor a manifest row."""
    folder, listed = Path(folder), {Path(p).resolve() for p in listed}
    return [q for q in folder.rglob("*") if q.is_file() and q.resolve() not in listed and q.name != "validation.txt"
            and not (q.parent == folder and q.suffix in (".csv", ".html", ".md"))]


def norm(text):
    return " ".join(text.split())


def report_text(folder):
    for name in ("report.html", "report.md"):
        path = Path(folder) / name
        if path.exists():
            return norm(html.unescape(re.sub(r"<[^>]+>", " ", path.read_text(encoding="utf-8"))))
    return None


def summary(risks, controls, findings):
    """The numbers the report quotes verbatim, so its counts can't drift from the CSVs."""
    def count(rows, field, values):
        return " · ".join(f"{v} {sum(r.get(field) == v for r in rows)}" for v in values)
    exceptions = [c for c in controls if c.get("type") == "exception"]
    controls = [c for c in controls if c.get("type") != "exception"]
    blocking = [c for c in controls if c.get("enforcement") == "blocking"]
    grave = [f for f in findings if f.get("grade") == "major" or f.get("severity") == "critical"]
    stop = sorted(f["finding_id"] for f in grave if f.get("owners_call") != "yes")
    owners = sorted(f["finding_id"] for f in grave if f.get("owners_call") == "yes")
    return [
        f"Method: agent-platform-audit {method_commit()}",
        f"Findings by grade: {count(findings, 'grade', ('major', 'minor', 'ofi', 'observation', 'conformity'))}",
        f"Needs validation: {', '.join(sorted(f['finding_id'] for f in findings if f.get('grade') == 'needs-validation')) or 'none'}",
        f"Rejected by the verifier: {', '.join(sorted(f['finding_id'] for f in findings if f.get('grade') == 'rejected')) or 'none'}",
        f"Findings by severity: {count(findings, 'severity', ('critical', 'high', 'medium', 'low'))}",
        f"Stop-ship: {', '.join(stop) or 'none'}",
        f"Owner's call, not stop-ship: {', '.join(owners) or 'none'}",
        f"Risks: {len(risks)}, residual 15+ {sum(r.get('residual_score', '').isdigit() and int(r['residual_score']) >= 15 for r in risks)}"
        f", residual 8-14 {sum(r.get('residual_score', '').isdigit() and 8 <= int(r['residual_score']) < 15 for r in risks)}",
        f"Risks by residual action priority: {count(risks, 'residual_action_priority', ('high', 'medium', 'low'))}",
        f"Impact changed at hold 2: {sum(r.get('impact_proposed') != r.get('impact') for r in risks)} of {len(risks)}"
        f", unconfirmed {sum(r.get('impact_source') == 'unconfirmed' for r in risks)}",
        f"Verifier overturned: {sum(f.get('verifier') == 'overturned' for f in findings)}"
        f" of {sum(f.get('verifier') in ('upheld', 'overturned') for f in findings)}",
        f"Controls by enforcement: {count(controls, 'enforcement', ('blocking', 'advisory', 'llm', 'prose'))}",
        f"Blocking controls seen refusing at the consumer: {sum(c.get('refused_at_consumer') == 'yes' for c in blocking)} of {len(blocking)}",
        f"Exceptions (grants, suppressions, bypasses): {len(exceptions)}",
    ]


def write(folder, name, rows):
    with (Path(folder) / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def self_test():
    risk = dict(risk_id="R-01", statement="s", effect="money", source="agent", likelihood="4", impact="5",
                inherent_score="20", depth="full", control_ids="C-001", residual_likelihood="2", residual_score="10",
                residual_detection="2", impact_proposed="4", impact_source="owner", residual_action_priority="medium",
                accepted_by="", accepted_until="")
    control = dict(control_id="C-001", control="cap", objective="CO-03", risk_ids="R-01", scope="client",
                   type="preventive", enforcement="blocking", stated_at="a:1", enforced_at="b:2", topic="cap",
                   conflicts="", design="effective", operation="effective", operation_evidence="sabotage: log",
                   refused_at_consumer="yes", intended_for="", loaded_by="")
    harness = dict(harness_id="H-01", harness="coding agent", version="1", model="m", provider="p", role="builder",
                   context_sources="~/.agent/RULES.md", on_system_list="yes")
    finding = dict(finding_id="F-001", title="t", risk_id="R-01", control_id="C-001", objective="", grade="minor",
                   severity="critical", evidence="confirmed", reference="b:2", criterion="CO-03",
                   classification="", requirement="r", statement="s", failure_case="fc", correction="c", root_cause="rc",
                   corrective_action="ca", effectiveness_check="e", proposal="p", owners_call="no",
                   systemic_id="S-01", verifier="upheld", due="2026-10-14")
    # one finding per remaining objective, so the coverage rule is satisfied
    others = [dict(finding, finding_id=f"F-{i:03}", risk_id="", control_id="", objective=o, grade="observation",
                   criterion="", severity="low", systemic_id="", verifier="not-run", due="") for i, o in enumerate(sorted(objectives() - {"CO-03"}), 2)]

    gaps = "Gaps: 2 named, 1 tested, 1 did-not-run, 0 out of scope"

    def run(r=risk, c=control, fs=None, report=True, drop=None, tamper=False, extra="", h=harness, room="Clean room: yes",
            stray=None, critic=gaps, critic_raw=True):
        rows = (fs or [finding]) + others
        lines = summary([r], [c], rows)
        body = "<p>" + "</p><p>".join(lines) + f"</p><p>R-01 F-001 S-01</p><p>Clean room: yes</p><p>Audit scope: full</p><p>{gaps}</p><p>Mutation score: 26 of 30</p>"
        with tempfile.TemporaryDirectory() as d:
            ev = Path(d) / "evidence"
            ev.mkdir()
            (ev / "out.txt").write_bytes(b"route list")
            digest = hashlib.sha256(b"tampered" if tamper else b"route list").hexdigest()
            (ev / "cleanroom-auditor.txt").write_text(f"ok    folder\n{room}\n", encoding="utf-8")
            if critic is not None:
                (Path(d) / "coverage-critic.md").write_text(f"| gap | disposition |\n\n{critic}\n", encoding="utf-8")
            if critic_raw:
                (ev / "coverage-critic.txt").write_bytes(b"gaps")
            room_digest = hashlib.sha256((ev / "cleanroom-auditor.txt").read_bytes()).hexdigest()
            write(ev, "manifest.csv", [dict(file="out.txt", sha256=digest, command="enum", tool_version="x 1",
                                             source_commit="abc", captured_at="2026-10-07T00:00:00Z"),
                                        dict(file="cleanroom-auditor.txt", sha256=room_digest, command="cleanroom.py",
                                             tool_version="x 1", source_commit="", captured_at="2026-10-07T00:00:00Z")]
                  + ([dict(file="coverage-critic.txt", sha256=hashlib.sha256(b"gaps").hexdigest(), command="critic",
                           tool_version="x 1", source_commit="", captured_at="2026-10-07T00:00:00Z")] if critic_raw else []))
            if stray:
                (Path(d) / stray).parent.mkdir(parents=True, exist_ok=True)
                (Path(d) / stray).write_bytes(b"x")
            write(d, "risks.csv", [r])
            write(d, "harnesses.csv", [h])
            write(d, "controls.csv", [c])
            write(d, "findings.csv", rows)
            if report:
                (Path(d) / "report.html").write_text((body.replace(drop, "") if drop else body) + extra, encoding="utf-8")
            return validate(d)

    assert run() == [], run()
    # the coverage critic ran, and every gap it named has a disposition the report quotes
    assert any("coverage-critic.md: missing" in e for e in run(critic=None))
    assert any("coverage-critic.txt: missing" in e for e in run(critic_raw=False))
    assert any("every gap named" in e for e in run(critic="Gaps: 3 named, 1 tested, 1 did-not-run, 0 out of scope"))
    assert any("does not quote: Gaps" in e for e in run(critic="Gaps: 1 named, 1 tested, 0 did-not-run, 0 out of scope"))
    # CO-21 in scope reports a mutation score, or says why none ran; a delta without CO-21 owes none
    no_mut = "<p>Mutation score: 26 of 30</p>"
    assert any("Mutation score" in e for e in run(drop=no_mut))
    assert any("Mutation score" in e for e in run(drop=no_mut, extra="<p>Mutation score: 31 of 30</p>"))
    assert any("Mutation score" in e for e in run(drop=no_mut, extra="<p>Mutation score: 0 of 0</p>"))
    assert run(drop=no_mut, extra="<p>Mutation score: did-not-run, no suite in the repos granted</p>") == []
    assert any("nonconformity on 'inferred'" in e for e in run(fs=[dict(finding, evidence="inferred")]))
    assert any("names no criterion" in e for e in run(fs=[dict(finding, criterion="")]))
    assert any("grade='nc'" in e for e in run(fs=[dict(finding, grade="nc")]))
    assert any("missing root_cause" in e for e in run(fs=[dict(finding, root_cause="")]))
    assert any("should be 'critical'" in e for e in run(fs=[dict(finding, severity="low")]))
    assert any("inherent_score 12" in e for e in run(r=dict(risk, inherent_score="12", depth="sample")))
    assert any("depth 'sample'" in e for e in run(r=dict(risk, depth="sample")))
    assert any("residual_action_priority 'low' should be 'medium'" in e for e in run(r=dict(risk, residual_action_priority="low")))
    # low residual score but undetectable Critical harm: AP High still demands a finding
    quiet = dict(risk, residual_likelihood="1", residual_score="5", residual_detection="5", residual_action_priority="high")
    assert run(r=quiet) == []
    assert any("AP high has no finding" in e for e in run(r=quiet, fs=[dict(finding, risk_id="", objective="CO-03")]))
    assert action_priority(5, 1, 1) == "medium" and action_priority(2, 5, 5) == "low" and action_priority(3, 1, 5) == "medium"
    assert action_priority(4, 2, 5) == "medium"  # detection alone no longer lifts impact 4 to High (CALIBRATION.md)
    assert depth_for(16) == "full" and depth_for(8) == "sample" and depth_for(7) == "design"
    assert any("has no finding" in e for e in run(fs=[dict(finding, risk_id="", objective="CO-03")]))
    assert any("needs re-performance" in e for e in run(c=dict(control, operation_evidence="inspection: cron")))
    assert any("CO-03: no control" in e for e in run(c=dict(control, objective=""), fs=[dict(finding, objective="")]))
    assert any("not in controls.csv" in e for e in run(fs=[dict(finding, control_id="C-999")]))
    assert any("report.html or report.md: missing" in e for e in run(report=False))
    assert any("does not quote: Stop-ship" in e for e in run(drop="Stop-ship"))
    assert any("does not name F-001" in e for e in run(drop="F-001"))
    assert any("must be upheld" in e for e in run(fs=[dict(finding, verifier="not-run")]))
    assert any("no due date" in e for e in run(fs=[dict(finding, due="")]))
    assert any("acceptance needs both" in e for e in run(r=dict(risk, accepted_by="owner")))
    assert any("sha256 does not match" in e for e in run(tamper=True))
    assert any("does not name S-01" in e for e in run(drop="S-01"))
    assert any("Clean room" in e for e in run(drop="Clean room: yes"))
    assert any("Clean room" in e for e in run(drop="Clean room: yes", extra="<p>Clean room: no</p>"))
    assert not any("Clean room" in e for e in run(
        drop="Clean room: yes", extra="<p>Clean room: no, the host loaded the owner's memory files</p>"))
    clash = dict(control, control_id="C-002", conflicts="contra:C-001", objective="CO-03", risk_ids="")
    def run2(fs):
        with tempfile.TemporaryDirectory() as d:
            rows = fs + others
            write(d, "risks.csv", [risk])
            write(d, "controls.csv", [control, clash])
            write(d, "findings.csv", rows)
            return validate(d)
    assert not any("contradicts" in e for e in run2([finding]))
    assert any("contradicts C-001" in e for e in run2([dict(finding, control_id="")]))
    assert any("impact_source is empty" in e for e in run(r=dict(risk, impact_source="")))
    assert any("Impact changed at hold 2: 1 of 1, unconfirmed 0" == line for line in summary([risk], [control], [finding]))
    # a rule meant for every harness that one harness never loads
    assert not any("which don't load it" in e for e in run(c=dict(control, intended_for="all", loaded_by="H-01")))
    assert any("meant for H-01" in e for e in run(c=dict(control, intended_for="all"), fs=[dict(finding, control_id="")]))
    assert any("loaded_by H-09 not in harnesses.csv" in e for e in run(c=dict(control, loaded_by="H-09")))
    # an exception stands only as a dated acceptance, or with a finding against it
    grant = dict(control, type="exception")
    assert any("exception raises R-01" in e for e in run(c=grant, fs=[dict(finding, control_id="")]))
    accepted = dict(risk, accepted_by="owner", accepted_until="2026-12-31")
    assert not any("exception" in e for e in run(r=accepted, c=grant, fs=[dict(finding, control_id="")]))
    assert any("CO-03: no control" in e for e in run(c=grant, fs=[dict(finding, control_id="", objective="")]))
    assert any("names no risk" in e for e in run(c=dict(grant, risk_ids="")))
    assert any("no finding cites CO-27" in e for e in run(h=dict(harness, on_system_list="no")))
    # the report's clean-room claim must match cleanroom.py's output
    assert any("no cleanroom.py output" in e for e in run(room="Clean room: no, BASH_ENV is set"))
    # a delta checks coverage only for what it selected, and must name what it left out
    left_out = sorted(objectives() - {"CO-03"})
    delta = "<p>Audit scope: delta, CO-03</p><p>Left out: " + ", ".join(left_out) + "</p>"
    assert run(drop="<p>Audit scope: full</p>", extra=delta) == []
    assert any("does not name CO-01" in e for e in run(drop="<p>Audit scope: full</p>", extra="<p>Audit scope: delta, CO-03</p>"))
    assert any("CO-03: no control" in e for e in run(c=dict(control, objective=""), fs=[dict(finding, objective="")],
                                                      drop="<p>Audit scope: full</p>", extra=delta))
    assert any("Audit scope" in e for e in run(drop="<p>Audit scope: full</p>"))
    assert any("CO-99" in e for e in run(drop="<p>Audit scope: full</p>", extra=delta.replace("CO-03</p>", "CO-03, CO-99</p>", 1)))
    # a file nobody accounts for fails, wherever it lands
    assert any("%SystemDrive%/Caches/x.db: not an audit output" in e for e in run(stray="%SystemDrive%/Caches/x.db"))
    assert any("evidence/unlisted.txt: not an audit output" in e for e in run(stray="evidence/unlisted.txt"))
    assert not any("not an audit output" in e for e in run(stray="notes.md"))
    # an evidence/ citation must name a real file, and lines inside it
    assert not any("reference" in e for e in run(fs=[dict(finding, reference="ws:~/a.py:3; evidence/out.txt:1")]))
    for bad in ("evidence/gone.txt", "evidence/tests/(F-T5-09)", "out/evidence/out.txt:1-9"):
        assert any("findings.csv F-001: reference" in e for e in run(fs=[dict(finding, reference=bad)])), bad
    # owner's-call items are noted apart, never stop-ship
    assert any("F-001: minor states no failure_case" in e for e in run(fs=[dict(finding, failure_case="")]))
    # needs-validation names the unseen fact and its check, carries no severity, and still covers its risk
    nv = dict(finding, grade="needs-validation", severity="", blocker="b", validation_plan="p")
    assert not any("F-001" in e for e in run(fs=[nv])), run(fs=[nv])
    for bad in (dict(nv, blocker=""), dict(nv, severity="critical")):
        assert any("F-001: needs-validation" in e for e in run(fs=[bad]))
    assert "Needs validation: F-001" in summary([risk], [control], [nv])
    # a rejected finding keeps its reason, and covers nothing
    rj = dict(finding, grade="rejected", severity="", verifier="overturned", reason="r")
    assert any("R-01: residual" in e for e in run(fs=[rj]))
    assert any("F-001: rejected needs" in e for e in run(fs=[dict(rj, reason="")]))
    lines = summary([risk], [control], [dict(finding, owners_call="yes")])
    assert "Stop-ship: none" in lines and "Owner's call, not stop-ship: F-001" in lines
    # with an agent reviewer, the owner still signs every impact
    assert any("impact is unconfirmed" in e for e in run(r=dict(risk, impact_source="unconfirmed")))
    print("self-test ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    elif len(sys.argv) == 3 and sys.argv[1] == "--summary":
        errs = []
        print("\n".join(summary(*(read(sys.argv[2], n, errs) for n in ("risks.csv", "controls.csv", "findings.csv")))))
    elif len(sys.argv) == 2:
        problems = validate(sys.argv[1])
        print("\n".join(problems) or "ok")
        if not problems:
            folder = Path(sys.argv[1])
            checked = sorted(q for q in folder.rglob("*") if q.is_file() and q.name != "validation.txt")
            (folder / "validation.txt").write_text(
                f"validate.py exit 0 at {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
                f"Method: agent-platform-audit {method_commit()}\n"
                + "".join(f"{hashlib.sha256(q.read_bytes()).hexdigest()}  {q.relative_to(folder).as_posix()}\n" for q in checked),
                encoding="utf-8")
        sys.exit(1 if problems else 0)
    else:
        sys.exit(__doc__)
