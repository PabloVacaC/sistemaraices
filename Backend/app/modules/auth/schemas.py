from typing import List, Optional
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    contraseña: str


class RolSimpleOut(BaseModel):
    id: int
    rol: str
    niveljerarquico: int
    permisos: List[str] = []

    class Config:
        from_attributes = True


class UsuarioTokenInfo(BaseModel):
    ci: str
    nombre: str
    apellido: str
    email: str
    rol: Optional[str] = None
    niveljerarquico: Optional[int] = None
    permisos: List[str] = []

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UsuarioTokenInfo
