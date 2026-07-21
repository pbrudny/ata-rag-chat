import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import settings

_security = HTTPBasic()


def require_admin_auth(credentials: HTTPBasicCredentials = Depends(_security)) -> None:
    valid_user = secrets.compare_digest(credentials.username, settings.basic_auth_user)
    valid_password = secrets.compare_digest(credentials.password, settings.basic_auth_password)
    if not (valid_user and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
