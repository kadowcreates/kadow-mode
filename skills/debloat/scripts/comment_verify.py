# Proves a comment-only change: for each file modified against HEAD, the code with comments
# stripped is identical, and every record ID in the old file survives in the new one.
#   python3 comment_verify.py <repo> <node_modules dir with typescript>
import ast, os, re, subprocess, sys
repo, nm = sys.argv[1], sys.argv[2]
os.chdir(repo)
ID = re.compile(r"\b(?:FEAT|BUG|ADR|PAT|OPS|INC|GOV|DEC|SEC|FIND|IDEA|OPP|L)-\d{4,}(?:-\d+)?\b|\bF-\d{3}\b|\bS-\d{2}\b")
TS = r"""const ts=require(process.argv[1]+'/typescript');const fs=require('fs');
const a=fs.readFileSync(0,'utf8').split('\u0000').map(s=>s.replace(/\{\s*\/\*[\s\S]*?\*\/\s*\}/g,''));
const name=process.argv[2];
const p=ts.createPrinter({removeComments:true});
const kind=name.endsWith('x')?ts.ScriptKind.TSX:(name.endsWith('ts')?ts.ScriptKind.TS:ts.ScriptKind.JS);
const out=a.map(s=>p.printFile(ts.createSourceFile(name,s,ts.ScriptTarget.Latest,false,kind)).replace(/^\s+$/gm,'').replace(/\n+/g,'\n'));
process.stdout.write(out[0]===out[1]?'same':'DIFF');"""
def py_norm(src):
    t = ast.parse(src)
    for n in ast.walk(t):
        b = getattr(n, "body", None)
        if isinstance(b, list):   # every bare string statement is a no-op, docstring or not
            n.body = [x for x in b if not (isinstance(x, ast.Expr) and isinstance(x.value, ast.Constant)
                                           and isinstance(x.value.value, str))] or [ast.Pass()]
    return ast.dump(t)
def sh_norm(src):
    out = []
    for l in src.splitlines():
        s = l.strip()
        if not s or (s.startswith("#") and not s.startswith("#!")): continue
        out.append(re.sub(r"\s+#\s[^'\"]*$", "", l).rstrip())
    return "\n".join(out)
bad = 0
files = subprocess.run(["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True).stdout.split()
for f in files:
    old = subprocess.run(["git", "show", f"HEAD:{f}"], capture_output=True, text=True).stdout
    new = open(f, encoding="utf-8").read()
    if new.startswith("﻿") != old.startswith("﻿"): print(f"BOM changed  {f}")
    old, new = old.lstrip("﻿"), new.lstrip("﻿")
    e = os.path.splitext(f)[1]
    if e == ".py": ok = py_norm(old) == py_norm(new)
    elif e in (".ts", ".tsx", ".js", ".mjs"):
        r = subprocess.run(["node", "-e", TS, nm, f], input=old + "\0" + new, capture_output=True, text=True)
        ok = r.stdout == "same"
    elif e == ".sh": ok = sh_norm(old) == sh_norm(new)
    elif e == ".css": ok = re.sub(r"/\*.*?\*/|\s+", "", old, flags=re.S) == re.sub(r"/\*.*?\*/|\s+", "", new, flags=re.S)
    else: ok = None
    lost = sorted(set(ID.findall(old)) - set(ID.findall(new)))
    if "\r" in new and "\r" not in old: ok = False; lost.append("CRLF")
    if ok is not True or lost:
        bad += 1; print(f"{'CODE CHANGED' if ok is False else ('UNCHECKED' if ok is None else 'ok')}  {f}  lost={lost}")
print(f"{len(files)} files changed, {bad} need a look")
