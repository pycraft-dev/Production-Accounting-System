"""Генерация Excel и PDF для отчётов."""

from __future__ import annotations

import io
from datetime import date, datetime
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

DATE_FMT = "%d.%m.%Y"


def format_ru_date(d: date | datetime) -> str:
    """Форматирует дату для отображения."""

    if isinstance(d, datetime):
        return d.strftime(DATE_FMT)
    return d.strftime(DATE_FMT)


def build_defects_excel(rows: list[dict[str, Any]]) -> bytes:
    """
    Строит Excel со списком брака.

    :param rows: словари с полями для таблицы.
    :returns: содержимое .xlsx в памяти.
    """

    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Брак")
    return buf.getvalue()


def build_simple_pdf(title: str, lines: list[str]) -> bytes:
    """
    Строит простой PDF с заголовком и строками текста.

    :param title: заголовок документа.
    :param lines: абзацы.
    :returns: bytes PDF.
    """

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story: list[Any] = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
    for line in lines:
        story.append(Paragraph(line.replace("\n", "<br/>"), styles["Normal"]))
        story.append(Spacer(1, 6))
    doc.build(story)
    return buf.getvalue()


def build_table_pdf(title: str, headers: list[str], data_rows: list[list[Any]]) -> bytes:
    """
    PDF с таблицей (аналитика, сводки).

    :param title: заголовок.
    :param headers: шапка таблицы.
    :param data_rows: строки (значения приводятся к строке).
    """

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
    table_data = [headers] + [[str(c) for c in row] for row in data_rows]
    tbl = Table(table_data, repeatRows=1)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    story.append(tbl)
    doc.build(story)
    return buf.getvalue()
