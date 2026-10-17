"""
Employees router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend import models
from backend.schemas import EmployeeOut

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("", response_model=List[EmployeeOut])
def list_employees(db: Session = Depends(get_db)):
    employees = db.query(models.Employee).order_by(models.Employee.name).all()
    result = []
    for e in employees:
        d = {
            "id": e.id,
            "name": e.name,
            "department": e.department,
            "role": e.role,
            "availability_hours_per_week": e.availability_hours_per_week,
            "allocated_hours": e.allocated_hours,
            "spare_hours": max(0, e.availability_hours_per_week - e.allocated_hours),
            "skills": e.skills or [],
            "interests": e.interests or [],
        }
        result.append(d)
    return result


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    emp = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {
        "id": emp.id,
        "name": emp.name,
        "department": emp.department,
        "role": emp.role,
        "availability_hours_per_week": emp.availability_hours_per_week,
        "allocated_hours": emp.allocated_hours,
        "spare_hours": max(0, emp.availability_hours_per_week - emp.allocated_hours),
        "skills": emp.skills or [],
        "interests": emp.interests or [],
    }
