"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


# ─── Employee ─────────────────────────────────────────────────────────────────

class SkillItem(BaseModel):
    name: str
    proficiency: int
    verified: bool = False


class EmployeeOut(BaseModel):
    id: int
    name: str
    department: str
    role: str
    availability_hours_per_week: int
    allocated_hours: int
    spare_hours: int
    skills: List[Dict[str, Any]]
    interests: List[str]

    class Config:
        from_attributes = True


# ─── Project ──────────────────────────────────────────────────────────────────

class ProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    deadline_days: int
    priority: int
    required_skills: List[Dict[str, Any]]
    status: str

    class Config:
        from_attributes = True


# ─── Skill Gap ────────────────────────────────────────────────────────────────

class SkillGapOut(BaseModel):
    skill_name: str
    required_proficiency: int
    required_headcount: int
    available_headcount: int
    gap_severity: str
    coverage_pct: float
    recommendation: str
    qualified_employees: List[Dict]
    available_employees: List[Dict]


class GapDetectionResponse(BaseModel):
    project_id: int
    project_name: str
    gaps: List[SkillGapOut]
    overall_coverage_pct: float
    critical_count: int
    moderate_count: int


# ─── Learning Path ────────────────────────────────────────────────────────────

class LearningPathRequest(BaseModel):
    employee_id: int
    skill_name: str
    target_proficiency: int
    project_deadline_days: int = 30


class LearningModuleOut(BaseModel):
    order: int
    title: str
    type: str
    duration_hours: float
    prerequisite: str


class LearningPathResponse(BaseModel):
    employee_name: str
    skill_name: str
    current_level: int
    target_level: int
    modules: List[LearningModuleOut]
    estimated_days: float
    feasible_in_days: int
    explanation: str


# ─── Allocation ───────────────────────────────────────────────────────────────

class AllocationResponse(BaseModel):
    assignments: List[Dict]
    project_coverage: Dict[str, float]
    overall_score: float
    baseline_score: float
    improvement_pct: float
    unmet_gaps: List[str]
    solver_used: str


class SimulateDeadlineRequest(BaseModel):
    deadline_changes: Dict[str, int]   # {"1": 7, "3": 20}  project_id → new days


# ─── Skill Inference ──────────────────────────────────────────────────────────

class InferSkillsRequest(BaseModel):
    text: str


class InferSkillsResponse(BaseModel):
    inferred_skills: List[Dict[str, Any]]


# ─── Audit ────────────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: int
    endpoint: str
    method: str
    user_role: str
    request_summary: Optional[str]
    response_status: Optional[int]
    timestamp: datetime

    class Config:
        from_attributes = True
