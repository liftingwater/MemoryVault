from typing import Any, Dict

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.auth import get_current_user
from app.config import settings
from app.routers import decks_router

app = FastAPI(title="MemoryVault API")

# Register routers under /api so the SPA (served from the same CloudFront
# domain) keeps ownership of its own client-side routes like /decks/[id].
app.include_router(decks_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard")
async def dashboard(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Protected dashboard endpoint. Returns basic user info."""
    return {
        "message": "Welcome to MemoryVault",
        "user_id": user["user_id"],
        "email": user.get("email"),
    }


handler = Mangum(app, lifespan="off")
