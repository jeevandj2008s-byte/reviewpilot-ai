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
    lifespan=lifespan
)

# Enable CORS for cross-origin flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
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

