from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.entities import Usuario
from app.modules.pagos.schemas import (
    PeriodoSalarialOut,
    PeriodoSalarialCreate,
    AnticipoOut,
    AnticipoCreate,
    LiquidacionOut,
    LiquidacionCreate,
    PagoLiquidacionOut,
    PagoLiquidacionCreate,
    PagoParcialDirectoCreate,
    ResumenSalarialTrabajador,
    ResumenTrabajadorPagosParcialesOut,
    ComprobanteAnticipoDetalladoOut,
    PanelResumenPagos,
    AnulacionRequest,
)
from app.modules.pagos import service

router = APIRouter(prefix="/pagos", tags=["Módulo de Pagos y Anticipos"])


# =========================================================================
# PERÍODOS SALARIALES
# =========================================================================
@router.get("/periodos", response_model=List[PeriodoSalarialOut])
def listar_periodos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.listar_periodos(db)


@router.post("/periodos", response_model=PeriodoSalarialOut, status_code=status.HTTP_201_CREATED)
def crear_periodo(
    payload: PeriodoSalarialCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.crear_periodo(db, payload, admin_ci=current_user.ci)


# =========================================================================
# PANEL GENERAL DE INDICADORES
# =========================================================================
@router.get("/panel-general", response_model=PanelResumenPagos)
def obtener_panel_general(
    periodo_id: Optional[int] = Query(None, description="Filtrar indicadores por período salarial"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.obtener_panel_general(db, periodo_id=periodo_id)


# =========================================================================
# RESUMEN SALARIAL DINÁMICO POR TRABAJADOR Y PERÍODO
# =========================================================================
@router.get("/trabajador/{trabajador_id}/resumen-salarial", response_model=ResumenSalarialTrabajador)
def obtener_resumen_salarial(
    trabajador_id: int,
    periodo_id: int = Query(..., description="ID del período salarial"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.obtener_resumen_salarial(db, trabajador_id=trabajador_id, periodo_id=periodo_id)


# =========================================================================
# ANTICIPOS
# =========================================================================
@router.get("/anticipos", response_model=List[AnticipoOut])
def listar_anticipos(
    periodo_id: Optional[int] = None,
    trabajador_id: Optional[int] = None,
    area_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.listar_anticipos(
        db, periodo_id=periodo_id, trabajador_id=trabajador_id, area_id=area_id
    )


@router.post("/anticipos", response_model=AnticipoOut, status_code=status.HTTP_201_CREATED)
def registrar_anticipo(
    payload: AnticipoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.registrar_anticipo(db, payload, usuario_ci=current_user.ci)


@router.get("/anticipos/{id}/comprobante", response_model=ComprobanteAnticipoDetalladoOut)
def obtener_comprobante_anticipo_detallado(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.obtener_comprobante_anticipo_detallado(db, anticipo_id=id)


@router.patch("/anticipos/{id}/anular")
def anular_anticipo(
    id: int,
    payload: AnulacionRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.anular_anticipo(db, id, motivo=payload.motivo, usuario_ci=current_user.ci)


# =========================================================================
# SUBMÓDULO DE PAGOS PARCIALES / CONTROL DE QUINCENA
# =========================================================================
@router.get("/pagos-parciales/resumen", response_model=List[ResumenTrabajadorPagosParcialesOut])
def listar_resumen_pagos_parciales(
    periodo_id: int = Query(..., description="ID del período salarial"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.listar_resumen_pagos_parciales(db, periodo_id=periodo_id)


@router.post("/pagos-parciales/directo", response_model=PagoLiquidacionOut, status_code=status.HTTP_201_CREATED)
def registrar_pago_parcial_directo(
    payload: PagoParcialDirectoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.registrar_pago_parcial_directo(db, payload, usuario_ci=current_user.ci)


# =========================================================================
# LIQUIDACIONES Y PAGOS DE LIQUIDACIÓN
# =========================================================================
@router.get("/liquidaciones", response_model=List[LiquidacionOut])
def listar_liquidaciones(
    periodo_id: Optional[int] = None,
    trabajador_id: Optional[int] = None,
    estado: Optional[str] = None,
    area_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.listar_liquidaciones(
        db, periodo_id=periodo_id, trabajador_id=trabajador_id, estado=estado, area_id=area_id
    )


@router.post("/liquidaciones", response_model=LiquidacionOut, status_code=status.HTTP_201_CREATED)
def registrar_liquidacion(
    payload: LiquidacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.registrar_liquidacion(db, payload, usuario_ci=current_user.ci)


@router.post("/liquidaciones/pagos", response_model=PagoLiquidacionOut, status_code=status.HTTP_201_CREATED)
def registrar_pago_liquidacion(
    payload: PagoLiquidacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.registrar_pago_liquidacion(db, payload, usuario_ci=current_user.ci)


@router.patch("/liquidaciones/pagos/{id}/anular")
def anular_pago_liquidacion(
    id: int,
    payload: AnulacionRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.anular_pago_liquidacion(db, id, motivo=payload.motivo, usuario_ci=current_user.ci)


@router.patch("/liquidaciones/{id}/anular")
def anular_liquidacion(
    id: int,
    payload: AnulacionRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.anular_liquidacion(db, id, motivo=payload.motivo, usuario_ci=current_user.ci)


# =========================================================================
# HISTORIAL DE MOVIMIENTOS POR TRABAJADOR
# =========================================================================
@router.get("/historial/{trabajador_id}")
def obtener_historial_trabajador(
    trabajador_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.obtener_historial_trabajador(db, trabajador_id=trabajador_id)
