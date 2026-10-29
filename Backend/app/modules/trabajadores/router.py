from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.entities import Usuario
from app.modules.trabajadores.schemas import (
    TrabajadorOut,
    TrabajadorCreate,
    TrabajadorUpdate,
    AreaOut,
    AreaCreate,
)
from app.modules.trabajadores import service

router = APIRouter(prefix="/trabajadores", tags=["Gestión de Trabajadores"])


# Áreas
@router.get("/areas/all", response_model=List[AreaOut])
def listar_areas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.listar_areas(db)


@router.post("/areas", response_model=AreaOut, status_code=status.HTTP_201_CREATED)
def crear_area(
    payload: AreaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.crear_area(db, payload, admin_ci=current_user.ci)


# Trabajadores
@router.get("/", response_model=List[TrabajadorOut])
def listar_trabajadores(
    busqueda: Optional[str] = None,
    area_id: Optional[int] = None,
    solo_activos: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.listar_trabajadores(
        db, busqueda=busqueda, area_id=area_id, solo_activos=solo_activos
    )


@router.get("/{id}", response_model=TrabajadorOut)
def obtener_trabajador(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.obtener_trabajador_por_id(db, id)


@router.post("/", response_model=TrabajadorOut, status_code=status.HTTP_201_CREATED)
def registrar_trabajador(
    payload: TrabajadorCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.crear_trabajador(db, payload, admin_ci=current_user.ci)


@router.put("/{id}", response_model=TrabajadorOut)
def actualizar_trabajador(
    id: int,
    payload: TrabajadorUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.actualizar_trabajador(db, id, payload, admin_ci=current_user.ci)


@router.patch("/{id}/toggle-estado", response_model=TrabajadorOut)
def inactivar_activar_trabajador(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.toggle_estado_trabajador(db, id, admin_ci=current_user.ci)
