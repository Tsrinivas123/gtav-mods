from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .config import ALLOWED_ORIGINS, DEBUG
from .routers import products, categories, cart, orders, newsletter, contact

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="PawanMod REST API",
    description="High-performance asynchronous API for PawanMod GTA V Marketplace. Powered by FastAPI & SQLAlchemy.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(products.router)
app.include_router(categories.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(newsletter.router)
app.include_router(contact.router)

# Mount Static & Media directories if present
static_dir = BASE_DIR / "static"
media_dir = BASE_DIR / "media"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

if media_dir.exists():
    app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")


@app.get("/", tags=["Root"])
def root():
    return {
        "app": "PawanMod FastAPI Backend",
        "version": "2.0.0",
        "status": "online",
        "documentation": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Diagnostic"])
def health_check():
    return {
        "status": "ok",
        "service": "fastapi",
        "engine": "uvicorn",
        "debug": DEBUG
    }

