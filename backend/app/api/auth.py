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


def create_token(user_id: int, cin: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "cin": cin, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ───────── REGISTER ─────────
@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):

    # Vérifier email unique
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    # Vérifier CIN unique
    if db.query(User).filter(User.cin == user.cin).first():
        raise HTTPException(status_code=400, detail="CIN déjà enregistré")

    # Générer mot de passe
    raw_password = generate_password()

    # Hasher le mot de passe
    hashed = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

    # Créer l'utilisateur
    new_user = User(
        nom=user.nom,
        cin=user.cin,
        email=user.email,
        password=hashed
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Envoyer l'email
    sent = send_password_email(user.email, user.nom, raw_password)

    if not sent:
        # Rollback si email échoue
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

    token = create_token(user.id, user.cin)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id":    user.id,
            "nom":   user.nom,
            "cin":   user.cin,
            "email": user.email
        }
    }


# ───────── TEST ─────────
@router.get("/test")
def test():
    return {"message": "Auth API OK"}