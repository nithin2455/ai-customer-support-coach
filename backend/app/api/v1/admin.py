from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_admin
from app.models.domain import Department, Agent, User

router = APIRouter()


@router.get("/departments")
def list_departments(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    depts = db.query(Department).all()
    return [{"id": d.id, "name": d.name, "code": d.code, "description": d.description} for d in depts]


@router.get("/agents")
def list_agents(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    agents = db.query(Agent).all()
    res = []
    for a in agents:
        u = a.user
        dept_name = a.department.name if a.department else "General Support"
        res.append({
            "id": a.id,
            "name": u.name,
            "email": u.email,
            "status": a.status,
            "skill_level": a.skill_level,
            "department": dept_name
        })
    return res
