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
    commit: bool = True,
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
        if commit:
            db.commit()
        else:
            db.flush()
    except Exception as e:
        # No se ejecuta db.rollback() para preservar la integridad transaccional del llamador
        print(f"Advertencia: no se pudo registrar en bitácora: {e}")
