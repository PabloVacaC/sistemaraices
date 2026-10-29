from datetime import date, time
from typing import Optional
from pydantic import BaseModel


class BitacoraOut(BaseModel):
    id: int
    fecha: date
    hora: time
    modulo: str
    accion: str
    descripcion: str
    usuario_ci: Optional[str] = None

    class Config:
        from_attributes = True
