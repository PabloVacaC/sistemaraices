from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.entities import Usuario
from app.modules.planilla.schemas import (
    PlanillaMensualOut,
    PlanillaFilaOut,
    ActualizarDiasTrabajadosIn,
    DescuentoCreate,
    DescuentoOut,
    CerrarPlanillaRequest,
)
from app.modules.pagos.schemas import AnulacionRequest
from app.modules.planilla import service

router = APIRouter(prefix="/planilla", tags=["Módulo de Planilla y Salarios"])


# =========================================================================
# PLANILLA MENSUAL
# =========================================================================
@router.get("/periodo/{periodo_id}", response_model=PlanillaMensualOut)
def obtener_planilla_periodo(
    periodo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Consulta o genera la planilla tabular completa (13 columnas de RF-9) para un período."""
    return service.obtener_o_generar_planilla(db, periodo_id)


@router.put("/dias-trabajados", response_model=PlanillaFilaOut)
def actualizar_dias_trabajados(
    datos: ActualizarDiasTrabajadosIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Permite ajustar los días trabajados en una planilla abierta y recalcula el total ganado."""
    return service.actualizar_dias_trabajados(db, datos, usuario_ci=current_user.ci)


@router.post("/cerrar/{periodo_id}")
def cerrar_planilla(
    periodo_id: int,
    datos: CerrarPlanillaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Cierra formalmente una planilla mensual bloqueando modificaciones ordinarias posteriores."""
    return service.cerrar_planilla_periodo(db, periodo_id, datos, usuario_ci=current_user.ci)


# =========================================================================
# DESCUENTOS SALARIALES DINÁMICOS (RF-29 A RF-32)
# =========================================================================
@router.get("/descuentos", response_model=List[DescuentoOut])
def listar_descuentos(
    periodo_id: int = Query(...),
    trabajador_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Consulta la lista de descuentos del período con filtro opcional por trabajador."""
    return service.listar_descuentos(db, periodo_id=periodo_id, trabajador_id=trabajador_id)


@router.post("/descuentos", response_model=DescuentoOut, status_code=status.HTTP_201_CREATED)
def registrar_descuento(
    datos: DescuentoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra una deducción salarial con comprobante oficial correlativo DESC-YYYYMM-XXXX."""
    return service.registrar_descuento(db, datos, usuario_ci=current_user.ci)


@router.post("/descuentos/{descuento_id}/anular", response_model=DescuentoOut)
def anular_descuento(
    descuento_id: int,
    datos: AnulacionRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Anula de forma justificada un descuento salarial conservando el registro histórico."""
    return service.anular_descuento(
        db, descuento_id=descuento_id, motivo=datos.motivo, usuario_ci=current_user.ci
    )

