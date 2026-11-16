#!/usr/bin/env python3
"""Check every skill in skills/: frontmatter, README, line endings, and that scripts compile.

    python scripts/check-skills.py        # exit 1 and list problems, 0 when clean
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESC_MAX = 1024
PRIVATE = re.compile(r"/home/[a-z]+/|C:\\Users\\|ghp_[A-Za-z0-9]{20}|sk-[A-Za-z0-9]{20}")


def frontmatter(text: str) -> dict[str, str]:
    """name and description from the leading --- block; handles quoted and `|` values."""
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out, key = {}, None
    for line in m.group(1).splitlines():
        kv = re.match(r"([a-z_-]+):\s*(.*)$", line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip()
            out[key] = "" if val in ("|", ">") else val.strip("\"'")
        elif key and line.startswith(" "):
            out[key] = (out[key] + " " + line.strip()).strip()
    return out


def check(skill: Path) -> list[str]:
    errs = []
    md = skill / "SKILL.md"
    if not md.is_file():
        return [f"{skill.name}: no SKILL.md"]
    if not (skill / "README.md").is_file():
        errs.append(f"{skill.name}: no README.md")
    fm = frontmatter(md.read_text(encoding="utf-8"))
    if fm.get("name") != skill.name:
        errs.append(f"{skill.name}: frontmatter name is {fm.get('name')!r}, not the folder name")
    desc = fm.get("description", "")
    if not desc:
        errs.append(f"{skill.name}: no description")
    elif len(desc) > DESC_MAX:
        errs.append(f"{skill.name}: description is {len(desc)} chars, over {DESC_MAX}")
    for f in skill.rglob("*"):
        if not f.is_file():
            continue
        data = f.read_bytes()
        if b"\r\n" in data:
            errs.append(f"{f.relative_to(ROOT)}: CRLF line endings")
        if PRIVATE.search(data.decode("utf-8", "replace")):
            errs.append(f"{f.relative_to(ROOT)}: looks like a home path or a token")
        if f.suffix == ".py":
            try:
                compile(data, str(f), "exec")   # syntax check, writes no .pyc
            except SyntaxError as e:
                errs.append(f"{f.relative_to(ROOT)}:{e.lineno}: {e.msg}")
    return errs


def main() -> int:
    skills = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
    errs = [e for s in skills for e in check(s)]
    print("\n".join(errs) if errs else f"{len(skills)} skills clean")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
