import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import Annotated

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette_csrf.middleware import CSRFMiddleware
from strawberry.fastapi import GraphQLRouter

from backend import schemas
from backend.auth import jwt_utils
from backend.config import settings
from backend.database.database import get_db
from backend.database.transaction_manager import (
    ConcurrentModificationError,
    DeadlockError,
    TransactionError,
)
from backend.graphql.dataloaders import create_dataloaders
from backend.graphql.schema import schema
from backend.jobs.contract_job import check_expired_contracts
from backend.jobs.fleet_notifications_job import check_fleet_notifications
from backend.jobs.inventory_check_job import check_inventory_levels
from backend.jobs.maintenance_job import check_scheduled_maintenance
from backend.jobs.rotation_job import check_and_rotate_keys
from backend.jobs.update_scheduler_job import check_scheduled_update
from backend.routers import (
    auth,
    deploy,
    documents,
    export,
    gateway,
    google,
    kiosk,
    notifications,
    system,
    terminal,
    trz_export,
    warehouse,
    webauthn,
)

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Set specific loggers to INFO
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)

from slowapi.errors import RateLimitExceeded

from backend.auth.limiter import limiter
from backend.exceptions import CHRONOSException

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Scheduler
    scheduler = AsyncIOScheduler()
    # Run once a day to check for rotation
    scheduler.add_job(check_and_rotate_keys, "interval", hours=24)
    # Run once a day to check for expired contracts
    scheduler.add_job(check_expired_contracts, "interval", hours=24)
    # Run daily at 2:00 AM for inventory check
    scheduler.add_job(check_inventory_levels, "cron", hour=2, minute=0)
    # Run daily at 6:00 AM for fleet notifications
    scheduler.add_job(check_fleet_notifications, "cron", hour=6, minute=0)
    # Silence APScheduler executor INFO logs (they spam "Running job..." every interval)
    logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)

    # Run every 1 minute to check for scheduled maintenance activation
    scheduler.add_job(check_scheduled_maintenance, "interval", minutes=1)
    # Run every 5 minutes to check for scheduled auto-update activation
    scheduler.add_job(check_scheduled_update, "interval", minutes=5)
    scheduler.start()

    # Run check with delay on startup to ensure DB is initialized
    async def delayed_startup_jobs():
        await asyncio.sleep(10) # 10 seconds buffer for DB initialization
        try:
            logger.info("Starting initial background jobs check...")
            await check_and_rotate_keys()
            await check_expired_contracts()
            logger.info("Initial background jobs check completed.")
        except Exception as e:
            logger.error(f"Error during initial background jobs check: {e}")

    asyncio.create_task(delayed_startup_jobs())

    # Start behavioral analysis scheduler
    try:
        from backend.modules.behavioral_analysis.scheduler import start_scheduler
        start_scheduler()
        logger.info("Behavioral analysis scheduler initialized")
    except Exception as e:
        logger.error(f"Failed to start behavioral analysis scheduler: {e}")

    yield

    # Shutdown behavioral analysis scheduler
    try:
        from backend.modules.behavioral_analysis.scheduler import stop_scheduler
        stop_scheduler()
    except Exception as e:
        logger.error(f"Failed to stop behavioral analysis scheduler: {e}")

    # Shutdown
    scheduler.shutdown()

# Force reload context - 2026-01-06 23:25
app = FastAPI(
    title="Chronos API",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors"""
    logger.warning(f"Rate limit exceeded: {request.method} {request.url}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "message": "Превишихте броя на заявките. Моля, изчакайте малко и опитайте отново.",
            "retry_after": 1,
        },
    )

# Transaction Error Handlers
@app.exception_handler(TransactionError)
async def transaction_exception_handler(request: Request, exc: TransactionError):
    """Handle transaction errors with proper rollback"""
    logger.error(f"Transaction error in {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database transaction failed",
            "message": "Възникна грешка при операция с базата данни. Моля, опитайте отново.",
            "detail": str(exc) if settings.DEBUG else None,
        },
    )

@app.exception_handler(DeadlockError)
async def deadlock_exception_handler(request: Request, exc: DeadlockError):
    """Handle deadlock errors with user-friendly message"""
    logger.warning(f"Deadlock detected in {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "Database conflict",
            "message": "Конфликт с друга операция. Моля, изчакайте няколко секунди и опитайте отново.",
            "retry_after": 2,  # Suggest retry after 2 seconds
        },
    )

@app.exception_handler(ConcurrentModificationError)
async def concurrent_modification_exception_handler(request: Request, exc: ConcurrentModificationError):
    """Handle concurrent modification errors"""
    logger.warning(f"Concurrent modification in {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "Concurrent modification",
            "message": "Данните са променени от друг потребител. Моля, опреснете страницата и опитайте отново.",
            "retry_after": 1,
        },
    )

# CHRONOS Custom Exception Handlers
@app.exception_handler(CHRONOSException)
async def chronos_exception_handler(request: Request, exc: CHRONOSException):
    """Handle CHRONOS custom exceptions
    
    Returns consistent error format:
    {
        "error": "ERROR_CODE",
        "message": "Human readable message",
        "timestamp": "2024-01-01T12:00:00",
        "context": {...}
    }
    """
    logger.error(
        f"CHRONOS error [{exc.error_code}] in {request.method} {request.url}: {exc.detail}",
        extra={"original_error": str(exc.original_error) if exc.original_error else None},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "Chronos API",
        "version": settings.VERSION,
        "uptime": "TODO",  # Could be implemented with a startup timestamp
    }

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # HSTS - only if HTTPS is intended (Strict Transport Security)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevent Clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permissions Policy - allow geolocation and camera for Kiosk mode
        response.headers["Permissions-Policy"] = "geolocation=(self), camera=(self), microphone=()"
        # Content Security Policy (CSP)
        # Added domains for Google OAuth and local development
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://accounts.google.com https://apis.google.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: blob: https://lh3.googleusercontent.com https://ssl.gstatic.com; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "connect-src 'self' https://chronos.oblak24.org https://dev.oblak24.org http://localhost:14240 http://192.168.1.92:14240 https://accounts.google.com https://oauth2.googleapis.com https://play.google.com; "
            "frame-src https://accounts.google.com; "
            "frame-ancestors 'none'; "
            "object-src 'none';"
        )
        return response

app.add_middleware(SecurityHeadersMiddleware)

# CSRF Protection - exempt auth endpoints, protect everything else
import re

app.add_middleware(
    CSRFMiddleware,
    secret=settings.CSRF_SECRET_KEY,
    cookie_name="csrf_token",
    cookie_path="/",
    cookie_domain=None,
    cookie_secure=settings.COOKIE_SECURE,
    cookie_httponly=False,
    cookie_samesite="strict",
    exempt_urls=[
        re.compile(r"^/auth/"),
        re.compile(r"^/google/"),
        re.compile(r"^/docs"),
        re.compile(r"^/redoc"),
        re.compile(r"^/gateways/"),
        re.compile(r"^/webhook/"),
        re.compile(r"^/kiosk/scan"),
        re.compile(r"^/kiosk/terminal/"),
        re.compile(r"^/terminal/"),
        re.compile(r"^/graphql"),
    ],
    safe_methods={"GET", "HEAD", "OPTIONS", "TRACE"},
)


# Configure CORS - from config with fallback defaults
# Enforce HTTPS in production (allow localhost for dev)
def get_cors_origins():
    raw = settings.BACKEND_CORS_ORIGINS
    if isinstance(raw, str):
        origins = [o.strip() for o in raw.split(",") if o.strip()]
    elif isinstance(raw, list):
        origins = [str(o).strip() for o in raw if o]
    else:
        origins = []
    if not origins:
        origins = [
            "https://chronos.oblak24.org",
            "https://auth.chronos.oblak24.org",
            "https://api.github.com",
            "http://localhost:5173",
            "http://localhost:14240",
            "http://192.168.1.92:5173",
            "http://192.168.1.92:4173",
            "http://192.168.1.92:14240",
        ]
    for origin in origins:
        if origin.startswith("http://") and "localhost" not in origin and "127.0.0.1" not in origin and "192.168." not in origin:
            logger.warning(f"Removing insecure HTTP origin: {origin}")
    origins = [o for o in origins if not (o.startswith("http://") and "localhost" not in o and "127.0.0.1" not in o and "192.168." not in o)]
    if settings.FRONTEND_URL not in origins:
        origins.append(settings.FRONTEND_URL)
    return origins

cors_origins = get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-CSRFToken",
        "X-Requested-With",
        "Accept",
        "Accept-Language",
    ],
    expose_headers=["Content-Length", "X-Request-ID"],
)

app.include_router(auth.router)
app.include_router(export.router)
app.include_router(trz_export.router)
app.include_router(system.router)
app.include_router(notifications.router)
app.include_router(warehouse.router)
app.include_router(kiosk.router)
app.include_router(gateway.router)
app.include_router(terminal.router)
app.include_router(webauthn.router)
app.include_router(google.router)
app.include_router(deploy.router)
import os

from fastapi.staticfiles import StaticFiles

app.include_router(documents.router)

# Mount uploads for static access (avatars, documents)
if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


async def get_context(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[schemas.User | None, Depends(jwt_utils.get_optional_current_user)],
):
    dataloaders = create_dataloaders(db)
    return {
        "request": request,
        "db": db,
        "current_user": current_user,
        "dataloaders": dataloaders,
    }

graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
async def read_root():
    return {"message": "Welcome to Chronos API!"}
