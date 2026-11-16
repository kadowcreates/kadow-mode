#!/usr/bin/env python3
"""Census of state machines in a Python tree: declared, implicit, and bypassed.

    python state_machines.py [paths...]        (default: every tracked *.py)

- declared:  a class whose name ends in Status/State/Phase/Stage/Verdict/Disposition and
             that subclasses an Enum or a project vocabulary class.
- implicit:  a status-like key or attribute that code branches on with three or more string
             literals. Writes often go through helpers, so writes are reported but not required.
- bypassed:  a raw string literal compared against a status-like key when that literal is
             also a member value of a declared class in the same file or a module it imports. Renaming the member will not catch it.

Heuristic, AST-only. A hit is a candidate: read the code before calling it a lifecycle
(a classification such as a bench verdict, or a state read from systemd, is not one).
"""
import ast, collections, re, subprocess, sys

KEY = re.compile(r"^_?(status|state|phase|stage|mode|step|lifecycle|disposition|verdict|outcome)$", re.I)
DECL = re.compile(r"(Status|State|Phase|Stage|Verdict|Disposition)$")


def keyname(n):
    if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str):
        return n.slice.value
    if isinstance(n, ast.Attribute):
        return n.attr
    if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get"
            and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)):
        return n.args[0].value
    if isinstance(n, ast.Name):
        return n.id


def lits(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return {n.value}
    if isinstance(n, (ast.Tuple, ast.List, ast.Set)):
        return {e.value for e in n.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)}
    return set()


def main(paths):
    files = paths or subprocess.run(["git", "ls-files", "*.py"], capture_output=True, text=True).stdout.split()
    writes, reads = collections.defaultdict(set), collections.defaultdict(set)
    compares = []                     # (file, line, key, literals)
    declared = []
    members = collections.defaultdict(set)   # module stem -> member values
    imports = collections.defaultdict(set)   # file -> module stems it imports
    for f in files:
        try:
            tree = ast.parse(open(f, encoding="utf-8").read())
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        stem = f.rsplit("/", 1)[-1][:-3]
        imports[f].add(stem)
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom):
                imports[f] |= {a.name for a in n.names} | {(n.module or "").rsplit(".", 1)[-1]}
            elif isinstance(n, ast.Import):
                imports[f] |= {a.name.rsplit(".", 1)[-1] for a in n.names}
            if isinstance(n, ast.ClassDef) and DECL.search(n.name) and n.bases:
                declared.append(f"{f}:{n.lineno} {n.name}")
                for s in n.body:
                    if isinstance(s, ast.Assign):
                        v = s.value.elts[0] if isinstance(s.value, ast.Tuple) and s.value.elts else s.value
                        members[stem] |= lits(v)
            elif isinstance(n, ast.Assign):
                for t in n.targets:
                    k = keyname(t)
                    if k and KEY.match(k):
                        writes[(f, k.lower().lstrip("_"))] |= lits(n.value)
            elif isinstance(n, ast.Dict):
                for k, v in zip(n.keys, n.values):
                    if isinstance(k, ast.Constant) and isinstance(k.value, str) and KEY.match(k.value):
                        writes[(f, k.value.lower())] |= lits(v)
            elif isinstance(n, ast.Compare):
                k = keyname(n.left)
                if k and KEY.match(k):
                    found = set().union(*(lits(c) for c in n.comparators))
                    reads[(f, k.lower().lstrip("_"))] |= found
                    compares.append((f, n.lineno, k, found))

    implicit = sorted(((len(reads[k] | writes[k]), k, sorted(reads[k] | writes[k])) for k in reads
                       if len(reads[k]) >= 3), reverse=True)
    def known(f):
        return set().union(*(members[m] for m in imports[f]))
    bypass = [(f, ln, k, sorted(s & known(f))) for f, ln, k, s in compares if s & known(f)]

    print(f"declared {len(declared)}")
    for d in declared:
        print("   ", d)
    print(f"implicit {len(implicit)} (key branched on >=3 literals; read each before counting it)")
    for n, (f, k), s in implicit:
        print(f"   {n:3} {f}:{k}  {s[:8]}")
    print(f"bypassed {len(bypass)} (raw literal that is a declared member value)")
    for f, ln, k, s in bypass[:40]:
        print(f"    {f}:{ln} {k} {s}")


if __name__ == "__main__":
    main(sys.argv[1:])
