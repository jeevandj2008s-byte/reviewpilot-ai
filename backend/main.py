import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.config import settings
from backend.database import init_db
from backend.routers import reviews, settings as settings_router, export

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema
    init_db()
    yield

app = FastAPI(
    title="ReviewPilot API",
    description="AI-powered customer review analysis and instant reply management for small businesses",
    version="1.0.0",
    docs_url="/docs" if (settings.debug or settings.environment == "development") else None,
    redoc_url="/redoc" if (settings.debug or settings.environment == "development") else None,
    openapi_url="/openapi.json" if (settings.debug or settings.environment == "development") else None,
    lifespan=lifespan
)

import time
import uuid
import logging
from collections import defaultdict
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger("reviewpilot.server")

# In-memory sliding-window rate limiter for sensitive endpoints
# Protects write / verification endpoints (e.g. settings updates, test pings, batch analyze)
RATE_LIMIT_STORE = defaultdict(list)

def check_rate_limit(client_ip: str, route_key: str, max_attempts: int, window_seconds: int) -> bool:
    """Checks if a client IP has exceeded the allowed request threshold within window_seconds."""
    now = time.time()
    key = f"{client_ip}:{route_key}"
    # Keep timestamps within the sliding window
    RATE_LIMIT_STORE[key] = [ts for ts in RATE_LIMIT_STORE[key] if now - ts < window_seconds]
    if len(RATE_LIMIT_STORE[key]) >= max_attempts:
        return False
    RATE_LIMIT_STORE[key].append(now)
    return True

# Determine allowed CORS origins
cors_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
if not cors_origins:
    if settings.environment == "production":
        # In production without explicit external origins, restrict to same-origin
        cors_origins = ["https://reviewpilot-web.onrender.com"]
    else:
        # Development local origins
        cors_origins = [
            f"http://localhost:{settings.port}",
            f"http://127.0.0.1:{settings.port}",
            "http://localhost:8000",
            "http://127.0.0.1:8000"
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
)

# Global Security Headers & Rate Limiting Middleware
@app.middleware("http")
async def security_headers_and_rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    # Rate limiting on Authentication endpoints (brute-force defense)
    if path.startswith("/api/auth/login") and request.method == "POST":
        if not check_rate_limit(client_ip, "auth_login", max_attempts=8, window_seconds=60):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many login attempts. Please wait 1 minute before trying again."}
            )

    if path.startswith("/api/auth/register") and request.method == "POST":
        if not check_rate_limit(client_ip, "auth_register", max_attempts=5, window_seconds=60):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many account registrations from this IP. Please try again later."}
            )

    # Rate limiting on write/sensitive routes (Settings, Telegram test ping, Batch analysis)
    if path == "/api/telegram/test" and request.method == "POST":
        if not check_rate_limit(client_ip, "telegram_test", max_attempts=5, window_seconds=60):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many verification requests. Please try again in 1 minute."}
            )

    if path == "/api/settings" and request.method == "POST":
        if not check_rate_limit(client_ip, "settings_update", max_attempts=10, window_seconds=60):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many settings modification requests. Please slow down."}
            )

    if path == "/api/analyze" and request.method == "POST":
        if not check_rate_limit(client_ip, "analyze_batch", max_attempts=20, window_seconds=60):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded for review batch analysis. Please try again shortly."}
            )

    # Protection against catastrophic data wipe abuse
    if path == "/api/data/delete-all" and request.method == "DELETE":
        if not check_rate_limit(client_ip, "delete_all_data", max_attempts=3, window_seconds=60):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many deletion requests. Please wait before attempting again."}
            )

    # Protection against mass data export scraping
    if path.startswith("/api/export") and request.method == "GET":
        if not check_rate_limit(client_ip, "export_data", max_attempts=10, window_seconds=60):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Export rate limit exceeded. Please wait a minute before requesting another export."}
            )

    response = await call_next(request)

    # Inject Production Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://api.anthropic.com https://api.telegram.org; "
        "frame-ancestors 'none';"
    )

    return response

# Global sanitized exception handler — never leak stack traces, database details, or file paths
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = str(uuid.uuid4())
    logger.error(f"Unhandled server exception [{correlation_id}] on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"An internal server error occurred. (Correlation ID: {correlation_id})"
        }
    )

# Include API Routers
from backend.routers import auth as auth_router
from backend.routers import ai_chat as ai_chat_router
app.include_router(auth_router.router)
app.include_router(ai_chat_router.router)
app.include_router(reviews.router)
app.include_router(settings_router.router)
app.include_router(export.router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ReviewPilot",
        "version": "1.0.0",
        "environment": settings.environment
    }

# Mount static frontend directory
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/dashboard")
    async def serve_dashboard():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/analyzer")
    async def serve_analyzer():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/settings")
    async def serve_settings():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.host, port=settings.port, reload=True)

