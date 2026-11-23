from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.entities import Usuario
from app.modules.agricultura import service
from app.modules.agricultura.schemas import (
    AreaAgricolaCreate,
    AreaAgricolaUpdate,
    AreaAgricolaOut,
    CicloAgricolaCreate,
    CicloAgricolaOut,
    CicloCambioFasePayload,
    ActividadPreparacionCreate,
    ActividadPreparacionUpdate,
    ActividadPreparacionOut,
    SiembraUpdate,
    ActividadManejoCreate,
    ActividadManejoOut,
    CosechaCreate,
    CosechaOut,
    AgriculturaKPIsOut,
)

router = APIRouter(prefix="/agricultura", tags=["Módulo de Agricultura"])


# =========================================================================
# KPIS GLOBALES
# =========================================================================

@router.get("/kpis", response_model=AgriculturaKPIsOut)
def obtener_kpis(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene los indicadores clave de producción y superficies agrícolas."""
    return service.obtener_kpis(db)


# =========================================================================
# ÁREAS AGRÍCOLAS (PARCELAS)
# =========================================================================

@router.get("/areas", response_model=List[AreaAgricolaOut])
def listar_areas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista todas las parcelas agrícolas activas con polígonos y ciclo activo."""
    return service.listar_areas(db)


@router.post("/areas", response_model=AreaAgricolaOut, status_code=status.HTTP_201_CREATED)
def crear_area(
    datos: AreaAgricolaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra y delimita una nueva parcela agrícola."""
    area = service.crear_area(db, datos, usuario_ci=current_user.ci)
    return service.obtener_area(db, area.id)


@router.get("/areas/{area_id}", response_model=AreaAgricolaOut)
def obtener_area(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Consulta los datos de una parcela específica."""
    return service.obtener_area(db, area_id)


@router.put("/areas/{area_id}", response_model=AreaAgricolaOut)
def actualizar_area(
    area_id: int,
    datos: AreaAgricolaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Edita nombre, polígono o superficie de una parcela agrícola."""
    area = service.actualizar_area(db, area_id, datos, usuario_ci=current_user.ci)
    return service.obtener_area(db, area.id)


@router.delete("/areas/{area_id}")
def eliminar_area(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Desactiva lógicamente una parcela agrícola."""
    return service.eliminar_area(db, area_id, usuario_ci=current_user.ci)


@router.get("/areas/{area_id}/historial", response_model=List[CicloAgricolaOut])
def obtener_historial_area(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene el historial cronológico de campañas agrícolas en una parcela."""
    return service.obtener_historial_area(db, area_id)


# =========================================================================
# CICLOS AGRÍCOLAS
# =========================================================================

@router.post("/areas/{area_id}/ciclos", response_model=CicloAgricolaOut, status_code=status.HTTP_201_CREATED)
def iniciar_ciclo(
    area_id: int,
    datos: CicloAgricolaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Inicia una nueva campaña o ciclo agrícola sobre la parcela."""
    return service.iniciar_ciclo(db, area_id, datos, usuario_ci=current_user.ci)


@router.get("/ciclos/{ciclo_id}", response_model=CicloAgricolaOut)
def obtener_ciclo(
    ciclo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Consulta el estado y actividades de un ciclo agrícola."""
    return service.obtener_ciclo(db, ciclo_id)


@router.put("/ciclos/{ciclo_id}/fase", response_model=CicloAgricolaOut)
def cambiar_fase_ciclo(
    ciclo_id: int,
    payload: CicloCambioFasePayload,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Avanza o actualiza la fase operativa del ciclo agrícola."""
    return service.cambiar_fase_ciclo(db, ciclo_id, payload.fase, usuario_ci=current_user.ci)


# =========================================================================
# FASE 1: PREPARACIÓN
# =========================================================================

@router.post("/ciclos/{ciclo_id}/preparacion", response_model=ActividadPreparacionOut, status_code=status.HTTP_201_CREATED)
def registrar_preparacion(
    ciclo_id: int,
    datos: ActividadPreparacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Agrega una labor de preparación del suelo."""
    return service.registrar_actividad_preparacion(db, ciclo_id, datos)


@router.put("/ciclos/{ciclo_id}/preparacion/{act_id}", response_model=ActividadPreparacionOut)
def actualizar_preparacion(
    ciclo_id: int,
    act_id: int,
    datos: ActividadPreparacionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Actualiza el estado (completado/pendiente) de una labor de preparación."""
    return service.actualizar_actividad_preparacion(db, ciclo_id, act_id, datos)


# =========================================================================
# FASE 2: SIEMBRA
# =========================================================================

@router.put("/ciclos/{ciclo_id}/siembra", response_model=CicloAgricolaOut)
def registrar_siembra(
    ciclo_id: int,
    datos: SiembraUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra la siembra y avanza automáticamente a Fase de Manejo."""
    return service.actualizar_siembra(db, ciclo_id, datos, usuario_ci=current_user.ci)


# =========================================================================
# FASE 3: FUMIGACIÓN Y MANEJO
# =========================================================================

@router.post("/ciclos/{ciclo_id}/manejo", response_model=ActividadManejoOut, status_code=status.HTTP_201_CREATED)
def registrar_actividad_manejo(
    ciclo_id: int,
    datos: ActividadManejoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra una aplicación fitosanitaria o nutricional en el cultivo."""
    return service.registrar_actividad_manejo(db, ciclo_id, datos, usuario_ci=current_user.ci)


@router.delete("/ciclos/{ciclo_id}/manejo/{act_id}")
def eliminar_actividad_manejo(
    ciclo_id: int,
    act_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Elimina una aplicación registrada."""
    return service.eliminar_actividad_manejo(db, ciclo_id, act_id)


# =========================================================================
# FASE 4: COSECHA Y CIERRE
# =========================================================================

@router.post("/ciclos/{ciclo_id}/cosecha", response_model=CosechaOut, status_code=status.HTTP_201_CREATED)
def registrar_cosecha(
    ciclo_id: int,
    datos: CosechaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra una jornada de cosecha con cálculo automático de rendimiento."""
    return service.registrar_cosecha(db, ciclo_id, datos, usuario_ci=current_user.ci)


@router.post("/ciclos/{ciclo_id}/finalizar", response_model=CicloAgricolaOut)
def finalizar_ciclo(
    ciclo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Finaliza y consolida la campaña agrícola."""
    return service.finalizar_ciclo(db, ciclo_id, usuario_ci=current_user.ci)
