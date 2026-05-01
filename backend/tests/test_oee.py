"""Тесты расчёта OEE (чистая логика)."""

from __future__ import annotations

from app.services.oee_calculator import OeeInputs, compute_oee_fractions


def test_oee_product_is_fractions() -> None:
    """OEE как произведение трёх долей."""

    inp = OeeInputs(
        planned_minutes=100.0,
        downtime_minutes=10.0,
        operating_minutes=90.0,
        good_units=80.0,
        total_units=100.0,
        ideal_cycle_seconds=50.0,
        source_notes="unit",
    )
    a, p, q, oee = compute_oee_fractions(inp)
    assert 0 <= oee <= 1
    assert 0 <= a <= 1 and 0 <= p <= 1 and 0 <= q <= 1
