import os

from contextlib import asynccontextmanager
from .services.http_client import init_http_clients, close_http_clients
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.v1.api import api_router
from .models import base
from .core.database import engine

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await init_http_clients()
    try:
        yield
    finally:
        # shutdown
        await close_http_clients()

def create_app() -> FastAPI:
    app = FastAPI(title="Land-SaaS", version="1.0.0", lifespan=lifespan)

    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router, prefix="/api/v1")

    @app.on_event("startup")
    async def on_startup() -> None:
        # run migrations automatically in dev
        if settings.AUTO_MIGRATE:
            import alembic.config, pathlib, os
            cfg = alembic.config.Config(str(pathlib.Path(__file__).parent.parent / "alembic.ini"))
            alembic.command.upgrade(cfg, "head")

    return app

app = create_app()
