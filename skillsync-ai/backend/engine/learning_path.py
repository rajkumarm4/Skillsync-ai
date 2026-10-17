"""
Learning Path Generator
Produces the minimal targeted learning plan needed to bridge a specific
skill gap, personalized to the employee's current proficiency level.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple


@dataclass
class LearningModule:
    order: int
    title: str
    type: str          # video | lab | assessment | reading
    duration_hours: float
    prerequisite: str  # name of prior module or ""


@dataclass
class LearningPathResult:
    employee_name: str
    skill_name: str
    current_level: int
    target_level: int
    modules: List[LearningModule]
    estimated_days: float          # assuming 2 hrs/day focused study
    explanation: str
    feasible_in_days: int          # project deadline check


# ─── Module Catalog ──────────────────────────────────────────────────────────
# Structure: (skill, from_level, to_level) → list of module dicts
# Proficiency: 1=aware, 2=beginner, 3=competent, 4=proficient, 5=expert

MODULE_CATALOG: Dict[Tuple, List[Dict]] = {
    ("Cloud Deployment", 1, 3): [
        {"title": "Cloud Fundamentals (AWS/Azure/GCP Overview)",   "type": "video",      "duration_hours": 3.0, "prerequisite": ""},
        {"title": "Deploying Your First App to the Cloud",          "type": "lab",        "duration_hours": 4.0, "prerequisite": "Cloud Fundamentals"},
        {"title": "Cloud Deployment Concepts Assessment",           "type": "assessment", "duration_hours": 1.0, "prerequisite": "Deploying Your First App"},
    ],
    ("Cloud Deployment", 2, 4): [
        {"title": "Cloud Deployment Patterns and Best Practices",   "type": "video",      "duration_hours": 3.0, "prerequisite": ""},
        {"title": "Hands-on: Deploy a Multi-Service App",           "type": "lab",        "duration_hours": 5.0, "prerequisite": "Cloud Deployment Patterns"},
        {"title": "CI/CD for Cloud Deployments",                    "type": "lab",        "duration_hours": 3.0, "prerequisite": "Multi-Service App Lab"},
        {"title": "Supervised Deployment Task (Real Project)",      "type": "lab",        "duration_hours": 4.0, "prerequisite": "CI/CD Lab"},
    ],
    ("Cloud Deployment", 3, 4): [
        {"title": "Advanced Cloud Deployment Strategies",           "type": "video",      "duration_hours": 2.0, "prerequisite": ""},
        {"title": "Hands-on: Blue-Green and Canary Deployments",    "type": "lab",        "duration_hours": 4.0, "prerequisite": "Advanced Strategies"},
        {"title": "Supervised Deployment Milestone Check",          "type": "assessment", "duration_hours": 2.0, "prerequisite": "Hands-on Lab"},
    ],
    ("Kubernetes", 1, 3): [
        {"title": "Kubernetes Architecture Overview",               "type": "video",      "duration_hours": 2.5, "prerequisite": ""},
        {"title": "kubectl Basics and Pod Management",              "type": "lab",        "duration_hours": 3.0, "prerequisite": "K8s Overview"},
        {"title": "Deployments, Services and ConfigMaps",           "type": "lab",        "duration_hours": 3.0, "prerequisite": "kubectl Basics"},
    ],
    ("Kubernetes", 2, 3): [
        {"title": "Kubernetes Workloads Deep Dive",                 "type": "video",      "duration_hours": 2.0, "prerequisite": ""},
        {"title": "Helm Charts and Package Management",             "type": "lab",        "duration_hours": 3.0, "prerequisite": "K8s Workloads"},
    ],
    ("Docker", 1, 3): [
        {"title": "Containers and Docker Fundamentals",             "type": "video",      "duration_hours": 2.0, "prerequisite": ""},
        {"title": "Building and Publishing Docker Images",          "type": "lab",        "duration_hours": 2.5, "prerequisite": "Docker Fundamentals"},
        {"title": "Docker Compose Multi-Service Setup",             "type": "lab",        "duration_hours": 2.0, "prerequisite": "Docker Images"},
    ],
    ("Docker", 2, 3): [
        {"title": "Advanced Dockerfile Optimization",               "type": "video",      "duration_hours": 1.5, "prerequisite": ""},
        {"title": "Docker Compose in Practice",                     "type": "lab",        "duration_hours": 2.5, "prerequisite": "Dockerfile Optimization"},
    ],
    ("Machine Learning", 2, 4): [
        {"title": "Supervised Learning Foundations",                "type": "video",      "duration_hours": 3.0, "prerequisite": ""},
        {"title": "scikit-learn Model Training Pipeline",           "type": "lab",        "duration_hours": 4.0, "prerequisite": "Supervised Learning"},
        {"title": "Model Evaluation and Hyperparameter Tuning",     "type": "lab",        "duration_hours": 3.0, "prerequisite": "Model Training"},
        {"title": "Deploying ML Models to Production",              "type": "lab",        "duration_hours": 3.0, "prerequisite": "Model Evaluation"},
    ],
    ("Machine Learning", 3, 4): [
        {"title": "Advanced ML: Ensembles and Feature Engineering", "type": "video",      "duration_hours": 2.5, "prerequisite": ""},
        {"title": "End-to-End ML Pipeline Lab",                     "type": "lab",        "duration_hours": 4.0, "prerequisite": "Advanced ML"},
    ],
    ("Test Automation", 1, 4): [
        {"title": "Testing Fundamentals and Pyramid",               "type": "video",      "duration_hours": 2.0, "prerequisite": ""},
        {"title": "pytest: Unit and Integration Testing",           "type": "lab",        "duration_hours": 3.0, "prerequisite": "Testing Fundamentals"},
        {"title": "Selenium: Browser Automation",                   "type": "lab",        "duration_hours": 3.5, "prerequisite": "pytest Lab"},
        {"title": "CI/CD Integration for Test Suites",              "type": "lab",        "duration_hours": 2.5, "prerequisite": "Selenium Lab"},
    ],
    ("Test Automation", 2, 4): [
        {"title": "Advanced pytest Fixtures and Parametrize",       "type": "video",      "duration_hours": 2.0, "prerequisite": ""},
        {"title": "Page Object Model with Selenium",                "type": "lab",        "duration_hours": 3.0, "prerequisite": "Advanced pytest"},
        {"title": "Integrating Tests into CI/CD",                   "type": "lab",        "duration_hours": 2.5, "prerequisite": "Page Object Lab"},
    ],
    ("SQL", 1, 4): [
        {"title": "SQL Basics: SELECT, JOIN, WHERE",                "type": "video",      "duration_hours": 2.5, "prerequisite": ""},
        {"title": "Intermediate SQL: Subqueries and Aggregates",    "type": "lab",        "duration_hours": 3.0, "prerequisite": "SQL Basics"},
        {"name": "Advanced SQL: Window Functions and Optimization", "type": "lab",        "duration_hours": 3.0, "prerequisite": "Intermediate SQL"},
    ],
    ("Data Pipelines", 2, 4): [
        {"title": "ETL vs ELT Fundamentals",                        "type": "video",      "duration_hours": 2.0, "prerequisite": ""},
        {"title": "Apache Airflow: DAGs and Operators",             "type": "lab",        "duration_hours": 4.0, "prerequisite": "ETL Fundamentals"},
        {"title": "Streaming Data with Kafka Basics",               "type": "lab",        "duration_hours": 3.0, "prerequisite": "Airflow Lab"},
    ],
    ("Java", 2, 4): [
        {"title": "Java OOP Principles Deep Dive",                  "type": "video",      "duration_hours": 3.0, "prerequisite": ""},
        {"title": "Spring Boot REST API Development",               "type": "lab",        "duration_hours": 5.0, "prerequisite": "Java OOP"},
        {"title": "Testing Spring Boot Applications",               "type": "lab",        "duration_hours": 3.0, "prerequisite": "Spring Boot Lab"},
    ],
    ("REST API Design", 2, 4): [
        {"title": "RESTful API Design Principles",                  "type": "video",      "duration_hours": 2.0, "prerequisite": ""},
        {"title": "OpenAPI / Swagger Documentation",                "type": "lab",        "duration_hours": 2.0, "prerequisite": "REST Principles"},
        {"title": "API Security: Auth, Rate Limiting",              "type": "lab",        "duration_hours": 2.5, "prerequisite": "OpenAPI Lab"},
    ],
}


def generate_path(
    employee_name: str,
    skill_name: str,
    current_level: int,
    target_level: int,
    project_deadline_days: int = 30,
) -> LearningPathResult:
    """
    Generate the minimal learning path to bring an employee from
    current_level to target_level for the given skill.
    """
    modules_raw = _lookup_modules(skill_name, current_level, target_level)

    if not modules_raw:
        # fallback: generic 2-module path
        modules_raw = [
            {"title": f"{skill_name} Foundations",          "type": "video",      "duration_hours": 3.0, "prerequisite": ""},
            {"title": f"{skill_name} Hands-on Practice Lab","type": "lab",        "duration_hours": 4.0, "prerequisite": f"{skill_name} Foundations"},
            {"title": f"{skill_name} Competency Assessment","type": "assessment", "duration_hours": 1.5, "prerequisite": "Hands-on Lab"},
        ]

    modules = [
        LearningModule(
            order=i + 1,
            title=m.get("title", m.get("name", f"Module {i+1}")),
            type=m["type"],
            duration_hours=m["duration_hours"],
            prerequisite=m["prerequisite"],
        )
        for i, m in enumerate(modules_raw)
    ]

    total_hours   = sum(m.duration_hours for m in modules)
    estimated_days = round(total_hours / 2.0, 1)   # 2 focused hours/day

    feasible = int(estimated_days) + 1              # +1 day buffer

    explanation = _build_explanation(
        employee_name, skill_name, current_level, target_level,
        modules, estimated_days, project_deadline_days
    )

    return LearningPathResult(
        employee_name=employee_name,
        skill_name=skill_name,
        current_level=current_level,
        target_level=target_level,
        modules=modules,
        estimated_days=estimated_days,
        explanation=explanation,
        feasible_in_days=feasible,
    )


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _lookup_modules(skill: str, from_lvl: int, to_lvl: int) -> List[Dict]:
    """Try exact key first, then nearest bridging path."""
    key = (skill, from_lvl, to_lvl)
    if key in MODULE_CATALOG:
        return MODULE_CATALOG[key]

    # Try bridging: find any path from from_lvl toward to_lvl
    for delta in range(1, 4):
        bridge = (skill, from_lvl, from_lvl + delta)
        if bridge in MODULE_CATALOG and from_lvl + delta >= to_lvl:
            return MODULE_CATALOG[bridge]

    # Fall back to highest available level path for this skill
    matches = [(k, v) for k, v in MODULE_CATALOG.items() if k[0] == skill]
    if matches:
        matches.sort(key=lambda x: abs(x[0][1] - from_lvl))
        return matches[0][1]

    return []


LEVEL_LABELS = {1: "Aware", 2: "Beginner", 3: "Competent", 4: "Proficient", 5: "Expert"}


def _build_explanation(name, skill, curr, target, modules, days, deadline):
    curr_label   = LEVEL_LABELS.get(curr, str(curr))
    target_label = LEVEL_LABELS.get(target, str(target))
    feasible_str = "feasible" if days + 1 <= deadline else "tight — consider alternative assignment"

    module_titles = ", ".join(f'"{m.title}"' for m in modules[:2])
    extra = f" and {len(modules) - 2} more module(s)" if len(modules) > 2 else ""

    return (
        f"{name} currently has '{skill}' at level {curr} ({curr_label}). "
        f"To reach level {target} ({target_label}), the recommended path includes "
        f"{len(modules)} module(s): {module_titles}{extra}. "
        f"Estimated completion: {days} days at 2 hours/day focused study. "
        f"Timeline vs project deadline ({deadline} days): {feasible_str}."
    )
