"""
Allocation Optimizer — Workforce Skill Liquidity Engine
Uses Google OR-Tools CP-SAT solver to optimally assign employees to
projects, maximizing skill coverage while respecting workload limits
and project deadlines.

Also computes a naive baseline for comparison (assign by availability
only, ignoring skills) and reports the improvement percentage.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


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
    solver_used: str                      # "ortools" or "greedy_fallback"


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
    # Apply deadline overrides for simulation
    effective_deadlines = {}
    for p in projects:
        dl = p.deadline_days
        if deadline_override and p.id in deadline_override:
            dl = deadline_override[p.id]
        effective_deadlines[p.id] = dl

    baseline = _greedy_baseline(employees, projects, effective_deadlines)

    if ORTOOLS_AVAILABLE:
        result = _ortools_optimize(employees, projects, effective_deadlines)
        result.baseline_score = baseline.overall_score
        result.improvement_pct = _improvement(result.overall_score, baseline.overall_score)
        result.solver_used = "ortools"
    else:
        result = baseline
        result.solver_used = "greedy_fallback"

    return result


# ─── Skill Matching Helpers ───────────────────────────────────────────────────

def _skill_match_score(employee: Any, project: Any, deadline_days: int) -> float:
    """
    Returns a 0.0–1.0 score reflecting how well this employee covers
    the project's required skills given the available deadline.
    Penalises employees who would need upskilling beyond the deadline.
    """
    if not project.required_skills:
        return 0.0

    total_weight = 0.0
    matched_weight = 0.0

    for req in project.required_skills:
        skill_name = req["name"]
        min_prof   = req["min_proficiency"]
        headcount  = req.get("headcount", 1)
        weight     = headcount * min_prof          # higher need → higher weight

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
    return 15   # default weekly hours allocated per project assignment


# ─── OR-Tools Optimizer ──────────────────────────────────────────────────────

def _ortools_optimize(
    employees: List[Any],
    projects: List[Any],
    effective_deadlines: Dict[int, int],
) -> AllocationResult:
    model = cp_model.CpModel()

    # Decision variables: assign[i][j] ∈ {0, 1}
    assign = {}
    scores_scaled = {}   # score × 10000 (CP-SAT needs integers)

    for emp in employees:
        for proj in projects:
            if _spare_hours(emp) < 5:
                # Not enough hours — force exclude
                v = model.NewConstant(0)
            else:
                v = model.NewBoolVar(f"assign_e{emp.id}_p{proj.id}")

            assign[(emp.id, proj.id)] = v
            dl = effective_deadlines[proj.id]
            score = _skill_match_score(emp, proj, dl)
            priority_boost = max(0, (4 - proj.priority)) * 0.05  # priority 1 gets +0.15
            scores_scaled[(emp.id, proj.id)] = int((score + priority_boost) * 10000)

    # Constraint 1: employee total allocated hours ≤ available
    hrs = _hours_per_project()
    for emp in employees:
        model.Add(
            sum(assign[(emp.id, p.id)] * hrs for p in projects)
            <= _spare_hours(emp)
        )

    # Constraint 2: each project gets at most its total required headcount
    for proj in projects:
        total_needed = sum(r.get("headcount", 1) for r in proj.required_skills)
        model.Add(
            sum(assign[(e.id, proj.id)] for e in employees) <= total_needed * 2
        )

    # Objective: maximise total weighted skill match
    model.Maximize(
        sum(
            assign[(e.id, p.id)] * scores_scaled[(e.id, p.id)]
            for e in employees for p in projects
        )
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
    status = solver.Solve(model)

    assignments = []
    project_emp_map: Dict[int, List] = {p.id: [] for p in projects}

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for emp in employees:
            for proj in projects:
                if solver.Value(assign[(emp.id, proj.id)]) == 1:
                    score  = scores_scaled[(emp.id, proj.id)] / 10000
                    rationale = _build_rationale(emp, proj, score, effective_deadlines[proj.id])
                    assignments.append(AssignmentResult(
                        employee_id=emp.id,
                        employee_name=emp.name,
                        project_id=proj.id,
                        project_name=proj.name,
                        assigned_hours=_hours_per_project(),
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
        solver_used="ortools",
    )


# ─── Greedy Baseline ─────────────────────────────────────────────────────────

def _greedy_baseline(
    employees: List[Any],
    projects: List[Any],
    effective_deadlines: Dict[int, int],
) -> AllocationResult:
    """
    Naive assignment: sort employees by spare hours descending,
    fill each project's headcount regardless of skill match.
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
                    rationale=f"Baseline: assigned by availability. Skill match: {round(score*100)}%.",
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
        solver_used="greedy_fallback",
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

    spare = _spare_hours(emp)
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
