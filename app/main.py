import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import advisor

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("DebtMind Advisor API starting up")
    yield
    logger.info("DebtMind Advisor API shutting down")


app = FastAPI(
    title="DebtMind Advisor API",
    description="AI-powered debt advisory API for n8n and LLM integration",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(advisor.router, prefix="/advisor", tags=["advisor"])


@app.get("/health")
async def health():
    return {"status": "ok"}
