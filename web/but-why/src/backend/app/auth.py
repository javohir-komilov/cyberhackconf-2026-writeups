import hashlib
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# INTENTIONALLY weak secret key
SECRET_KEY = "!!!luckynumber7"
ALGORITHM = "HS256"

security = HTTPBearer()


def md5_hash(value: int) -> str:
    return hashlib.md5(str(value).encode()).hexdigest()


def create_token(username: str, user_id: int, role: str) -> str:
    payload = {
        "username": username,
        "user_id": md5_hash(user_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
