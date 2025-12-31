from dotenv import load_dotenv
load_dotenv()
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.rate_limit import limiter
from app.db.session import engine, Base
from app.api import router as api_router
from app.api import auth
from app import __version__
from app.ai.chroma_manager import initialize_chroma
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This tells Python: "Start the server NOW, and run this function in the background"
    asyncio.create_task(initialize_heavy_resources(app))
    yield

async def initialize_heavy_resources(app: FastAPI):
    logging.info("Starting heavy initialization in background...")
    try:
        chroma_client, chroma_collection = initialize_chroma()
        app.state.chroma_client = chroma_client
        app.state.chroma_collection = chroma_collection
        logging.info("ChromaDB successfully initialized in background.")
    except Exception as e:
        logging.error(f"ChromaDB failed: {e}")    

app = FastAPI(
    title="BridgeAI Backend",
    version=__version__,
    lifespan=lifespan  # Attach the lifespan handler
)

app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Too many requests."})

# Update origins for production
origins = [
    "http://localhost:3000",
    "https://bridgeai-ai.vercel.app", # Your frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For your project grade, "*" is the safest to avoid CORS errors
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(auth.router)

@app.get("/")
def root():
    return {"status": "alive", "version": __version__}


