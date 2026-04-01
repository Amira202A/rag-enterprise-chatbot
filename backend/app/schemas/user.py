from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    nom:   str
    cin:   str
    email: EmailStr

class UserLogin(BaseModel):
    cin:      str
    password: str

class UserCreate(BaseModel):
    email:    EmailStr
    password: str