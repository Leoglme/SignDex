"""SignDex FastAPI application."""

from __future__ import annotations

import logging

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from core.security import get_current_user, require_admin
from routes import access as access_routes
from routes import auth as auth_routes
from routes import clients as clients_routes
from routes import generate as generate_routes
from routes import organizations as organizations_routes
from routes import portal as portal_routes
from routes import render as render_routes
from routes import services as services_routes
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
    except Exception as exc:
        logger.exception("Request failed: %s %s", request.method, request.url.path)
        # On RENVOIE la 500 ici (au lieu de re-raise) : ce middleware est à l'intérieur du
        # CORSMiddleware, donc la réponse ressort avec les en-têtes CORS. Sinon un 500 non géré
        # remonte au-dessus du CORS → réponse sans `Access-Control-Allow-Origin` → le navigateur
        # affiche une erreur « CORS » opaque au lieu de la vraie erreur 500.
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": str(exc) or "Internal Server Error",
                "error": "internal_server_error",
                "path": request.url.path,
            },
        )


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


# Auth : ouvert. Accès (invitations) : auth par endpoint (admin OU propriétaire de l'espace).
# Tout le reste (outils d'administration SignDex) : réservé à l'admin.
app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(access_routes.router, prefix="/organizations", tags=["access"])
app.include_router(portal_routes.router, prefix="/portal", tags=["portal"])
app.include_router(
    clients_routes.router, prefix="/clients", tags=["clients"], dependencies=[Depends(require_admin)],
)
app.include_router(
    organizations_routes.router,
    prefix="/organizations",
    tags=["organizations"],
    dependencies=[Depends(require_admin)],
)
app.include_router(
    templates_routes.router, prefix="/templates", tags=["templates"], dependencies=[Depends(require_admin)],
)
app.include_router(render_routes.router, tags=["render"], dependencies=[Depends(require_admin)])
app.include_router(generate_routes.router, tags=["deliverables"], dependencies=[Depends(require_admin)])
app.include_router(services_routes.router, tags=["services"], dependencies=[Depends(require_admin)])

