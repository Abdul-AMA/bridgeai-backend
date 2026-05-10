import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

# Configure logging to show INFO level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from slowapi.errors import RateLimitExceeded  # noqa: E402
from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware  # noqa: E402

from app import __version__  # noqa: E402
from app.ai.chroma_manager import initialize_chroma  # noqa: E402
from app.api import auth  # noqa: E402
from app.api import memory  # noqa: E402
from app.api import router as api_router  # noqa: E402
from app.core.middleware import SecurityHeadersMiddleware  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402

async def _run_worker(name: str, coro, critical: bool = False):
    """Start or stop a background worker, logging errors. Re-raises if critical=True."""
    try:
        await coro()
        logging.info(f"{name} started.")
    except Exception as e:
        logging.error(f"{name} failed: {e}")
        if critical:
            raise


async def _stop_worker(name: str, coro):
    try:
        await coro()
        logging.info(f"{name} stopped.")
    except Exception as e:
        logging.error(f"Failed to stop {name}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting BridgeAI services...")

    # ChromaDB is critical — if it fails, RAG and embeddings are broken for all requests.
    try:
        chroma_client, chroma_collection = initialize_chroma()
        app.state.chroma_client = chroma_client
        app.state.chroma_collection = chroma_collection
        logging.info("ChromaDB initialized.")
    except Exception as e:
        logging.error(f"ChromaDB initialization failed: {e}")
        raise

    from app.services.background_crs_generator import start_crs_worker, stop_crs_worker
    from app.services.background_summary_generator import start_summary_worker, stop_summary_worker

    await _run_worker("CRS worker", start_crs_worker)
    await _run_worker("Summary worker", start_summary_worker)

    yield

    await _stop_worker("CRS worker", stop_crs_worker)
    await _stop_worker("Summary worker", stop_summary_worker)


app = FastAPI(
    title="BridgeAI Backend",
    version=__version__,
    lifespan=lifespan,  # Attach the lifespan handler
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Too many requests."})


# Update origins for production
origins = [
    "http://localhost:3000",  # your frontend React app
    "http://localhost:3001",  # alternative frontend port
    "http://127.0.0.1:3000",  # localhost IP variant
    "http://127.0.0.1:3001",  # alternative port IP variant
    "https://bridgeai-ai.vercel.app",  # Your frontend URL
]

# ✅ Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)


# Request size limit middleware
class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Limit request body size to 10MB
        max_size = 10 * 1024 * 1024
        if request.headers.get("content-length"):
            content_length = int(request.headers["content-length"])
            if content_length > max_size:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large. Maximum size is 10MB."},
                )
        return await call_next(request)


app.add_middleware(RequestSizeLimitMiddleware)

# ✅ Add CORS middleware only once
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Trust proxy headers (X-Forwarded-Proto, X-Forwarded-For) from nginx
# This ensures redirects use HTTPS when behind a reverse proxy
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

app.include_router(api_router, prefix="/api")

# Mount static files for avatars
import os
# Ensure public directory exists
os.makedirs("public/avatars", exist_ok=True)

# Mount static files with HTML=True to serve files properly
app.mount("/public", StaticFiles(directory="public"), name="public")


@app.get("/")
def root():
    return {"status": "alive", "version": __version__}


@app.get("/health")
def health_check():
    """Health check endpoint for Docker and monitoring"""
    return {"status": "healthy", "version": __version__}
