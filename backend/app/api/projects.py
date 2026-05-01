"""CRUD проектов (изделий)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.deps import get_current_user, require_any_role
from app.models.project import Project
from app.models.user import User, UserRole
from app.schemas.projects import ProjectCreate, ProjectRead
from app.utils.audit import write_audit

router = APIRouter(prefix="/projects", tags=["Проекты"])
can_manage_projects = require_any_role(UserRole.admin, UserRole.constructor)


@router.get("/", response_model=list[ProjectRead])
def list_projects(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 50,
) -> list[Project]:
    """Список проектов."""

    q = select(Project).offset(skip).limit(min(limit, 200))
    return list(db.scalars(q).all())


@router.post("/", response_model=ProjectRead)
def create_project(
    payload: ProjectCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(can_manage_projects)],
) -> Project:
    """Создание проекта (admin/constructor)."""

    p = Project(name=payload.name, code=payload.code, description=payload.description)
    db.add(p)
    db.flush()
    write_audit(db, user_id=user.id, action="project.create", entity_type="Project", entity_id=p.id)
    db.commit()
    db.refresh(p)
    return p


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Project:
    """Проект по идентификатору."""

    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Проект не найден")
    return p
