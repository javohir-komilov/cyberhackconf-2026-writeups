import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import md5_hash, verify_token
from app.database import get_db
from app.models import User

router = APIRouter()

# NavkarX's real user_id
NAVKARX_USER_ID = 144
NAVKARX_USER_ID_MD5 = md5_hash(NAVKARX_USER_ID)


class PenguinMessage(BaseModel):
    message: str


# ──────────────────────────────────────
# 6️⃣  /penguin – Blind OS Command Injection
# ──────────────────────────────────────
@router.post("/penguin")
def penguin(body: PenguinMessage, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """
    INTENTIONAL VULNERABILITY:
    - Only NavkarX (user_id=144) can access this endpoint.
    - The `message` field is directly concatenated into a shell command.
    - No sanitization → Blind OS Command Injection.
    """
    # Check if the authenticated user is NavkarX
    if token.get("user_id") != NAVKARX_USER_ID_MD5:
        raise HTTPException(status_code=403, detail="Access denied")

    # INTENTIONALLY UNSAFE: direct shell command execution
    command = f"echo {body.message}"
    os.system(command)  # noqa: S605 S607 – intentionally vulnerable

    return {"detail": "Message sent to penguin!"}
