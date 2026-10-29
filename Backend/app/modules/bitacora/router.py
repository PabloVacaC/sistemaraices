from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.entities import Bitacora, Usuario
from app.modules.bitacora.schemas import BitacoraOut

router = APIRouter(prefix="/bitacora", tags=["Bitácora"])


@router.get("/", response_model=List[BitacoraOut])
def listar_bitacora(
    limit: int = Query(50, le=200),
    modulo: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    stmt = select(Bitacora)
    if modulo:
        stmt = stmt.where(Bitacora.modulo == modulo)
    stmt = stmt.order_by(desc(Bitacora.id)).limit(limit)
    registros = db.execute(stmt).scalars().all()
    return registros
