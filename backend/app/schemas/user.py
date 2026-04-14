from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserRegister(BaseModel):
    nom:         str
    prenom:      str
    cin:         str
    email:       EmailStr
    departments: Optional[List[str]] = []

class UserLogin(BaseModel):
    cin:      str
    password: str

class UserCreate(BaseModel):
    email:    EmailStr
    password: str