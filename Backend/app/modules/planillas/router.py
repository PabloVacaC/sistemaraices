from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.entities import Usuario
from app.modules.planillas.schemas import (
    PlanillaResumenOut,
    CierrePlanillaRequest,
    ReaperturaPlanillaRequest,
    PeriodoPlanillaListItem,
)
from app.modules.planillas import service

router = APIRouter(prefix="/planillas", tags=["Módulo de Planillas Salariales"])


@router.get("/periodos", response_model=List[PeriodoPlanillaListItem])
def listar_periodos_planilla(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Retorna la lista de todos los períodos con sus métricas consolidadas de planilla."""
    return service.listar_resumen_periodos(db)


@router.get("/periodo-actual", response_model=PlanillaResumenOut)
def obtener_planilla_periodo_actual(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Selecciona automáticamente la planilla del mes actual. Si no existe,
    la genera y habilita automáticamente (RF-2 y RF-6).
    """
    periodo = service.asegurar_periodo_actual(db, usuario_ci=current_user.ci)
    return service.obtener_planilla_consolidada(db, periodo.id)


@router.get("/{periodo_id}", response_model=PlanillaResumenOut)
def obtener_planilla_por_periodo(
    periodo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Consulta la planilla mensual consolidada de un período específico (RF-3)."""
    return service.obtener_planilla_consolidada(db, periodo_id)


@router.post("/{periodo_id}/cerrar", response_model=PlanillaResumenOut)
def cerrar_planilla_periodo(
    periodo_id: int,
    datos: CierrePlanillaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Ejecuta el cierre formal de la planilla mensual: valida pagos pendientes,
    congela datos históricos y bloquea ediciones posteriores (RF-9, RF-10, RF-11, RF-12).
    """
    return service.cerrar_planilla(
        db=db,
        periodo_id=periodo_id,
        request=datos,
        usuario_ci=current_user.ci,
    )


@router.post("/{periodo_id}/reabrir", response_model=PlanillaResumenOut)
def reabrir_planilla_periodo(
    periodo_id: int,
    datos: ReaperturaPlanillaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Reapertura administrativa justificada de una planilla cerrada,
    registrando la operación en la bitácora de auditoría.
    """
    return service.reabrir_planilla(
        db=db,
        periodo_id=periodo_id,
        request=datos,
        usuario_ci=current_user.ci,
    )
