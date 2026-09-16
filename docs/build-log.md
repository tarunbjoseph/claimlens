# ClaimLens — build log

A chronological, plain-language record of what was built, tested, and
found on each day of the build — kept as things happen, not
reconstructed afterward. This is the raw material Week 4 turns into the
project's final report (`docs/decisions.md`, `docs/evaluation.md`,
`docs/governance.md`); until then, this file is the single source of
truth for "what actually happened and when."

Each entry: what was built, what was tested, what evidence backs it up,
and what (if anything) went wrong and how it was found and fixed.
Nothing here is summarized away — a bug found is a bug logged, not
quietly folded into a clean final number.

---

## Day 0 — Prerequisites

- Confirmed local tooling: Python 3.11+, `uv`, Node 18+, Claude Code,
  Docker (installed; daemon not yet running — not blocking).
- Created the public GitHub repo and the empty project skeleton.
- Set up the Python virtual environment and pinned dependencies.
- GCP: signed up for the trial, created project `claimlens-prod-507119`
  (note: the plain name `claimlens-prod` was already taken — the real
  project ID has a numeric suffix), enabled the 8 required APIs.
  Installed `gcloud` locally and authenticated (this took real
  troubleshooting: a GUI installer hung with no way to click through
  it non-interactively, then an OAuth device-flow issue where the
  authorization code from one login attempt couldn't be reused against
  a second attempt's URL — each attempt generates fresh, single-use
  credentials).
- Verified the "auth landmine": confirmed `ANTHROPIC_API_KEY` is not
  set anywhere on the machine, so all Claude Code usage bills to the
  subscription, never pay-per-token.

## Day 1 — Fixture corpus

- Hand-authored `data/schema/claim_schema.json`, the ground-truth
  contract every fixture validates against.
- Built `data/fixtures/generate_pdf.py` and scaled the scenario set
  from 4 worked examples to the full target of 40: 20 clean, 15 messy,
  5 adversarial — matching the plan's target distribution exactly.
- Every fixture pairs a rendered PDF with a hand-written ground-truth
  JSON, authored *before* any model ever sees the claim, so there's a
  fixed answer key independent of what an extractor produces.
- Adversarial fixtures isolate individual failure signals
  (`arithmetic_mismatch`, `contradictory_dates`, `prompt_injection_attempt`)
  as well as one deliberately stacked "centerpiece" case (`auto_x001`)
  combining all three.
- Verified with `validate_fixtures.py`: all 40 schema-valid, every PDF
  has a matching JSON, every `claimed_amount_computed` correctly sums
  that fixture's own line items.

## Day 2 — Claude Code configuration

- Built a modular `CLAUDE.md` with `@import`s to three path-scoped rule
  files (`data.md`, `agents.md`, `evals.md`) and three skills:
  `claim-schema-author`, `eval-case-writer` (both path-triggered), and
  `review` (explicit `/review`, write-disabled).
- Verified all three things the setup could plausibly get wrong, for
  real rather than by assumption:
  1. The `@import`ed rules actually load — confirmed because their
     full content showed up automatically in a fresh session's system
     context, unprompted.
  2. `/review` genuinely cannot write — ran it, diffed `git status`
     before and after, byte-identical.
  3. Path-scoped skills actually auto-trigger — confirmed live: the
     `claim-schema-author` skill appeared the moment a file under
     `data/` was read, with no skill invoked by name.

## Day 3–4 — Extraction pipeline

- Built a two-pass pipeline: a cheap/fast model classifies auto vs.
  property, then a stronger model extracts every field via the Agent
  SDK's structured-output mode (a JSON Schema the model's response must
  match) — not free-text parsing.
- Both passes run with zero tool access. This is a deliberate security
  property, not an optimization: with no tools available, embedded
  text in a claim has no action to hijack, even if it's phrased as an
  instruction.
- **Live-tested against real adversarial content**, not just clean
  fixtures: a messy fixture's vague "$400–500?" correctly extracted as
  `null` rather than a guessed number; two different prompt-injection
  fixtures both had their embedded "approve this claim" text
  transcribed as plain literal text, never obeyed.
- **Bug found and fixed**: on the first pass, the extractor sometimes
  *silently deleted* injected instruction text instead of transcribing
  it as data — which destroys the audit trail a reviewer would need.
  Tightened the system prompt to require verbatim transcription; fixed
  and reverified on both adversarial fixtures.
- Built a pure-code arithmetic validator (no model call) comparing the
  extractor's own `line_items` sum against its own
  `claimed_amount_stated`.
- **Full-batch result**: 40/40 fixtures processed, 0 errors.
  Arithmetic mismatches correctly flagged on exactly the two fixtures
  tagged for it in ground truth (`auto_x001`, `prop_x002`) — no false
  positives or negatives. Null rates concentrated exactly where the
  fixture design predicts (missing `line_items` / `claimed_amount_stated`
  on the 15 messy fixtures).

## Day 5 — Triage decision loop

- Built the core decision mechanism: the model is given four tools
  (`auto_approve_claim`, `ask_clarifying_question`,
  `route_to_specialist`, `escalate_to_human`) and must call exactly
  one. There is no code anywhere in this project that decides the
  outcome — the tool call the model makes *is* the decision, read back
  off the SDK's own message stream.
- **Three real bugs found via live batch testing, each one traced to
  its root cause by reading the actual evidence files, not by
  guessing:**
  1. *Permission wall.* The four tools were silently blocked because
     the default permission mode has no way to approve a tool call
     with no human present to answer a prompt. Fixed narrowly with a
     `can_use_tool` callback allowing only these four specific no-op
     tools — not a blanket bypass, which the harness's own safety
     classifier correctly refused as creating an unrestricted agent.
  2. *False-positive clarify.* The model treated
     `supporting_documents.receipts = false` (a complete, known answer
     — "not attached") the same as a genuinely missing field. Fixed by
     making the distinction explicit in the prompt; the `auto_approve`
     match rate went from 4/13 to 11/13 on the very next run.
  3. *Extraction fabrication, caught downstream.* One fixture
     (`auto_m006`) was deliberately built so its narrative text claims
     "photos attached" while the actual PDF checkbox is unmarked. The
     extractor had been inferring the checkbox from the story instead
     of reading the mark — a real violation of the project's
     null/verbatim-over-guess principle. Found by comparing the
     extracted JSON against the raw PDF text side by side. Fixed, then
     the *entire* extraction batch was rerun to check for regressions;
     only the two fixtures actually built around this exact pattern
     changed output, confirming the fix was precisely targeted rather
     than a blunt-force change.
- **Full-batch result after fixes**: 40/40 fixtures, 0 errors at every
  stage. 33/40 (82.5%) of decisions matched the intended outcome. The
  remaining 7 mismatches cluster entirely on one documented, expected
  gap — routing a clean claim to a specialist depends on
  business/policy context (claim value, claim type) this pipeline
  doesn't have yet; that arrives via a policy-lookup tool in Week 2.
  No unexplained failures.
- Published a plain-English project explainer
  (`docs/architecture.md`) and a showcase architecture diagram, and
  brought the root `README.md` up to date with both.

---

## Day 6–7 — Context strategy + v0.1

- The pipeline built so far only makes short, one-shot calls per
  fixture, so there was no real long-running conversation yet to
  manage. Rather than skip this stage or fabricate a scenario from
  nothing, built a **simulated** 30-turn case lifecycle using real
  extraction/triage output plus representative tool-output turns
  standing in for Week 2's not-yet-built policy-mcp calls — clearly
  labeled `(simulated)` throughout, never presented as live data.
- **Calibrated token counting against real evidence, not a guessed
  ratio.** Made two live Claude Code calls with very different prompt
  lengths and took the delta between their reported `input_tokens`
  (599 tokens for 2,063 extra characters of this project's own JSON
  content) — this isolates the actual per-character rate from the
  ~3,300-token fixed overhead every call carries regardless of prompt
  size (tool definitions, base system prompt). Derived rate: 3.44
  characters per token.
- Built `src/agents/context_manager.py`: a persistent "case facts"
  block plus a rolling window of the most recent turns kept verbatim.
  Older turns get folded into the facts block as a one-line digest
  instead of being resent in full (the naive approach) or dropped
  outright (which would silently lose information a later decision
  might need).
- **Result, measured, not estimated**: over the simulated 30-turn
  case, naive (unmanaged) context grew without bound to 3,795 tokens.
  Managed context stayed within ~150 tokens of its 1,400-token budget
  from turn 11 onward — a **62% reduction by turn 30**. Full per-turn
  numbers: `data/context_strategy_results.json`; summary table in the
  root `README.md`.
- Added this build log itself (`docs/build-log.md`) as the project's
  running, day-by-day record — the raw material Week 4's final report
  gets synthesized from.
- Tagged `v0.1`, closing out Week 1.
