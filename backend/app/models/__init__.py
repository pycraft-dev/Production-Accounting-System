"""ORM-модели (импорт для Alembic и метаданных)."""

from app.models.audit import AuditLog
from app.models.defect import Defect, DefectAttachment, DefectComment, DefectStatusHistory
from app.models.equipment import DowntimeRecord, Equipment
from app.models.erp import ErpEntityLink, ErpSyncRecord
from app.models.file import StoredFile
from app.models.project import Project
from app.models.report import DailyReport
from app.models.scheme import SchemeApprovalHistory, SchemeChange
from app.models.user import User, UserRole

__all__ = [
    "AuditLog",
    "User",
    "UserRole",
    "Project",
    "StoredFile",
    "Defect",
    "DefectAttachment",
    "DefectComment",
    "DefectStatusHistory",
    "SchemeChange",
    "SchemeApprovalHistory",
    "DailyReport",
    "Equipment",
    "DowntimeRecord",
    "ErpEntityLink",
    "ErpSyncRecord",
]
