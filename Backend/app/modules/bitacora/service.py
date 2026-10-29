from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.entities import Bitacora


def registrar_bitacora(
    db: Session,
    modulo: str,
    accion: str,
    descripcion: str,
    usuario_ci: Optional[str] = None,
):
    try:
        now = datetime.now()
        registro = Bitacora(
            fecha=now.date(),
            hora=now.time(),
            modulo=modulo,
            accion=accion,
            descripcion=descripcion,
            usuario_ci=usuario_ci,
        )
        db.add(registro)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error al registrar bitácora: {e}")
