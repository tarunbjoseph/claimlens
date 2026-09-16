"""Pydantic models for the extraction pipeline's structured output.

Mirrors data/schema/claim_schema.json's extraction-relevant fields, with two
deliberate omissions:

- claim_id: never printed on the claim form itself (it's fixture
  bookkeeping), so a real extraction pipeline has nothing to extract it
  from.
- claimed_amount_computed: the arithmetic validator derives this from the
  model's own extracted line_items in code, after the fact. Asking the
  model to produce it would blur the line the validator exists to check —
  whether the model faithfully transcribes claimed_amount_stated or
  silently "corrects" it to match its own arithmetic.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

ClaimType = Literal["auto", "property"]


class LineItem(BaseModel):
    description: str
    amount: float


class SupportingDocuments(BaseModel):
    police_report: bool = False
    photos: bool = False
    receipts: bool = False


class ClassificationResult(BaseModel):
    claim_type: Optional[ClaimType] = Field(
        default=None,
        description=(
            "Null only if the form itself never states a type clearly "
            "enough to classify — do not guess."
        ),
    )


class ExtractedClaim(BaseModel):
    claim_type: Optional[ClaimType] = None
    policy_id: Optional[str] = None
    claimant_name: Optional[str] = None
    incident_date: Optional[str] = Field(
        default=None, description="ISO 8601 date, or null if not stated / illegible"
    )
    date_reported: Optional[str] = Field(
        default=None, description="ISO 8601 date, or null if not stated"
    )
    incident_description: Optional[str] = None
    line_items: Optional[list[LineItem]] = Field(
        default=None, description="Null if the form gives no itemized breakdown at all"
    )
    claimed_amount_stated: Optional[float] = Field(
        default=None,
        description=(
            "The total exactly as written on the form — extract verbatim, "
            "do not correct it to match the line items."
        ),
    )
    supporting_documents: SupportingDocuments = Field(default_factory=SupportingDocuments)
