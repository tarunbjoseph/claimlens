# ClaimLens — Verified 4-Week Build Plan (v2, corrected)

**One project, all four Nanodegree courses, deployed on GCP, mapped to CCAR-P and the GCP Professional Agentic Architect beta. Genuinely $0 out of pocket.**

---

## Change log — what was wrong before and why this version is different

This plan went through two corrections. Both are recorded here on purpose — the goal is a plan you can trust, not one that reads clean by hiding the mistakes.

1. **First draft** assumed Claude on Vertex AI Model Garden could be billed to the GCP $300 free-trial credit. **Wrong.** Google's own docs classify Claude as a "model as a service" (MaaS) partner model, and the free-trial terms explicitly exclude MaaS generative-AI partner models from the $300 credit. Verified directly against `cloud.google.com/vertex-ai/generative-ai/docs/partner-models` and the free-trial terms you supplied.

2. **Second draft** proposed working around that by running the Agent SDK in a Cloud Run Job authenticated with a `claude setup-token` OAuth token from your Pro subscription. **Risky, not confirmed safe.** Anthropic's Legal & Compliance page states OAuth tokens from Free/Pro/Max accounts are not permitted "in any other product, tool, or service — including the Agent SDK" outside Claude Code and Claude.ai. This exact question (subscription auth for programmatic/deployed use) has flipped four times in 2026 — banned, reinstated with a credit, credit paused, clarified again. It is not settled enough to build a certification portfolio piece on.

**This version (v2) avoids both problems by construction:** every live Claude call happens inside Claude Code itself, on a machine you are personally logged into. GCP hosts only the pieces that never touch a Claude model. No MaaS conflict (no Claude inference on GCP at all) and no OAuth-boundary question (Claude Code is the one context every version of the policy agrees is fine).

---

## 1. Architecture (verified)

```
   YOUR MACHINE (or a self-hosted GitHub Actions runner on it)
   ┌──────────────────────────────────────────────────────┐
   │  Claude Code / claude -p — your own subscription login│
   │                                                        │
   │   ORCHESTRATOR (Agent SDK, local process)              │
   │   ├─ stop_reason loop: clarify / route / escalate      │
   │   ├─ context manager (prune / compress / pin)          │
   │   ├─ PreToolUse + PostToolUse hooks (hard limits)       │
   │   ├─► extractor subagent                                │
   │   ├─► validator subagent                                │
   │   └─► risk-scorer subagent                               │
   └───────┬─────────────────────────────┬────────────────┘
           │ MCP (HTTP)                  │ writes results
           ▼                              ▼
   ┌───────────────────┐        ┌──────────────────────┐
   │ Cloud Run:        │        │ Firestore             │
   │ policy-mcp        │        │  ├ cases              │
   │ (no Claude calls, │        │  ├ audit_log (append) │
   │  serves tool data)│        │  └ agent_state         │
   └───────────────────┘        └──────────────────────┘
                                          │
                                          ▼
                          ┌───────────────────────────────┐
                          │ Cloud Run: claimlens-dashboard │
                          │ (reads Firestore/BigQuery only,│
                          │  zero Claude calls, public URL)│
                          └───────────────────────────────┘
                                          ▲
                          ┌───────────────────────────────┐
                          │ BigQuery: eval_runs,            │
                          │ Cloud Logging + Trace            │
                          └───────────────────────────────┘
```

**GCP-hosted (billed to $300 free trial — confirmed clean, no MaaS involvement):**
Cloud Run (`policy-mcp` + `claimlens-dashboard`), Firestore, Cloud Storage, Artifact Registry, BigQuery, Cloud Logging/Trace, Secret Manager.

**Locally-hosted (billed to Claude Code Pro subscription — the unambiguous, always-permitted context):**
Every orchestrator/subagent call, every extraction, every eval run.

**Trigger for periodic runs:** a cron entry / Task Scheduler job on your machine, or a GitHub Actions workflow using a **self-hosted runner** you register to your own hardware — the job still executes under your own Claude Code login either way.

---

## 2. Cost reality — two options, stated plainly

### Option A — recommended, $0 (this plan is built around it)
Everything above. No Anthropic Console signup needed. No Vertex model request needed. Only cost is whatever GCP usage exceeds the free trial for the hosted pieces, which is very unlikely at this scale (Cloud Run scale-to-zero, Firestore/BigQuery free tier).

### Option B — optional fallback, small real cost
If at some point you want the pipeline fully cloud-native with no dependency on your own machine being on, swap only the orchestrator to a real Anthropic Console API key (pay-as-you-go), deployed as a genuine Cloud Run Job. This is unambiguously compliant — API-key billing is explicitly the recommended path for any automated/production use — but it costs real money.

**Verified current pricing** (as of today; Anthropic's pricing page is the source of truth going forward):
- Haiku 4.5: $1 / $5 per million input/output tokens
- Sonnet 5: $2 / $10 through Aug 31, 2026; standard $3 / $15 from Sept 1, 2026 onward

For a 4-week build with a 25-case eval suite, using Haiku for dev iteration and Sonnet for final runs, a realistic estimate is **$15–40 total**. New Anthropic Console accounts also get a small signup credit that offsets part of this. This plan does not require Option B — it's here so the choice is informed, not because you need it.

---

## 3. Today — prerequisites checklist

Nothing here waits on external approval. You can finish this today and start Day 1 tomorrow.

### GCP (30–40 min)
- [ ] Sign up at `cloud.google.com/free`, activate the $300 / 90-day trial
- [ ] Create a dedicated project (e.g. `claimlens-prod`)
- [ ] **Billing → Budgets & alerts → new budget, $25 threshold, email notification** — set this before anything else, as a safety net even though the architecture shouldn't need it
- [ ] Install `gcloud` CLI → `gcloud init` → `gcloud auth application-default login` → `gcloud config set project claimlens-prod`
- [ ] Enable only the APIs this architecture actually needs (no Vertex AI needed):
```
gcloud services enable run.googleapis.com \
  firestore.googleapis.com storage.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com cloudtrace.googleapis.com \
  logging.googleapis.com bigquery.googleapis.com
```
- [ ] `gcloud services list --enabled` to confirm all seven show as active

### Local tooling (20–30 min)
- [ ] Python 3.11+ confirmed (`python3 --version`)
- [ ] `uv` installed (or plain `venv`)
- [ ] Node.js 18+ confirmed (`node --version`)
- [ ] Claude Code updated to a recent version: `npm i -g @anthropic-ai/claude-code`, then `claude --version`
- [ ] Confirm you're logged into Claude Code with your Pro account (not an API key): run `claude`, check `/status`
- [ ] **Auth landmine check:** `echo $ANTHROPIC_API_KEY` — if anything prints, `unset` it and remove it from your shell profile. An exported key silently overrides your subscription login and switches you to pay-per-token billing without warning. Re-run this check any time something looks off.
- [ ] Docker installed

### Repo (10 min)
- [ ] New public GitHub repo `claimlens`
- [ ] Clone locally, create skeleton: `src/agents/ src/mcp/ src/schemas/ evals/ data/fixtures/ .claude/ docs/`
- [ ] Commit the empty structure

### Python environment (10 min)
```
uv venv && source .venv/bin/activate
uv pip install claude-agent-sdk fastmcp pydantic \
  fastapi uvicorn google-cloud-firestore google-cloud-storage \
  opentelemetry-sdk opentelemetry-exporter-gcp-trace pytest
```
Note: no `anthropic[vertex]` package needed in this version — the orchestrator talks to Claude only through Claude Code's own Agent SDK path, never through a Vertex or direct-API client.

### Data prep (45–60 min) — doesn't depend on anything above, can run in parallel
- [ ] Draft your ground-truth JSON schema by hand: required fields (claimant, policy_id, incident_date, claimed_amount, description, supporting_docs) and which are nullable
- [ ] Draft 5–8 realistic claim scenarios in plain text/markdown (name, policy number, incident description, claimed amount, dates) — you'll turn these into PDFs with Claude Code on Day 1
- [ ] Deliberately include: one with missing fields, one with arithmetic that doesn't add up, one with contradictory dates

### What's different from the earlier checklist
- No Vertex AI Model Garden request (was a 24–48 hr wait — gone entirely)
- No Anthropic Console signup (only needed for optional Option B)
- No `anthropic[vertex]` package
- One fewer GCP API enabled (no `aiplatform.googleapis.com`)

---

## 4. Syllabus mapping (unchanged from earlier plan — this part wasn't affected by the correction)

| Nanodegree lesson | ClaimLens component |
|---|---|
| C1 L3 — Model selection | Haiku for classification, Sonnet for extraction/reasoning; documented cost table |
| C1 L8 — Claims intake, stop_reason loop | The core triage loop — clarify / route / escalate |
| C1 L9 — Long-conversation context strategy | Case-facts block + tool-output pruning + compression on token budget |
| C1 L11–L14 — Claude Code config, Skills, monorepo | `CLAUDE.md` hierarchy, `/review` command, custom Skills, 35-test validator |
| C1 L15 — Multi-shift orchestration, tiered state | Locally-triggered periodic re-scoring w/ hot/warm/cold state + resume-vs-fresh recovery |
| C2 L6–L7 — Build & integrate MCP servers | `policy-mcp`: policy lookup, claims history, fraud signals |
| C2 L8 — Tool descriptions, tool_choice policy | Differentiated tool descriptions + built-in-vs-custom selection framework |
| C2 L11 — MCP governance, audited loop | Scoped config registry, secret-leak CI gate, append-only audit trail |
| C3 L2–L4 — Structured outputs, resilient extraction | Schema that refuses to fabricate; two-pass classify-then-extract; arithmetic validator |
| C3 L5–L6 — Agent evaluation | 25-case eval harness w/ trace, step and trajectory scoring |
| C3 L7 — Validated routed pipeline | Retry-the-fixable / escalate-the-unfixable; batch path; independent reviewer |
| C3 L8 — Multi-source synthesis | Fusing disagreeing signals (policy vs. history vs. fraud) with provenance |
| C4 L3–L4 — Hub-and-spoke multi-agent | Orchestrator + extractor/validator/risk subagents, Pydantic handoffs |
| C4 L5 — Deterministic hooks | PreToolUse hook hard-blocking auto-approval above payout threshold + comparison harness |

---

## 5. Day-by-day plan

### WEEK 1 — Harness foundation + extraction core

**Day 1**
- Confirm auth (auth landmine check), generate synthetic claim PDFs + ground-truth JSON via Claude Code from your drafted scenarios (aim for 40: 20 clean, 15 messy, 5 adversarial)
- **DoD:** `data/fixtures/` has 40 PDF+JSON pairs; a script validates every JSON against your schema.

**Day 2 — Claude Code configuration**
- Modular `CLAUDE.md` hierarchy with `@import` standards; path-scoped rules
- Two custom Skills (e.g. `claim-schema-author`, `eval-case-writer`); a read-only `/review` command
- **DoD:** a fresh Claude Code session picks up your standards unprompted; `/review` runs and writes nothing.

**Day 3–4 — Extraction pipeline (C3 L4)**
- JSON Schema designed to refuse to fabricate — nullable fields, explicit `"unresolved"` states
- Two-pass: classify (Haiku, forced tool choice) → extract (Sonnet, `any` tool choice)
- Arithmetic validator catching silently "corrected" totals
- **DoD:** run over all 40 fixtures; log per-field null rate for Week 3.

**Day 5 — stop_reason triage loop (C1 L8)**
- The model decides: clarify / auto-approve / route / escalate — no hardcoded if/else doing the deciding
- **DoD:** ambiguous claim → clarifying question; clean claim → approval.

**Day 6–7 — Context strategy (C1 L9) + wrap**
- Persistent case-facts block, tool-output pruning, compression on a token budget
- Measure tokens before/after on a 30-turn simulated case; README table
- Tag `v0.1`

*Cert study (3 hrs): CCAR-F Domain 1 — Agentic Architecture & Orchestration.*

---

### WEEK 2 — MCP layer + governance

**Day 8–9 — Build `policy-mcp` (C2 L6)**
- FastMCP server: tools (`policy_lookup`, `claims_history`, `fraud_signals`), one resource (claim schema), two prompts
- Backed by Firestore seed data
- **DoD:** MCP Inspector connects; every primitive responds standalone.

**Day 10 — Integrate with orchestrator (C2 L7)**
- **DoD:** triage loop enriches a claim with policy + history before deciding; tool calls visible in transcript.

**Day 11 — Tool design discipline (C2 L8)**
- Differentiated descriptions, written `tool_choice` policy, built-in-vs-custom decision doc
- **DoD:** `docs/tool-policy.md` exists; 10-case tool-selection test passes 10/10.

**Day 12–13 — MCP governance (C2 L11)**
- Scoped config registry, secret-leak CI gate, append-only audit trail in Firestore (enforce immutability in Firestore rules, not just code)
- **DoD:** scope violation → denied and logged; fake key commit → CI fails.

**Day 14 — deploy `policy-mcp` to Cloud Run + wrap**
- This is your first genuinely GCP-hosted piece — deploy it now, confirm the local orchestrator can reach it over HTTP
- **DoD:** end-to-end local run: PDF in → extracted → enriched via Cloud Run-hosted MCP → triaged → audited. Tag `v0.2`.

*Cert study (3 hrs): CCAR-F tool & MCP design domain. GCP: register for the Agentic Architect beta (opens Sept 3), start the Google Skills learning path.*

---

### WEEK 3 — Multi-agent orchestration, guardrails, evaluation

**Day 15–16 — Hub-and-spoke multi-agent (C4 L3–L4)**
- Orchestrator + three scoped subagents (extractor, validator, risk-scorer); Pydantic-validated handoffs; bounded refinement loop
- **DoD:** malformed handoff raises a validation error; refinement loop terminates on a bound.

**Day 17 — Multi-source synthesis (C3 L8)**
- Fuse disagreeing signals with provenance; escalate on explicit criteria; keep running when a source fails
- **DoD:** kill `fraud_signals` mid-run — degraded-but-honest output, not a crash or silent omission.

**Day 18–19 — Deterministic hooks (C4 L5) — the centrepiece**
- `PreToolUse` hook hard-blocking auto-approval above a payout threshold; `PostToolUse` normalising tool output; a prerequisite gate
- **Comparison harness:** 20 adversarial cases, prompt-only guardrail vs. deterministic hooks
- **DoD:** results table showing prompt-only leaks violations, hooks block 100%.

**Day 20–21 — Evaluation harness (C3 L5–L6)**
- 25 test cases across happy path / messy / adversarial / degraded-source; score task completion, extraction accuracy, tool-use correctness, routing correctness, latency, cost
- Write results to BigQuery (this is the first thing you push from your local machine to a GCP data store for the dashboard to read)
- **DoD:** `pytest evals/` emits a scorecard. Tag `v0.3`.

*Cert study (3 hrs): CCAR-F context management + safety domains; timed mock exam.*

---

### WEEK 4 — Deploy the dashboard, observe, document, ship

**Day 22 — `claimlens-dashboard` (Cloud Run Service, no Claude calls)**
- Reads Firestore (cases, audit log) and BigQuery (eval scorecard) — displays them
- Service account: Firestore Viewer + BigQuery Data Viewer only — nothing more
- **DoD:** a public URL shows real triage decisions and the eval scorecard from your local runs.

**Day 23 — Observability**
- Structured local logging with case IDs; push summary metrics to Cloud Logging/Trace from your local process
- A Cloud Monitoring dashboard: decisions by route, escalation rate, hook-block count
- **DoD:** trace a single claim from upload to decision end to end.

**Day 24 — Scheduled operations (C1 L15) — the local version**
- Set up a cron entry (or GitHub Actions self-hosted runner registered to your machine) that periodically re-runs the local worker against open/updated cases
- Tiered hot/warm/cold state with atomic writes; fsync'd manifest; resume-vs-fresh recovery rule
- **DoD:** kill the job mid-run; on restart it resumes rather than redoing work or losing it.

**Day 25 — CI/CD**
- GitHub Actions: lint → unit tests → secret-leak gate (GitHub-hosted runner, no Claude involved) → build & deploy `policy-mcp` and `claimlens-dashboard` to Cloud Run
- Eval suite step runs on a **self-hosted runner** (your machine) since it needs live Claude calls; posts the scorecard delta as a PR comment
- **DoD:** a PR that degrades extraction accuracy is visibly flagged before merge.

**Day 26–28 — Portfolio artifacts**
1. **`README.md`** — architecture diagram, demo GIF, run instructions, cost table (including the $0-vs-Option-B tradeoff, stated honestly)
2. **`docs/decisions.md`** — ADR log: why Haiku for classification, why hub-and-spoke, why hooks over prompts, **why the local-Claude-Code / GCP-dashboard split instead of a single cloud service** — this last one is a genuinely good architecture decision to defend for CCAR-P
3. **`docs/evaluation.md`** — scorecard, prompt-vs-hooks comparison table, known failure modes
4. **`docs/governance.md`** — audit model, scope registry, least-privilege IAM, and an explicit note on the auth-boundary reasoning behind the architecture
- **DoD:** a stranger can clone, understand every architectural choice — including the constraint-driven ones — without asking you a question. Tag `v1.0`.

*Cert study (3 hrs): GCP labs in Google Skills; CCAR-F mock exam retake.*

---

## 6. Certification mapping (unaffected by the correction)

### CCAR-P
120 minutes, MCQ/MRQ, pass at 720/1000, Pearson VUE, $175, valid 12 months. Seven domains: architecture & orchestration, integration, governance & risk, lifecycle, stakeholder communication, developer enablement, plus the Foundations core.

| CCAR-P theme | ClaimLens evidence |
|---|---|
| Agentic architecture & orchestration | Hub-and-spoke, scoped subagents, bounded refinement loop |
| Integration | MCP server, tool policy, Cloud Run, Firestore |
| Governance & risk | Audit trail, scope registry, deterministic hooks, least-privilege IAM |
| Lifecycle | CI/CD, eval-on-PR, scheduled re-scoring, recovery semantics |
| Stakeholder communication | `docs/decisions.md`, `docs/governance.md` — including the auth-constraint reasoning |
| Developer enablement | `CLAUDE.md` hierarchy, custom Skills, `/review`, validator |

Sequence: CCAR-F ($125) around Week 4 → CCAR-P ($175) a few weeks later. Free CCAR-F prep: claudecertificationguide.com (30 lessons, 250+ questions, mock exam).

### GCP Professional Agentic Architect (beta)
**Registration opens 3 September 2026.** ~80 MCQ, 3 hours, Pearson-proctored, $120 (beta price), no prerequisites, plus mandatory hands-on labs in Google Skills — both are required to earn the credential.

| Exam capability | ClaimLens evidence | Gap? |
|---|---|---|
| Build agents using low-code tools | — | Yes — see §7, Project 2 |
| Use coding agents for app development | Entire project built with Claude Code | Covered |
| Develop custom agents | Orchestrator + subagents + MCP | Covered |
| Evaluate and deploy agentic workflows | Eval harness, BigQuery scorecards, Cloud Run CI/CD | Covered |
| Secure and govern agentic workflows | Hooks, audit trail, IAM, Secret Manager, scope registry | Covered |

Total exam spend across both certs: **$125 + $175 + $120 = $420.** Everything else in this plan is $0.

---

## 7. After v1 — scaling to future projects

- **Project 2 — "SupplyLens"**: closes the GCP low-code gap — built with Google's Agent Development Kit on Vertex AI Agent Engine, one agent authored in a low-code builder
- **Project 3 — "RepoWarden"**: the Nanodegree's C4 capstone — enterprise multi-agent code-review orchestrator, reuses your orchestrator/hooks/eval harness
- **Project 4**: cross-model benchmark, Claude vs. Gemini on identical eval cases (this one legitimately can use Vertex, since it's explicitly a model comparison, not a way to dodge Claude billing — though note it would need Option B or a Vertex-billed path either way, since MaaS exclusion still applies)

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| `ANTHROPIC_API_KEY` silently present, overrides subscription | Landmine check on Day 1 and whenever something looks off |
| Local machine is off when a scheduled run should happen | Acceptable for a portfolio project; note this limitation honestly in the README rather than hiding it |
| Anthropic further restricts Claude Code's own headless/`-p` usage | This plan doesn't depend on any contested interpretation — Claude Code itself is the one context that's stayed permitted throughout 2026's policy churn |
| GCP beta seats fill | Register 3 September |
| Week 3 overruns (densest week) | Hooks + comparison harness are non-negotiable; multi-source synthesis (Day 17) is first to cut |
| Scope creep into a live public "type your own claim" demo | Explicitly out of scope for v1 — that would mean third-party input driving billed inference through personal auth, the exact pattern this architecture avoids |
