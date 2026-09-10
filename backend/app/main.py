from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_database
from app.errors import register_exception_handlers
from app.orders.router import router as orders_router
from app.schemas import ApiResponse


def create_app(initialize_database: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        if initialize_database:
            init_database()
        yield

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
