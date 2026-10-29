from datetime import date
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel


class AreaOut(BaseModel):
    id: int
    nombre: str
    estado: bool
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True


class AreaCreate(BaseModel):
    nombre: str
    estado: bool = True
    descripcion: Optional[str] = None


class ContactoEmergenciaSchema(BaseModel):
    id: Optional[int] = None
    nombrecompleto: str
    parentesco: str
    celular: str

    class Config:
        from_attributes = True


class TrabajadorCreate(BaseModel):
    ci: Optional[str] = None
    nombres: str
    apellidos: str
    fotografia: Optional[str] = None
    celular: Optional[str] = None
    fecha_ingreso: date = date.today()
    cargo: str
    sueldoBase: Decimal
    area_id: Optional[int] = None
    contactos: List[ContactoEmergenciaSchema] = []


class TrabajadorUpdate(BaseModel):
    ci: Optional[str] = None
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    fotografia: Optional[str] = None
    celular: Optional[str] = None
    fecha_ingreso: Optional[date] = None
    cargo: Optional[str] = None
    sueldoBase: Optional[Decimal] = None
    estado: Optional[bool] = None
    area_id: Optional[int] = None
    contactos: Optional[List[ContactoEmergenciaSchema]] = None


class TrabajadorOut(BaseModel):
    id: int
    ci: Optional[str] = None
    nombres: str
    apellidos: str
    fotografia: Optional[str] = None
    celular: Optional[str] = None
    fecha_ingreso: date
    cargo: str
    sueldoBase: Decimal
    estado: bool
    area_id: Optional[int] = None
    area: Optional[AreaOut] = None
    contactos_emergencia: List[ContactoEmergenciaSchema] = []

    class Config:
        from_attributes = True
