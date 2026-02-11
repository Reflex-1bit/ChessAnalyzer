from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import init_db
from app.routers import health, games, recommendations, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init DB (SQLite by default)
    await init_db()
    yield
    # Shutdown (if needed)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Chess Coach AI (heuristic)",
        version="0.1.0",
        lifespan=lifespan
    )

    # CORS middleware - Allow frontend to access backend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=False,  # Must be False when using "*"
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Routers
    app.include_router(health.router, prefix="", tags=["health"])
    app.include_router(games.router)
    app.include_router(recommendations.router)
    app.include_router(analytics.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
