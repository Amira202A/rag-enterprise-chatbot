from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form, BackgroundTasks
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
import os
import asyncio
from pydantic import BaseModel as PydanticBase
from typing import List

router = APIRouter(prefix="/admin", tags=["Admin"])


class DepartmentUpdate(PydanticBase):
    department: str


class DepartmentsUpdate(PydanticBase):
    departments: List[str]


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
    return {
        "total_users": db.query(User).count(),
        "active_users": db.query(User).filter(User.is_active == True).count(),
        "inactive_users": db.query(User).filter(User.is_active == False).count(),
        "total_conversations": conversations_collection.count_documents({}),
        "total_messages": messages_collection.count_documents({})
    }


# ─── USERS ───────────────────────────────────────
@router.get("/users")
def get_users(admin=Depends(get_admin_user), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "nom": u.nom,
            "prenom": u.prenom,
            "cin": u.cin,
            "email": u.email,
            "departments": u.get_departments_list(),
            "is_active": u.is_active,
            "is_admin": u.is_admin,
            "add_date": str(u.add_date)
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
    return {"is_active": user.is_active}


@router.put("/users/{user_id}/department")
def update_department(user_id: int, data: DepartmentUpdate, admin=Depends(get_admin_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.department = data.department
    db.commit()
    return {"message": f"Département mis à jour → {data.department}"}


@router.put("/users/{user_id}/departments")
def update_departments(
    user_id: int,
    data: DepartmentsUpdate,
    admin=Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    user.set_departments_list(data.departments)
    db.commit()

    return {
        "message": "Départements mis à jour",
        "departments": data.departments
    }


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
@router.get("/documents")
def get_documents(admin=Depends(get_admin_user)):
    from qdrant_client import QdrantClient
    from app.core.config import QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    result = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=100,
        with_payload=True
    )

    docs = []
    seen_sources = {}

    for point in result[0]:
        source = point.payload.get("source", "Inconnu")
        department = point.payload.get("department", "Non défini")
        page = point.payload.get("page", "?")

        key = f"{source}_{department}"
        if key not in seen_sources:
            seen_sources[key] = {
                "source": source,
                "department": department,
                "pages": set(),
                "chunks": 0
            }

        seen_sources[key]["pages"].add(page)
        seen_sources[key]["chunks"] += 1

    for doc in seen_sources.values():
        docs.append({
            "source": doc["source"],
            "department": doc["department"],
            "pages": len(doc["pages"]),
            "chunks": doc["chunks"]
        })

    return docs