"""
Seed data: 20 synthetic employees + 5 projects.
The critical bottleneck is P1 (Legacy App Migration) — needs 3 cloud deployment engineers
at proficiency >= 4, but only 2 exist and both are overloaded.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend import models

EMPLOYEES = [
    # Cluster 1: Strong Python, weak cloud → upskilling candidates (4 employees)
    {
        "name": "Aisha Patel", "department": "Engineering", "role": "Backend Developer",
        "availability_hours_per_week": 40, "allocated_hours": 10,
        "skills": [
            {"name": "Python", "proficiency": 5, "verified": True},
            {"name": "REST API Design", "proficiency": 4, "verified": True},
            {"name": "PostgreSQL", "proficiency": 3, "verified": True},
            {"name": "Cloud Deployment", "proficiency": 2, "verified": False},
            {"name": "Docker", "proficiency": 2, "verified": False},
        ],
        "interests": ["cloud", "backend"]
    },
    {
        "name": "Rohan Mehta", "department": "Engineering", "role": "Backend Developer",
        "availability_hours_per_week": 40, "allocated_hours": 8,
        "skills": [
            {"name": "Python", "proficiency": 4, "verified": True},
            {"name": "Django", "proficiency": 4, "verified": True},
            {"name": "REST API Design", "proficiency": 3, "verified": True},
            {"name": "Cloud Deployment", "proficiency": 1, "verified": False},
            {"name": "Linux", "proficiency": 3, "verified": True},
        ],
        "interests": ["cloud", "devops"]
    },
    {
        "name": "Li Wei", "department": "Engineering", "role": "Software Engineer",
        "availability_hours_per_week": 40, "allocated_hours": 5,
        "skills": [
            {"name": "Python", "proficiency": 4, "verified": True},
            {"name": "Machine Learning", "proficiency": 3, "verified": True},
            {"name": "REST API Design", "proficiency": 3, "verified": True},
            {"name": "Cloud Deployment", "proficiency": 2, "verified": False},
            {"name": "Kubernetes", "proficiency": 1, "verified": False},
        ],
        "interests": ["ml", "cloud"]
    },
    {
        "name": "Fatima Al-Rashid", "department": "Engineering", "role": "Software Engineer",
        "availability_hours_per_week": 35, "allocated_hours": 10,
        "skills": [
            {"name": "Python", "proficiency": 4, "verified": True},
            {"name": "Flask", "proficiency": 4, "verified": True},
            {"name": "PostgreSQL", "proficiency": 4, "verified": True},
            {"name": "Cloud Deployment", "proficiency": 2, "verified": False},
        ],
        "interests": ["backend", "databases"]
    },
    # Cluster 2: Strong cloud skills, overloaded (3 employees — P1 bottleneck!)
    {
        "name": "Carlos Mendez", "department": "DevOps", "role": "Cloud Architect",
        "availability_hours_per_week": 40, "allocated_hours": 38,
        "skills": [
            {"name": "Cloud Deployment", "proficiency": 5, "verified": True},
            {"name": "Kubernetes", "proficiency": 5, "verified": True},
            {"name": "Docker", "proficiency": 5, "verified": True},
            {"name": "Terraform", "proficiency": 4, "verified": True},
            {"name": "Linux", "proficiency": 5, "verified": True},
        ],
        "interests": ["cloud", "infrastructure"]
    },
    {
        "name": "Priya Sharma", "department": "DevOps", "role": "Senior DevOps Engineer",
        "availability_hours_per_week": 40, "allocated_hours": 36,
        "skills": [
            {"name": "Cloud Deployment", "proficiency": 5, "verified": True},
            {"name": "Docker", "proficiency": 5, "verified": True},
            {"name": "Kubernetes", "proficiency": 4, "verified": True},
            {"name": "CI/CD Pipelines", "proficiency": 5, "verified": True},
            {"name": "Python", "proficiency": 3, "verified": True},
        ],
        "interests": ["devops", "automation"]
    },
    {
        "name": "James O'Brien", "department": "DevOps", "role": "DevOps Engineer",
        "availability_hours_per_week": 40, "allocated_hours": 35,
        "skills": [
            {"name": "Cloud Deployment", "proficiency": 4, "verified": True},
            {"name": "Linux", "proficiency": 4, "verified": True},
            {"name": "Terraform", "proficiency": 3, "verified": True},
            {"name": "Docker", "proficiency": 4, "verified": True},
        ],
        "interests": ["cloud", "linux"]
    },
    # Cluster 3: Strong Java/backend (4 employees)
    {
        "name": "Elena Volkova", "department": "Engineering", "role": "Java Developer",
        "availability_hours_per_week": 40, "allocated_hours": 20,
        "skills": [
            {"name": "Java", "proficiency": 5, "verified": True},
            {"name": "Spring Boot", "proficiency": 5, "verified": True},
            {"name": "REST API Design", "proficiency": 4, "verified": True},
            {"name": "Microservices", "proficiency": 4, "verified": True},
            {"name": "PostgreSQL", "proficiency": 3, "verified": True},
        ],
        "interests": ["backend", "architecture"]
    },
    {
        "name": "Kwame Asante", "department": "Engineering", "role": "Java Developer",
        "availability_hours_per_week": 40, "allocated_hours": 15,
        "skills": [
            {"name": "Java", "proficiency": 4, "verified": True},
            {"name": "Spring Boot", "proficiency": 4, "verified": True},
            {"name": "Microservices", "proficiency": 3, "verified": True},
            {"name": "REST API Design", "proficiency": 4, "verified": True},
        ],
        "interests": ["backend", "api"]
    },
    {
        "name": "Sofia Rossi", "department": "Engineering", "role": "Senior Software Engineer",
        "availability_hours_per_week": 40, "allocated_hours": 12,
        "skills": [
            {"name": "Java", "proficiency": 5, "verified": True},
            {"name": "Microservices", "proficiency": 4, "verified": True},
            {"name": "Kafka", "proficiency": 3, "verified": True},
            {"name": "REST API Design", "proficiency": 4, "verified": True},
            {"name": "Docker", "proficiency": 3, "verified": True},
        ],
        "interests": ["backend", "messaging"]
    },
    {
        "name": "Ahmed Hassan", "department": "Engineering", "role": "Backend Engineer",
        "availability_hours_per_week": 35, "allocated_hours": 18,
        "skills": [
            {"name": "Java", "proficiency": 4, "verified": True},
            {"name": "Spring Boot", "proficiency": 3, "verified": True},
            {"name": "PostgreSQL", "proficiency": 4, "verified": True},
            {"name": "REST API Design", "proficiency": 3, "verified": True},
        ],
        "interests": ["backend", "databases"]
    },
    # Cluster 4: QA/Testing specialists (3 employees)
    {
        "name": "Yuki Tanaka", "department": "QA", "role": "Senior QA Engineer",
        "availability_hours_per_week": 40, "allocated_hours": 10,
        "skills": [
            {"name": "Test Automation", "proficiency": 5, "verified": True},
            {"name": "Python", "proficiency": 4, "verified": True},
            {"name": "Selenium", "proficiency": 5, "verified": True},
            {"name": "CI/CD Pipelines", "proficiency": 3, "verified": True},
            {"name": "Cloud Deployment", "proficiency": 2, "verified": False},
        ],
        "interests": ["testing", "automation"]
    },
    {
        "name": "Maria Santos", "department": "QA", "role": "QA Engineer",
        "availability_hours_per_week": 40, "allocated_hours": 8,
        "skills": [
            {"name": "Test Automation", "proficiency": 4, "verified": True},
            {"name": "Python", "proficiency": 3, "verified": True},
            {"name": "Selenium", "proficiency": 4, "verified": True},
            {"name": "PostgreSQL", "proficiency": 2, "verified": False},
        ],
        "interests": ["testing", "quality"]
    },
    {
        "name": "Lars Andersen", "department": "QA", "role": "QA Lead",
        "availability_hours_per_week": 40, "allocated_hours": 15,
        "skills": [
            {"name": "Test Automation", "proficiency": 5, "verified": True},
            {"name": "Python", "proficiency": 3, "verified": True},
            {"name": "CI/CD Pipelines", "proficiency": 4, "verified": True},
            {"name": "REST API Design", "proficiency": 2, "verified": False},
        ],
        "interests": ["testing", "leadership"]
    },
    # Cluster 5: Data/ML focused (3 employees)
    {
        "name": "Nadia Kowalski", "department": "Data", "role": "Data Scientist",
        "availability_hours_per_week": 40, "allocated_hours": 20,
        "skills": [
            {"name": "Machine Learning", "proficiency": 5, "verified": True},
            {"name": "Python", "proficiency": 5, "verified": True},
            {"name": "SQL", "proficiency": 4, "verified": True},
            {"name": "Data Pipelines", "proficiency": 4, "verified": True},
            {"name": "Cloud Deployment", "proficiency": 2, "verified": False},
        ],
        "interests": ["ml", "data"]
    },
    {
        "name": "Tariq Al-Amin", "department": "Data", "role": "Data Engineer",
        "availability_hours_per_week": 40, "allocated_hours": 25,
        "skills": [
            {"name": "SQL", "proficiency": 5, "verified": True},
            {"name": "Data Pipelines", "proficiency": 5, "verified": True},
            {"name": "Python", "proficiency": 4, "verified": True},
            {"name": "Cloud Deployment", "proficiency": 3, "verified": True},
            {"name": "Kafka", "proficiency": 3, "verified": True},
        ],
        "interests": ["data", "cloud"]
    },
    {
        "name": "Ingrid Berg", "department": "Data", "role": "ML Engineer",
        "availability_hours_per_week": 40, "allocated_hours": 18,
        "skills": [
            {"name": "Machine Learning", "proficiency": 4, "verified": True},
            {"name": "Python", "proficiency": 5, "verified": True},
            {"name": "Data Pipelines", "proficiency": 3, "verified": True},
            {"name": "SQL", "proficiency": 3, "verified": True},
        ],
        "interests": ["ml", "automation"]
    },
    # Cluster 6: Generalists (3 employees)
    {
        "name": "Raj Krishnamurthy", "department": "Engineering", "role": "Full Stack Developer",
        "availability_hours_per_week": 40, "allocated_hours": 22,
        "skills": [
            {"name": "Python", "proficiency": 3, "verified": True},
            {"name": "Java", "proficiency": 3, "verified": True},
            {"name": "REST API Design", "proficiency": 3, "verified": True},
            {"name": "Cloud Deployment", "proficiency": 2, "verified": False},
            {"name": "PostgreSQL", "proficiency": 3, "verified": True},
        ],
        "interests": ["fullstack", "cloud"]
    },
    {
        "name": "Amara Diallo", "department": "Engineering", "role": "Software Developer",
        "availability_hours_per_week": 35, "allocated_hours": 12,
        "skills": [
            {"name": "Python", "proficiency": 3, "verified": True},
            {"name": "REST API Design", "proficiency": 3, "verified": True},
            {"name": "Test Automation", "proficiency": 2, "verified": False},
            {"name": "SQL", "proficiency": 3, "verified": True},
        ],
        "interests": ["backend", "testing"]
    },
    {
        "name": "Viktor Novak", "department": "Engineering", "role": "Software Engineer",
        "availability_hours_per_week": 40, "allocated_hours": 16,
        "skills": [
            {"name": "Java", "proficiency": 3, "verified": True},
            {"name": "Python", "proficiency": 3, "verified": True},
            {"name": "Docker", "proficiency": 3, "verified": True},
            {"name": "Linux", "proficiency": 3, "verified": True},
            {"name": "Cloud Deployment", "proficiency": 2, "verified": False},
        ],
        "interests": ["backend", "devops"]
    },
]

PROJECTS = [
    {
        "name": "P1: Legacy App Migration to Cloud",
        "description": "Migrate a monolithic legacy Java application to a cloud-native microservices architecture on Kubernetes. Critical business dependency.",
        "deadline_days": 14,
        "priority": 1,
        "required_skills": [
            {"name": "Cloud Deployment", "min_proficiency": 4, "headcount": 3},
            {"name": "Kubernetes", "min_proficiency": 3, "headcount": 2},
            {"name": "Docker", "min_proficiency": 3, "headcount": 2},
            {"name": "Java", "min_proficiency": 3, "headcount": 2},
        ],
        "status": "upcoming"
    },
    {
        "name": "P2: ML Pipeline Automation",
        "description": "Build an automated ML training and inference pipeline using Python and cloud infrastructure.",
        "deadline_days": 21,
        "priority": 1,
        "required_skills": [
            {"name": "Machine Learning", "min_proficiency": 4, "headcount": 2},
            {"name": "Python", "min_proficiency": 4, "headcount": 3},
            {"name": "Data Pipelines", "min_proficiency": 3, "headcount": 2},
        ],
        "status": "upcoming"
    },
    {
        "name": "P3: API Gateway Refactor",
        "description": "Redesign the company's API gateway layer using Java Spring Boot microservices.",
        "deadline_days": 30,
        "priority": 2,
        "required_skills": [
            {"name": "Java", "min_proficiency": 4, "headcount": 3},
            {"name": "Microservices", "min_proficiency": 3, "headcount": 2},
            {"name": "REST API Design", "min_proficiency": 4, "headcount": 3},
        ],
        "status": "upcoming"
    },
    {
        "name": "P4: Test Automation Suite",
        "description": "Build a comprehensive automated test suite covering unit, integration, and end-to-end tests.",
        "deadline_days": 10,
        "priority": 2,
        "required_skills": [
            {"name": "Test Automation", "min_proficiency": 4, "headcount": 2},
            {"name": "Python", "min_proficiency": 3, "headcount": 2},
            {"name": "CI/CD Pipelines", "min_proficiency": 3, "headcount": 1},
        ],
        "status": "upcoming"
    },
    {
        "name": "P5: Data Warehouse Modernization",
        "description": "Migrate on-premise data warehouse to a cloud-based solution with modern ETL pipelines.",
        "deadline_days": 45,
        "priority": 2,
        "required_skills": [
            {"name": "SQL", "min_proficiency": 4, "headcount": 2},
            {"name": "Data Pipelines", "min_proficiency": 4, "headcount": 2},
            {"name": "Cloud Deployment", "min_proficiency": 3, "headcount": 1},
            {"name": "Python", "min_proficiency": 3, "headcount": 2},
        ],
        "status": "upcoming"
    },
]


def seed():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Clear existing data
        db.query(models.AuditLog).delete()
        db.query(models.Allocation).delete()
        db.query(models.LearningPath).delete()
        db.query(models.SkillGap).delete()
        db.query(models.Employee).delete()
        db.query(models.Project).delete()
        db.commit()

        # Insert employees
        for emp_data in EMPLOYEES:
            emp = models.Employee(**emp_data)
            db.add(emp)
        db.commit()

        # Insert projects
        for proj_data in PROJECTS:
            proj = models.Project(**proj_data)
            db.add(proj)
        db.commit()

        print(f"✅ Seeded {len(EMPLOYEES)} employees and {len(PROJECTS)} projects.")
        print("⚠️  P1 critical bottleneck: Cloud Deployment needs 3 engineers at proficiency ≥ 4.")
        print("   Only 2 qualify (Carlos Mendez, Priya Sharma) — both allocated ≥ 35 hrs/week.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
