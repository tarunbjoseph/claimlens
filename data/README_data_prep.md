# ClaimLens data prep — COMPLETE (40/40 fixtures)

Originally scoped for Week 1 Day 1. Finished ahead of schedule, today, so Day 1
tomorrow starts directly on the extraction pipeline instead of fixture generation.

## What's here

```
schema/claim_schema.json         the ground-truth contract everything else targets
fixtures/generate_pdf.py         generator — all 40 scenarios, run to reproduce every PDF+JSON pair
fixtures/additional_scenarios.py the 32 scenarios added beyond the original 8 (imported by generate_pdf.py)
fixtures/validate_fixtures.py    schema + cross-check validator, exits non-zero on failure
fixtures/fixtures_manifest.md    auto-generated table of all 40: type, tier, expected routing, known issues
fixtures/*.pdf, fixtures/*.json  the 40 fixture pairs themselves
```

Drop `schema/` and `fixtures/` straight into your `claimlens` repo at `data/schema/`
and `data/fixtures/` — the paths in the scripts already assume that layout.

## Final distribution (verified, not just targeted)

**20 clean / 15 messy / 5 adversarial — exactly matching Week 1 Day 1's target.**

- Clean: 11 auto, 9 property. Within clean, routing genuinely varies —
  13 fixtures expect `auto_approve`, 7 expect `route_specialist` (property
  damage and higher-value/theft claims route to a specialist queue even when
  the data itself is perfectly clean). This matters for testing the triage
  loop honestly: "clean" should not be a proxy for "always approved."
- Messy: 8 auto, 7 property. Every one expects `clarify`. Missing fields are
  deliberately varied — missing policy_id, missing claimant name, missing
  incident_date, missing date_reported, a vague dollar range instead of a
  number, a description that trails off mid-sentence, a checkbox that
  contradicts the prose next to it, and one claim (`auto_m008`) that
  genuinely straddles both claim types and should classify as ambiguous
  rather than being forced into one.
- Adversarial: 3 auto, 2 property. **Not all five stack every red flag.**
  `auto_x001` stacks all three (contradictory dates + arithmetic mismatch +
  prompt injection) as the obvious/centerpiece case. The other four each
  isolate a single signal — `auto_x002` is contradictory dates *only* on an
  otherwise mundane low-value claim, `prop_x002` is an arithmetic mismatch
  *only*, `auto_x003` is a prompt-injection attempt *only* on a claim where
  literally everything else looks like an easy approval, and `prop_x001`
  tests escalation triggered by an *absence* of verifiable detail rather
  than a detectable contradiction. See `fixtures_manifest.md` for the full
  breakdown.

All 40 passed `validate_fixtures.py` on the first full run: schema-valid,
every PDF has a matching JSON, and every `claimed_amount_computed` correctly
equals the sum of that fixture's own line items (including the ones designed
to disagree with `claimed_amount_stated` on purpose).

## Why ground truth is authored by hand, not extracted after the fact

The eval harness (Week 3) needs an answer key that exists independently of
what any model produces — otherwise "is the extraction correct" has no fixed
reference point. `ground_truth` is written first as a plain dict; `form_text`
is derived from it, sometimes deliberately diverging. The PDF is the *input*
the pipeline will see; the JSON is the *answer* it's graded against.

## Where each piece gets used later in the plan

| This artifact | Used in |
|---|---|
| All 40 PDF fixtures | Week 1 Day 3-4 — extraction pipeline test corpus |
| `validate_fixtures.py` | Already run once today; wire it into Week 2's CI/secret-leak gate step so it runs on every PR |
| `known_issues` tags | Week 3 Day 20-21 — eval harness's per-issue-type scorecard breakdown |
| `resolution_expectation` | Week 1 Day 5 (does the stop_reason loop route correctly?) and Week 3 Day 20-21 (routing-correctness scoring) |
| `auto_x001` (stacked) | Week 3 Day 18-19 hooks-vs-prompt harness — the "obvious" adversarial case |
| `auto_x002`, `prop_x002`, `auto_x003` (isolated signals) | Same harness — these tell you *which specific signal* a prompt-only guardrail fails on, rather than just "guardrails matter in general" |
| `auto_m008` (ambiguous type) | Tests whether the classify step says "uncertain" instead of forcing a guess — directly relevant to C3's "refuses to fabricate" design goal |

## Running it yourself

```bash
cd data/fixtures
python generate_pdf.py       # regenerates all 40 PDF+JSON pairs from scratch
python validate_fixtures.py  # confirms schema validity and internal consistency
```

## Day 1 tomorrow — updated

With fixture generation done, Day 1's actual work shrinks to:
1. Confirm the auth landmine check (`echo $ANTHROPIC_API_KEY` is empty)
2. Copy `data/` into the repo, commit it
3. Move straight into the extraction pipeline (originally Day 3-4) — you're
   effectively a day and a half ahead of the original plan
