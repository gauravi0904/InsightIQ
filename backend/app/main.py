import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.app.core.config import settings
from backend.app.core.database import init_db, get_db_status
from backend.app.api.routes import api_router

# Setup application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("insightiq.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application startup
    logger.info("Initializing %s backend...", settings.PROJECT_NAME)
    settings.ensure_directories()
    db_ok = init_db()
    if not db_ok:
        logger.warning(
            "Startup Notice: Could not connect to primary MySQL database. "
            "InsightIQ is operating in degraded / fallback mode. "
            "Please ensure MySQL is running and verify DATABASE_URL in .env."
        )
    else:
        logger.info("Database initialized successfully.")
    yield
    # Application shutdown
    logger.info("Shutting down %s backend.", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="InsightIQ - Smart Data Analytics & Machine Learning Platform API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    clean_errors = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        clean_errors.append(f"{loc}: {err.get('msg')}")
    logger.warning("Validation error on %s: %s", request.url.path, clean_errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Invalid request parameters.",
            "errors": clean_errors
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception processing %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred while processing your request. Please try again or inspect backend logs."
        }
    )


# Health Endpoint
@app.get("/health", tags=["Health"])
def health_check():
    db_status = get_db_status()
    is_healthy = db_status.get("connected", False)
    return {
        "status": "ok" if is_healthy else "degraded",
        "service": settings.PROJECT_NAME,
        "tagline": settings.PROJECT_TAGLINE,
        "database": "connected" if is_healthy else "disconnected",
        "database_info": db_status
    }


# Include API Routers
app.include_router(api_router)
