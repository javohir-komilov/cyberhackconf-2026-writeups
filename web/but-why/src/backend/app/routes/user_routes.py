from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import md5_hash, verify_token
from app.database import get_db
from app.models import User

router = APIRouter()


# ──────────────────────────────────────
# 5️⃣  /me – trusts query param (IDOR)
# ──────────────────────────────────────
@router.get("/me")
def me(user_id: Optional[str] = None, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """
    INTENTIONAL VULNERABILITY:
    The endpoint trusts the `user_id` query parameter instead of the JWT payload.
    An attacker can supply any MD5-hashed user_id to access other users' data.
    """
    # No user_id param → simple greeting from JWT
    if user_id is None:
        return {"message": f"Hello {token.get('username')}"}

    # Find user whose md5(real_user_id) matches the supplied query param
    all_users = db.query(User).all()
    for u in all_users:
        if md5_hash(u.user_id) == user_id:
            return {"username": u.username, "user_id": u.user_id, "role": u.role}

    raise HTTPException(status_code=404, detail="User not found")
