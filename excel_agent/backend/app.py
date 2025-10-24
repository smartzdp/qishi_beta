"""
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import ingest, query, code, voice, files
from backend.config import settings
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Excel Agent API",
    description="智能Excel分析助手API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(code.router)
app.include_router(voice.router)
app.include_router(files.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Excel Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Starting Excel Agent API")
    logger.info(f"Data directory: {settings.data_dir}")
    logger.info(f"Knowledge base directory: {settings.knowledge_base_dir}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down Excel Agent API")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True
    )

