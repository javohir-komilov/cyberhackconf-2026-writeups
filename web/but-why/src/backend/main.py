import random
import string

from fastapi import FastAPI

from app.database import Base, SessionLocal, engine
from app.models import User
from app.routes.auth_routes import router as auth_router
from app.routes.penguin_routes import router as penguin_router
from app.routes.user_routes import router as user_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

app = FastAPI(
    title="CTF Challenge API",
    version="1.0.0",
    docs_url=None,        # отключаем Swagger UI (/docs)
    redoc_url=None,       # отключаем ReDoc (/redoc)
    openapi_url=None      # отключаем OpenAPI JSON (/openapi.json)
)

# =====================CORS==================================


# Разрешить всё
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # все домены
    allow_credentials=True,   # разрешить cookies
    allow_methods=["*"],      # все HTTP методы
    allow_headers=["*"],      # все заголовки
)
# ===========================================================

# ── Register routers ──────────────────────────────────────
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(penguin_router)


# ── Helpers ───────────────────────────────────────────────
def _random_password(length: int = 12) -> str:
    chars = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.choices(chars, k=length))


# ── Seed data ─────────────────────────────────────────────
SEED_USERS = [
    {"username": "QoraTulpor", "user_id": 104},
    {"username": "ZiyoWave",   "user_id": 127},
    {"username": "OltinShamol","user_id": 112},
    {"username": "SamoSky",    "user_id": 102},
    {"username": "YulduzFlow", "user_id": 56},
    {"username": "NavkarX",    "user_id": 144, "role": "manager"},
    {"username": "BunyodX",    "user_id": 52},
    {"username": "SirdaryoX",  "user_id": 12},
    {"username": "EchoUz",     "user_id": 48},
    {"username": "RuxDev",     "user_id": 174},
    {"username": "Turanix",    "user_id": 5},
    {"username": "MirzoByte",  "user_id": 108},
    {"username": "QalqonDev",  "user_id": 10},
    {"username": "ShukhratOne","user_id": 186},
]

SPECIAL_USER = {"username": "turandev", "password": "turandev!@#", "user_id": 110}


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Only seed if the table is empty
        if db.query(User).count() > 0:
            return

        # Regular users with random passwords
        for u in SEED_USERS:
            db.add(User(
                user_id=u["user_id"],
                username=u["username"],
                password=_random_password(),
                role=u.get("role", "user"),
            ))

        # Special user with known credentials
        db.add(User(
            user_id=SPECIAL_USER["user_id"],
            username=SPECIAL_USER["username"],
            password=SPECIAL_USER["password"],
        ))

        db.commit()
    finally:
        db.close()


# ── Startup event ─────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    seed_database()
