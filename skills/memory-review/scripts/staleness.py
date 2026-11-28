#!/usr/bin/env python3
"""Check an agent memory folder against the files it describes. Read-only.

    python staleness.py MEMORY_DIR [--host NAME] [--budget N]   exit 0 clean, 1 findings, 2 could not run
    python staleness.py --self-test

A memory states a checkable claim in a fact line, an HTML comment the agent never sees:

    <!-- fact: ~/repo/app.py contains "retry_limit" -->
    <!-- fact: buildbox:~/svc/unit.service lacks "Restart=no" -->
    <!-- fact: ~/app/config.json json:server.ports.0 "8080" -->   (dotted key; a number indexes a list)
    <!-- fact: none (a preference; nothing to read) -->

The script only reads files on the machine it runs on and opens no network connection.
A fact for another machine (`buildbox:...`) is listed as not checked here; run the script on
that machine with `--host buildbox` to check those. The report lists: false facts, facts that
could not be read, facts for other machines, memories with no fact line that name a file,
backticked paths whose folder exists but the file does not, [[links]] to missing memories,
index lines pointing at missing files, memories missing from the index, and an index over
budget. Standard library only.
"""
import json, os, pathlib, re, sys, tempfile

FACT = re.compile(r'<!--\s*fact:\s*(\S+)\s+(contains|lacks|json:[\w.-]+)\s+"([^"]*)"\s*-->')
NO_FACT = re.compile(r"<!--\s*fact:\s*none\b")
LINK = re.compile(r"\[\[([^\]]+)\]\]")
INDEX_REF = re.compile(r"\]\(([^)]+\.md)\)")
REF = re.compile(r"`((?:~|/|[A-Za-z]:)[^` ]*)`")
INDEX = "MEMORY.md"
MAX_BYTES = 5_000_000   # a fact names a source or config file; anything larger is not read


def split_host(path):
    """('host', 'path') for host:path; (None, path) for a local or drive-letter path."""
    m = re.match(r"^([A-Za-z0-9_.-]{2,}):(.+)$", path)
    return (m.group(1), m.group(2)) if m else (None, path)


def check(path, verb, needle):
    p = pathlib.Path(os.path.expanduser(path))
    try:
        if not p.is_file() or p.stat().st_size > MAX_BYTES:
            return "unreadable"
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unreadable"
    if verb.startswith("json:"):
        try:
            v = json.loads(text)
        except ValueError:
            return "unreadable"
        for k in verb[5:].split("."):
            if isinstance(v, list) and k.isdigit() and int(k) < len(v):
                v = v[int(k)]
            elif isinstance(v, dict) and k in v:
                v = v[k]
            else:
                return "false"   # the key is gone: the memory's claim no longer holds
        return "true" if (v if isinstance(v, str) else json.dumps(v)) == needle else "false"
    return "true" if (needle in text) == (verb == "contains") else "false"


def review(d, host=None, budget=200):
    d = pathlib.Path(d)
    mems = {p.stem: p.read_text(encoding="utf-8", errors="replace")
            for p in sorted(d.glob("*.md")) if p.name != INDEX}
    index = (d / INDEX).read_text(encoding="utf-8") if (d / INDEX).exists() else ""
    f = {"false fact": [], "unreadable fact": [], "fact for another machine": [],
         "no fact line, names a file": [], "missing path": [], "dead link": [],
         "index points at missing file": [], "not in index": [], "index over budget": []}
    n = 0
    for name, text in mems.items():
        for path, verb, needle in FACT.findall(text):
            n += 1
            h, p = split_host(path)
            if h and h != host:
                f["fact for another machine"].append(f"{name}: {path}")
                continue
            v = check(p, verb, needle)
            if v == "false":
                f["false fact"].append(f'{name}: {path} {verb} "{needle}"')
            elif v == "unreadable":
                f["unreadable fact"].append(f"{name}: {path}")
        refs = REF.findall(text)
        if refs and not FACT.search(text) and not NO_FACT.search(text):
            f["no fact line, names a file"].append(name)
        for r in refs:
            p = os.path.expanduser(r).rstrip("/")
            parent = os.path.dirname(p)
            # Missing only when its folder is here and is not home or root: a path on another
            # machine (~/.otherapp) or a URL route (/api/x) says nothing about this one.
            if not any(c in r for c in "*<>$") and parent != os.path.expanduser("~") \
                    and os.path.dirname(parent) != parent \
                    and os.path.isdir(parent) and not os.path.exists(p):
                f["missing path"].append(f"{name}: {r}")
        for k in sorted(set(LINK.findall(text))):
            if k not in mems:
                f["dead link"].append(f"{name} -> {k}")
    indexed = set(INDEX_REF.findall(index))
    f["index points at missing file"] = sorted(r for r in indexed if not (d / r).exists())
    f["not in index"] = sorted(m for m in mems if f"{m}.md" not in indexed)
    lines = len(index.splitlines())
    if lines > budget:
        f["index over budget"].append(f"{lines} lines > {budget}")
    return n, f


def main(argv):
    if "--self-test" in argv:
        return self_test()
    opts = {"--host": None, "--budget": "200"}
    args = []
    it = iter(argv)
    for a in it:
        if a in opts:
            opts[a] = next(it, None)
        else:
            args.append(a)
    if len(args) != 1 or not pathlib.Path(args[0]).is_dir() or not (opts["--budget"] or "").isdigit():
        print(__doc__.strip(), file=sys.stderr)
        return 2
    n, f = review(args[0], opts["--host"], int(opts["--budget"]))
    found = sum(len(v) for k, v in f.items() if k != "fact for another machine")
    print(f"{n} fact lines; {len(f['false fact'])} false, {len(f['unreadable fact'])} unreadable, "
          f"{len(f['fact for another machine'])} for another machine; {found} findings.")
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
        (d / "far.md").write_text(f'<!-- fact: box:{tgt} contains "alpha" -->\n')
        (d / "nofact.md").write_text(f"reads `{tgt}`, `{d.as_posix()}/missing.py` and `/no-such-root/x.py`\n")
        (d / "pref.md").write_text("<!-- fact: none (a preference) -->\n")
        (d / INDEX).write_text("- [g](good.md)\n- [b](bad.md)\n- [x](deleted.md)\n- [p](pref.md)\n- [f](far.md)\n")
        n, f = review(d, budget=4)
        assert n == 3, n
        assert f["false fact"] == [f'bad: {tgt} contains "gamma"'], f["false fact"]
        assert f["fact for another machine"] == [f"far: box:{tgt}"], f
        assert f["dead link"] == ["bad -> gone"], f["dead link"]
        assert f["no fact line, names a file"] == ["nofact"], f
        assert f["missing path"] == [f"nofact: {d.as_posix()}/missing.py"], f["missing path"]
        assert f["index points at missing file"] == ["deleted.md"]
        assert f["not in index"] == ["nofact"]
        assert f["index over budget"] == ["5 lines > 4"]
        n, f = review(d, host="box", budget=9)
        assert f["fact for another machine"] == [] and f["false fact"] == [f'bad: {tgt} contains "gamma"']
        (d / "c.json").write_text('{"a": {"b": ["x", 8080]}}')
        cj = (d / "c.json").as_posix()
        assert FACT.findall(f'<!-- fact: {cj} json:a.b.1 "8080" -->') == [(cj, "json:a.b.1", "8080")]
        assert check(cj, "json:a.b.0", "x") == "true" and check(cj, "json:a.b.1", "8080") == "true"
        assert check(cj, "json:a.b.1", "80") == "false" and check(cj, "json:a.z", "x") == "false"
        assert check(tgt, "json:a", "x") == "unreadable"
        assert check(d.as_posix(), "contains", "x") == "unreadable"   # a folder is not a file
        assert split_host("C:/x/y") == (None, "C:/x/y") and split_host("box:~/a") == ("box", "~/a")
    print("self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
