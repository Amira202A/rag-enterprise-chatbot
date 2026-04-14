from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import bcrypt
import jwt

from app.database.sql import SessionLocal
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin
from app.services.email_service import generate_password, send_password_email
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ MODIFICATION: ajout departments + is_admin dans le token
def create_token(user_id: int, cin: str, departments: list = None, is_admin: bool = False) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub":         str(user_id),
        "cin":         cin,
        "departments": departments or [],
        "is_admin":    is_admin,
        "exp":         expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ───────── REGISTER ─────────
@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):

    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    if db.query(User).filter(User.cin == user.cin).first():
        raise HTTPException(status_code=400, detail="CIN déjà enregistré")

    raw_password = generate_password()
    hashed = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

    new_user = User(
        nom=user.nom,
        prenom=user.prenom,
        cin=user.cin,
        email=user.email,
        password=hashed,
        departments=user.departments
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    sent = send_password_email(user.email, user.nom, raw_password)

    if not sent:
        db.delete(new_user)
        db.commit()
        raise HTTPException(status_code=500, detail="Erreur envoi email — compte non créé")

    return {"message": f"Compte créé ! Mot de passe envoyé à {user.email}"}


# ───────── LOGIN ─────────
@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.cin == credentials.cin).first()

    if not user:
        raise HTTPException(status_code=401, detail="CIN introuvable")

    if not bcrypt.checkpw(credentials.password.encode(), user.password.encode()):
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé")

    departments = user.get_departments_list()

    # ✅ token avec is_admin
    token = create_token(user.id, user.cin, departments, user.is_admin)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id":          user.id,
            "nom":         user.nom,
            "prenom":      user.prenom,
            "cin":         user.cin,
            "email":       user.email,
            "departments": departments,
            "is_admin":    user.is_admin
        }
    }


# ───────── TEST ─────────
@router.get("/test")
def test():
    return {"message": "Auth API OK"}


# ───────── ADMIN LOGIN ─────────
@router.post("/admin/login")
def admin_login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.cin == credentials.cin).first()

    if not user:
        raise HTTPException(status_code=401, detail="CIN introuvable")

    if not bcrypt.checkpw(credentials.password.encode(), user.password.encode()):
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")

    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Accès admin requis")

    departments = user.get_departments_list()

    # ✅ token avec is_admin
    token = create_token(user.id, user.cin, departments, user.is_admin)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id":          user.id,
            "nom":         user.nom,
            "prenom":      user.prenom,
            "cin":         user.cin,
            "email":       user.email,
            "departments": departments,
            "is_admin":    user.is_admin
        }
    }