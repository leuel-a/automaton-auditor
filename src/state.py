#!/usr/bin/env python3
from __future__ import annotations

import operator
from langchain.messages import AnyMessage
from typing import Annotated, Dict, List, Literal, Optional, TypedDict, Required

from pydantic import BaseModel, Field

class RubricMetadata(BaseModel):
    name: str = Field()
    grading_target: str = Field()
    version: str = Field()

class Evidence(BaseModel):
    goal: str = Field()
    found: bool = Field(description="Whether the artifact exists")
    content: Optional[str] = Field(default=None)
    location: str = Field(description="File path or commit hash")
    rationale: str = Field(
        description="Your rationale for your confidence on the evidence you find for this particular goal"
    )
    confidence: float


# --- Judge Output ---
class JudicialOpinion(BaseModel):
    judge: Literal["Prosecutor", "Defense", "TechLead"]
    criterion_id: str
    score: int = Field(ge=1, le=5)
    argument: str
    cited_evidence: List[str]


# --- Chief Justice Output ---
class CriterionResult(BaseModel):
    dimension_id: str
    dimension_name: str
    final_score: int = Field(ge=1, le=5)
    judge_opinions: List[JudicialOpinion]
    dissent_summary: Optional[str] = Field(
        default=None,
        description="Required when score variance > 2",
    )
    remediation: str = Field(
        description="Specific file-level instructions " "for improvement",
    )


class AuditReport(BaseModel):
    repo_url: str
    executive_summary: str
    overall_score: float
    criteria: List[CriterionResult]
    remediation_plan: str


# --- Graph State ---
class AgentState(TypedDict, total=False):
    repo_url: Required[str]
    pdf_path: Required[str]

    repo_path: str
    repo_dimensions_prompt: str
    repo_investigator_messages: Annotated[List[AnyMessage], operator.add]

    rubric_meta_data: RubricMetadata
    rubric_dimensions: List[Dict]
    rubric_synthesis_rules: Dict
    evidences: Annotated[
        Dict[str, List[Evidence]], operator.ior
    ]  # Use reducers to prevent parallel agents from overwriting data
    opinions: Annotated[List[JudicialOpinion], operator.add]
    final_report: AuditReport
