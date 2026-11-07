from datetime import date, datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.entities import Bitacora

# Zona horaria oficial de Bolivia: UTC-4 (America/La_Paz, sin horario de verano)
TZ_BOLIVIA = timezone(timedelta(hours=-4))


def obtener_ahora_bolivia() -> datetime:
    """Retorna la fecha y hora actual en la zona horaria oficial de Bolivia (UTC-4)."""
    return datetime.now(TZ_BOLIVIA)


def registrar_bitacora(
    db: Session,
    modulo: str,
    accion: str,
    descripcion: str,
    usuario_ci: Optional[str] = None,
    commit: bool = True,
):
    try:
        now = obtener_ahora_bolivia()
        registro = Bitacora(
            fecha=now.date(),
            hora=now.time().replace(microsecond=0),
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
