"""Оборудование и журнал простоев."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import DEFAULT_PAGE_SIZE
from app.db.database import get_db
from app.deps import get_current_user, require_any_role
from app.models.equipment import DowntimeRecord, Equipment
from app.models.user import User, UserRole
from app.schemas.equipment import (
    DowntimeCreate,
    DowntimeRead,
    DowntimeUpdate,
    EquipmentCreate,
    EquipmentRead,
    EquipmentUpdate,
)
from app.utils.audit import write_audit

router = APIRouter(prefix="/equipment", tags=["Оборудование"])
can_manage = require_any_role(UserRole.admin, UserRole.constructor)


@router.get("", response_model=list[EquipmentRead])
def list_equipment(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = DEFAULT_PAGE_SIZE,
) -> list[Equipment]:
    """Список оборудования."""

    q = select(Equipment).offset(skip).limit(min(limit, 200))
    return list(db.scalars(q).all())


@router.post("", response_model=EquipmentRead, status_code=201)
def create_equipment(
    payload: EquipmentCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(can_manage)],
) -> Equipment:
    """Создание записи оборудования."""

    e = Equipment(
        name=payload.name,
        workshop=payload.workshop,
        ideal_cycle_seconds=payload.ideal_cycle_seconds,
        is_active=payload.is_active,
    )
    db.add(e)
    db.flush()
    write_audit(db, user_id=user.id, action="equipment.create", entity_type="Equipment", entity_id=e.id)
    db.commit()
    db.refresh(e)
    return e


@router.patch("/{equipment_id}", response_model=EquipmentRead)
def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(can_manage)],
) -> Equipment:
    """Обновление оборудования."""

    e = db.get(Equipment, equipment_id)
    if not e:
        raise HTTPException(status_code=404, detail="Оборудование не найдено")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data:
        e.name = data["name"]
    if "workshop" in data:
        e.workshop = data["workshop"]
    if "ideal_cycle_seconds" in data:
        e.ideal_cycle_seconds = data["ideal_cycle_seconds"]
    if "is_active" in data and data["is_active"] is not None:
        e.is_active = data["is_active"]
    write_audit(db, user_id=user.id, action="equipment.update", entity_type="Equipment", entity_id=e.id, details=data)
    db.commit()
    db.refresh(e)
    return e


@router.delete("/{equipment_id}", status_code=204)
def delete_equipment(
    equipment_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(can_manage)],
) -> Response:
    """Удаление оборудования."""

    e = db.get(Equipment, equipment_id)
    if not e:
        raise HTTPException(status_code=404, detail="Оборудование не найдено")
    write_audit(db, user_id=user.id, action="equipment.delete", entity_type="Equipment", entity_id=e.id)
    db.delete(e)
    db.commit()
    return Response(status_code=204)


@router.get("/downtime", response_model=list[DowntimeRead])
def list_downtime(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    equipment_id: int | None = None,
    skip: int = 0,
    limit: int = DEFAULT_PAGE_SIZE,
) -> list[DowntimeRecord]:
    """Список записей простоя."""

    q = select(DowntimeRecord).order_by(DowntimeRecord.started_at.desc()).offset(skip).limit(min(limit, 200))
    if equipment_id is not None:
        q = q.where(DowntimeRecord.equipment_id == equipment_id)
    return list(db.scalars(q).all())


@router.post("/downtime", response_model=DowntimeRead, status_code=201)
def create_downtime(
    payload: DowntimeCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> DowntimeRecord:
    """Регистрация простоя."""

    if payload.ended_at <= payload.started_at:
        raise HTTPException(status_code=400, detail="Время окончания должно быть позже начала")
    d = DowntimeRecord(
        equipment_id=payload.equipment_id,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        reason_code=payload.reason_code,
        note=payload.note,
        created_by_id=user.id,
    )
    db.add(d)
    db.flush()
    write_audit(db, user_id=user.id, action="downtime.create", entity_type="DowntimeRecord", entity_id=d.id)
    db.commit()
    db.refresh(d)
    return d


@router.patch("/downtime/{downtime_id}", response_model=DowntimeRead)
def update_downtime(
    downtime_id: int,
    payload: DowntimeUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> DowntimeRecord:
    """Изменение записи простоя."""

    d = db.get(DowntimeRecord, downtime_id)
    if not d:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    data = payload.model_dump(exclude_unset=True)
    if "started_at" in data and data["started_at"] is not None:
        d.started_at = data["started_at"]
    if "ended_at" in data and data["ended_at"] is not None:
        d.ended_at = data["ended_at"]
    if "reason_code" in data:
        d.reason_code = data["reason_code"]
    if "note" in data:
        d.note = data["note"]
    if d.ended_at <= d.started_at:
        raise HTTPException(status_code=400, detail="Время окончания должно быть позже начала")
    write_audit(db, user_id=user.id, action="downtime.update", entity_type="DowntimeRecord", entity_id=d.id, details=data)
    db.commit()
    db.refresh(d)
    return d


@router.delete("/downtime/{downtime_id}", status_code=204)
def delete_downtime(
    downtime_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Удаление записи простоя."""

    d = db.get(DowntimeRecord, downtime_id)
    if not d:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    write_audit(db, user_id=user.id, action="downtime.delete", entity_type="DowntimeRecord", entity_id=d.id)
    db.delete(d)
    db.commit()
    return Response(status_code=204)
