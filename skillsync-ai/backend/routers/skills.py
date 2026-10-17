"""
Skills router — gap detection + skill inference
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend import models
from backend.schemas import (
    GapDetectionResponse, SkillGapOut,
    InferSkillsRequest, InferSkillsResponse,
)
from backend.engine.gap_detector import detect_gaps, overall_gap_score, SEVERITY_CRITICAL, SEVERITY_MODERATE
from backend.engine.skill_inference import infer_skills

router = APIRouter(tags=["Skills"])


@router.post("/gaps/detect/{project_id}", response_model=GapDetectionResponse)
def detect_project_gaps(project_id: int, db: Session = Depends(get_db)):
    proj = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    employees = db.query(models.Employee).all()
    gaps = detect_gaps(proj, employees)

    gap_outs = [
        SkillGapOut(
            skill_name=g.skill_name,
            required_proficiency=g.required_proficiency,
            required_headcount=g.required_headcount,
            available_headcount=g.available_headcount,
            gap_severity=g.gap_severity,
            coverage_pct=g.coverage_pct,
            recommendation=g.recommendation,
            qualified_employees=g.qualified_employees,
            available_employees=g.available_employees,
        )
        for g in gaps
    ]

    critical_count = sum(1 for g in gaps if g.gap_severity == SEVERITY_CRITICAL)
    moderate_count = sum(1 for g in gaps if g.gap_severity == SEVERITY_MODERATE)

    # Persist gaps to DB
    db.query(models.SkillGap).filter(models.SkillGap.project_id == project_id).delete()
    for g in gaps:
        db_gap = models.SkillGap(
            project_id=project_id,
            skill_name=g.skill_name,
            required_proficiency=g.required_proficiency,
            required_headcount=g.required_headcount,
            available_headcount=g.available_headcount,
            gap_severity=g.gap_severity,
        )
        db.add(db_gap)
    db.commit()

    return GapDetectionResponse(
        project_id=project_id,
        project_name=proj.name,
        gaps=gap_outs,
        overall_coverage_pct=overall_gap_score(gaps),
        critical_count=critical_count,
        moderate_count=moderate_count,
    )


@router.post("/skills/infer", response_model=InferSkillsResponse)
def infer_employee_skills(body: InferSkillsRequest):
    results = infer_skills(body.text)
    return InferSkillsResponse(
        inferred_skills=[{"skill": name, "confidence": score} for name, score in results]
    )
