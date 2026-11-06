from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func

from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.entities import Bitacora, Usuario
from app.modules.bitacora.schemas import BitacoraOut

router = APIRouter(prefix="/bitacora", tags=["Bitácora"])


@router.get("/", response_model=List[BitacoraOut])
def listar_bitacora(
    response: Response,
    limit: int = Query(50, ge=1, le=500),
    page: int = Query(1, ge=1),
    skip: Optional[int] = Query(None, ge=0),
    modulo: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    stmt = select(Bitacora)
    if modulo:
        stmt = stmt.where(Bitacora.modulo == modulo)

    # Conteo total para paginación
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0
    response.headers["X-Total-Count"] = str(total)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"

    offset = skip if skip is not None else (page - 1) * limit
    stmt = stmt.order_by(desc(Bitacora.id)).offset(offset).limit(limit)
    registros = db.execute(stmt).scalars().all()
    return registros
