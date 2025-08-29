"""
app/schema.py
Purpose: Define the **IO contract** for the API and internal pipeline.
What to implement:
- Pydantic models for Evidence, ClaimCard, Report, and VerifyRequest.
Implementation notes:
- Keep enums/strings simple for hackathon speed.
- This file is the single source of truth for the output schema shown to judges.
"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

Label = Literal["hallucination", "supported", "uncertain"]
Status = Literal["pass", "fail", "uncertain"]

class Evidence(BaseModel):
    title: str
    snippet: str
    url: str
    source: Literal["wikipedia", "wikidata"] = "wikipedia"

class ClaimCard(BaseModel):
    text: str
    status: Status
    evidence: Optional[Evidence] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)

class Report(BaseModel):
    label: Label
    probability: float = Field(ge=0.0, le=1.0, default=0.0)
    claims: List[ClaimCard]
    rationale: str

class VerifyRequest(BaseModel):
    prompt: str
    answer: str
