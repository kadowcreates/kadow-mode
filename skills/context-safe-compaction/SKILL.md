---
name: context-safe-compaction
description: "Compact a file that rides in every prompt (CLAUDE.md, MCP tool schemas) without losing a rule. Use when a bootstrap file is over its inject limit, when the gateway logs 'truncating in injected context', when a protocol seems to have stopped being followed for no reason, or when asked to cut prompt size or token cost per turn. Cuts fluff by rewriting in controlled language (ASD-STE100), never by dropping content. Not for ordinary prose editing, and not for files outside the system prompt."
---

# Context-safe compaction

A file injected into every prompt is not a document, it is **the running config of an
agent's behaviour**. Deleting a line from it is a behaviour change with no error message.
Silent truncation is worse: the file keeps its content on disk, so the rule looks present
in every review, and only the agent's behaviour disagrees.

Precedent: `AGENTS.md` overran the 20,000-char inject limit and severed the `#ideas`
capture protocol. Nothing failed loudly. Nine days of posts were dropped
(FIND-260804-008). The 2026-08-04 fix reordered the file — which rescued `#ideas` by
pushing *three other sections* past the cut instead. Reordering is not compaction; it
moves the loss somewhere you are not looking.

<!-- PLATFORM:claude-code -->
## 1. Stop the loss before you optimise

Find out what is actually in the window before changing anything. `/context` breaks the
current usage down by component — system prompt, `CLAUDE.md`, tool schemas, MCP servers,
transcript.

```bash
wc -c CLAUDE.md ~/.claude/CLAUDE.md 2>/dev/null       # project + user memory, both injected
ls ~/.claude/skills/*/SKILL.md | xargs wc -c | tail -1 # skill DESCRIPTIONS ride in the prompt
```

Claude Code auto-compacts the transcript as it approaches the limit, so runtime pressure
is handled for you. What is **not** handled is the static half: `CLAUDE.md`, skill
descriptions and MCP tool schemas are re-sent on every single turn and nothing warns you
when they grow. That is the half this skill is for.

If something is already being cut, widen the budget or drop an MCP server first, and
compact afterwards. Compacting under pressure is how rules get dropped.
<!-- /PLATFORM -->

## 2. Find what is being cut — truncation is tail-first

Never assume which end goes. Map sections against the cut point:

```bash
python3 - <<'PY'
import pathlib, re
LIMIT = 20000
t = pathlib.Path("AGENTS.md").read_text(encoding="utf-8")
h = [(m.start(), m.group(0).strip()) for m in re.finditer(r"^#{1,3} .+$", t, re.M)] + [(len(t), "(EOF)")]
for i in range(len(h)-1):
    st, name = h[i]; en = h[i+1][0]
    flag = "  <-- DROPPED" if st >= LIMIT else ("  <-- CUT MID-SECTION" if en > LIMIT else "")
    print(f"{st:>7,} {en-st:>6,}  {name[:60]}{flag}")
PY
```

What sits past the line is what the agent has not been reading. Check that against the
behaviour you have been puzzled by — it usually explains something.

## 3. Inventory the rules BEFORE editing

Extract every load-bearing item, so "did we lose anything" is a diff and not a memory
test. Load-bearing means:

- an **id** — `GOV-…`, `ADR-…`, a Discord channel id, an endpoint, a file path
- an **absolute** — never / always / must / exactly one / NO_REPLY is not valid
- a **numbered procedure** whose steps have consequences
- a **command** the agent is expected to run verbatim

```bash
grep -nE '\b[A-Z]{2,4}-[0-9]{6,8}-[0-9]{3}\b|\bADR-[0-9]{4}\b|[0-9]{17,20}|\b(never|always|must|exactly one)\b|^[0-9]+\.|`[^`]+`' AGENTS.md | sort > /tmp/rules-before.txt
```

## 4. Cut by LAYER, in order — cheapest and most reversible first

Do not start by rewriting. The field converged on a hierarchy and every layer above the
one below is cheaper, more reversible, and loses less:

1. **Prevention** — never put it in the window. Scope tools per agent, retrieve snippets
   instead of whole files, cap tool-result size. *Measured here: 9x the return of the best
   rewrite, at zero fidelity cost.*
2. **Reversible offload** — write it to disk, keep a pointer and a preview.
3. **Algorithmic pruning** — drop old tool results and thinking blocks, cap results at
   ~2k chars, strip ANSI. Zero LLM cost, zero hallucination risk.
4. **Relocation** — move a procedure into a skill body; its `description` keeps the
   trigger in the prompt while the body costs nothing until it fires. (Section 5.)
5. **Anchored structured summary** — fixed sections, summarize only the newly dropped
   span, merge into the previous summary.
6. **Free-form summarization** — last resort. Highest ratio, fastest drift.

**Controlled language is a refinement of the LAST rung, not the first move.** An earlier
version of this skill had it at the top and called it "the safest"; that was wrong, and
the scorer in section 6 caught it — a 39% rewrite scored 51.3% prose retention because it
took the failure precedent and a negative case with it. Rewrite only what nobody quotes,
and only after layers 1-4 are exhausted.

### Controlled language, when you get there

ASD-STE100 (Simplified Technical English) is the field-proven version. The rules that pay
on a prompt file:

- **One instruction per sentence.** Procedural sentences ≤ 20 words, descriptive ≤ 25.
- **Imperative and active.** "Read `NOW.md` at the start" beats "`NOW.md` should be read".
- **One word per meaning.** Pick `stamp` or `refresh` and never alternate. Synonyms make
  a model think two different things are being asked for.
- **No noun clusters over three words.**
- **Keep the articles.** "the ledger", not "ledger" — telegraphic prose reads as ambiguous.
- **Cut hedges and connective tissue**: *in a glance*, *precisely because*, *and kin*,
  *that gap is closed here*, *it is worth noting*.

Measured on `AGENTS.md § Session checkpoint`: **1,814 → 1,104 chars, 39% saved**, mean
sentence 24.8 → 14.4 words, with every rule and every trigger phrase intact.

### What looks like fluff and is not

The objective is not the smallest file. It is the smallest file that **loses nothing
relevant to the goal, including on a long run**. These survive compression — shortened,
never removed:

- **The failure that produced the rule.** "AGENTS.md overran and severed #ideas for nine
  days" is why an agent obeys the rule at hour six instead of optimising it away. A bare
  imperative with no cost attached is the first thing a long run rationalises around.
- **Ids** — `GOV-…`, `ADR-…`, `PAT-…`, channel ids, endpoints. They are the handle for
  everything the file could not fit.
- **The negative case.** "Do NOT capture ordinary conversation" prevents more damage than
  the positive rule next to it, and cannot be inferred from it.
- **Exact trigger words.** If the rule fires on the owner saying "wrap up", the string
  `"wrap up"` is data, not prose. Paraphrasing it breaks the trigger.

Fluff is: restating the same rule twice, narrative transitions, hedging, glosses that
re-explain a term already used correctly, and rationale for a decision nobody will revisit.

## 5. Then compact by RELOCATION, not deletion

The rule that survives: **the prompt file holds triggers and absolutes; procedures live
in a skill, loaded on demand.** A skill's `description` is in the prompt — that is what
carries the trigger — while its body costs nothing until it fires.

Ranked by safety:

1. **Duplicated procedure** → cut to a pointer. Check first that a skill really covers it:
   `grep -l "<distinctive phrase>" <skills dir>/*/SKILL.md`
2. **Procedure with no trigger ambiguity** → move to a skill, leave the trigger + absolutes.
3. **Narrative, history, rationale** → move to a doc, leave the decision.
4. **Prose tightening** → last, smallest, and the only one that risks nothing.

Never relocate: the trigger condition itself, an absolute, or anything whose failure mode
is silent. If losing it would produce no error, it stays in the prompt.

## 6. Score it — before and after, with a tolerance

**Use `probe.py`. `score.py` is the weaker screen and is kept only for a first look.**

```bash
python3 probe.py suite.md before.md after.md
```

A suite is a list of probes, each one thing the file asserts that a reader must be able
to recover. Two classes, deliberately NOT averaged:

- **critical retention, tolerance 0** — ids, channel ids, endpoints, backticked commands
  and exact quoted trigger phrases. These are DATA. Paraphrasing one breaks it outright,
  so a single loss is a fail no matter how good the other number looks. Averaging the two
  classes would let you drop a channel id and still report 98%.
- **prose retention, tolerance 3%** — content-word overlap, stopwords removed.

**Read this before you trust the prose number.** It is a screen, not a verdict: word
overlap cannot tell "dropped the word *glance*" from "dropped the fact that nine days of
ideas were lost". It weights both the same. So it will flag more than is wrong — and
every flagged item still has to be looked at by name.

**Write the suite against the BASELINE, before the rewrite exists.** A suite written
afterwards encodes the rewrite's own wording and scores it high by construction — the
first real run did exactly that, scoring the original 80% and the rewrite 100%, which is
a mirror and not a result. `probe.py` refuses to report when the baseline is below 100%:
if the original fails your suite, the anchors are wrong, not the file.

**A real result.** The same 1,814 -> 1,104 rewrite: **39.1% saved for 0.0pp of rule
recall**, critical 12/12, rules 10/10. PASS. The word-overlap screen had called it 51.3%
and a catastrophe. It was measuring vocabulary, and vocabulary is not the thing you care
about — which is why the earlier claim that "a 3% budget and a 39% cut cannot both be
had" was simply wrong, and was retracted on this measurement.

Verified to discriminate on both classes: dropping the close-check rule takes rules to
90% and critical to 75%; paraphrasing one trigger phrase leaves rules at 100% and drops
critical to 91.7% — prose perfect, data broken, which is exactly why the two numbers are
never averaged.

## 7. Prove the loss is zero

Do not eyeball it. Re-run the step-3 extraction and diff:

```bash
grep -nE '<same pattern>' AGENTS.md | sort > /tmp/rules-after.txt
diff <(cut -d: -f2- /tmp/rules-before.txt) <(cut -d: -f2- /tmp/rules-after.txt)
```

Every removed line must be accounted for by name: relocated to <file>, or deliberately
dropped with a reason. "It felt redundant" is not a reason.

**Normalise before you diff, or the check lies to you.** Run it lowercase, with newlines
collapsed. A real run reported three losses. Two were the check's own bugs: `Never`
missed by a case-sensitive pattern, and `"checkpoint this"` split across a line wrap.
Only one was real. A loss report you have learned to discount is worse than none.

The same applies to any style metric you write here. A sentence-length check counts a
bullet list as one long sentence unless you split on the bullets first. Verify the
checker on known input before you trust its verdict on the file.

```bash
norm() { tr 'A-Z' 'a-z' < "$1" | tr '
' ' ' | tr -s ' '; }
```

<!-- PLATFORM:claude-code -->
## 8. Verify against the INJECTED context, not the file

The file is not the prompt. Run `/context` after the change and compare the component
breakdown against the numbers you took in section 1. A file that shrank while the total
did not means the saving went somewhere else — usually a tool schema that grew.

Check the MCP tool payload specifically. It is machine-generated, nobody reviews it, and
in a measured case one server was **79% of a 65-tool payload**. Removing a server you do
not use beats any amount of prose editing.
<!-- /PLATFORM -->

## 9. Leave a guard, or it comes back

Compaction without a check is a dated fix: the next three additions undo it silently.
Assert the budget somewhere that runs on its own — a test, or the nightly scan — so
exceeding it fails loudly instead of deleting behaviour.

## Look at the tools first

Before compacting prose at all, measure the tool schemas. They are usually the larger
half and nobody writes them: one MCP server was 79% of a 65-tool payload — 66,676 bytes,
~16.6k tokens on every turn of every agent. Scoping it to the one agent that needed it
saved 9x what rewriting the whole of AGENTS.md could have. Cheap tokens are in the
schema, expensive ones are in the rules.
