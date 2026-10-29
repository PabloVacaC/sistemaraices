from datetime import date
from typing import List, Optional
from pydantic import BaseModel, EmailStr


class PermisoOut(BaseModel):
    id: int
    permisos: str

    class Config:
        from_attributes = True


class RolOut(BaseModel):
    id: int
    rol: str
    niveljerarquico: int
    descripcion: Optional[str] = None
    permisos: List[PermisoOut] = []

    class Config:
        from_attributes = True


class RolCreate(BaseModel):
    rol: str
    niveljerarquico: int
    descripcion: Optional[str] = None
    permiso_ids: List[int] = []


class UsuarioCreate(BaseModel):
    ci: str
    nombre: str
    apellido: str
    email: EmailStr
    contraseña: str
    rol_id: int
    genero: Optional[str] = None
    fechanacimiento: Optional[date] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    foto: Optional[str] = None
    estado: bool = True


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[EmailStr] = None
    contraseña: Optional[str] = None
    rol_id: Optional[int] = None
    genero: Optional[str] = None
    fechanacimiento: Optional[date] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    foto: Optional[str] = None
    estado: Optional[bool] = None


class UsuarioOut(BaseModel):
    ci: str
    nombre: str
    apellido: str
    email: str
    genero: Optional[str] = None
    fechanacimiento: Optional[date] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    foto: Optional[str] = None
    estado: bool
    rol_id: int
    rol: Optional[RolOut] = None

    class Config:
        from_attributes = True
