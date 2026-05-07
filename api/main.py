"""SignDex FastAPI application."""

from __future__ import annotations

import logging

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from routes import clients as clients_routes
from routes import generate as generate_routes
from routes import render as render_routes
from routes import templates as templates_routes

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("signdex")

settings = get_settings()

app = FastAPI(
    title="SignDex API",
    description="Email signature templates + client database + ComeUp deliverables.",
    version="0.1.0",
)


@app.middleware("http")
async def log_errors_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Request failed: %s %s", request.method, request.url.path)
        raise


_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins if _origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,  # noqa: ARG001
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": str(exc) or "Internal Server Error",
            "error": "internal_server_error",
            "path": request.url.path,
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(clients_routes.router, prefix="/clients", tags=["clients"])
app.include_router(templates_routes.router, prefix="/templates", tags=["templates"])
app.include_router(render_routes.router, tags=["render"])
app.include_router(generate_routes.router, tags=["deliverables"])

