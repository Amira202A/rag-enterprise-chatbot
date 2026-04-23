from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional, List
import jwt
import bcrypt
import csv
import io

from app.database.sql import SessionLocal
from app.models.user import User
from app.models.employee import Employee
from app.core.config import SECRET_KEY, ALGORITHM
from app.services.email_service import generate_password, send_password_email

router = APIRouter(prefix="/employees", tags=["Employees"])


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


# ─── RECHERCHE ───────────────────────────────────
@router.get("/search")
def search_employees(
    q: str = "",
    admin=Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    query = db.query(Employee)

    if q.strip():
        search = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Employee.nom.ilike(search),
                Employee.prenom.ilike(search),
                Employee.cin.ilike(search),
                Employee.email.ilike(search),
                Employee.unit_label.ilike(search),
                Employee.matricule.ilike(search)
            )
        )

    employees = query.limit(50).all()

    # Récupérer les CINs déjà enregistrés comme users
    registered_cins = {u.cin for u in db.query(User).all()}

    return [
        {
            "id":               e.id,
            "nom":              e.nom,
            "prenom":           e.prenom,
            "cin":              e.cin,
            "email":            e.email,
            "matricule":        e.matricule,
            "num_poste":        e.num_poste,
            "unit_label":       e.unit_label,
            "subsidiary_label": e.subsidiary_label,
            "is_registered":    e.cin in registered_cins
        }
        for e in employees
    ]


# ─── AJOUTER EMPLOYÉ ─────────────────────────────
class AddEmployeeRequest(BaseModel):
    cin:              str
    nom:              str
    prenom:           str
    email:            str
    matricule:        Optional[str] = None
    num_poste:        Optional[str] = None
    unit_label:       Optional[str] = None
    subsidiary_label: Optional[str] = None
    departments:      Optional[List[str]] = None


@router.post("/add")
def add_employee(
    data: AddEmployeeRequest,
    admin=Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # Vérifications
    if db.query(User).filter(User.cin == data.cin).first():
        raise HTTPException(status_code=400, detail="Cet employé est déjà enregistré")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    # Générer mot de passe
    raw_password = generate_password()
    hashed = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

    # Créer l'utilisateur
    new_user = User(
        nom=data.nom,
        prenom=data.prenom,
        cin=data.cin,
        email=data.email,
        password=hashed,
        matricule=data.matricule,
        num_poste=data.num_poste,
        unit_label=data.unit_label,
        subsidiary_label=data.subsidiary_label,
        is_active=True,
        is_admin=False
    )

    # Département automatique selon unit_label
    depts = data.departments or ([data.unit_label] if data.unit_label else [])
    new_user.set_departments_list(depts)

    db.add(new_user)

    # Marquer comme enregistré dans la table employees
    emp = db.query(Employee).filter(Employee.cin == data.cin).first()
    if emp:
        emp.is_registered = True

    db.commit()
    db.refresh(new_user)

    # Envoyer email
    sent = send_password_email(data.email, data.nom, raw_password)
    if not sent:
        db.delete(new_user)
        db.commit()
        raise HTTPException(status_code=500, detail="Erreur envoi email")

    return {
        "message":    f"✅ {data.nom} {data.prenom} ajouté — email envoyé à {data.email}",
        "user_id":    new_user.id,
        "department": new_user.get_departments_list()
    }


# ─── IMPORT CSV ──────────────────────────────────
@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    admin=Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Importer des employés depuis un fichier CSV"""
    content = await file.read()
    text    = content.decode("utf-8")
    reader  = csv.DictReader(io.StringIO(text))

    added = 0
    skipped = 0
    errors = []

    for row in reader:
        cin = row.get("cin", "").strip()
        if not cin:
            continue

        # Vérifier si déjà dans la table employees
        if db.query(Employee).filter(Employee.cin == cin).first():
            skipped += 1
            continue

        try:
            emp = Employee(
                nom=row.get("nom", "").strip(),
                prenom=row.get("prenom", "").strip(),
                cin=cin,
                email=row.get("email", "").strip(),
                matricule=row.get("matricule", "").strip() or None,
                num_poste=row.get("num_poste", "").strip() or None,
                num_personnel=row.get("num_personnel", "").strip() or None,
                unit_label=row.get("unit_label", "").strip() or None,
                subsidiary_label=row.get("subsidiary_label", "").strip() or None,
                upper_hierarchy=row.get("upper_hierarchy", "").strip() or None,
            )
            db.add(emp)
            added += 1
        except Exception as e:
            errors.append(f"CIN {cin}: {str(e)}")

    db.commit()

    return {
        "message": f"✅ Import terminé",
        "added":   added,
        "skipped": skipped,
        "errors":  errors
    }


# ─── LISTE COMPLÈTE ──────────────────────────────
@router.get("/all")
def get_all_employees(
    admin=Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    registered_cins = {u.cin for u in db.query(User).all()}
    employees = db.query(Employee).all()
    return [
        {
            "id":            e.id,
            "nom":           e.nom,
            "prenom":        e.prenom,
            "cin":           e.cin,
            "email":         e.email,
            "unit_label":    e.unit_label,
            "is_registered": e.cin in registered_cins
        }
        for e in employees
    ]


# ─── AJOUTER MANUELLEMENT UN EMPLOYÉ ─────────────
class CreateEmployeeRequest(BaseModel):
    nom:              str
    prenom:           str
    cin:              str
    email:            str
    matricule:        Optional[str] = None
    num_poste:        Optional[str] = None
    unit_label:       Optional[str] = None
    subsidiary_label: Optional[str] = None


@router.post("/create")
def create_employee(
    data: CreateEmployeeRequest,
    admin=Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Ajouter manuellement un employé dans la table employees"""
    if db.query(Employee).filter(Employee.cin == data.cin).first():
        raise HTTPException(status_code=400, detail="CIN déjà existant")

    emp = Employee(
        nom=data.nom,
        prenom=data.prenom,
        cin=data.cin,
        email=data.email,
        matricule=data.matricule,
        num_poste=data.num_poste,
        unit_label=data.unit_label,
        subsidiary_label=data.subsidiary_label
    )
    db.add(emp)
    db.commit()
    return {"message": f"✅ Employé {data.nom} {data.prenom} ajouté à la liste"}