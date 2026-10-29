from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.entities import Usuario, Rol, Permiso, RolPermiso
from app.core.security import get_password_hash
from app.modules.users.schemas import UsuarioCreate, UsuarioUpdate, RolCreate
from app.modules.bitacora.service import registrar_bitacora


def listar_usuarios(db: Session) -> List[Usuario]:
    stmt = select(Usuario).order_by(Usuario.apellido, Usuario.nombre)
    return list(db.execute(stmt).scalars().unique().all())


def obtener_usuario_por_ci(db: Session, ci: str) -> Usuario:
    stmt = select(Usuario).where(Usuario.ci == ci)
    usuario = db.execute(stmt).scalars().first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con CI {ci} no encontrado",
        )
    return usuario


def crear_usuario(db: Session, datos: UsuarioCreate, admin_ci: Optional[str] = None) -> Usuario:
    # Verificar si CI ya existe
    if db.execute(select(Usuario).where(Usuario.ci == datos.ci)).scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un usuario con el CI {datos.ci}",
        )

    # Verificar si email ya existe
    if db.execute(select(Usuario).where(Usuario.email == datos.email)).scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un usuario con el correo {datos.email}",
        )

    # Verificar rol
    rol = db.execute(select(Rol).where(Rol.id == datos.rol_id)).scalars().first()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El rol especificado con ID {datos.rol_id} no existe",
        )

    nuevo_usuario = Usuario(
        ci=datos.ci,
        nombre=datos.nombre,
        apellido=datos.apellido,
        email=datos.email,
        genero=datos.genero,
        contraseña=get_password_hash(datos.contraseña),
        fechanacimiento=datos.fechanacimiento,
        telefono=datos.telefono,
        direccion=datos.direccion,
        foto=datos.foto,
        estado=datos.estado,
        rol_id=datos.rol_id,
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    registrar_bitacora(
        db=db,
        modulo="USUARIOS",
        accion="CREAR",
        descripcion=f"Se creó el usuario {nuevo_usuario.nombre} {nuevo_usuario.apellido} (CI: {nuevo_usuario.ci}) con rol {rol.rol}",
        usuario_ci=admin_ci,
    )

    return nuevo_usuario


def actualizar_usuario(
    db: Session, ci: str, datos: UsuarioUpdate, admin_ci: Optional[str] = None
) -> Usuario:
    usuario = obtener_usuario_por_ci(db, ci)

    if datos.email and datos.email != usuario.email:
        existente = db.execute(
            select(Usuario).where(Usuario.email == datos.email)
        ).scalars().first()
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El correo {datos.email} ya está registrado por otro usuario",
            )
        usuario.email = datos.email

    if datos.nombre is not None:
        usuario.nombre = datos.nombre
    if datos.apellido is not None:
        usuario.apellido = datos.apellido
    if datos.genero is not None:
        usuario.genero = datos.genero
    if datos.fechanacimiento is not None:
        usuario.fechanacimiento = datos.fechanacimiento
    if datos.telefono is not None:
        usuario.telefono = datos.telefono
    if datos.direccion is not None:
        usuario.direccion = datos.direccion
    if datos.foto is not None:
        usuario.foto = datos.foto
    if datos.estado is not None:
        usuario.estado = datos.estado
    if datos.rol_id is not None:
        rol = db.execute(select(Rol).where(Rol.id == datos.rol_id)).scalars().first()
        if not rol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El rol {datos.rol_id} no existe",
            )
        usuario.rol_id = datos.rol_id

    if datos.contraseña and datos.contraseña.strip():
        usuario.contraseña = get_password_hash(datos.contraseña)

    db.commit()
    db.refresh(usuario)

    registrar_bitacora(
        db=db,
        modulo="USUARIOS",
        accion="MODIFICAR",
        descripcion=f"Se actualizó la información del usuario CI: {usuario.ci}",
        usuario_ci=admin_ci,
    )

    return usuario


def toggle_estado_usuario(db: Session, ci: str, admin_ci: Optional[str] = None) -> Usuario:
    usuario = obtener_usuario_por_ci(db, ci)
    usuario.estado = not usuario.estado
    db.commit()
    db.refresh(usuario)

    estado_str = "Activado" if usuario.estado else "Inactivado"
    registrar_bitacora(
        db=db,
        modulo="USUARIOS",
        accion="CAMBIAR_ESTADO",
        descripcion=f"{estado_str} usuario CI: {usuario.ci}",
        usuario_ci=admin_ci,
    )

    return usuario


def listar_roles(db: Session) -> List[Rol]:
    stmt = select(Rol).order_by(Rol.niveljerarquico, Rol.rol)
    return list(db.execute(stmt).scalars().unique().all())


def listar_permisos(db: Session) -> List[Permiso]:
    stmt = select(Permiso).order_by(Permiso.permisos)
    return list(db.execute(stmt).scalars().all())


def crear_rol(db: Session, datos: RolCreate, admin_ci: Optional[str] = None) -> Rol:
    if db.execute(select(Rol).where(Rol.rol == datos.rol)).scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un rol con el nombre {datos.rol}",
        )

    nuevo_rol = Rol(
        rol=datos.rol,
        niveljerarquico=datos.niveljerarquico,
        descripcion=datos.descripcion,
    )
    db.add(nuevo_rol)
    db.commit()
    db.refresh(nuevo_rol)

    if datos.permiso_ids:
        for pid in datos.permiso_ids:
            db.add(RolPermiso(rol_id=nuevo_rol.id, permiso_id=pid))
        db.commit()
        db.refresh(nuevo_rol)

    registrar_bitacora(
        db=db,
        modulo="ROLES",
        accion="CREAR",
        descripcion=f"Se creó el rol {nuevo_rol.rol} (ID: {nuevo_rol.id})",
        usuario_ci=admin_ci,
    )

    return nuevo_rol
