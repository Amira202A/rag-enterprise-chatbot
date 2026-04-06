from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from sqlalchemy.orm import Session
from app.database.sql import SessionLocal
from app.database.mongo import conversations_collection, messages_collection
from app.models.user import User
from app.core.config import SECRET_KEY, ALGORITHM
from app.services.document_service import add_document, create_collection
from app.rag.chunker import chunk_text
import jwt
from pypdf import PdfReader
import io

router = APIRouter(prefix="/admin", tags=["Admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_admin_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token manquant")
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Accès admin requis")
    return user


# ─── STATS ───────────────────────────────────────
@router.get("/stats")
def get_stats(admin=Depends(get_admin_user), db: Session = Depends(get_db)):
    total_users       = db.query(User).count()
    active_users      = db.query(User).filter(User.is_active == True).count()
    inactive_users    = db.query(User).filter(User.is_active == False).count()
    total_convs       = conversations_collection.count_documents({})
    total_messages    = messages_collection.count_documents({})
    return {
        "total_users":    total_users,
        "active_users":   active_users,
        "inactive_users": inactive_users,
        "total_conversations": total_convs,
        "total_messages": total_messages
    }


# ─── USERS ───────────────────────────────────────
@router.get("/users")
def get_users(admin=Depends(get_admin_user), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [
        {
            "id":        u.id,
            "nom":       u.nom,
            "prenom":    u.prenom,
            "cin":       u.cin,
            "email":     u.email,
            "is_active": u.is_active,
            "is_admin":  u.is_admin,
            "add_date":  str(u.add_date)
        }
        for u in users
    ]


@router.put("/users/{user_id}/toggle")
def toggle_user(user_id: int, admin=Depends(get_admin_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.is_active = not user.is_active
    db.commit()
    return {"message": f"Utilisateur {'activé' if user.is_active else 'désactivé'}", "is_active": user.is_active}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin=Depends(get_admin_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Impossible de supprimer un admin")
    db.delete(user)
    db.commit()
    return {"message": "Utilisateur supprimé"}


# ─── DOCUMENTS ───────────────────────────────────
@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    admin=Depends(get_admin_user)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Fichier PDF requis")

    content = await file.read()
    reader  = PdfReader(io.BytesIO(content))

    total_chunks = 0
    seen = set()

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text or len(text.strip()) < 30:
            continue
        chunks = chunk_text(text)
        for chunk in chunks:
            h = hash(chunk[:100])
            if h in seen:
                continue
            seen.add(h)
            add_document(chunk, metadata={
                "source": file.filename,
                "page": page_num + 1
            })
            total_chunks += 1

    return {
        "message": f"✅ {file.filename} ingéré avec succès",
        "chunks":  total_chunks,
        "pages":   len(reader.pages)
    }