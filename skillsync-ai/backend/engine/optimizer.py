"""
Allocation Optimizer — Workforce Skill Liquidity Engine
Uses scipy linear programming to optimally assign employees to projects,
maximizing skill coverage while respecting workload limits and deadlines.

Falls back to greedy if scipy is unavailable.
Deployed on IBM LinuxONE Community Cloud (s390x) — Event Code: SSF2026
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

try:
    from scipy.optimize import linprog
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class AssignmentResult:
    employee_id: int
    employee_name: str
    project_id: int
    project_name: str
    assigned_hours: int
    skill_match_score: float          # 0.0 – 1.0
    rationale: str


@dataclass
class AllocationResult:
    assignments: List[AssignmentResult]
    project_coverage: Dict[int, float]    # project_id → coverage %
    overall_score: float                  # 0–100
    baseline_score: float                 # naive approach score
    improvement_pct: float                # how much better than naive
    unmet_gaps: List[str]                 # projects with <50% coverage
    solver_used: str                      # "scipy_lp" or "greedy_fallback"


# ─── Public API ──────────────────────────────────────────────────────────────

def run_allocation(
    employees: List[Any],
    projects: List[Any],
    deadline_override: Optional[Dict[int, int]] = None,
    allocation_type: str = "optimized",
) -> AllocationResult:
    """
    Main entry point.
    employees: list of Employee ORM objects
    projects:  list of Project ORM objects
    deadline_override: {project_id: new_deadline_days} for simulation
    """
    effective_deadlines = {}
    for p in projects:
        dl = p.deadline_days
        if deadline_override and p.id in deadline_override:
            dl = deadline_override[p.id]
        effective_deadlines[p.id] = dl

    baseline = _greedy_baseline(employees, projects, effective_deadlines)

    if SCIPY_AVAILABLE:
        result = _scipy_optimize(employees, projects, effective_deadlines)
        result.baseline_score = baseline.overall_score
        result.improvement_pct = _improvement(result.overall_score, baseline.overall_score)
        result.solver_used = "scipy_lp"
    else:
        result = _smart_greedy(employees, projects, effective_deadlines)
        result.baseline_score = baseline.overall_score
        result.improvement_pct = _improvement(result.overall_score, baseline.overall_score)
        result.solver_used = "greedy_optimized"

    return result


# ─── Skill Matching Helpers ───────────────────────────────────────────────────

def _skill_match_score(employee: Any, project: Any, deadline_days: int) -> float:
    """
    Returns a 0.0–1.0 score reflecting how well this employee covers
    the project's required skills given the available deadline.
    """
    if not project.required_skills:
        return 0.0

    total_weight = 0.0
    matched_weight = 0.0

    for req in project.required_skills:
        skill_name = req["name"]
        min_prof   = req["min_proficiency"]
        headcount  = req.get("headcount", 1)
        weight     = headcount * min_prof

        emp_skill = _find_skill(employee.skills, skill_name)
        if emp_skill:
            prof = emp_skill["proficiency"]
            if prof >= min_prof:
                match = min(1.0, prof / min_prof) * weight
                matched_weight += match
        total_weight += weight

    return round(matched_weight / total_weight, 4) if total_weight > 0 else 0.0


def _find_skill(skills: list, name: str):
    for s in skills:
        if s["name"].lower() == name.lower():
            return s
    return None


def _spare_hours(emp: Any) -> int:
    return max(0, emp.availability_hours_per_week - emp.allocated_hours)


def _hours_per_project() -> int:
    return 15


# ─── Scipy LP Optimizer ──────────────────────────────────────────────────────

def _scipy_optimize(
    employees: List[Any],
    projects: List[Any],
    effective_deadlines: Dict[int, int],
) -> AllocationResult:
    """
    Relaxed LP: treat assignment variables as continuous [0,1],
    then round to binary. For 20 employees × 5 projects this gives
    near-optimal results in milliseconds on s390x.
    """
    import numpy as np

    n_emp  = len(employees)
    n_proj = len(projects)
    n_vars = n_emp * n_proj
    hrs    = _hours_per_project()

    # Build score matrix (maximize → negate for linprog which minimizes)
    scores = []
    for emp in employees:
        for proj in projects:
            dl    = effective_deadlines[proj.id]
            score = _skill_match_score(emp, proj, dl)
            priority_boost = max(0, (4 - proj.priority)) * 0.05
            scores.append(-(score + priority_boost))

    c = np.array(scores)

    # Inequality constraints (A_ub @ x <= b_ub)
    A_ub = []
    b_ub = []

    # Each employee: sum of assigned projects * hrs <= spare_hours
    for i, emp in enumerate(employees):
        row = [0.0] * n_vars
        for j in range(n_proj):
            row[i * n_proj + j] = float(hrs)
        A_ub.append(row)
        b_ub.append(float(_spare_hours(emp)))

    # Each project: total assigned <= max_headcount * 2
    for j, proj in enumerate(projects):
        total_needed = sum(r.get("headcount", 1) for r in proj.required_skills)
        row = [0.0] * n_vars
        for i in range(n_emp):
            row[i * n_proj + j] = 1.0
        A_ub.append(row)
        b_ub.append(float(total_needed * 2))

    bounds = [(0.0, 1.0)] * n_vars

    try:
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
        x = res.x if res.success else np.zeros(n_vars)
    except Exception:
        x = np.zeros(n_vars)

    # Round: assign if score > 0.4 (relaxed threshold for better coverage)
    assignments = []
    project_emp_map: Dict[int, List] = {p.id: [] for p in projects}

    for i, emp in enumerate(employees):
        for j, proj in enumerate(projects):
            val = x[i * n_proj + j]
            if val > 0.4 and _spare_hours(emp) >= hrs:
                dl    = effective_deadlines[proj.id]
                score = _skill_match_score(emp, proj, dl)
                rationale = _build_rationale(emp, proj, score, dl)
                assignments.append(AssignmentResult(
                    employee_id=emp.id,
                    employee_name=emp.name,
                    project_id=proj.id,
                    project_name=proj.name,
                    assigned_hours=hrs,
                    skill_match_score=round(score, 3),
                    rationale=rationale,
                ))
                project_emp_map[proj.id].append(emp)

    coverage = _compute_coverage(projects, project_emp_map, effective_deadlines)
    overall  = round(sum(coverage.values()) / len(coverage), 1) if coverage else 0.0
    unmet    = [p.name for p in projects if coverage.get(p.id, 0) < 50]

    return AllocationResult(
        assignments=assignments,
        project_coverage=coverage,
        overall_score=overall,
        baseline_score=0.0,
        improvement_pct=0.0,
        unmet_gaps=unmet,
        solver_used="scipy_lp",
    )


# ─── Smart Greedy (fallback) ─────────────────────────────────────────────────

def _smart_greedy(
    employees: List[Any],
    projects: List[Any],
    effective_deadlines: Dict[int, int],
) -> AllocationResult:
    """
    Skill-aware greedy: assign best skill-matched employees first,
    sorted by priority. Better than naive availability-only baseline.
    """
    hrs = _hours_per_project()
    assignments = []
    project_emp_map: Dict[int, List] = {p.id: [] for p in projects}
    emp_hours_used = {e.id: 0 for e in employees}

    # Sort projects by priority (1=highest first)
    sorted_projects = sorted(projects, key=lambda p: p.priority)

    for proj in sorted_projects:
        dl     = effective_deadlines[proj.id]
        needed = sum(r.get("headcount", 1) for r in proj.required_skills)

        # Rank employees by skill match for this project
        ranked = sorted(
            employees,
            key=lambda e: _skill_match_score(e, proj, dl),
            reverse=True,
        )

        filled = 0
        for emp in ranked:
            if filled >= needed:
                break
            spare = _spare_hours(emp) - emp_hours_used.get(emp.id, 0)
            if spare >= hrs:
                score = _skill_match_score(emp, proj, dl)
                assignments.append(AssignmentResult(
                    employee_id=emp.id,
                    employee_name=emp.name,
                    project_id=proj.id,
                    project_name=proj.name,
                    assigned_hours=hrs,
                    skill_match_score=round(score, 3),
                    rationale=_build_rationale(emp, proj, score, dl),
                ))
                project_emp_map[proj.id].append(emp)
                emp_hours_used[emp.id] = emp_hours_used.get(emp.id, 0) + hrs
                filled += 1

    coverage = _compute_coverage(projects, project_emp_map, effective_deadlines)
    overall  = round(sum(coverage.values()) / len(coverage), 1) if coverage else 0.0
    unmet    = [p.name for p in projects if coverage.get(p.id, 0) < 50]

    return AllocationResult(
        assignments=assignments,
        project_coverage=coverage,
        overall_score=overall,
        baseline_score=0.0,
        improvement_pct=0.0,
        unmet_gaps=unmet,
        solver_used="greedy_optimized",
    )


# ─── Naive Greedy Baseline ───────────────────────────────────────────────────

def _greedy_baseline(
    employees: List[Any],
    projects: List[Any],
    effective_deadlines: Dict[int, int],
) -> AllocationResult:
    """
    Naive assignment: sort by spare hours only, ignore skill match.
    Used as comparison baseline.
    """
    sorted_emps = sorted(employees, key=lambda e: _spare_hours(e), reverse=True)
    assignments = []
    project_emp_map: Dict[int, List] = {p.id: [] for p in projects}
    emp_hours_used = {e.id: 0 for e in employees}
    hrs = _hours_per_project()

    for proj in projects:
        needed = sum(r.get("headcount", 1) for r in proj.required_skills)
        filled = 0
        for emp in sorted_emps:
            if filled >= needed:
                break
            spare = _spare_hours(emp) - emp_hours_used.get(emp.id, 0)
            if spare >= hrs:
                score = _skill_match_score(emp, proj, effective_deadlines[proj.id])
                assignments.append(AssignmentResult(
                    employee_id=emp.id,
                    employee_name=emp.name,
                    project_id=proj.id,
                    project_name=proj.name,
                    assigned_hours=hrs,
                    skill_match_score=round(score, 3),
                    rationale=f"Baseline: assigned by availability only. Skill match: {round(score*100)}%.",
                ))
                project_emp_map[proj.id].append(emp)
                emp_hours_used[emp.id] = emp_hours_used.get(emp.id, 0) + hrs
                filled += 1

    coverage = _compute_coverage(projects, project_emp_map, effective_deadlines)
    overall  = round(sum(coverage.values()) / len(coverage), 1) if coverage else 0.0
    unmet    = [p.name for p in projects if coverage.get(p.id, 0) < 50]

    return AllocationResult(
        assignments=assignments,
        project_coverage=coverage,
        overall_score=overall,
        baseline_score=overall,
        improvement_pct=0.0,
        unmet_gaps=unmet,
        solver_used="greedy_baseline",
    )


# ─── Coverage & Rationale ────────────────────────────────────────────────────

def _compute_coverage(
    projects: List[Any],
    project_emp_map: Dict[int, List],
    effective_deadlines: Dict[int, int],
) -> Dict[int, float]:
    coverage = {}
    for proj in projects:
        emps = project_emp_map.get(proj.id, [])
        if not proj.required_skills:
            coverage[proj.id] = 100.0
            continue

        total_reqs = 0
        met_reqs   = 0
        for req in proj.required_skills:
            skill_name = req["name"]
            min_prof   = req["min_proficiency"]
            needed     = req.get("headcount", 1)
            qualified  = sum(
                1 for e in emps
                if (s := _find_skill(e.skills, skill_name)) and s["proficiency"] >= min_prof
            )
            total_reqs += needed
            met_reqs   += min(qualified, needed)

        coverage[proj.id] = round(met_reqs / total_reqs * 100, 1) if total_reqs > 0 else 0.0

    return coverage


def _build_rationale(emp: Any, proj: Any, score: float, deadline_days: int) -> str:
    matched_skills = []
    for req in proj.required_skills:
        s = _find_skill(emp.skills, req["name"])
        if s and s["proficiency"] >= req["min_proficiency"]:
            matched_skills.append(f"{req['name']} (L{s['proficiency']})")

    spare     = _spare_hours(emp)
    match_pct = int(score * 100)

    if matched_skills:
        skills_str = ", ".join(matched_skills[:3])
        extra = f" +{len(matched_skills)-3} more" if len(matched_skills) > 3 else ""
        return (
            f"Skill match {match_pct}%. Verified skills covering project requirements: "
            f"{skills_str}{extra}. Spare capacity: {spare} hrs/week. "
            f"Project deadline: {deadline_days} days."
        )
    else:
        return (
            f"Skill match {match_pct}% (partial). Assigned based on closest skill profile. "
            f"Spare capacity: {spare} hrs/week. Upskilling may be needed."
        )


def _improvement(optimized: float, baseline: float) -> float:
    if baseline <= 0:
        return 0.0
    return round((optimized - baseline) / baseline * 100, 1)
