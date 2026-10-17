"""
Skill Gap Detector
Analyzes a project's required skills against the available workforce
and returns a ranked list of gaps with severity scores.
"""
from dataclasses import dataclass
from typing import List, Dict, Any


SEVERITY_CRITICAL = "critical"
SEVERITY_MODERATE = "moderate"
SEVERITY_LOW      = "low"
SEVERITY_OK       = "ok"


@dataclass
class SkillGapResult:
    skill_name: str
    required_proficiency: int
    required_headcount: int
    qualified_employees: List[Dict]       # employees who meet min proficiency
    available_employees: List[Dict]       # qualified AND have spare capacity
    available_headcount: int
    gap_severity: str
    coverage_pct: float                   # 0–100 %
    recommendation: str


def detect_gaps(project: Any, employees: List[Any]) -> List[SkillGapResult]:
    """
    Given a Project ORM object and list of Employee ORM objects,
    return a SkillGapResult for every required skill, sorted by severity.
    """
    results = []

    for req in project.required_skills:
        skill_name      = req["name"]
        min_prof        = req["min_proficiency"]
        needed_headcount = req["headcount"]

        qualified   = []   # proficiency >= min_prof
        available   = []   # qualified + has spare hours

        for emp in employees:
            emp_skill = _find_skill(emp.skills, skill_name)
            if emp_skill and emp_skill["proficiency"] >= min_prof:
                entry = {
                    "id":   emp.id,
                    "name": emp.name,
                    "proficiency": emp_skill["proficiency"],
                    "verified":    emp_skill.get("verified", False),
                    "spare_hours": emp.availability_hours_per_week - emp.allocated_hours,
                }
                qualified.append(entry)
                if entry["spare_hours"] > 5:        # at least 5 hrs/week free
                    available.append(entry)

        avail_count  = len(available)
        coverage_pct = min(100.0, round(avail_count / needed_headcount * 100, 1))

        # Severity rules
        if avail_count == 0 and len(qualified) == 0:
            severity = SEVERITY_CRITICAL
            rec = (
                f"No employee meets '{skill_name}' at proficiency ≥ {min_prof}. "
                f"Upskilling plan required for at least {needed_headcount} employee(s)."
            )
        elif avail_count == 0 and len(qualified) > 0:
            severity = SEVERITY_CRITICAL
            rec = (
                f"{len(qualified)} qualified for '{skill_name}' but all are overloaded. "
                f"Either reduce their current load or upskill available employees."
            )
        elif avail_count < needed_headcount:
            severity = SEVERITY_MODERATE
            rec = (
                f"Only {avail_count}/{needed_headcount} available for '{skill_name}'. "
                f"Consider upskilling {needed_headcount - avail_count} additional employee(s)."
            )
        else:
            severity = SEVERITY_OK
            rec = f"Sufficient coverage for '{skill_name}' ({avail_count} available, {needed_headcount} needed)."

        results.append(SkillGapResult(
            skill_name=skill_name,
            required_proficiency=min_prof,
            required_headcount=needed_headcount,
            qualified_employees=qualified,
            available_employees=available,
            available_headcount=avail_count,
            gap_severity=severity,
            coverage_pct=coverage_pct,
            recommendation=rec,
        ))

    # Sort: critical first, then moderate, then low, then ok
    _order = {SEVERITY_CRITICAL: 0, SEVERITY_MODERATE: 1, SEVERITY_LOW: 2, SEVERITY_OK: 3}
    results.sort(key=lambda r: _order.get(r.gap_severity, 4))
    return results


def overall_gap_score(gaps: List[SkillGapResult]) -> float:
    """
    Returns a 0–100 score representing how well the current workforce
    covers a project's requirements (100 = fully covered).
    """
    if not gaps:
        return 100.0
    total = sum(g.coverage_pct for g in gaps)
    return round(total / len(gaps), 1)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _find_skill(skills: list, name: str):
    """Case-insensitive skill lookup in an employee's skills list."""
    for s in skills:
        if s["name"].lower() == name.lower():
            return s
    return None
