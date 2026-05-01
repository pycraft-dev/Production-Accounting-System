"""Администрирование: пользователи и журнал аудита."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.database import get_db
from app.deps import require_role
from app.models.audit import AuditLog
from app.models.user import User, UserRole
from app.schemas.users import AdminPasswordChange, AuditLogRead, UserCreate, UserRead, UserUpdate
from app.utils.audit import write_audit

router = APIRouter(prefix="/admin", tags=["Администрирование"])
admin_user = require_role(UserRole.admin)


def _docs_root() -> Path:
    """Каталог docs в корне репозитория (рядом с backend/)."""

    return Path(__file__).resolve().parents[3] / "docs"


def _safe_doc_file(filename: str) -> Path:
    if "/" in filename or "\\" in filename or not filename.lower().endswith(".md"):
        raise HTTPException(status_code=404, detail="Недопустимый файл")
    root = _docs_root()
    if not root.is_dir():
        raise HTTPException(status_code=404, detail="Папка docs не найдена на сервере")
    candidate = (root / Path(filename).name).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        raise HTTPException(status_code=404, detail="Недопустимый путь")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return candidate


class AdminDocItem(BaseModel):
    """Элемент списка документации."""

    filename: str
    title: str


@router.get("/docs", response_model=list[AdminDocItem])
def list_admin_docs(_: Annotated[User, Depends(admin_user)]) -> list[AdminDocItem]:
    """Список markdown из каталога docs/ (только admin)."""

    root = _docs_root()
    if not root.is_dir():
        return []
    return [
        AdminDocItem(filename=p.name, title=p.stem.replace("_", " "))
        for p in sorted(root.glob("*.md"), key=lambda x: x.name.lower())
    ]


@router.get("/docs/{filename}")
def get_admin_doc(
    filename: str,
    _: Annotated[User, Depends(admin_user)],
) -> PlainTextResponse:
    """Текст одного файла документации."""

    path = _safe_doc_file(filename)
    return PlainTextResponse(path.read_text(encoding="utf-8"), media_type="text/markdown; charset=utf-8")


@router.get("/users", response_model=list[UserRead])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(admin_user)],
    skip: int = 0,
    limit: int = 50,
) -> list[User]:
    """Список пользователей."""

    q = select(User).offset(skip).limit(min(limit, 200))
    return list(db.scalars(q).all())


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(admin_user)],
) -> User:
    """Создаёт пользователя (только admin)."""

    exists = db.scalar(select(User).where(User.email == payload.login))
    if exists:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже есть")
    user = User(
        email=payload.login,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        profile_notes=payload.profile_notes,
        must_change_password=payload.must_change_password,
    )
    db.add(user)
    db.flush()
    write_audit(
        db,
        user_id=actor.id,
        action="user.create",
        entity_type="User",
        entity_id=user.id,
        details={"login": user.email},
    )
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(admin_user)],
) -> User:
    """Обновляет пользователя."""

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    data = payload.model_dump(exclude_unset=True)
    if "full_name" in data:
        user.full_name = data["full_name"]
    if "role" in data:
        user.role = data["role"]
    if "is_active" in data:
        user.is_active = data["is_active"]
    if "profile_notes" in data:
        user.profile_notes = data["profile_notes"]
    write_audit(db, user_id=actor.id, action="user.update", entity_type="User", entity_id=user.id, details=data)
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/change-password", status_code=status.HTTP_204_NO_CONTENT)
def admin_change_password(
    user_id: int,
    payload: AdminPasswordChange,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(admin_user)],
) -> Response:
    """Смена пароля выбранного пользователя (только admin)."""

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.hashed_password = hash_password(payload.new_password)
    user.must_change_password = False
    write_audit(
        db,
        user_id=actor.id,
        action="user.change_password",
        entity_type="User",
        entity_id=user.id,
        details={"target_login": user.email},
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(admin_user)],
) -> Response:
    """
    Отключает учётную запись (мягкое «удаление»: ``is_active=False``).

    Полное удаление строки из БД невозможно при связанных записях (брак и т.д.).
    """

    if user_id == actor.id:
        raise HTTPException(status_code=400, detail="Нельзя отключить свою учётную запись")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.is_active = False
    write_audit(db, user_id=actor.id, action="user.deactivate", entity_type="User", entity_id=user.id, details={"login": user.email})
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/audit", response_model=list[AuditLogRead])
def list_audit(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(admin_user)],
    action: str | None = None,
    entity_type: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[AuditLog]:
    """Просмотр журнала аудита с фильтрами."""

    q = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(min(limit, 200))
    if action:
        q = q.where(AuditLog.action == action)
    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)
    return list(db.scalars(q).all())
