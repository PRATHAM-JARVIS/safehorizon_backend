from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.app_debug)

# CORS
origins = settings.allowed_origins if settings.allowed_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
