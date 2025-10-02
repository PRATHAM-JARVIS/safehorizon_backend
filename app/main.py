from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import traceback

from .config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.app_debug)

# CORS - Allow frontend to access the API
origins = settings.get_allowed_origins if hasattr(settings, 'get_allowed_origins') else settings.allowed_origins
if not origins or origins == ["*"]:
    # Default to allow localhost and common frontend ports
    origins = [
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",  # React/Next default
        "http://localhost:8080",  # Vue default
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "*"  # Allow all for development
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Expose all headers to frontend
)

logger.info(f"CORS configured with origins: {origins}")


# Global exception handler for better error responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return proper error response"""
    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error occurred. Please check server logs for details.",
            "error_type": type(exc).__name__
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


# Include routers (registered later once created)
from .routers import tourist, authority, admin, ai, notify  # noqa: E402

app.include_router(tourist.router, prefix=settings.api_prefix, tags=["tourist"])
app.include_router(authority.router, prefix=settings.api_prefix, tags=["authority"])
app.include_router(admin.router, prefix=settings.api_prefix, tags=["admin"])
app.include_router(ai.router, prefix=settings.api_prefix, tags=["ai"])
app.include_router(notify.router, prefix=settings.api_prefix, tags=["notify"])
