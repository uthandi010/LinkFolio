from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401 - registers all tables on Base.metadata before create_all()
from .config import get_settings
from .database import Base, engine
from .routers import analytics, auth, links, me, public

settings = get_settings()

# Creates tables if they don't exist yet. Fine for a project this size; a
# larger app would use Alembic migrations instead.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LinkFolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(me.router)
app.include_router(links.router)
app.include_router(analytics.router)
app.include_router(public.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
