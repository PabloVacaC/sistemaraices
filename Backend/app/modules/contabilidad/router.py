from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.entities import Usuario
from app.core.security import get_current_user
from app.modules.contabilidad.schemas import (
    ContabilidadReporteMensual,
    ContabilidadReporteAnual,
)
from app.modules.contabilidad.service import (
    obtener_reporte_contable_mensual,
    obtener_reporte_contable_anual,
    obtener_anios_disponibles,
)

router = APIRouter(prefix="/contabilidad", tags=["Contabilidad y Finanzas"])


@router.get("/anios-disponibles", response_model=List[int])
def get_anios_disponibles(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Retorna la lista de años disponibles con movimientos en el sistema."""
    return obtener_anios_disponibles(db)


@router.get("/mensual", response_model=ContabilidadReporteMensual)
def get_reporte_mensual(
    mes: int = Query(..., ge=1, le=12, description="Mes a consultar (1-12)"),
    anio: int = Query(..., ge=2000, le=2100, description="Año a consultar"),
    area_id: Optional[int] = Query(None, description="Filtrar por centro de costo / área"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene el reporte y balance contable consolidado para un mes y año específicos."""
    try:
        return obtener_reporte_contable_mensual(db, mes=mes, anio=anio, area_id=area_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar reporte contable mensual: {str(e)}",
        )


@router.get("/anual", response_model=ContabilidadReporteAnual)
def get_reporte_anual(
    anio: int = Query(..., ge=2000, le=2100, description="Año a consultar"),
    area_id: Optional[int] = Query(None, description="Filtrar por centro de costo / área"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene el balance contable comparativo consolidado de todo el año."""
    try:
        return obtener_reporte_contable_anual(db, anio=anio, area_id=area_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar reporte contable anual: {str(e)}",
        )
