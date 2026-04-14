from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database.sql import Base

class User(Base):
    __tablename__ = "users"

    id                = Column(Integer, primary_key=True, index=True)
    nom               = Column(String(100), nullable=False)
    prenom            = Column(String(100), nullable=True)
    cin               = Column(String(20),  unique=True, index=True, nullable=False)
    email             = Column(String(255), unique=True, index=True, nullable=False)
    password          = Column(String(255), nullable=False)

    # ✅ Plusieurs départements stockés sous forme de string séparée par virgule
    # Exemple: "RH,IT,Marketing"
    departments       = Column(String(500), nullable=True)

    # Champs RH — remplis par l'admin
    matricule         = Column(String(50),  nullable=True)
    num_poste         = Column(String(50),  nullable=True)
    num_personnel     = Column(String(50),  nullable=True)
    upper_hierarchy   = Column(String(100), nullable=True)
    unit_label        = Column(String(100), nullable=True)
    subsidiary_label  = Column(String(100), nullable=True)

    is_active         = Column(Boolean, default=True)
    is_admin          = Column(Boolean, default=False)
    add_date          = Column(DateTime, server_default=func.now())

    # ============================
    # 🔁 Helpers pour les départements
    # ============================

    def get_departments_list(self):
        """Retourne la liste des départements"""
        if not self.departments:
            return []
        return [d.strip() for d in self.departments.split(",")]

    def set_departments_list(self, dept_list: list):
        """Sauvegarde la liste des départements"""
        if not dept_list:
            self.departments = None
        else:
            self.departments = ",".join([d.strip() for d in dept_list])