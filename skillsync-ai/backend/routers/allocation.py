"""
Allocation router — optimizer + learning path + deadline simulation
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db
from backend import models
from backend.schemas import (
    AllocationResponse,
    LearningPathRequest, LearningPathResponse, LearningModuleOut,
    SimulateDeadlineRequest,
)
from backend.engine.optimizer import run_allocation
from backend.engine.learning_path import generate_path

router = APIRouter(tags=["Allocation"])


# ─── Learning Path ────────────────────────────────────────────────────────────

@router.post("/learning-path", response_model=LearningPathResponse)
def get_learning_path(body: LearningPathRequest, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == body.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Find current level for the requested skill
    current_level = 1
    for s in (emp.skills or []):
        if s["name"].lower() == body.skill_name.lower():
            current_level = s["proficiency"]
            break

    if current_level >= body.target_proficiency:
        return LearningPathResponse(
            employee_name=emp.name,
            skill_name=body.skill_name,
            current_level=current_level,
            target_level=body.target_proficiency,
            modules=[],
            estimated_days=0.0,
            feasible_in_days=0,
            explanation=(
                f"{emp.name} already meets '{body.skill_name}' at level {current_level} "
                f"(target: {body.target_proficiency}). No upskilling required."
            ),
        )

    path = generate_path(
        employee_name=emp.name,
        skill_name=body.skill_name,
        current_level=current_level,
        target_level=body.target_proficiency,
        project_deadline_days=body.project_deadline_days,
    )

    # Persist to DB
    db_path = models.LearningPath(
        employee_id=emp.id,
        skill_name=body.skill_name,
        current_level=current_level,
        target_level=body.target_proficiency,
        modules=[
            {
                "order": m.order,
                "title": m.title,
                "type": m.type,
                "duration_hours": m.duration_hours,
                "prerequisite": m.prerequisite,
            }
            for m in path.modules
        ],
        estimated_days=path.estimated_days,
        explanation=path.explanation,
    )
    db.add(db_path)
    db.commit()

    return LearningPathResponse(
        employee_name=emp.name,
        skill_name=body.skill_name,
        current_level=current_level,
        target_level=body.target_proficiency,
        modules=[
            LearningModuleOut(
                order=m.order,
                title=m.title,
                type=m.type,
                duration_hours=m.duration_hours,
                prerequisite=m.prerequisite,
            )
            for m in path.modules
        ],
        estimated_days=path.estimated_days,
        feasible_in_days=path.feasible_in_days,
        explanation=path.explanation,
    )


# ─── Allocation ───────────────────────────────────────────────────────────────

@router.post("/allocate", response_model=AllocationResponse)
def allocate(db: Session = Depends(get_db)):
    employees = db.query(models.Employee).all()
    projects  = db.query(models.Project).all()

    result = run_allocation(employees, projects)

    # Persist allocations
    db.query(models.Allocation).filter(
        models.Allocation.allocation_type == "optimized"
    ).delete()
    for a in result.assignments:
        db.add(models.Allocation(
            employee_id=a.employee_id,
            project_id=a.project_id,
            assigned_hours=a.assigned_hours,
            skill_match_score=a.skill_match_score,
            rationale=a.rationale,
            allocation_type="optimized",
        ))
    db.commit()

    return _to_allocation_response(result)


# ─── Simulate Deadline Change ─────────────────────────────────────────────────

@router.post("/simulate/deadline-change", response_model=AllocationResponse)
def simulate_deadline_change(body: SimulateDeadlineRequest, db: Session = Depends(get_db)):
    employees = db.query(models.Employee).all()
    projects  = db.query(models.Project).all()

    deadline_override = {int(k): v for k, v in body.deadline_changes.items()}
    result = run_allocation(employees, projects, deadline_override=deadline_override, allocation_type="simulated")

    return _to_allocation_response(result)


# ─── Helper ───────────────────────────────────────────────────────────────────

def _to_allocation_response(result) -> AllocationResponse:
    return AllocationResponse(
        assignments=[
            {
                "employee_id":       a.employee_id,
                "employee_name":     a.employee_name,
                "project_id":        a.project_id,
                "project_name":      a.project_name,
                "assigned_hours":    a.assigned_hours,
                "skill_match_score": a.skill_match_score,
                "rationale":         a.rationale,
            }
            for a in result.assignments
        ],
        project_coverage={str(k): v for k, v in result.project_coverage.items()},
        overall_score=result.overall_score,
        baseline_score=result.baseline_score,
        improvement_pct=result.improvement_pct,
        unmet_gaps=result.unmet_gaps,
        solver_used=result.solver_used,
    )
