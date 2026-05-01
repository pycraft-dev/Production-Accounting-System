"""API версий схем (чертежей)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants import DEFAULT_PAGE_SIZE, MAX_PHOTO_UPLOAD_BYTES
from app.db.database import get_db
from app.deps import get_current_user, require_any_role
from app.models.project import Project
from app.models.scheme import ApprovalStatus, SchemeApprovalHistory, SchemeChange
from app.models.user import User, UserRole
from app.schemas.schemes import (
    PdfAnnotationCreate,
    SchemeApprovalNote,
    SchemeChangeRead,
    SchemeChangeUpdate,
)
from app.services import file_service
from app.services.notification_service import notify_scheme_updated
from app.utils.audit import write_audit

router = APIRouter(prefix="/schematics", tags=["Схемы"])
can_edit = require_any_role(UserRole.admin, UserRole.constructor)


def _run_notify_scheme(user_ids: list[int], project_name: str, version: int) -> None:
    """Фоновая рассылка об обновлении схемы."""

    import asyncio

    from sqlalchemy import select as sa_select

    from app.db.database import get_session_factory
    from app.models.user import User

    factory = get_session_factory()
    with factory() as session:
        users = list(session.scalars(sa_select(User).where(User.id.in_(user_ids))).all())
    asyncio.run(notify_scheme_updated(users, project_name, version))


@router.get("/project/{project_id}", response_model=list[SchemeChangeRead])
def list_scheme_versions(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = DEFAULT_PAGE_SIZE,
) -> list[SchemeChange]:
    """История версий схем по проекту."""

    q = (
        select(SchemeChange)
        .where(SchemeChange.project_id == project_id)
        .order_by(SchemeChange.version.desc())
        .offset(skip)
        .limit(min(limit, 200))
    )
    return list(db.scalars(q).all())


@router.post("/project/{project_id}", response_model=SchemeChangeRead, status_code=201)
async def upload_new_version(
    project_id: int,
    background: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(can_edit)],
    change_description: str = Form(..., min_length=1),
    approval_status: str = Form(default="draft"),
    file: UploadFile = File(...),
) -> SchemeChange:
    """
    Загрузка новой версии файла схемы (multipart: описание + файл).
    """

    proj = db.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Проект не найден")
    try:
        appr = ApprovalStatus(approval_status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректный статус согласования")
    content = await file.read()
    if len(content) > MAX_PHOTO_UPLOAD_BYTES * 5:
        raise HTTPException(status_code=400, detail="Файл слишком большой")
    mime = file.content_type or "application/octet-stream"
    if mime not in file_service.ALLOWED_SCHEME_TYPES:
        raise HTTPException(status_code=400, detail="Допустимы PDF или изображения PNG/JPEG")
    ver = db.scalar(select(func.coalesce(func.max(SchemeChange.version), 0)).where(SchemeChange.project_id == project_id))
    next_ver = int(ver or 0) + 1
    sf = file_service.save_uploaded_file(
        db,
        content=content,
        original_filename=file.filename or "scheme.pdf",
        mime_type=mime,
        uploaded_by_id=user.id,
    )
    row = SchemeChange(
        project_id=project_id,
        version=next_ver,
        change_description=change_description,
        approval_status=appr,
        file_id=sf.id,
        created_by_id=user.id,
    )
    db.add(row)
    db.flush()
    write_audit(db, user_id=user.id, action="scheme.create", entity_type="SchemeChange", entity_id=row.id)
    db.commit()
    db.refresh(row)

    user_ids = [u.id for u in db.scalars(select(User)).all()]
    background.add_task(_run_notify_scheme, user_ids, proj.name, row.version)
    return row


@router.get("/{scheme_id}", response_model=SchemeChangeRead)
def get_scheme(
    scheme_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> SchemeChange:
    """Версия схемы по id."""

    s = db.get(SchemeChange, scheme_id)
    if not s:
        raise HTTPException(status_code=404, detail="Версия не найдена")
    return s


@router.patch("/{scheme_id}", response_model=SchemeChangeRead)
def patch_scheme(
    scheme_id: int,
    payload: SchemeChangeUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(can_edit)],
) -> SchemeChange:
    """Обновление метаданных версии."""

    s = db.get(SchemeChange, scheme_id)
    if not s:
        raise HTTPException(status_code=404, detail="Версия не найдена")
    data = payload.model_dump(exclude_unset=True)
    old = s.approval_status
    if "change_description" in data:
        s.change_description = data["change_description"]
    if "approval_status" in data and data["approval_status"] is not None:
        s.approval_status = data["approval_status"]
        db.add(
            SchemeApprovalHistory(
                scheme_change_id=s.id,
                user_id=user.id,
                old_status=old,
                new_status=data["approval_status"],
            )
        )
    write_audit(db, user_id=user.id, action="scheme.update", entity_type="SchemeChange", entity_id=s.id, details=data)
    db.commit()
    db.refresh(s)
    return s


@router.post("/{scheme_id}/annotations", response_model=SchemeChangeRead)
def add_annotation(
    scheme_id: int,
    payload: PdfAnnotationCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> SchemeChange:
    """Добавляет аннотацию к PDF (хранится как JSON, отдельно от файла)."""

    s = db.get(SchemeChange, scheme_id)
    if not s:
        raise HTTPException(status_code=404, detail="Версия не найдена")
    ann = payload.model_dump()
    lst = list(s.pdf_annotations or [])
    lst.append(ann)
    s.pdf_annotations = lst
    write_audit(db, user_id=user.id, action="scheme.annotate", entity_type="SchemeChange", entity_id=s.id)
    db.commit()
    db.refresh(s)
    return s


@router.post("/{scheme_id}/approval", response_model=SchemeChangeRead)
def approval_transition(
    scheme_id: int,
    payload: SchemeApprovalNote,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(can_edit)],
) -> SchemeChange:
    """Смена статуса согласования с примечанием."""

    s = db.get(SchemeChange, scheme_id)
    if not s:
        raise HTTPException(status_code=404, detail="Версия не найдена")
    old = s.approval_status
    s.approval_status = payload.new_status
    db.add(
        SchemeApprovalHistory(
            scheme_change_id=s.id,
            user_id=user.id,
            old_status=old,
            new_status=payload.new_status,
            note=payload.note,
        )
    )
    write_audit(db, user_id=user.id, action="scheme.approval", entity_type="SchemeChange", entity_id=s.id)
    db.commit()
    db.refresh(s)
    return s
