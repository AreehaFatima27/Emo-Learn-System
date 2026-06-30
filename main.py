from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

from database.connection import engine
from database.models import Base

# Import routers
from routes.auth import router as auth_router
from routes.quiz import router as quiz_router
from routes.sentiment import router as sentiment_router, router_emotions
from routes.users import router as users_router
from routes.admin import router as admin_router
from routes.placeholders import router as placeholders_router

# ─────────────────────────────────────────
# App Init
# ─────────────────────────────────────────
app = FastAPI(
    title="EmoLearn API",
    description="Emotion-Aware AI Quiz Platform — Phase 1 MVP",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ─────────────────────────────────────────
# CORS — allow frontend on port 5173
# ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
# Startup — create all tables
# ─────────────────────────────────────────
@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    print("EmoLearn API started - all tables ready.")


# ─────────────────────────────────────────
# Register Routers
# ─────────────────────────────────────────
app.include_router(auth_router)
app.include_router(quiz_router)
app.include_router(sentiment_router)
app.include_router(router_emotions)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(placeholders_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "app": "EmoLearn API",
        "version": "1.0.0",
        "phase": 1,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
