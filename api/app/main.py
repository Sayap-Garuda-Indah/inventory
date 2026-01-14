from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import (
    auth,
    users_route,
    units_route,
    items_route,
    category_route,
    issue_route,
    issue_item_route,
    settings_route,
    locations_route,
    stock_tx_route,
    audit_route,
    # test_auth
)
from app.middleware import LoggingMiddleware, AuthContextMiddleware
from db.pool import init_pool, close_pool
from core.logging import configure_logging
from core.config import settings
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Configure logging
    configure_logging()

    # Startup: Initialize DB pool
    init_pool()
    yield

    # Shutdown: Close DB pool
    close_pool()

app = FastAPI(title="Inventory API", version="1.0.0", lifespan=lifespan)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# CORS middleware (restrict to LAN only)
# app.middleware("http")(LoggingMiddleware)
# app.middleware("http")(AuthContextMiddleware)

app.include_router(auth.router)
app.include_router(users_route.router)
# app.include_router(items_route.router)
app.include_router(units_route.router)
app.include_router(items_route.router)
app.include_router(category_route.router)
app.include_router(issue_route.router)
app.include_router(issue_item_route.router)
app.include_router(settings_route.router)
app.include_router(locations_route.router)
app.include_router(stock_tx_route.router)
app.include_router(audit_route.router)
if settings.DEBUG:
    pass
    # app.include_router(test_auth.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
