from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import bcrypt
import jwt
import random
import string
from pydantic import BaseModel

from app.database.sql import SessionLocal
from app.models.user import User
from app.models.otp import OTPCode
from app.schemas.user import UserLogin
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS
from app.services.email_service import send_otp_email

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─────────────── TOKEN ───────────────
def create_token(
    user_id: int,
    cin: str,
    departments: list = None,
    is_admin: bool = False,
    nom: str = "",
    first_login: bool = False
) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub":         str(user_id),
        "cin":         cin,
        "departments": departments or [],
        "is_admin":    is_admin,
        "nom":         nom,
        "first_login": first_login,
        "exp":         expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ─────────────── LOGIN ───────────────
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

    token = create_token(
        user.id,
        user.cin,
        departments,
        user.is_admin,
        f"{user.nom} {user.prenom or ''}".strip(),
        user.first_login
    )

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
            "is_admin":    user.is_admin,
            "first_login": user.first_login
        }
    }


# ─────────────── CHANGE PASSWORD ───────────────
class ChangePasswordRequest(BaseModel):
    cin:          str
    old_password: str
    new_password: str


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.cin == data.cin).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if not bcrypt.checkpw(data.old_password.encode(), user.password.encode()):
        raise HTTPException(status_code=401, detail="Mot de passe actuel incorrect")

    if data.old_password == data.new_password:
        raise HTTPException(
            status_code=400,
            detail="Le nouveau mot de passe doit être différent"
        )

    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Le mot de passe doit contenir au moins 8 caractères"
        )

    hashed = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
    user.password = hashed
    user.first_login = False

    db.commit()

    return {"message": "✅ Mot de passe changé avec succès"}


# ─────────────── SCHEMAS OTP ───────────────
class ForgotPasswordRequest(BaseModel):
    cin: str


class VerifyOTPRequest(BaseModel):
    cin: str
    code: str


class ResetPasswordRequest(BaseModel):
    cin: str
    code: str
    new_password: str


# ─────────────── FORGOT PASSWORD ───────────────
@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.cin == data.cin).first()

    if not user:
        raise HTTPException(status_code=404, detail="CIN introuvable")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé")

    old_otps = db.query(OTPCode).filter(
        OTPCode.cin == data.cin,
        OTPCode.used == "0"
    ).all()

    for o in old_otps:
        o.used = "1"

    code = ''.join(random.choices(string.digits, k=6))

    otp = OTPCode(
        cin=data.cin,
        code=code,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        used="0"
    )
    db.add(otp)
    db.commit()

    sent = send_otp_email(user.email, user.nom, code)
    if not sent:
        raise HTTPException(status_code=500, detail="Erreur envoi email")

    return {
        "message": f"✅ Code envoyé à {user.email[:3]}***",
        "email_hint": f"{user.email[:3]}***@{user.email.split('@')[1]}"
    }


# ─────────────── VERIFY OTP ───────────────
@router.post("/verify-otp")
def verify_otp(
    data: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    otp = db.query(OTPCode).filter(
        OTPCode.cin == data.cin,
        OTPCode.code == data.code,
        OTPCode.used == "0"
    ).order_by(OTPCode.id.desc()).first()

    if not otp or not otp.is_valid():
        raise HTTPException(
            status_code=400,
            detail="Code invalide ou expiré"
        )

    return {"message": "✅ Code vérifié"}


# ─────────────── RESET PASSWORD ───────────────
@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    otp = db.query(OTPCode).filter(
        OTPCode.cin == data.cin,
        OTPCode.code == data.code,
        OTPCode.used == "0"
    ).order_by(OTPCode.id.desc()).first()

    if not otp or not otp.is_valid():
        raise HTTPException(
            status_code=400,
            detail="Code invalide ou expiré"
        )

    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Minimum 8 caractères requis"
        )

    user = db.query(User).filter(User.cin == data.cin).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    hashed = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
    user.password = hashed
    user.first_login = False

    otp.used = "1"

    db.commit()

    return {"message": "✅ Mot de passe réinitialisé avec succès"}


# ─────────────── ADMIN LOGIN ───────────────
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

    token = create_token(
        user.id,
        user.cin,
        departments,
        user.is_admin,
        f"{user.nom} {user.prenom or ''}".strip(),
        user.first_login
    )

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
            "is_admin":    user.is_admin,
            "first_login": user.first_login
        }
    }


@router.get("/test")
def test():
    return {"message": "Auth API OK"}