from fastapi import APIRouter, Depends, HTTPException, status

from engine import db as db_module
from .. import auth
from ..schemas import UserCreate, LoginRequest, TokenResponse
from ..deps import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: UserCreate, conn=Depends(get_db)):
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (payload.email,)).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    hash_hex, salt_hex = auth.hash_password(payload.password)
    cur = conn.execute(
        "INSERT INTO users (email, password_hash, password_salt, role) VALUES (?, ?, ?, ?)",
        (payload.email, hash_hex, salt_hex, payload.role),
    )
    conn.commit()
    user_id = cur.lastrowid
    token = auth.create_access_token(user_id, payload.email, payload.role)
    return TokenResponse(access_token=token, role=payload.role)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, conn=Depends(get_db)):
    row = conn.execute("SELECT * FROM users WHERE email = ?", (payload.email,)).fetchone()
    if not row or not auth.verify_password(payload.password, row["password_hash"], row["password_salt"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    conn.execute(
        "INSERT INTO audit_log (user_id, action, detail_json) VALUES (?, 'login', '{}')",
        (row["id"],),
    )
    conn.commit()
    token = auth.create_access_token(row["id"], row["email"], row["role"])
    return TokenResponse(access_token=token, role=row["role"])