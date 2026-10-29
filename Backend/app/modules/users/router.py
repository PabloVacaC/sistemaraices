from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user, require_permission
from app.models.entities import Usuario
from app.modules.users.schemas import (
    UsuarioOut,
    UsuarioCreate,
    UsuarioUpdate,
    RolOut,
    RolCreate,
    PermisoOut,
)
from app.modules.users import service

router = APIRouter(prefix="/users", tags=["Gestión de Usuarios"])


@router.get("/roles/all", response_model=List[RolOut])
def obtener_roles(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.listar_roles(db)


@router.post("/roles", response_model=RolOut, status_code=status.HTTP_201_CREATED)
def crear_nuevo_rol(
    payload: RolCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.crear_rol(db, payload, admin_ci=current_user.ci)


@router.get("/permisos/all", response_model=List[PermisoOut])
def obtener_permisos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.listar_permisos(db)


@router.get("/", response_model=List[UsuarioOut])
def listar_todos_los_usuarios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.listar_usuarios(db)


@router.get("/{ci}", response_model=UsuarioOut)
def obtener_usuario(
    ci: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.obtener_usuario_por_ci(db, ci)


@router.post("/", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def crear_usuario_endpoint(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.crear_usuario(db, payload, admin_ci=current_user.ci)


@router.put("/{ci}", response_model=UsuarioOut)
def actualizar_usuario_endpoint(
    ci: str,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.actualizar_usuario(db, ci, payload, admin_ci=current_user.ci)


@router.patch("/{ci}/toggle-estado", response_model=UsuarioOut)
def cambiar_estado_endpoint(
    ci: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.toggle_estado_usuario(db, ci, admin_ci=current_user.ci)
