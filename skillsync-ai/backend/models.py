from sqlalchemy import Column, Integer, String, JSON, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)
    availability_hours_per_week = Column(Integer, default=40)
    allocated_hours = Column(Integer, default=0)
    skills = Column(JSON, nullable=False, default=list)
    # skills format: [{"name": "Python", "proficiency": 4, "verified": true}, ...]
    interests = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    allocations = relationship("Allocation", back_populates="employee")
    learning_paths = relationship("LearningPath", back_populates="employee")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    deadline_days = Column(Integer, nullable=False)
    priority = Column(Integer, default=2)  # 1=high, 2=medium, 3=low
    required_skills = Column(JSON, nullable=False, default=list)
    # required_skills: [{"name": "Cloud Deployment", "min_proficiency": 4, "headcount": 3}, ...]
    status = Column(String(50), default="upcoming")  # upcoming, active, completed
    created_at = Column(DateTime, default=datetime.utcnow)

    allocations = relationship("Allocation", back_populates="project")
    skill_gaps = relationship("SkillGap", back_populates="project")


class SkillGap(Base):
    __tablename__ = "skill_gaps"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    required_proficiency = Column(Integer, nullable=False)
    required_headcount = Column(Integer, nullable=False)
    available_headcount = Column(Integer, default=0)
    gap_severity = Column(String(20), nullable=False)  # critical, moderate, low
    detected_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="skill_gaps")


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    current_level = Column(Integer, nullable=False)
    target_level = Column(Integer, nullable=False)
    modules = Column(JSON, nullable=False, default=list)
    # modules: [{"title": "...", "type": "video/lab/assessment", "duration_hours": 2, "order": 1}, ...]
    estimated_days = Column(Float, nullable=False)
    explanation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="learning_paths")


class Allocation(Base):
    __tablename__ = "allocations"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    assigned_hours = Column(Integer, nullable=False)
    skill_match_score = Column(Float, default=0.0)
    rationale = Column(Text)
    allocation_type = Column(String(50), default="optimized")  # optimized, baseline, simulated
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="allocations")
    project = relationship("Project", back_populates="allocations")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    user_role = Column(String(50), default="anonymous")
    request_summary = Column(Text)
    response_status = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
