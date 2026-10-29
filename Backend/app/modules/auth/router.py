from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.entities import Usuario
from app.modules.auth.schemas import LoginRequest, TokenResponse, UsuarioTokenInfo
from app.modules.auth.service import login_usuario

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return login_usuario(db, payload.email, payload.contraseña)


@router.get("/me", response_model=UsuarioTokenInfo)
def obtener_perfil_actual(current_user: Usuario = Depends(get_current_user)):
    permisos_lista = []
    rol_nombre = None
    nivel_jerarquico = None
    if current_user.rol:
        rol_nombre = current_user.rol.rol
        nivel_jerarquico = current_user.rol.niveljerarquico
        permisos_lista = [p.permisos for p in current_user.rol.permisos]

    return UsuarioTokenInfo(
        ci=current_user.ci,
        nombre=current_user.nombre,
        apellido=current_user.apellido,
        email=current_user.email,
        rol=rol_nombre,
        niveljerarquico=nivel_jerarquico,
        permisos=permisos_lista,
    )
