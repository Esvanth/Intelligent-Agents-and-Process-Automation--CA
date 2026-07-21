"""Pydantic schemas for structured LLM output."""
from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict


class CriterionScore(BaseModel):
    name: str
    score: int = Field(ge=0, le=10)
    evidence: str


class CandidateScore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_name: str
    overall_score: int = Field(ge=0, le=100)
    criteria: List[CriterionScore]
    strengths: List[str]
    gaps: List[str]
    recommendation: Literal["invite_to_interview", "reject", "hold"]
    rationale: str
