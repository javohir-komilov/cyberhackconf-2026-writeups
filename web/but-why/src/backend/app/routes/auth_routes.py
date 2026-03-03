from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import create_token
from app.database import get_db
from app.models import User

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


# ──────────────────────────────────────
# 1️⃣  Registration – ALWAYS broken
# ──────────────────────────────────────
@router.post("/register")
def register(body: RegisterRequest):
    raise HTTPException(status_code=400, detail="But Why?")


# ──────────────────────────────────────
# 2️⃣  Login – user enumeration vuln
# ──────────────────────────────────────
@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # INTENTIONALLY plaintext comparison
    if user.password != body.password:
        raise HTTPException(status_code=401, detail="Wrong password")

    token = create_token(user.username, user.user_id, user.role)
    return {"access_token": token, "token_type": "bearer"}
