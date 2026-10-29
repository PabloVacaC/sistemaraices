from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from fastapi import HTTPException, status

from app.models.entities import Trabajador, Area, ContactoEmergencia
from app.modules.trabajadores.schemas import (
    TrabajadorCreate,
    TrabajadorUpdate,
    AreaCreate,
)
from app.modules.bitacora.service import registrar_bitacora


def listar_trabajadores(
    db: Session,
    busqueda: Optional[str] = None,
    area_id: Optional[int] = None,
    solo_activos: Optional[bool] = None,
) -> List[Trabajador]:
    stmt = select(Trabajador).order_by(Trabajador.apellidos, Trabajador.nombres)

    if area_id is not None:
        stmt = stmt.where(Trabajador.area_id == area_id)

    if solo_activos is not None:
        stmt = stmt.where(Trabajador.estado == solo_activos)

    if busqueda:
        pattern = f"%{busqueda.strip()}%"
        stmt = stmt.where(
            or_(
                Trabajador.nombres.ilike(pattern),
                Trabajador.apellidos.ilike(pattern),
                Trabajador.ci.ilike(pattern),
                Trabajador.cargo.ilike(pattern),
            )
        )

    return list(db.execute(stmt).scalars().unique().all())


def obtener_trabajador_por_id(db: Session, trabajador_id: int) -> Trabajador:
    stmt = select(Trabajador).where(Trabajador.id == trabajador_id)
    t = db.execute(stmt).scalars().first()
    if not t:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trabajador con ID {trabajador_id} no encontrado",
        )
    return t


def crear_trabajador(
    db: Session, datos: TrabajadorCreate, admin_ci: Optional[str] = None
) -> Trabajador:
    # Si ingresó CI, verificar que no esté repetido
    if datos.ci and datos.ci.strip():
        existente = db.execute(
            select(Trabajador).where(Trabajador.ci == datos.ci.strip())
        ).scalars().first()
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un trabajador registrado con el CI {datos.ci}",
            )

    nuevo = Trabajador(
        ci=datos.ci.strip() if datos.ci else None,
        nombres=datos.nombres.strip(),
        apellidos=datos.apellidos.strip(),
        fotografia=datos.fotografia,
        celular=datos.celular,
        fecha_ingreso=datos.fecha_ingreso,
        cargo=datos.cargo.strip(),
        sueldoBase=datos.sueldoBase,
        estado=True,
        area_id=datos.area_id,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    # Agregar contactos de emergencia
    if datos.contactos:
        for c in datos.contactos:
            contacto = ContactoEmergencia(
                nombrecompleto=c.nombrecompleto,
                parentesco=c.parentesco,
                celular=c.celular,
                trabajador_id=nuevo.id,
            )
            db.add(contacto)
        db.commit()
        db.refresh(nuevo)

    registrar_bitacora(
        db=db,
        modulo="TRABAJADORES",
        accion="REGISTRAR",
        descripcion=f"Se registró el trabajador {nuevo.nombres} {nuevo.apellidos} (ID: {nuevo.id}, Cargo: {nuevo.cargo})",
        usuario_ci=admin_ci,
    )

    return nuevo


def actualizar_trabajador(
    db: Session, trabajador_id: int, datos: TrabajadorUpdate, admin_ci: Optional[str] = None
) -> Trabajador:
    t = obtener_trabajador_por_id(db, trabajador_id)

    if datos.ci is not None and datos.ci != t.ci:
        if datos.ci.strip():
            existente = db.execute(
                select(Trabajador).where(
                    Trabajador.ci == datos.ci.strip(), Trabajador.id != trabajador_id
                )
            ).scalars().first()
            if existente:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El CI {datos.ci} ya pertenece a otro trabajador",
                )
            t.ci = datos.ci.strip()
        else:
            t.ci = None

    if datos.nombres is not None:
        t.nombres = datos.nombres.strip()
    if datos.apellidos is not None:
        t.apellidos = datos.apellidos.strip()
    if datos.fotografia is not None:
        t.fotografia = datos.fotografia
    if datos.celular is not None:
        t.celular = datos.celular
    if datos.fecha_ingreso is not None:
        t.fecha_ingreso = datos.fecha_ingreso
    if datos.cargo is not None:
        t.cargo = datos.cargo.strip()
    if datos.sueldoBase is not None:
        t.sueldoBase = datos.sueldoBase
    if datos.estado is not None:
        t.estado = datos.estado
    if datos.area_id is not None:
        t.area_id = datos.area_id

    # Actualizar contactos de emergencia si se enviaron
    if datos.contactos is not None:
        # Borrar los anteriores y recrear
        for old_c in list(t.contactos_emergencia):
            db.delete(old_c)
        db.flush()
        for c in datos.contactos:
            nuevo_contacto = ContactoEmergencia(
                nombrecompleto=c.nombrecompleto,
                parentesco=c.parentesco,
                celular=c.celular,
                trabajador_id=t.id,
            )
            db.add(nuevo_contacto)

    db.commit()
    db.refresh(t)

    registrar_bitacora(
        db=db,
        modulo="TRABAJADORES",
        accion="MODIFICAR",
        descripcion=f"Se actualizaron los datos del trabajador {t.nombres} {t.apellidos} (ID: {t.id})",
        usuario_ci=admin_ci,
    )

    return t


def toggle_estado_trabajador(
    db: Session, trabajador_id: int, admin_ci: Optional[str] = None
) -> Trabajador:
    t = obtener_trabajador_por_id(db, trabajador_id)
    t.estado = not t.estado
    db.commit()
    db.refresh(t)

    estado_str = "Activado" if t.estado else "Inactivado"
    registrar_bitacora(
        db=db,
        modulo="TRABAJADORES",
        accion="CAMBIAR_ESTADO",
        descripcion=f"{estado_str} al trabajador {t.nombres} {t.apellidos} (ID: {t.id})",
        usuario_ci=admin_ci,
    )

    return t


# Funciones de Áreas
def listar_areas(db: Session) -> List[Area]:
    stmt = select(Area).order_by(Area.nombre)
    return list(db.execute(stmt).scalars().all())


def crear_area(db: Session, datos: AreaCreate, admin_ci: Optional[str] = None) -> Area:
    existente = db.execute(select(Area).where(Area.nombre == datos.nombre.strip())).scalars().first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El área '{datos.nombre}' ya existe",
        )

    nueva = Area(
        nombre=datos.nombre.strip(),
        estado=datos.estado,
        descripcion=datos.descripcion,
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    registrar_bitacora(
        db=db,
        modulo="AREAS",
        accion="CREAR",
        descripcion=f"Se creó el área de trabajo '{nueva.nombre}' (ID: {nueva.id})",
        usuario_ci=admin_ci,
    )

    return nueva
