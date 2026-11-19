"""Check that this session starts in a clean room (METHOD.md § Independence).

    python cleanroom.py --harness claude [--harness codex] [--harness NAME=CONFIG_FOLDER]
    python cleanroom.py --self-test

Run it from the working folder, first, in every session that takes an audit role. It checks
files on disk, not the agent's account of its own context. It prints each check, then
'Clean room: yes' or 'Clean room: no, <what leaked in>'. Exit 0 on yes, 1 on no.
Save the output as evidence/cleanroom-<role>.txt, with its manifest row.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

# harness: (environment variable that moves its user config folder, default folder under home)
HARNESSES = {
    "claude": ("CLAUDE_CONFIG_DIR", ".claude"),
    "codex": ("CODEX_HOME", ".codex"),
    "gemini": ("", ".gemini"),
    "grok": ("GROK_HOME", ".grok"),
}
# folders inside a config folder that carry context when they hold anything
CONTEXT_DIRS = {"memory", "memories", "skills", "agents", "commands", "plugins", "extensions",
                "prompts", "hooks", "rules", "output-styles"}
# settings keys that load code or tools into the session when they hold anything
CONTEXT_KEYS = {"hooks", "mcpServers", "mcp_servers", "enabledPlugins"}
# instruction files a harness loads from the working folder, its parents or below
FOLDER_FILES = {"CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", "AGENTS.override.md", "GEMINI.md",
                "GROK.md", ".cursorrules", ".windsurfrules", ".mcp.json"}
FOLDER_DIRS = {".claude", ".codex", ".gemini", ".grok", ".cursor"}
INJECTING_ENV = ("BASH_ENV", "ENV", "PROMPT_COMMAND", "NODE_OPTIONS", "PYTHONSTARTUP")
# a parent agent session's identity or messaging channel: a way back into the system's own agents
SESSION_ENV = re.compile(r"^CLAUDECODE$|^CLAUDE_CODE_\w*(TOKEN|SESSION)\w*$|_SESSION_ID$")
# what a harness sets in its own shell, keyed by the variable that marks the check running inside it.
# audit.py strips every SESSION_ENV name before launch, so inside the session these are the session's own.
OWN_SESSION_ENV = {
    "CLAUDECODE": {"CLAUDECODE", "CLAUDE_CODE_CHILD_SESSION", "CLAUDE_CODE_MESSAGING_TOKEN",
                   "CLAUDE_CODE_SESSION_ATTENDED", "CLAUDE_CODE_SESSION_ID"},
    "GROK_AGENT": {"GROK_AGENT", "GROK_SESSION_ID"},
}
CREDENTIAL_ENV = re.compile(r"TOKEN|SECRET|PASSWORD|API_KEY|CREDENTIAL|_PAT$", re.I)
MANAGED = [Path(r"C:\Program Files\ClaudeCode"), Path(r"C:\ProgramData\ClaudeCode"),
           Path("/Library/Application Support/ClaudeCode"), Path("/etc/claude-code")]


def keys_with_content(data):
    """Every CONTEXT_KEYS key, at any depth, whose value isn't empty, and any statusLine that runs a command.
    A statusLine that is only a string (Claude Code caches feature-flag text under that name) runs nothing."""
    if isinstance(data, dict):
        for k, v in data.items():
            if (k in CONTEXT_KEYS and v) or (k == "statusLine" and isinstance(v, dict) and v.get("command")):
                yield k
            yield from keys_with_content(v)
    elif isinstance(data, list):
        for v in data:
            yield from keys_with_content(v)


def settings_leaks(path):
    try:
        text = path.read_text(encoding="utf-8")
        data = tomllib.loads(text) if path.suffix == ".toml" else json.loads(text)
    except (OSError, ValueError) as e:
        return [f"{path} can't be read ({type(e).__name__}), so it can't be cleared"]
    return [f"{path} sets {k}" for k in sorted(set(keys_with_content(data)))]


def synced_names(folder):
    """What a harness syncs from the account it is logged in with: synced/<account>/<name>."""
    return sorted({p.name for bucket in folder.glob("synced/*") if bucket.is_dir()
                   for p in bucket.iterdir() if not p.name.startswith(".")})


def installed_plugins(plugins):
    """Installed plugin names. No list means none installed; a list that can't be read fails closed."""
    path = plugins / "installed_plugins.json"
    if not path.exists():
        return []
    try:
        return sorted(json.loads(path.read_text(encoding="utf-8")).get("plugins") or {})
    except (OSError, ValueError, AttributeError):
        return [f"(unreadable {path.name}, so none can be cleared)"]


def config_leaks(folder, extra=(), notes=None):
    """Context the harness would load from its config folder. Claude Code recreates some folders on every
    launch: plugins/ with marketplace catalogs (loaded only once a plugin is installed) and skills/synced/
    from the logged-in account. Those are the harness's own defaults: noted, not failed."""
    leaks, notes = [], notes if notes is not None else []
    if folder.is_dir():
        leaks += [f"instruction file {p}" for p in sorted(folder.glob("*.md"))]
        for root, dirs, _ in os.walk(folder):
            for d in sorted(dirs):
                path = Path(root) / d
                if d == "plugins":
                    leaks += [f"installed plugin {n} in {path}" for n in installed_plugins(path)]
                elif d == "skills":
                    leaks += [f"skill {p.name} in {path}" for p in sorted(path.iterdir())
                              if p.name != "synced" and not p.name.startswith(".")]
                elif d in CONTEXT_DIRS and any(f.is_file() for f in path.rglob("*")):
                    leaks.append(f"{d} in {path}")
                if d in ("plugins", "skills") and (synced := synced_names(path)):
                    notes.append(f"{d} synced from the logged-in account: {', '.join(synced)}. These come with "
                                 "the account, not the system; any you made yourself on it are context, so "
                                 "run claude --safe-mode to drop them")
            # report the outermost context folder only, and skip git's own sample hooks
            dirs[:] = [d for d in dirs if d not in CONTEXT_DIRS and d != ".git"]
        for p in sorted(list(folder.glob("*.json")) + list(folder.glob("*.toml"))):
            leaks += settings_leaks(p)
    for p in extra:
        if p.is_file():
            leaks += settings_leaks(p)
    return leaks


def folder_leaks(cwd):
    leaks = [f"{p} (parent of the working folder)" for parent in cwd.parents
             for p in sorted(parent.glob("*")) if p.name in FOLDER_FILES]
    # a working folder inside a git repo makes the repo root the project, and its .claude/ etc. load as project config
    root = next((q for q in cwd.parents if (q / ".git").exists()), None)
    if root:
        leaks += [f"{p} (project config at the git root above the working folder)"
                  for p in sorted(root.glob(".*")) if p.name in FOLDER_DIRS]
    for root, dirs, files in os.walk(cwd):
        dirs[:] = [d for d in dirs if d != ".git"]
        leaks += [str(Path(root) / n) for n in sorted(files) if n in FOLDER_FILES]
        leaks += [str(Path(root) / n) for n in sorted(dirs) if n in FOLDER_DIRS]
    return leaks


def git_leaks():
    leaks = []
    for scope in ("--system", "--global"):
        try:
            out = subprocess.run(["git", "config", scope, "--get", "core.hooksPath"],
                                 capture_output=True, text=True, timeout=10).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return []
        if out:
            leaks.append(f"git {scope[2:]} core.hooksPath is {out}")
    return leaks


def grok_loaded(data):
    """What `grok inspect --json` says Grok loads, other than its own built-in and bundled parts. Grok also
    reads ~/.claude and ~/.cursor, and its compat switches don't stop plugins or hooks, so its report is the oracle."""
    found = []
    for key in ("projectInstructions", "skills", "agents", "plugins", "hooks", "mcpServers", "lspServers"):
        for x in data.get(key) or []:
            source = x.get("source") or {}
            if x.get("disabled") or x.get("enabled") is False or source.get("type") in ("builtin", "bundled"):
                continue
            found.append(" ".join(filter(None, (key, x.get("name") or x.get("event"), x.get("path") or source.get("path")))))
    return found


def grok_leaks(cwd, env):
    try:
        out = subprocess.run([shutil.which("grok", path=env.get("PATH")) or "grok", "inspect", "--json"], cwd=cwd,
                             env=env, capture_output=True, text=True, encoding="utf-8", timeout=120)
        return grok_loaded(json.loads(out.stdout))
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        return [f"grok inspect --json didn't run ({type(e).__name__}), so what Grok loads can't be cleared"]


def check(harnesses, home, cwd, env, run_tools=True):
    """Return (printed lines, leaks). An empty leaks list is a clean room."""
    lines, leaks = [], []

    def record(label, found):
        leaks.extend(f"{label}: {x}" for x in found)
        lines.extend(f"FAIL  {label}: {x}" for x in found)
        if not found:
            lines.append(f"ok    {label}")

    claude_folder = None
    for spec in harnesses:
        name, _, given = spec.partition("=")
        var, default = HARNESSES.get(name, ("", ""))
        if not given and not default:
            raise SystemExit(f"unknown harness {name!r}: pass it as {name}=CONFIG_FOLDER")
        folder = Path(given or env.get(var) or home / default)
        # Claude Code keeps MCP servers in ~/.claude.json unless its config folder was moved
        extra = [home / ".claude.json"] if name == "claude" and not given and not env.get(var) else []
        notes = []
        if name == "claude":
            claude_folder = folder
        found = config_leaks(folder, extra, notes)
        # claude --safe-mode keeps the login but loads none of the config folder's skills, plugins, hooks, MCP or CLAUDE.md
        if name == "claude" and env.get("CLAUDE_CODE_SAFE_MODE") == "1":
            lines.extend(f"note  on disk, not loaded (claude --safe-mode): {x}" for x in found + notes)
            lines.append(f"ok    {name} config {folder}: claude --safe-mode")
            continue
        record(f"{name} config {folder}", found)
        lines.extend(f"note  {n}" for n in notes)
        if name == "grok" and run_tools:
            record("grok inspect", grok_leaks(cwd, env))
    record(f"folder {cwd}", folder_leaks(cwd))
    # A harness sets these in its own shell. Grok's count as the session's own when GROK_AGENT marks the check
    # running inside it. Claude Code's count only when the session ID's transcript is in the config folder being
    # checked, because every Claude session, a parent too, sets CLAUDECODE.
    own_id = env.get("CLAUDE_CODE_SESSION_ID", "")
    proven = {"CLAUDECODE": bool(own_id and claude_folder and any((claude_folder / "projects").glob(f"*/{own_id}.jsonl"))),
              "GROK_AGENT": bool(env.get("GROK_AGENT"))}
    own = {n for marker, names in OWN_SESSION_ENV.items() if proven[marker] for n in names}
    record("environment", [f"{v} is set" for v in INJECTING_ENV if env.get(v)]
           + [f"{v} is set (a parent agent session)" for v in sorted(env) if SESSION_ENV.search(v) and v not in own])
    if own & set(env):
        lines.append(f"note  this session's own harness set {', '.join(sorted(own & set(env)))}; its messaging "
                     "channel can reach other local agent sessions, so the auditor never uses it")
    if run_tools:
        record("git", git_leaks())
    for name in sorted(v for v in env if CREDENTIAL_ENV.search(v) and not SESSION_ENV.search(v)):
        lines.append(f"note  credential in the environment: {name}; confirm it is the scoped audit credential")
    for d in MANAGED:
        if d.is_dir() and any(d.iterdir()):
            lines.append(f"note  managed settings in {d} load regardless of the config folder; record them as a limitation")
    lines.append("note  not checked here: the shell profile (a separate OS user clears it) and any hosted assistant's memory")
    return lines, leaks


def verdict(leaks):
    return "Clean room: yes" if not leaks else f"Clean room: no, {'; '.join(leaks)}"


def self_test():
    with tempfile.TemporaryDirectory() as t:
        home, work = Path(t) / "home", Path(t) / "outer" / "work"
        (home / ".claude" / "projects" / "p" / "memory").mkdir(parents=True)
        work.mkdir(parents=True)
        # what Claude Code recreates on a fresh launch: catalogs, account-synced skills, a feature-flag string
        own = home / ".claude"
        (own / "plugins" / "marketplaces" / "official" / "plugins" / "x" / "hooks").mkdir(parents=True)
        (own / "plugins" / "marketplaces" / "official" / "plugins" / "x" / "hooks" / "h.json").write_text("{}", encoding="utf-8")
        (own / "plugins" / "installed_plugins.json").write_text('{"version": 2, "plugins": {}}', encoding="utf-8")
        (own / "skills" / "synced" / "acct" / "docx").mkdir(parents=True)
        (own / "skills" / "synced" / "acct" / "docx" / "SKILL.md").write_text("s", encoding="utf-8")
        (home / ".claude.json").write_text('{"flags": {"f": {"statusLine": "Lower priority"}}}', encoding="utf-8")
        lines, leaks = check(["claude"], home, work, {}, run_tools=False)
        assert leaks == [] and verdict(leaks) == "Clean room: yes", lines
        assert any("synced from the logged-in account: docx" in x for x in lines), lines
        (own / "plugins" / "installed_plugins.json").write_text('{"plugins": {"tool@m": []}}', encoding="utf-8")
        (own / "skills" / "mine").mkdir()
        (own / "settings.local.json").write_text('{"statusLine": {"type": "command", "command": "x"}}', encoding="utf-8")
        _, leaks = check(["claude"], home, work, {}, run_tools=False)
        for want in ("installed plugin tool@m", "skill mine", "settings.local.json sets statusLine"):
            assert any(want in x for x in leaks), (want, leaks)
        (own / "plugins" / "installed_plugins.json").write_text("not json", encoding="utf-8")
        _, leaks = check(["claude"], home, work, {}, run_tools=False)
        assert any("unreadable installed_plugins.json" in x for x in leaks), leaks
        (own / "plugins" / "installed_plugins.json").write_text('{"plugins": {}}', encoding="utf-8")
        (own / "skills" / "mine").rmdir()
        (own / "settings.local.json").unlink()
        (home / ".claude" / "CLAUDE.md").write_text("rules", encoding="utf-8")
        (home / ".claude" / "projects" / "p" / "memory" / "m.md").write_text("fact", encoding="utf-8")
        (home / ".claude.json").write_text('{"projects": {"x": {"mcpServers": {"s": {}}}}}', encoding="utf-8")
        (work.parent / "AGENTS.md").write_text("rules", encoding="utf-8")
        (work.parent / ".claude").mkdir()
        (work.parent / ".git").mkdir()
        (work / "snap" / ".claude").mkdir(parents=True)
        lines, leaks = check(["claude"], home, work, {"BASH_ENV": "/x", "GH_TOKEN": "s3cr3t-value"}, run_tools=False)
        text = "\n".join(lines)
        for want in ("CLAUDE.md", "memory in", "sets mcpServers", "AGENTS.md (parent", "outer" + os.sep + ".claude (project config at the git root",
                     "BASH_ENV is set",
                     "credential in the environment: GH_TOKEN"):
            assert want in text, (want, text)
        assert "s3cr3t-value" not in text, "a credential value was printed"
        _, leaks = check(["claude"], home, Path(t) / "elsewhere", {"CLAUDE_CODE_MESSAGING_TOKEN": "x", "CLAUDE_SESSION_ID": "y",
                                                                  "CLAUDE_CODE_GIT_BASH_PATH": "z"}, run_tools=False)
        assert sum("parent agent session" in x for x in leaks) == 2, leaks
        # inside the audit session, the harness's own variables pass; a parent's other session id still fails
        bare = Path(t) / "bare"
        (bare / ".claude" / "projects" / "p").mkdir(parents=True)
        (bare / ".claude" / "projects" / "p" / "a.jsonl").write_text("{}", encoding="utf-8")
        inside = {"CLAUDECODE": "1", "CLAUDE_CODE_SESSION_ID": "a", "CLAUDE_CODE_MESSAGING_TOKEN": "b"}
        _, leaks = check(["claude"], bare, Path(t) / "elsewhere", inside, run_tools=False)
        assert leaks == [], leaks
        _, leaks = check(["claude"], bare, Path(t) / "elsewhere", {**inside, "GROK_SESSION_ID": "c"}, run_tools=False)
        assert leaks == ["environment: GROK_SESSION_ID is set (a parent agent session)"], leaks
        # a parent Claude session sets the same names, but its transcript isn't in the checked config folder
        _, leaks = check(["claude"], bare, Path(t) / "elsewhere", dict(inside, CLAUDE_CODE_SESSION_ID="parent"), run_tools=False)
        assert sum("parent agent session" in x for x in leaks) == 3, leaks
        assert verdict(leaks).startswith("Clean room: no, ")
        # a moved config folder is the one checked, and ~/.claude.json no longer applies
        clean = Path(t) / "clean"
        clean.mkdir()
        (clean / "settings.json").write_text('{"hooks": {}}', encoding="utf-8")
        _, leaks = check(["claude"], home, Path(t) / "elsewhere", {"CLAUDE_CONFIG_DIR": str(clean)}, run_tools=False)
        assert leaks == [], leaks
        (clean / "settings.json").write_text('{"hooks": {"PreToolUse": [1]}}', encoding="utf-8")
        _, leaks = check(["claude"], home, Path(t) / "elsewhere", {"CLAUDE_CONFIG_DIR": str(clean)}, run_tools=False)
        assert any("sets hooks" in x for x in leaks), leaks
        # safe mode clears the config folder, but not the working folder
        safe = {"CLAUDE_CODE_SAFE_MODE": "1"}
        _, leaks = check(["claude"], home, Path(t) / "elsewhere", {**safe, "CLAUDE_CONFIG_DIR": str(clean)}, run_tools=False)
        assert leaks == [], leaks
        _, leaks = check(["claude"], home, work, safe, run_tools=False)
        assert leaks and all("folder" in x for x in leaks), leaks
    # Grok's own report: bundled, built-in and disabled parts pass; a plugin or a user hook fails
    seen = grok_loaded({"skills": [{"name": "docx", "source": {"type": "bundled"}}],
                        "agents": [{"name": "plan", "source": {"type": "builtin"}}],
                        "projectInstructions": [{"path": "/h/.claude/CLAUDE.md", "disabled": True}],
                        "plugins": [{"name": "p", "path": "/h/.claude/plugins/p", "enabled": True}],
                        "hooks": [{"event": "stop", "source": {"type": "user", "path": "/h/.claude"}}]})
    assert seen == ["plugins p /h/.claude/plugins/p", "hooks stop /h/.claude"], seen
    print("self-test ok")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--self-test"]:
        self_test()
    elif args and len(args) % 2 == 0 and all(a == "--harness" for a in args[::2]):
        lines, leaks = check(args[1::2], Path.home(), Path.cwd(), dict(os.environ))
        print("\n".join(lines + [verdict(leaks)]))
        sys.exit(1 if leaks else 0)
    else:
        sys.exit(__doc__)
