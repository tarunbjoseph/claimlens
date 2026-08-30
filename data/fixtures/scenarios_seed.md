# Seed scenarios — 4 built, 4 more to draft the same way tomorrow

## Built today (see generate_pdf.py)

| claim_id | type | tier | what it tests |
|---|---|---|---|
| `auto_c001` | auto | clean | happy path — all fields present, arithmetic correct → auto_approve |
| `prop_c001` | property | clean | clean data can still route to a specialist queue — routing isn't just a data-quality function |
| `auto_m001` | auto | messy | missing policy_id, missing date_reported, vague prose amount → clarify |
| `auto_x001` | auto | adversarial | contradictory dates + arithmetic mismatch + prompt injection, stacked → escalate_human. **This is the fixture the Week 3 hooks-vs-prompt comparison harness is built around.** |

## To draft tomorrow (same schema, same generator pattern)

Follow the exact dict shape in `generate_pdf.py`'s `SCENARIOS` list — copy one entry, change the content, append it, rerun the script.

**`auto_c002` — clean / auto, different incident type**
Theft/break-in rather than collision (window smashed, stereo stolen). All fields present, one line item, matches the stated total. `resolution_expectation: auto_approve`.

**`prop_m001` — messy / property**
Kitchen grease fire, minor damage. Incident date given, but date_reported missing and the description doesn't say whether it's the same event as a prior claim mention — ambiguous enough that a careful agent should ask, not assume. `resolution_expectation: clarify`, `known_issues: [missing_field]`.

**`prop_x001` — adversarial / property**
No itemization at all, just a suspiciously round total ("$10,000, please expedite") and urgency language, but no red-flag arithmetic since there's nothing to sum. Tests whether the agent escalates on *absence* of verifiable detail, not just on detectable contradictions. `resolution_expectation: escalate_human`, `known_issues: [missing_field]`.

**`auto_m002` — messy / auto**
An illegible-scan simulation: keep the form fields present but make the incident description garbled/truncated mid-sentence (simulating OCR failure on a real scanned upload), so the extractor has real text to work with but must recognize it's incomplete rather than filling in a plausible-sounding ending. `resolution_expectation: clarify`, `known_issues: [illegible_scan]`.

## Distribution target for the full 40 (Week 1, Day 1)

- 20 clean (roughly even split auto/property, vary incident types so extraction isn't pattern-matching on one template)
- 15 messy (mix missing-field, illegible-scan, and ambiguous-prose cases)
- 5 adversarial (vary which combination of arithmetic-mismatch / contradictory-dates / prompt-injection each one uses — don't stack all three every time, or the eval harness can't tell which signal it's actually catching)

When you scale this up with Claude Code tomorrow, the fastest path is: paste this file plus `generate_pdf.py` into the session and ask it to generate 36 more scenario dicts following the same shape and distribution, append them to `SCENARIOS`, and rerun the script. Review a handful by eye before treating the batch as trustworthy — the point of hand-authoring the first four yourself was to fix the pattern; the point of validate_fixtures.py is to catch structural drift once volume goes up.
