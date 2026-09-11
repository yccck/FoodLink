from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from typing import AsyncIterator, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import SessionLocal, init_database
from app.errors import register_exception_handlers
from app.orders.service import auto_complete_overdue_orders
from app.orders.router import router as orders_router
from app.auth_routes.router import router as auth_router
from app.products.router import router as products_router
from app.admin.router import router as admin_router
from app.schemas import ApiResponse


logger = logging.getLogger(__name__)
AUTO_SETTLEMENT_INTERVAL_SECONDS = 15


def _run_auto_settlement_once() -> None:
    with SessionLocal() as db:
        auto_complete_overdue_orders(db)


async def _auto_settlement_worker() -> None:
    while True:
        try:
            await asyncio.to_thread(_run_auto_settlement_once)
        except Exception:
            logger.exception("automatic order settlement failed")
        await asyncio.sleep(AUTO_SETTLEMENT_INTERVAL_SECONDS)


def create_app(initialize_database: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        settlement_task = None
        if initialize_database:
            init_database()
            settlement_task = asyncio.create_task(_auto_settlement_worker())
        try:
            yield
        finally:
            if settlement_task is not None:
                settlement_task.cancel()
                with suppress(asyncio.CancelledError):
                    await settlement_task

    application = FastAPI(
        title="FoodLink API",
        version="1.0.0",
        description="食愿 Web 项目公共后端接口",
        docs_url="/doc.html",
        redoc_url=None,
        openapi_url="/openapi.json",
        swagger_ui_parameters={"persistAuthorization": True},
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(application)
    application.include_router(auth_router)
    application.include_router(products_router)
    application.include_router(admin_router)
    application.include_router(orders_router)

    @application.get(
        "/api/health",
        response_model=ApiResponse[Dict[str, str]],
        tags=["系统"],
        summary="服务健康检查",
    )
    def health() -> ApiResponse[Dict[str, str]]:
        return ApiResponse(data={"status": "ok"})

    return application


app = create_app()
