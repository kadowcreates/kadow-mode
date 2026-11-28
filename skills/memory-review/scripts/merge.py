#!/usr/bin/env python3
"""Fold absorbed memories into a survivor the agent has already written.

    python merge.py MEMORY_DIR SURVIVOR ABSORBED [ABSORBED ...]
    python merge.py MEMORY_DIR - DROPPED [DROPPED ...]      archive with no survivor (a drop)
    python merge.py --self-test

For each absorbed memory: move it to archive-YYMMDD/ (git mv when the folder is a git repo,
so history follows), repoint every [[absorbed]] link to [[survivor]], and delete its line in
MEMORY.md. Then drop duplicate and self links in each paragraph, and print any dead link.
Run it BEFORE rewriting the survivor, then write the survivor from the archived files: an
existing survivor's old text is then still the old text (without git it is also copied to the
archive as SURVIVOR.pre-merge.md); a new survivor may not exist yet. The survivor's own index
line is the agent's to write. Nothing is deleted: the archive
holds every absorbed file in full. Standard library only.
"""
import datetime, pathlib, re, shutil, subprocess, sys, tempfile

LINK = re.compile(r"\[\[([^\]]+)\]\]")
INDEX = "MEMORY.md"


RUN = re.compile(r"\[\[[^\]]+\]\](?:\s*,\s*\[\[[^\]]+\]\])*")


def tidy(text, name):
    """Drop repeated and self links inside each comma-separated run of links.

    A run that empties becomes "this memory" so the sentence around it still reads. A link
    standing in prose is never deleted: removing it leaves holes like "against ." or "See .".
    """
    def fix(m):
        seen, kept = set(), []
        for k in LINK.findall(m.group(0)):
            if k != name and k not in seen:
                seen.add(k)
                kept.append(f"[[{k}]]")
        if len(kept) == len(LINK.findall(m.group(0))):
            return m.group(0)   # nothing dropped: keep the run's own line breaks
        return ", ".join(kept) or "this memory"
    return RUN.sub(fix, text)


def merge(d, survivor, absorbed, today=None):
    d = pathlib.Path(d)
    drop = survivor == "-"
    for n in ([] if drop else [survivor]) + list(absorbed):
        # A memory name is a bare file stem; a path would move files outside the folder.
        if not re.fullmatch(r"[\w.-]+", n) or n.startswith("."):
            raise SystemExit(f"not a memory name: {n!r}")
    if survivor in absorbed:
        raise SystemExit("the survivor cannot also be absorbed")
    for a in absorbed:
        if not (d / f"{a}.md").exists():
            raise SystemExit(f"{a}.md not found; nothing moved")
    arch = d / f"archive-{(today or datetime.date.today()).strftime('%y%m%d')}"
    arch.mkdir(exist_ok=True)
    git = (d / ".git").exists()
    if not git and not drop and (d / f"{survivor}.md").exists():
        # No history to undo the coming survivor rewrite: keep its text from before it.
        shutil.copy2(d / f"{survivor}.md", arch / f"{survivor}.pre-merge.md")
    for a in absorbed:
        if git:
            subprocess.run(["git", "-C", str(d), "mv", f"{a}.md", f"{arch.name}/{a}.md"], check=True)
        else:
            shutil.move(str(d / f"{a}.md"), str(arch / f"{a}.md"))
    dead = []
    names = {p.stem for p in d.glob("*.md")} | (set() if drop else {survivor})
    for p in d.glob("*.md"):
        text = p.read_text(encoding="utf-8")
        new = text
        if p.name == INDEX:
            new = "".join(l for l in text.splitlines(True)
                          if not any(f"({a}.md)" in l for a in absorbed))
        elif not drop:   # a drop leaves its links dead, so they are printed for the agent to fix
            for a in absorbed:
                new = new.replace(f"[[{a}]]", f"[[{survivor}]]")
            new = tidy(new, p.stem)
        if p.name != INDEX:
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
        (d / "gone.md").write_text("g\n"); (d / "ref.md").write_text("see [[gone]]\n")
        (d / INDEX).write_text("- [G](gone.md)\n- [R](ref.md)\n")
        _, dead = merge(d, "-", ["gone"], datetime.date(2026, 11, 27))
        assert (arch / "gone.md").exists() and (d / INDEX).read_text() == "- [R](ref.md)\n"
        assert "ref -> gone" in dead, dead
        (d / "x.md").write_text("see [[y]]\n"); (d / "y.md").write_text("y\n")
        _, dead = merge(d, "fresh", ["y"], datetime.date(2026, 11, 27))   # new survivor, not yet written
        assert (d / "x.md").read_text() == "see [[fresh]]\n" and not any("fresh" in x for x in dead)
        for bad in (["../x"], ["keep"], [".hidden"]):
            try:
                merge(d, "keep", bad)
                raise AssertionError(f"accepted {bad}")
            except SystemExit:
                pass
        assert (arch / "keep.pre-merge.md").read_text() == "kept\n"
        assert tidy("x [[self]] y", "self") == "x this memory y"
        assert tidy("against [[a]], see [[a]].", "z") == "against [[a]], see [[a]]."
        assert tidy("See [[a]], [[b]], [[a]].", "b") == "See [[a]]."
        assert tidy("See [[a]],\n[[b]].", "z") == "See [[a]],\n[[b]]."
    print("self-test passed")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    if len(sys.argv) < 4:
        sys.exit(__doc__.strip())
    arch, dead = merge(sys.argv[1], sys.argv[2], sys.argv[3:])
    print(f"archived {len(sys.argv) - 3} file(s) to {arch.name}/")
    if sys.argv[2] != "-":
        print(f"now write {sys.argv[2]}.md from the archived files, then its index line")
    print("\n".join(f"dead link: {x}" for x in dead) or "no dead links")
