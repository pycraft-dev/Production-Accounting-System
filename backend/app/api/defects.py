"""API учёта брака."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import DEFECT_WORKSHOP_CHOICES, MAX_DEFECT_MEDIA_BYTES, DEFAULT_PAGE_SIZE
from app.db.database import get_db
from app.deps import get_current_user
from app.models.defect import Defect, DefectAttachment, DefectComment, DefectStatus, DefectStatusHistory
from app.models.user import User
from app.schemas.defects import (
    DefectCommentCreate,
    DefectCommentRead,
    DefectCreate,
    DefectRead,
    DefectReadDetail,
    DefectUpdate,
)
from app.services import file_service
from app.services.notification_service import notify_defect_created
from app.utils.audit import write_audit

router = APIRouter(prefix="/defects", tags=["Брак"])


def _run_notify_defect_created(user_ids: list[int], title: str, defect_id: int) -> None:
    """Синхронная обёртка для фоновой рассылки (создаёт новую сессию БД)."""

    import asyncio

    from sqlalchemy import select

    from app.db.database import get_session_factory
    from app.models.user import User

    factory = get_session_factory()
    with factory() as session:
        users = list(session.scalars(select(User).where(User.id.in_(user_ids))).all())
    asyncio.run(notify_defect_created(users, title, defect_id))


@router.get("", response_model=list[DefectRead])
def list_defects(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = DEFAULT_PAGE_SIZE,
    workshop: str | None = None,
    status_filter: DefectStatus | None = None,
    mine: bool = False,
) -> list[Defect]:
    """Список заявок с фильтрами. ``mine=true`` — только созданные текущим пользователем."""

    q = select(Defect).order_by(Defect.created_at.desc()).offset(skip).limit(min(limit, 200))
    if mine:
        q = q.where(Defect.created_by_id == user.id)
    if workshop:
        q = q.where(Defect.workshop == workshop)
    if status_filter is not None:
        q = q.where(Defect.status == status_filter)
    return list(db.scalars(q).all())


@router.get("/workshops", response_model=list[str])
def list_defect_workshops(_: Annotated[User, Depends(get_current_user)]) -> list[str]:
    """Список цехов для выбора в форме брака (синхронно с клиентами)."""

    return list(DEFECT_WORKSHOP_CHOICES)


@router.get("/{defect_id}", response_model=DefectReadDetail)
def get_defect(
    defect_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> DefectReadDetail:
    """Детали заявки."""

    d = db.get(Defect, defect_id)
    if not d:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    ids = [a.file_id for a in d.attachments]
    base = DefectRead.model_validate(d)
    return DefectReadDetail(**base.model_dump(), attachment_file_ids=ids)


@router.post("", response_model=DefectRead, status_code=201)
async def create_defect(
    payload: DefectCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    background: BackgroundTasks,
) -> Defect:
    """Создание заявки."""

    d = Defect(
        description=payload.description,
        workshop=payload.workshop,
        priority=payload.priority,
        category=payload.category,
        part_number=payload.part_number,
        machine=payload.machine,
        project_id=payload.project_id,
        assignee_id=payload.assignee_id,
        created_by_id=user.id,
    )
    db.add(d)
    db.flush()
    write_audit(db, user_id=user.id, action="defect.create", entity_type="Defect", entity_id=d.id)
    db.commit()
    db.refresh(d)

    all_users = list(db.scalars(select(User)).all())
    user_ids = [u.id for u in all_users]
    background.add_task(_run_notify_defect_created, user_ids, d.description[:120], d.id)
    return d


@router.post("/{defect_id}/photos", response_model=DefectReadDetail)
async def upload_defect_photo(
    defect_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
) -> DefectReadDetail:
    """Загрузка фото к заявке."""

    d = db.get(Defect, defect_id)
    if not d:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    content = await file.read()
    if len(content) > MAX_DEFECT_MEDIA_BYTES:
        raise HTTPException(status_code=400, detail="Файл слишком большой (макс. 50 МБ)")
    mime = file.content_type or "application/octet-stream"
    if mime not in file_service.ALLOWED_DEFECT_MEDIA_TYPES:
        raise HTTPException(status_code=400, detail="Недопустимый тип файла (разрешены фото JPEG/PNG/WebP и видео MP4/WebM/MOV)")
    sf = file_service.save_uploaded_file(
        db,
        content=content,
        original_filename=file.filename or "attach.bin",
        mime_type=mime,
        uploaded_by_id=user.id,
    )
    kind = "video" if mime.startswith("video/") else "photo"
    att = DefectAttachment(defect_id=d.id, file_id=sf.id, kind=kind)
    db.add(att)
    write_audit(db, user_id=user.id, action="defect.photo", entity_type="Defect", entity_id=d.id, details={"file_id": sf.id})
    db.commit()
    db.refresh(d)
    ids = [a.file_id for a in d.attachments]
    base = DefectRead.model_validate(d)
    return DefectReadDetail(**base.model_dump(), attachment_file_ids=ids)


@router.patch("/{defect_id}", response_model=DefectRead)
def update_defect(
    defect_id: int,
    payload: DefectUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Defect:
    """Обновление заявки."""

    d = db.get(Defect, defect_id)
    if not d:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    old_status = d.status
    data = payload.model_dump(exclude_unset=True)
    if "description" in data:
        d.description = data["description"]
    if "workshop" in data:
        d.workshop = data["workshop"]
    if "status" in data and data["status"] is not None:
        d.status = data["status"]
        db.add(
            DefectStatusHistory(
                defect_id=d.id,
                user_id=user.id,
                old_status=old_status,
                new_status=data["status"],
            )
        )
    if "priority" in data:
        d.priority = data["priority"]
    if "category" in data:
        d.category = data["category"]
    if "part_number" in data:
        d.part_number = data["part_number"]
    if "machine" in data:
        d.machine = data["machine"]
    if "project_id" in data:
        d.project_id = data["project_id"]
    if "assignee_id" in data:
        d.assignee_id = data["assignee_id"]
    write_audit(db, user_id=user.id, action="defect.update", entity_type="Defect", entity_id=d.id, details=data)
    db.commit()
    db.refresh(d)
    return d


@router.delete("/{defect_id}", status_code=204)
def delete_defect(
    defect_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Удаление заявки (автор или администратор — проверка упрощена: любой авторизованный в v1)."""

    d = db.get(Defect, defect_id)
    if not d:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    write_audit(db, user_id=user.id, action="defect.delete", entity_type="Defect", entity_id=d.id)
    db.delete(d)
    db.commit()
    return Response(status_code=204)


@router.post("/{defect_id}/comments", response_model=DefectCommentRead, status_code=201)
def add_comment(
    defect_id: int,
    payload: DefectCommentCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> DefectComment:
    """Комментарий к заявке."""

    d = db.get(Defect, defect_id)
    if not d:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    c = DefectComment(defect_id=d.id, user_id=user.id, body=payload.body)
    db.add(c)
    write_audit(db, user_id=user.id, action="defect.comment", entity_type="Defect", entity_id=d.id)
    db.commit()
    db.refresh(c)
    return c
