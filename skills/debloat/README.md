# debloat

A measured simplification pass on a codebase. Lines of code are the proxy; the goal is a
system that is simpler and still correct.

The skill sets up a worktree, a single line counter used at both ends, and a green test
baseline before anything is cut. Then it works safest-first:

1. dead code, confirmed by grep (including systemd units and timers outside the repo);
2. placeholder subsystems and misplaced scaffolding;
3. real duplication only;
4. a census of state machines: declared, implicit, and bypassed;
5. a whole-tree comment pass, proven comment-only by `scripts/comment_verify.py`, with
   every record ID kept.

It stops with numbers when only restructuring or scope cuts are left. Trimming comments,
packing lines and reformatting are refused as ways to move the count.

**Scripts** (Python 3.10+, standard library):

- `scripts/state_machines.py [paths]`: lists declared, implicit and bypassed state machines.
- `scripts/comment_verify.py <repo> <node_modules>`: checks that each file changed against
  HEAD differs only in comments, and lists any record ID it lost. The `node_modules` folder
  must contain `typescript`; it is used for TS/JS files.

Adapted from [goal-sloc](https://github.com/maxim-saplin/goal-sloc) (MIT); see
[NOTICE](NOTICE).
