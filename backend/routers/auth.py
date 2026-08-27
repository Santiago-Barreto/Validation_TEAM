from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.core.auth import AuthUser, require_user, verify_id_token
from backend.core.config import AUTH_ALLOWED_DOMAINS, GOOGLE_OAUTH_CLIENT_ID

router = APIRouter(prefix="/auth", tags=["Auth"])


class TokenBody(BaseModel):
    credential: str


@router.get("/config")
def auth_config():
    return {
        "client_id": GOOGLE_OAUTH_CLIENT_ID or "",
        "allowed_domains": sorted(AUTH_ALLOWED_DOMAINS),
        "enabled": bool(GOOGLE_OAUTH_CLIENT_ID),
    }


@router.post("/verify")
def auth_verify(body: TokenBody):
    user = verify_id_token(body.credential)
    return {
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }


@router.get("/me")
def auth_me(user: AuthUser = Depends(require_user)):
    return {
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }
