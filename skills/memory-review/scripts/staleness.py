#!/usr/bin/env python3
"""Check an agent memory folder against the systems it describes.

    python staleness.py MEMORY_DIR [--budget N]      report; exit 0 clean, 1 findings, 2 could not run
    python staleness.py --self-test

A memory states a checkable claim in a fact line, an HTML comment the agent never sees:

    <!-- fact: ~/repo/app.py contains "retry_limit" -->
    <!-- fact: myhost:~/svc/unit.service lacks "Restart=no" -->
    <!-- fact: none (a preference; nothing to read) -->

A path with a `host:` prefix is read over `ssh host`, one call per host. The report lists:
false facts, facts that could not be read, memories with no fact line that name a file,
backticked local paths that no longer exist, [[links]] to missing memories, index lines
pointing at missing files, memories missing from the index, and an index over budget.
Standard library only.
"""
import json, os, pathlib, re, subprocess, sys, tempfile

FACT = re.compile(r'<!--\s*fact:\s*(\S+)\s+(contains|lacks)\s+"([^"]*)"\s*-->')
NO_FACT = re.compile(r"<!--\s*fact:\s*none\b")
LINK = re.compile(r"\[\[([^\]]+)\]\]")
INDEX_REF = re.compile(r"\]\(([^)]+\.md)\)")
REF = re.compile(r"`((?:~|/|[A-Za-z]:)[^` ]*)`")
INDEX = "MEMORY.md"
REMOTE = r'''
import json, os, sys
out = []
for path, verb, needle in json.loads(sys.stdin.read()):
    p = os.path.expanduser(path)
    try:
        has = needle in open(p, encoding="utf-8", errors="replace").read()
        out.append("true" if has == (verb == "contains") else "false")
    except OSError:
        out.append("unreadable")
print(json.dumps(out))
'''


def split_host(path):
    """('host', 'path') for host:path; (None, path) for a local or drive-letter path."""
    m = re.match(r"^([A-Za-z0-9_.-]{2,}):(.+)$", path)
    return (m.group(1), m.group(2)) if m else (None, path)


def check_local(path, verb, needle):
    try:
        text = pathlib.Path(os.path.expanduser(path)).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unreadable"
    return "true" if (needle in text) == (verb == "contains") else "false"


def check_remote(host, facts):
    """One ssh call per host; every fact is 'unreadable' if the host does not answer."""
    script = "import sys; sys.stdin = __import__('io').StringIO(%r)\n%s" % (
        json.dumps([[p, v, n] for p, v, n in facts]), REMOTE)
    try:
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", host, "python3", "-"], input=script,
                           capture_output=True, text=True, timeout=60)
        res = json.loads(r.stdout.strip().splitlines()[-1])
        return res if len(res) == len(facts) else ["unreadable"] * len(facts)
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return ["unreadable"] * len(facts)


def review(d, budget=200):
    d = pathlib.Path(d)
    mems = {p.stem: p.read_text(encoding="utf-8", errors="replace")
            for p in sorted(d.glob("*.md")) if p.name != INDEX}
    index = (d / INDEX).read_text(encoding="utf-8") if (d / INDEX).exists() else ""
    facts = [(n, *f) for n, t in mems.items() for f in FACT.findall(t)]
    verdict = {}
    by_host = {}
    for i, (n, path, verb, needle) in enumerate(facts):
        host, p = split_host(path)
        if host:
            by_host.setdefault(host, []).append((i, p, verb, needle))
        else:
            verdict[i] = check_local(p, verb, needle)
    for host, items in by_host.items():
        for (i, *_), v in zip(items, check_remote(host, [x[1:] for x in items])):
            verdict[i] = v
    f = {"false fact": [], "unreadable fact": [], "no fact line, names a file": [],
         "missing path": [], "dead link": [], "index points at missing file": [],
         "not in index": [], "index over budget": []}
    for i, (n, path, verb, needle) in enumerate(facts):
        if verdict[i] == "false":
            f["false fact"].append(f'{n}: {path} {verb} "{needle}"')
        elif verdict[i] == "unreadable":
            f["unreadable fact"].append(f"{n}: {path}")
    for n, t in mems.items():
        refs = REF.findall(t)
        if refs and not FACT.search(t) and not NO_FACT.search(t):
            f["no fact line, names a file"].append(n)
        for r in refs:
            p = os.path.expanduser(r).rstrip("/")
            # Missing only when its folder is here and is not home or root: a path on another
            # machine (~/.otherapp) or a URL route (/api/x) says nothing about this box.
            parent = os.path.dirname(p)
            if split_host(r)[0] is None and not any(c in r for c in "*<>$") \
                    and parent != os.path.expanduser("~") and os.path.dirname(parent) != parent \
                    and os.path.isdir(parent) and not os.path.exists(p):
                f["missing path"].append(f"{n}: {r}")
        for k in set(LINK.findall(t)):
            if k not in mems:
                f["dead link"].append(f"{n} -> {k}")
    indexed = set(INDEX_REF.findall(index))
    f["index points at missing file"] = sorted(r for r in indexed if not (d / r).exists())
    f["not in index"] = sorted(n for n in mems if f"{n}.md" not in indexed)
    lines = index.count("\n") + (1 if index and not index.endswith("\n") else 0)
    if lines > budget:
        f["index over budget"].append(f"{lines} lines > {budget}")
    return len(facts), f


def main(argv):
    if "--self-test" in argv:
        return self_test()
    budget = 200
    if "--budget" in argv:
        i = argv.index("--budget")
        budget = int(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1 or not pathlib.Path(args[0]).is_dir():
        print(__doc__.strip(), file=sys.stderr)
        return 2
    n, f = review(args[0], budget)
    found = sum(len(v) for v in f.values())
    print(f"{n} fact lines read; {len(f['false fact'])} false, {len(f['unreadable fact'])} unreadable; "
          f"{found} findings in all.")
    for k, v in f.items():
        if v:
            print(f"\n{k} ({len(v)}):")
            print("\n".join(f"- {x}" for x in v))
    return 1 if found else 0


def self_test():
    with tempfile.TemporaryDirectory() as t:
        d = pathlib.Path(t)
        (d / "target.txt").write_text("alpha beta\n")
        tgt = (d / "target.txt").as_posix()
        (d / "good.md").write_text(f'see [[bad]]\n<!-- fact: {tgt} contains "alpha" -->\n')
        (d / "bad.md").write_text(f'<!-- fact: {tgt} contains "gamma" -->\n[[gone]]\n')
        (d / "nofact.md").write_text(f"reads `{tgt}`, `{d.as_posix()}/missing.py` and `/no-such-root/x.py`\n")
        (d / "pref.md").write_text("<!-- fact: none (a preference) -->\n")
        (d / INDEX).write_text("- [g](good.md)\n- [b](bad.md)\n- [x](deleted.md)\n- [p](pref.md)\n")
        n, f = review(d, budget=3)
        assert n == 2, n
        assert f["false fact"] == [f'bad: {tgt} contains "gamma"'], f["false fact"]
        assert f["dead link"] == ["bad -> gone"], f["dead link"]
        assert f["no fact line, names a file"] == ["nofact"], f
        assert f["missing path"] == [f"nofact: {d.as_posix()}/missing.py"], f["missing path"]
        assert f["index points at missing file"] == ["deleted.md"]
        assert f["not in index"] == ["nofact"]
        assert f["index over budget"] == ["4 lines > 3"]
        assert split_host("C:/x/y") == (None, "C:/x/y") and split_host("box:~/a") == ("box", "~/a")
    print("self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
