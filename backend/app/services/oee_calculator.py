"""Расчёт OEE: приоритет детального журнала, fallback на отчёты."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.equipment import DowntimeRecord, Equipment
from app.models.report import DailyReport


@dataclass
class OeeInputs:
    """Промежуточные величины для расчёта."""

    planned_minutes: float
    downtime_minutes: float
    operating_minutes: float
    good_units: float
    total_units: float
    ideal_cycle_seconds: float | None
    source_notes: str


def _combine_date(dt: date, end_of_day: bool = False) -> datetime:
    """Строит datetime в UTC для границы дня (начало или конец)."""

    if end_of_day:
        return datetime.combine(dt, time(23, 59, 59, 999999), tzinfo=timezone.utc)
    return datetime.combine(dt, time.min, tzinfo=timezone.utc)


def collect_oee_inputs(
    db: Session,
    date_from: date,
    date_to: date,
    equipment_id: int | None,
) -> OeeInputs:
    """
    Собирает входные данные для OEE за период.

    Правило слияния:
    - Если задан ``equipment_id`` и есть записи ``DowntimeRecord`` на этом
      оборудовании, **простои суммируются из журнала**; плановое время берётся
      как сумма фактических минут работы из ``DailyReport``, отфильтрованных
      по тому же ``equipment_id``, либо, если отчётов нет — как сумма длительностей
      интервалов минус простой (оценка эксплуатации).
    - Если журнала простоев нет, используются агрегаты ``planned_work_minutes``,
      ``actual_work_minutes``, ``good_quantity``, ``scrap_quantity`` из отчётов
      (без привязки к оборудованию либо с фильтром по ``equipment_id``).

    Данные **не дублируются**: при наличии детальных простоев для выбранного
    оборудования расчёт доступности опирается на них; иначе — только на отчёты.
    """

    t0 = _combine_date(date_from, False)
    t1 = _combine_date(date_to, True)

    ideal_cycle: float | None = None
    notes: list[str] = []

    dt_sum = (
        select(func.coalesce(func.sum(func.extract("epoch", DowntimeRecord.ended_at - DowntimeRecord.started_at) / 60.0), 0.0))
        .where(
            DowntimeRecord.started_at >= t0,
            DowntimeRecord.ended_at <= t1,
        )
    )
    if equipment_id is not None:
        dt_sum = dt_sum.where(DowntimeRecord.equipment_id == equipment_id)
        eq = db.get(Equipment, equipment_id)
        if eq and eq.ideal_cycle_seconds is not None:
            ideal_cycle = float(eq.ideal_cycle_seconds)

    downtime_minutes = float(db.scalar(dt_sum) or 0.0)

    q_reports = select(DailyReport).where(DailyReport.report_date >= date_from, DailyReport.report_date <= date_to)
    if equipment_id is not None:
        q_reports = q_reports.where(DailyReport.equipment_id == equipment_id)
    reports = list(db.scalars(q_reports).all())

    planned = sum(float(r.planned_work_minutes or 0) for r in reports)
    actual = sum(float(r.actual_work_minutes or 0) for r in reports)
    good = sum(float(r.good_quantity or 0) for r in reports)
    scrap = sum(float(r.scrap_quantity or 0) for r in reports)

    has_journal = False
    if equipment_id is not None:
        cnt = db.scalar(
            select(func.count()).select_from(DowntimeRecord).where(
                DowntimeRecord.equipment_id == equipment_id,
                DowntimeRecord.started_at >= t0,
                DowntimeRecord.ended_at <= t1,
            )
        )
        has_journal = bool(cnt and cnt > 0)

    if has_journal:
        notes.append("Доступность: учтены простои из журнала оборудования.")
        operating = max(actual - downtime_minutes, 0.0) if actual else max(planned - downtime_minutes, 0.0)
        planned_for_a = planned if planned > 0 else max(actual, operating + downtime_minutes)
    else:
        notes.append("Детальный журнал простоев за период отсутствует — используются отчёты.")
        planned_for_a = planned if planned > 0 else actual
        operating = actual if actual > 0 else max(planned_for_a - downtime_minutes, 0.0)

    total_units = good + scrap
    source_notes = " ".join(notes)
    return OeeInputs(
        planned_minutes=max(planned_for_a, 1e-6),
        downtime_minutes=downtime_minutes,
        operating_minutes=max(operating, 1e-6),
        good_units=good,
        total_units=max(total_units, 1e-6),
        ideal_cycle_seconds=ideal_cycle,
        source_notes=source_notes,
    )


def compute_oee_fractions(inp: OeeInputs) -> tuple[float, float, float, float]:
    """
    Считает доли доступности, производительности, качества и OEE.

    :returns: (availability, performance, quality, oee) в диапазоне [0, 1].
    """

    availability = min(max(inp.operating_minutes / inp.planned_minutes, 0.0), 1.0)
    if inp.ideal_cycle_seconds and inp.ideal_cycle_seconds > 0:
        ideal_run_minutes = (inp.total_units * inp.ideal_cycle_seconds) / 60.0
        performance = min(max(ideal_run_minutes / inp.operating_minutes, 0.0), 1.0)
    else:
        performance = 1.0 if inp.total_units <= 0 else min(max((inp.good_units / inp.total_units) * 1.0, 0.0), 1.0)
    quality = min(max(inp.good_units / inp.total_units, 0.0), 1.0)
    oee = availability * performance * quality
    return availability, performance, quality, oee
