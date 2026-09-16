"""Run the Day 5 triage loop over every already-extracted fixture in
data/extractions/, save each decision, and compare against each fixture's
resolution_expectation for an informal scorecard.

This is NOT the Week 3 eval harness — route_to_specialist in particular is
expected to be unreliable here, since it depends on policy context
(policy-mcp) that doesn't exist until Week 2. auto_approve/clarify/
escalate_human are the three decisions this stage is actually accountable
for (see src/agents/triage.py's scope note).

Usage:
    python -m src.agents.run_triage
"""

from __future__ import annotations

import asyncio
import json
from collections import Counter
from pathlib import Path

from src.agents.arithmetic_validator import validate_arithmetic
from src.agents.triage import triage_claim
from src.schemas.claim import ExtractedClaim

REPO_ROOT = Path(__file__).parent.parent.parent
EXTRACTIONS_DIR = REPO_ROOT / "data" / "extractions"
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"
OUT_DIR = REPO_ROOT / "data" / "triage"

CONCURRENCY = 4


async def process_one(extraction_path: Path, semaphore: asyncio.Semaphore) -> dict:
    claim_id = extraction_path.stem
    payload = json.loads(extraction_path.read_text())
    extracted = ExtractedClaim.model_validate(payload["extraction"])
    arithmetic = payload["arithmetic"]

    ground_truth = json.loads((FIXTURES_DIR / f"{claim_id}.json").read_text())
    expected = ground_truth["resolution_expectation"]

    async with semaphore:
        try:
            triage = await triage_claim(extracted, arithmetic)
        except Exception as exc:  # noqa: BLE001 — batch run must not die on one fixture
            return {"claim_id": claim_id, "error": str(exc), "expected": expected}

    result = {
        "claim_id": claim_id,
        "expected": expected,
        "decision": triage["decision"],
        "match": triage["decision"] == expected,
        "tool_name": triage["tool_name"],
        "args": triage["args"],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{claim_id}.json").write_text(json.dumps(result, indent=2))
    return result


async def main() -> None:
    extraction_paths = sorted(p for p in EXTRACTIONS_DIR.glob("*.json") if p.stem != "_summary")
    semaphore = asyncio.Semaphore(CONCURRENCY)
    results = await asyncio.gather(*(process_one(p, semaphore) for p in extraction_paths))

    errors = [r for r in results if "error" in r]
    ok = [r for r in results if "error" not in r]

    print(f"Processed {len(results)} fixtures: {len(ok)} ok, {len(errors)} errors")
    for e in errors:
        print(f"  ERROR {e['claim_id']}: {e['error']}")

    overall_matches = sum(1 for r in ok if r["match"])
    print(f"\nOverall match vs resolution_expectation: {overall_matches}/{len(ok)}")

    by_expected: dict[str, list[dict]] = {}
    for r in ok:
        by_expected.setdefault(r["expected"], []).append(r)

    print("\nBy expected outcome:")
    for expected, rows in sorted(by_expected.items()):
        matches = sum(1 for r in rows if r["match"])
        print(f"  {expected:18s} {matches}/{len(rows)}")
        for r in rows:
            if not r["match"]:
                print(f"      MISMATCH {r['claim_id']}: got {r['decision']!r}")

    decision_counts = Counter(r["decision"] for r in ok)
    print("\nDecision distribution:")
    for decision, count in sorted(decision_counts.items()):
        print(f"  {decision:18s} {count}")

    summary = {
        "total": len(results),
        "ok": len(ok),
        "errors": len(errors),
        "overall_matches": overall_matches,
        "by_expected": {
            expected: {
                "matches": sum(1 for r in rows if r["match"]),
                "total": len(rows),
                "mismatch_ids": [r["claim_id"] for r in rows if not r["match"]],
            }
            for expected, rows in by_expected.items()
        },
    }
    (OUT_DIR / "_summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
