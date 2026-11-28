#!/usr/bin/env python3
"""Fold absorbed memories into a survivor the agent has already written.

    python merge.py MEMORY_DIR SURVIVOR ABSORBED [ABSORBED ...]
    python merge.py --self-test

For each absorbed memory: move it to archive-YYMMDD/ (git mv when the folder is a git repo,
so history follows), repoint every [[absorbed]] link to [[survivor]], and delete its line in
MEMORY.md. Then drop duplicate and self links in each paragraph, and print any dead link.
The survivor's own index line is the agent's to write. Nothing is deleted: the archive
holds every absorbed file in full. Standard library only.
"""
import datetime, pathlib, re, shutil, subprocess, sys, tempfile

LINK = re.compile(r"\[\[([^\]]+)\]\]")
INDEX = "MEMORY.md"


def tidy(text, name):
    """Drop repeated and self links per paragraph, then the commas they leave behind."""
    out = []
    for para in text.split("\n\n"):
        seen = set()

        def keep(m):
            k = m.group(1)
            if k in seen or k == name:
                return ""
            seen.add(k)
            return m.group(0)

        new = LINK.sub(keep, para)
        if new != para:
            new = re.sub(r",(\s*,)+", ",", new)
            new = re.sub(r":\s*,\s*", ": ", new)
            new = re.sub(r",\s*(?=\.|$)", "", new)
            new = re.sub(r"[ \t]+\n", "\n", new)
        out.append(new)
    return "\n\n".join(out)


def merge(d, survivor, absorbed, today=None):
    d = pathlib.Path(d)
    if not (d / f"{survivor}.md").exists():
        raise SystemExit(f"write {survivor}.md first: the survivor carries what is kept")
    for a in absorbed:
        if not (d / f"{a}.md").exists():
            raise SystemExit(f"{a}.md not found; nothing moved")
    arch = d / f"archive-{(today or datetime.date.today()).strftime('%y%m%d')}"
    arch.mkdir(exist_ok=True)
    git = (d / ".git").exists()
    for a in absorbed:
        if git:
            subprocess.run(["git", "-C", str(d), "mv", f"{a}.md", f"{arch.name}/{a}.md"], check=True)
        else:
            shutil.move(str(d / f"{a}.md"), str(arch / f"{a}.md"))
    dead = []
    names = {p.stem for p in d.glob("*.md")}
    for p in d.glob("*.md"):
        text = p.read_text(encoding="utf-8")
        new = text
        if p.name == INDEX:
            new = "".join(l for l in text.splitlines(True)
                          if not any(f"({a}.md)" in l for a in absorbed))
        else:
            for a in absorbed:
                new = new.replace(f"[[{a}]]", f"[[{survivor}]]")
            new = tidy(new, p.stem)
            dead += [f"{p.stem} -> {k}" for k in sorted(set(LINK.findall(new))) if k not in names]
        if new != text:
            p.write_bytes(new.encode("utf-8"))
    return arch, dead


def self_test():
    with tempfile.TemporaryDirectory() as t:
        d = pathlib.Path(t)
        (d / "keep.md").write_text("kept\n")
        (d / "old-a.md").write_text("a\n")
        (d / "old-b.md").write_text("b, see [[keep]]\n")
        (d / "other.md").write_text("Related: [[old-a]], [[old-b]], [[keep]], [[nowhere]].\n")
        (d / "self.md").write_text("x [[self]] y\n")
        (d / INDEX).write_text("- [K](keep.md)\n- [A](old-a.md)\n- [B](old-b.md)\n")
        arch, dead = merge(d, "keep", ["old-a", "old-b"], datetime.date(2026, 11, 27))
        assert arch.name == "archive-261127" and (arch / "old-a.md").exists()
        assert not (d / "old-a.md").exists()
        assert (d / "other.md").read_text() == "Related: [[keep]], [[nowhere]].\n", (d / "other.md").read_text()
        assert (d / INDEX).read_text() == "- [K](keep.md)\n"
        assert dead == ["other -> nowhere"], dead
        try:
            merge(d, "missing", ["keep"])
            raise AssertionError("merged into an unwritten survivor")
        except SystemExit:
            pass
        assert tidy("x [[self]] y", "self") == "x  y"
    print("self-test passed")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    if len(sys.argv) < 4:
        sys.exit(__doc__.strip())
    arch, dead = merge(sys.argv[1], sys.argv[2], sys.argv[3:])
    print(f"archived {len(sys.argv) - 3} file(s) to {arch.name}/")
    print("\n".join(f"dead link: {x}" for x in dead) or "no dead links")
