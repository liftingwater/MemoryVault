from typing import Any, Dict

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.auth import get_current_user
from app.config import settings
from app.routers import cards_router, coaching_router, decks_router, review_router
from app.services import review_service

app = FastAPI(title="MemoryVault API")

# Register routers under /api so the SPA (served from the same CloudFront
# domain) keeps ownership of its own client-side routes like /decks/[id].
app.include_router(decks_router, prefix="/api")
app.include_router(cards_router, prefix="/api")
app.include_router(review_router, prefix="/api")
app.include_router(coaching_router, prefix="/api")

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
    """Protected dashboard endpoint. Returns basic user info plus review stats."""
    user_id = user["user_id"]
    return {
        "message": "Welcome to MemoryVault",
        "user_id": user_id,
        "email": user.get("email"),
        "cards_due": review_service.get_cards_due_count(user_id),
        "streak": review_service.get_streak(user_id),
    }


handler = Mangum(app, lifespan="off")
