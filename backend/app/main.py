from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.auth import get_current_user
from app.config import settings

app = FastAPI(title="MemoryVault API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/dashboard")
async def dashboard(user: dict[str, str | None] = Depends(get_current_user)) -> dict[str, str | None]:
    """Protected dashboard endpoint. Returns basic user info."""
    return {
        "message": "Welcome to MemoryVault",
        "user_id": user["user_id"],
        "email": user.get("email"),
    }


handler = Mangum(app, lifespan="off")
