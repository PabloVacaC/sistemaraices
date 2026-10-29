from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.entities import Usuario
from app.core.security import verify_password, create_access_token
from app.modules.auth.schemas import TokenResponse, UsuarioTokenInfo
from app.modules.bitacora.service import registrar_bitacora


def login_usuario(db: Session, email: str, contrasena: str) -> TokenResponse:
    stmt = select(Usuario).where(Usuario.email == email)
    user = db.execute(stmt).scalars().first()

    if not user or not verify_password(contrasena, user.contraseña):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos",
        )

    if not user.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta de usuario se encuentra inactiva. Contacta al administrador.",
        )

    # Permisos del usuario según su rol
    permisos_lista = []
    rol_nombre = None
    nivel_jerarquico = None
    if user.rol:
        rol_nombre = user.rol.rol
        nivel_jerarquico = user.rol.niveljerarquico
        permisos_lista = [p.permisos for p in user.rol.permisos]

    token = create_access_token(data={"sub": user.email, "ci": user.ci})

    # Registrar en bitácora
    registrar_bitacora(
        db=db,
        modulo="AUTENTICACION",
        accion="LOGIN",
        descripcion=f"Inicio de sesión exitoso para el usuario {user.email}",
        usuario_ci=user.ci,
    )

    user_info = UsuarioTokenInfo(
        ci=user.ci,
        nombre=user.nombre,
        apellido=user.apellido,
        email=user.email,
        rol=rol_nombre,
        niveljerarquico=nivel_jerarquico,
        permisos=permisos_lista,
    )

    return TokenResponse(access_token=token, token_type="bearer", user=user_info)
