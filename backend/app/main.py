"""Точка входа FastAPI."""

from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import admin, analytics, auth, daily_reports, defects, equipment, erp, export, files, projects, schematics, version
from app.core.config import get_settings
from app.core.logging_config import setup_logging

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Создаёт и настраивает приложение."""

    settings = get_settings()
    setup_logging(settings.log_path)
    app = FastAPI(title="Production Accounting System", version=settings.app_version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        """Добавляет идентификатор запроса в заголовок ответа."""

        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        """Сообщения валидации на русском."""

        return JSONResponse(
            status_code=422,
            content={"detail": "Ошибка валидации входных данных", "errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        """Необработанные ошибки: лог и общий ответ."""

        if isinstance(exc, HTTPException):
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        logger.exception("Необработанное исключение: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Внутренняя ошибка сервера"},
        )

    app.include_router(auth.router, prefix="/api")
    app.include_router(version.router, prefix="/api")
    app.include_router(admin.router, prefix="/api")
    app.include_router(projects.router, prefix="/api")
    app.include_router(defects.router, prefix="/api")
    app.include_router(schematics.router, prefix="/api")
    app.include_router(daily_reports.router, prefix="/api")
    app.include_router(equipment.router, prefix="/api")
    app.include_router(files.router, prefix="/api")
    app.include_router(analytics.router, prefix="/api")
    app.include_router(export.router, prefix="/api")
    app.include_router(erp.router, prefix="/api")

    @app.get("/health")
    def health() -> dict[str, str]:
        """Проверка работоспособности."""

        return {"status": "ok"}

    return app


app = create_app()
