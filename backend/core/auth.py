from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from backend.core.config import AUTH_ALLOWED_DOMAINS, GOOGLE_OAUTH_CLIENT_ID

logger = logging.getLogger(__name__)
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthUser:
    email: str
    name: str
    picture: str = ""


def _domain_allowed(email: str) -> bool:
    email = (email or "").strip().lower()
    if "@" not in email:
        return False
    domain = email.rsplit("@", 1)[-1]
    return domain in AUTH_ALLOWED_DOMAINS


def verify_id_token(token: str) -> AuthUser:
    if not GOOGLE_OAUTH_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="GOOGLE_OAUTH_CLIENT_ID no configurado en el servidor.",
        )
    try:
        payload = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            GOOGLE_OAUTH_CLIENT_ID,
            clock_skew_in_seconds=60,
        )
    except Exception as e:
        logger.warning("Token Google inválido: %s", e)
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada.") from e

    email = str(payload.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=401, detail="El token no incluye correo.")
    if not payload.get("email_verified", False):
        raise HTTPException(status_code=401, detail="Correo de Google no verificado.")
    if not _domain_allowed(email):
        raise HTTPException(
            status_code=403,
            detail=f"Solo se permiten cuentas @{', @'.join(sorted(AUTH_ALLOWED_DOMAINS))}.",
        )

    name = str(payload.get("name") or email.split("@")[0]).strip()
    picture = str(payload.get("picture") or "")
    return AuthUser(email=email, name=name, picture=picture)


def require_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> AuthUser:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión.")
    return verify_id_token(creds.credentials)
