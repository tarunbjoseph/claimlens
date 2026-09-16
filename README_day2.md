# ClaimLens Day 2 — Claude Code configuration (drafted, not yet verified)

## What this is

Everything Day 2 originally called for: a modular `CLAUDE.md` hierarchy with
`@import`s, two custom Skills, and a read-only `/review` command. Drafted and
internally checked today; **actual verification needs your Claude Code
session**, which can't run inside this chat's sandbox.

## What's here (drop directly into your `claimlens` repo root)

```
CLAUDE.md                                  root — always loaded, imports the three files below
.claude/rules/data.md                      path-scoped rules for data/
.claude/rules/agents.md                    path-scoped rules for src/
.claude/rules/evals.md                     path-scoped rules for evals/
.claude/skills/claim-schema-author/SKILL.md   model-invoked when working under data/
.claude/skills/eval-case-writer/SKILL.md      model-invoked when working under evals/
.claude/skills/review/SKILL.md                explicit /review — disallowed-tools blocks writes
```

## What I verified here

- All three `SKILL.md` frontmatter blocks parse as valid YAML.
- The three `@import` lines in `CLAUDE.md` sit outside any code fence, so
  they'll actually resolve (an `@import` inside a fenced code block is
  treated as literal text and silently ignored — a common mistake).
- Current Claude Code convention confirmed before drafting: Skills live at
  `.claude/skills/<name>/SKILL.md` (canonical; `.claude/commands/` still
  works as an alias), and a `paths` frontmatter field triggers automatic
  model-invocation when you're working on matching files.
- `/review`'s `disallowed-tools: Write, Edit, NotebookEdit` blocks write
  access at the tool-permission level — the same "enforce in code, not
  prompt wording" principle the project applies to the guardrail hooks
  themselves, applied here to Claude Code's own configuration.

## What only your terminal can verify tomorrow

1. Open a fresh Claude Code session in the repo and ask something that
   should trigger the standards unprompted (e.g. "add a new clean auto
   fixture for a windshield chip claim") — confirm it follows the
   schema-first order from `claim-schema-author` without you restating it.
2. Run `/review` after making a small change and confirm the diff summary
   comes back with **zero file writes** — check `git status` immediately
   after to be sure.
3. Run `/memory` (or your Claude Code version's equivalent) to confirm all
   three `@import`ed rule files actually loaded — this is the one thing
   that's easy to get subtly wrong (path typos, wrong relative base) and
   only shows up at runtime.

If any of the three fail, it's almost always one of: a stray typo in the
`@path`, the repo not being the directory Claude Code was launched from, or
`ANTHROPIC_API_KEY` being set somewhere and silently changing auth context —
worth an `echo $ANTHROPIC_API_KEY` check if anything behaves unexpectedly.

## Updated Day 1 + Day 2 status

Both done today. Tomorrow starts directly on Week 1 Day 3–4: the extraction
pipeline, against the 40 fixtures already sitting in `data/fixtures/`.
