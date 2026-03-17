import asyncio
from typing import Annotated, Optional
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette_csrf import CSRFMiddleware
from backend.routers import auth, export, system, kiosk, webauthn, google, documents, notifications, warehouse, gateway, terminal, trz_export
from backend.graphql.schema import schema
from backend.database.database import get_db
from backend.database.session_proxy import LockedSession
from backend.database.transaction_manager import TransactionError, DeadlockError, ConcurrentModificationError
from backend.auth import jwt_utils
from backend import schemas
from backend.config import settings
from backend.graphql.dataloaders import create_dataloaders 
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.jobs.rotation_job import check_and_rotate_keys
from backend.jobs.contract_job import check_expired_contracts
from backend.jobs.inventory_check_job import check_inventory_levels
from backend.jobs.fleet_notifications_job import check_fleet_notifications
from fastapi.responses import JSONResponse
from fastapi import status
import logging
from backend.auth.limiter import limiter
from slowapi.errors import RateLimitExceeded
from backend.exceptions import CHRONOSException
from backend.utils.error_handling import get_error_message

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Scheduler
    scheduler = AsyncIOScheduler()
    # Run once a day to check for rotation
    scheduler.add_job(check_and_rotate_keys, 'interval', hours=24)
    # Run once a day to check for expired contracts
    scheduler.add_job(check_expired_contracts, 'interval', hours=24)
    # Run daily at 2:00 AM for inventory check
    scheduler.add_job(check_inventory_levels, 'cron', hour=2, minute=0)
    # Run daily at 6:00 AM for fleet notifications
    scheduler.add_job(check_fleet_notifications, 'cron', hour=6, minute=0)
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
    
    yield
    
    # Shutdown
    scheduler.shutdown()

# Force reload context - 2026-01-06 23:25
app = FastAPI(
    title="Chronos API", 
    version="1.3.0.0", 
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
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
            "retry_after": 1
        }
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
            "detail": str(exc) if settings.DEBUG else None
        }
    )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors"""
    logger.warning(f"Rate limit exceeded: {request.method} {request.url}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "message": "Превишихте броя на заявките. Моля, изчакайте малко и опитайте отново.",
            "retry_after": 1
        }
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
            "retry_after": 2  # Suggest retry after 2 seconds
        }
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
            "retry_after": 1
        }
    )

# CHRONOS Custom Exception Handlers
@app.exception_handler(CHRONOSException)
async def chronos_exception_handler(request: Request, exc: CHRONOSException):
    """Handle CHRONOS custom exceptions"""
    logger.error(f"CHRONOS error in {request.method} {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.detail
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "Chronos API",
        "version": "1.3.0.0"
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
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com https://apis.google.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: blob: https://lh3.googleusercontent.com https://ssl.gstatic.com; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "connect-src 'self' https://dev.oblak24.org http://localhost:14240 http://localhost:5173 http://192.168.1.92:4173 http://192.168.1.92:5173 http://192.168.1.92:14240 https://accounts.google.com https://oauth2.googleapis.com https://play.google.com; "
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
    cookie_secure=True,           # HTTPS only
    cookie_httponly=False,        # Allow JS to read for double-submit
    cookie_samesite="strict",    # Strict same-site policy
    exempt_urls=[
        re.compile(r"^/auth/.*"),      # Exempt auth endpoints
        re.compile(r"^/google/.*"),   # Exempt Google auth
        re.compile(r"^/docs.*"),      # Exempt docs
        re.compile(r"^/redoc.*"),     # Exempt redoc
        re.compile(r"^/graphql.*"),    # Exempt GraphQL for now
        re.compile(r"^/gateways/.*"),  # Exempt Gateway endpoints
        re.compile(r"^/kiosk/scan"),   # Exempt Kiosk scan
        re.compile(r"^/kiosk/terminal/.*"), # Exempt unified terminal endpoints
    ],
    safe_methods={"GET", "HEAD", "OPTIONS", "TRACE"},
)


# Configure CORS - specific origins only
ALLOWED_ORIGINS = [
    "https://dev.oblak24.org",
    "https://oblak24.org",
    "https://auth.oblak24.org",
    "https://auth.dev.oblak24.org",
    "http://localhost:5173",
    "http://localhost:14240",
    "http://192.168.1.92:5173",
    "http://192.168.1.92:4173",
    "http://192.168.1.92:14240",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
from fastapi.staticfiles import StaticFiles
import os

# ... same imports ...

app.include_router(documents.router)

# Mount uploads for static access (avatars, documents)
if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

from backend.graphql.dataloaders import create_dataloaders 

async def get_context(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Optional[schemas.User], Depends(jwt_utils.get_optional_current_user)],
):
    dataloaders = create_dataloaders(db)
    return {
        "request": request,
        "db": db,
        "current_user": current_user,
        "dataloaders": dataloaders,
    }

graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
async def read_root():
    return {"message": "Welcome to Chronos API!"}
