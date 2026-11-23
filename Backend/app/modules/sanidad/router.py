from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.entities import Usuario
from app.modules.sanidad import service
from app.modules.sanidad.schemas import (
    SanidadVacunaCreate,
    SanidadVacunaUpdate,
    SanidadVacunaOut,
    SanidadMedicamentoCreate,
    SanidadMedicamentoUpdate,
    SanidadMedicamentoOut,
    SanidadOperacionCreate,
    SanidadOperacionOut,
    SanidadOperacionDetalladaOut,
    SanidadSeguimientoCreate,
    SanidadSeguimientoOut,
    AnulacionSanidadIn,
    AlertaRetiroOut,
    SanidadKPIsOut,
    HistorialSanitarioAnimalOut,
)

router = APIRouter(prefix="/sanidad", tags=["Módulo de Ganadería - Sanidad y Tratamientos"])


# =========================================================================
# KPIS Y ALERTAS DE PERÍODO DE RETIRO
# =========================================================================

@router.get("/kpis", response_model=SanidadKPIsOut)
def obtener_kpis(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Consulta indicadores clave de sanidad y tratamientos veterinarios."""
    return service.obtener_kpis_sanidad(db)


@router.get("/alertas-retiro", response_model=List[AlertaRetiroOut])
def obtener_alertas_retiro(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene la lista de animales actualmente bajo período de retiro de carne o leche."""
    return service.obtener_alertas_retiro(db)


# =========================================================================
# CATÁLOGO DE VACUNAS
# =========================================================================

@router.get("/vacunas", response_model=List[SanidadVacunaOut])
def listar_vacunas(
    solo_activas: bool = Query(False, description="Filtrar solo vacunas con estado ACTIVO"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene el catálogo de vacunas configuradas."""
    return service.listar_vacunas(db, solo_activas=solo_activas)


@router.post("/vacunas", response_model=SanidadVacunaOut, status_code=status.HTTP_201_CREATED)
def crear_vacuna(
    payload: SanidadVacunaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra una nueva vacuna en el catálogo oficial."""
    return service.crear_vacuna(db, payload, current_user.ci)


@router.put("/vacunas/{vacuna_id}", response_model=SanidadVacunaOut)
def actualizar_vacuna(
    vacuna_id: int,
    payload: SanidadVacunaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Actualiza los datos técnicos de una vacuna."""
    return service.actualizar_vacuna(db, vacuna_id, payload, current_user.ci)


@router.patch("/vacunas/{vacuna_id}/estado", response_model=SanidadVacunaOut)
def alternar_estado_vacuna(
    vacuna_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Activa o desactiva una vacuna en el catálogo."""
    return service.desactivar_vacuna(db, vacuna_id, current_user.ci)


# =========================================================================
# CATÁLOGO DE MEDICAMENTOS Y FÁRMACOS
# =========================================================================

@router.get("/medicamentos", response_model=List[SanidadMedicamentoOut])
def listar_medicamentos(
    solo_activos: bool = Query(False, description="Filtrar solo fármacos con estado ACTIVO"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene el catálogo de medicamentos veterinarios."""
    return service.listar_medicamentos(db, solo_activos=solo_activos)


@router.post("/medicamentos", response_model=SanidadMedicamentoOut, status_code=status.HTTP_201_CREATED)
def crear_medicamento(
    payload: SanidadMedicamentoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra un nuevo medicamento en el catálogo."""
    return service.crear_medicamento(db, payload, current_user.ci)


@router.put("/medicamentos/{medicamento_id}", response_model=SanidadMedicamentoOut)
def actualizar_medicamento(
    medicamento_id: int,
    payload: SanidadMedicamentoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Actualiza la ficha técnica de un medicamento."""
    return service.actualizar_medicamento(db, medicamento_id, payload, current_user.ci)


@router.patch("/medicamentos/{medicamento_id}/estado", response_model=SanidadMedicamentoOut)
def alternar_estado_medicamento(
    medicamento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Activa o desactiva un medicamento en el catálogo."""
    return service.desactivar_medicamento(db, medicamento_id, current_user.ci)


# =========================================================================
# OPERACIONES SANITARIAS (VACUNACIONES Y TRATAMIENTOS)
# =========================================================================

@router.get("/operaciones", response_model=List[SanidadOperacionOut])
def listar_operaciones(
    tipo_operacion: Optional[str] = Query(None, description="VACUNACION_INDIVIDUAL, VACUNACION_GRUPAL, TRATAMIENTO_INDIVIDUAL, TRATAMIENTO_GRUPAL, PREVENTIVO"),
    potrero_id: Optional[int] = Query(None, description="Filtrar por potrero de aplicación"),
    estado: Optional[str] = Query(None, description="EJECUTADO, PROGRAMADO, ANULADO"),
    fecha_desde: Optional[date] = Query(None, description="Fecha de inicio YYYY-MM-DD"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha de fin YYYY-MM-DD"),
    busqueda: Optional[str] = Query(None, description="Texto de búsqueda en comprobante, diagnóstico, responsable"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista las operaciones sanitarias con filtros avanzados y paginación."""
    return service.listar_operaciones_sanitarias(
        db,
        tipo_operacion=tipo_operacion,
        potrero_id=potrero_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        busqueda=busqueda,
        skip=skip,
        limit=limit,
    )


@router.post("/operaciones", response_model=SanidadOperacionOut, status_code=status.HTTP_201_CREATED)
def crear_operacion(
    payload: SanidadOperacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra una jornada de vacunación o tratamiento clínico (individual o por lote/potrero)."""
    return service.crear_operacion_sanitaria(db, payload, current_user.ci)


@router.get("/operaciones/{operacion_id}", response_model=SanidadOperacionDetalladaOut)
def obtener_operacion_detalle(
    operacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene los detalles completos de una operación sanitaria y su lista de animales."""
    return service.obtener_operacion_por_id(db, operacion_id)


@router.patch("/operaciones/{operacion_id}/anular", response_model=SanidadOperacionOut)
def anular_operacion(
    operacion_id: int,
    payload: AnulacionSanidadIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Anula una operación sanitaria con motivo obligatorio y reversión de inventario."""
    return service.anular_operacion_sanitaria(db, operacion_id, payload, current_user.ci)


# =========================================================================
# SEGUIMIENTO CLÍNICO Y DETALLES
# =========================================================================

@router.post("/detalles/{detalle_id}/seguimiento", response_model=SanidadSeguimientoOut, status_code=status.HTTP_201_CREATED)
def registrar_seguimiento(
    detalle_id: int,
    payload: SanidadSeguimientoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra la evolución clínica de un animal en tratamiento."""
    return service.registrar_seguimiento_clinico(db, detalle_id, payload, current_user.ci)


# =========================================================================
# HISTORIAL SANITARIO INDIVIDUAL (VINCULACIÓN PERFIL 360 - SPEC-001)
# =========================================================================

@router.get("/animales/{animal_id}/historial", response_model=HistorialSanitarioAnimalOut)
def obtener_historial_sanitario_animal(
    animal_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene el historial sanitario completo de un animal (vacunas, tratamientos y retiros)."""
    return service.obtener_historial_sanitario_animal(db, animal_id)
