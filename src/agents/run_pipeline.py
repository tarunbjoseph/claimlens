"""Run the two-pass extraction pipeline over every fixture in data/fixtures/,
save each result, and log the per-field null rate across the batch — the
Week 3 eval harness's starting input.

Usage:
    python -m src.agents.run_pipeline
"""

from __future__ import annotations

import asyncio
import json
from collections import Counter
from pathlib import Path

from src.agents.arithmetic_validator import validate_arithmetic
from src.agents.extractor import run_extraction

REPO_ROOT = Path(__file__).parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"
OUT_DIR = REPO_ROOT / "data" / "extractions"

NULLABLE_FIELDS = [
    "claim_type",
    "policy_id",
    "claimant_name",
    "incident_date",
    "date_reported",
    "incident_description",
    "line_items",
    "claimed_amount_stated",
]

CONCURRENCY = 4


async def process_one(pdf_path: Path, semaphore: asyncio.Semaphore) -> dict:
    claim_id = pdf_path.stem
    async with semaphore:
        try:
            classification, extraction = await run_extraction(pdf_path)
        except Exception as exc:  # noqa: BLE001 — batch run must not die on one fixture
            return {"claim_id": claim_id, "error": str(exc)}

    arithmetic = validate_arithmetic(extraction)
    result = {
        "claim_id": claim_id,
        "classification": classification.model_dump(),
        "extraction": extraction.model_dump(),
        "arithmetic": arithmetic,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{claim_id}.json").write_text(json.dumps(result, indent=2))
    return result


async def main() -> None:
    pdf_paths = sorted(FIXTURES_DIR.glob("*.pdf"))
    semaphore = asyncio.Semaphore(CONCURRENCY)
    results = await asyncio.gather(*(process_one(p, semaphore) for p in pdf_paths))

    errors = [r for r in results if "error" in r]
    ok = [r for r in results if "error" not in r]

    null_counts: Counter[str] = Counter()
    for r in ok:
        for field in NULLABLE_FIELDS:
            if r["extraction"].get(field) is None:
                null_counts[field] += 1

    print(f"Processed {len(results)} fixtures: {len(ok)} ok, {len(errors)} errors")
    for e in errors:
        print(f"  ERROR {e['claim_id']}: {e['error']}")

    print("\nPer-field null rate:")
    null_rates: dict[str, float] = {}
    for field in NULLABLE_FIELDS:
        rate = null_counts[field] / len(ok) if ok else 0.0
        null_rates[field] = rate
        print(f"  {field:24s} {null_counts[field]:3d}/{len(ok)}  ({rate:.0%})")

    mismatches = [r for r in ok if r["arithmetic"].get("arithmetic_mismatch")]
    print(f"\nArithmetic mismatches flagged: {len(mismatches)}")
    for r in mismatches:
        print(f"  {r['claim_id']}")

    summary = {
        "total": len(results),
        "ok": len(ok),
        "errors": len(errors),
        "error_ids": [e["claim_id"] for e in errors],
        "null_rates": null_rates,
        "arithmetic_mismatch_ids": [r["claim_id"] for r in mismatches],
    }
    (OUT_DIR / "_summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
