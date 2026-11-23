from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, desc, text
from fastapi import HTTPException, status

from app.models.entities import (
    Animal,
    PesajeGanado,
    HistorialArete,
    NacimientoGanado,
    CompraGanado,
    CompraGanadoDetalle,
    VentaGanado,
    VentaGanadoDetalle,
    BajaGanado,
    Usuario,
    Potrero,
    MovimientoGanado,
    MovimientoGanadoDetalle,
)
import json
import math
import random
from app.modules.bitacora.service import registrar_bitacora
from app.modules.ganaderia.schemas import (
    AnimalCreate,
    AnimalUpdate,
    PesajeCreate,
    NacimientoCreate,
    NacimientoUpdate,
    CompraGanadoCreate,
    VentaGanadoCreate,
    BajaGanadoCreate,
    GanaderiaKPIsOut,
    PotreroCreate,
    PotreroUpdate,
    PotreroOut,
    PotreroDetalleOut,
    MovimientoGanadoCreate,
    MovimientoGanadoOut,
    MovimientoGanadoDetalleOut,
    MapaDistribucionOut,
    AnimalPuntoMapa,
)

TZ_BOLIVIA = timezone(timedelta(hours=-4))


def obtener_ahora_bolivia() -> datetime:
    return datetime.now(TZ_BOLIVIA)


def obtener_fecha_bolivia() -> date:
    return datetime.now(TZ_BOLIVIA).date()


# =========================================================================
# GENERADORES DE CÓDIGOS Y COMPROBANTES CORRELATIVOS
# =========================================================================
def generar_codigo_interno_animal(db: Session) -> str:
    """Genera código interno secuencial único e inmutable tipo GAN-0001, GAN-0002..."""
    total = db.scalar(select(func.count(Animal.id))) or 0
    correlativo = total + 1
    codigo = f"GAN-{correlativo:04d}"
    while db.scalar(select(Animal.id).where(Animal.codigo_interno == codigo)):
        correlativo += 1
        codigo = f"GAN-{correlativo:04d}"
    return codigo


def generar_comprobante_ganaderia(db: Session, prefijo: str) -> str:
    """Genera comprobantes tipo CMP-GAN-202611-0001, VNT-GAN-202611-0001, BAJ-GAN-202611-0001, NAC-GAN-202611-0001"""
    now = obtener_ahora_bolivia()
    ym = now.strftime("%Y%m")
    prefix_ym = f"{prefijo}-{ym}-"

    correlativo = 1
    if prefijo == "CMP-GAN":
        total = db.scalar(select(func.count(CompraGanado.id)).where(CompraGanado.numero_comprobante.like(f"{prefix_ym}%"))) or 0
        correlativo = total + 1
        while db.scalar(select(CompraGanado.id).where(CompraGanado.numero_comprobante == f"{prefix_ym}{correlativo:04d}")):
            correlativo += 1
    elif prefijo == "VNT-GAN":
        total = db.scalar(select(func.count(VentaGanado.id)).where(VentaGanado.numero_comprobante.like(f"{prefix_ym}%"))) or 0
        correlativo = total + 1
        while db.scalar(select(VentaGanado.id).where(VentaGanado.numero_comprobante == f"{prefix_ym}{correlativo:04d}")):
            correlativo += 1
    elif prefijo == "BAJ-GAN":
        total = db.scalar(select(func.count(BajaGanado.id)).where(BajaGanado.numero_comprobante.like(f"{prefix_ym}%"))) or 0
        correlativo = total + 1
        while db.scalar(select(BajaGanado.id).where(BajaGanado.numero_comprobante == f"{prefix_ym}{correlativo:04d}")):
            correlativo += 1
    elif prefijo == "NAC-GAN":
        total = db.scalar(select(func.count(NacimientoGanado.id)).where(NacimientoGanado.numero_comprobante.like(f"{prefix_ym}%"))) or 0
        correlativo = total + 1
        while db.scalar(select(NacimientoGanado.id).where(NacimientoGanado.numero_comprobante == f"{prefix_ym}{correlativo:04d}")):
            correlativo += 1
    elif prefijo == "MOV-GAN":
        total = db.scalar(select(func.count(MovimientoGanado.id)).where(MovimientoGanado.numero_comprobante.like(f"{prefix_ym}%"))) or 0
        correlativo = total + 1
        while db.scalar(select(MovimientoGanado.id).where(MovimientoGanado.numero_comprobante == f"{prefix_ym}{correlativo:04d}")):
            correlativo += 1

    return f"{prefix_ym}{correlativo:04d}"


def validar_unicidad_arete(db: Session, arete: Optional[str], animal_id_actual: Optional[int] = None):
    """
    Verifica que el número de arete sea único globalmente en todo el sistema.
    Regla CE-005 y CE-006: Un arete de animal vendido o dado de baja JAMÁS puede reutilizarse.
    """
    if not arete or not arete.strip():
        return
    arete_limpio = arete.strip()
    stmt = select(Animal).where(Animal.numero_arete == arete_limpio)
    if animal_id_actual is not None:
        stmt = stmt.where(Animal.id != animal_id_actual)
    existente = db.execute(stmt).scalars().first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El número de arete '{arete_limpio}' ya está registrado y pertenece al animal "
                f"{existente.codigo_interno} ({existente.nombre or 'Sin nombre'}, Estado: {existente.estado}). "
                f"La identificación física debe ser única en todo el sistema y no puede duplicarse ni reutilizarse."
            ),
        )


def calcular_edad_en_meses(fecha_nac: date) -> int:
    hoy = obtener_fecha_bolivia()
    anios = hoy.year - fecha_nac.year
    meses = hoy.month - fecha_nac.month
    dias = hoy.day - fecha_nac.day
    total_meses = anios * 12 + meses
    if dias < 0:
        total_meses -= 1
    return max(0, total_meses)


def resolver_potrero(
    db: Session,
    potrero_id: Optional[int] = None,
    ubicacion: Optional[str] = None
) -> Tuple[Optional[int], str]:
    """
    Resuelve atómicamente el potrero_id y el nombre sincronizado de ubicación (RF-008 / SPEC-002).
    1. Si se provee potrero_id, busca el Potrero. Si existe y está activo, retorna (pot.id, pot.nombre).
    2. Si se provee ubicacion (texto), busca coincidencia exacta o insensible a mayúsculas en la tabla Potrero.
    3. Si no hay coincidencia directa pero existen potreros activos, asigna el primer potrero activo para
       garantizar que el animal tenga coordenadas y aparezca en la cartografía satelital.
    4. Si no existen potreros en el sistema, retorna (None, ubicacion).
    """
    if potrero_id:
        pot = db.get(Potrero, potrero_id)
        if pot and pot.estado == "ACTIVO":
            return pot.id, pot.nombre

    if ubicacion and ubicacion.strip():
        ubi_clean = ubicacion.strip()
        # Coincidencia insensible a mayúsculas
        pot = db.scalar(
            select(Potrero).where(
                Potrero.estado == "ACTIVO",
                func.lower(Potrero.nombre) == func.lower(ubi_clean),
            )
        )
        if pot:
            return pot.id, pot.nombre

        # Coincidencia parcial (e.g. "Potrero 1" con "POTRERO 1")
        pot_parcial = db.scalar(
            select(Potrero).where(
                Potrero.estado == "ACTIVO",
                Potrero.nombre.ilike(f"%{ubi_clean}%"),
            )
        )
        if pot_parcial:
            return pot_parcial.id, pot_parcial.nombre

    # Fallback al primer potrero activo disponible en el establecimiento
    primer_potrero = db.scalar(
        select(Potrero).where(Potrero.estado == "ACTIVO").order_by(Potrero.id.asc())
    )
    if primer_potrero:
        return primer_potrero.id, primer_potrero.nombre

    return None, (ubicacion.strip() if ubicacion else "Sin Potrero Asignado")


# =========================================================================
# GESTIÓN DE ANIMALES (CRUD, PERFIL, FILTROS)
# =========================================================================
def registrar_animal_manual(db: Session, datos: AnimalCreate, usuario_ci: str) -> Animal:
    """Registra manualmente un animal según RF-005 y RF-006."""
    fecha_nac = datos.fecha_nacimiento or obtener_fecha_bolivia()
    if datos.fecha_nacimiento and datos.fecha_nacimiento > obtener_fecha_bolivia():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de nacimiento no puede ser una fecha futura.",
        )

    # Validar unicidad de arete si se proporcionó
    validar_unicidad_arete(db, datos.numero_arete)

    # Validar genealogía
    if datos.madre_id:
        madre = db.get(Animal, datos.madre_id)
        if not madre:
            raise HTTPException(status_code=404, detail="El animal seleccionado como madre no existe.")
        if madre.sexo != "HEMBRA":
            raise HTTPException(status_code=400, detail="El animal asignado como madre debe ser de sexo HEMBRA.")

    if datos.padre_id:
        padre = db.get(Animal, datos.padre_id)
        if not padre:
            raise HTTPException(status_code=404, detail="El animal seleccionado como padre no existe.")
        if padre.sexo != "MACHO":
            raise HTTPException(status_code=400, detail="El animal asignado como padre debe ser de sexo MACHO.")

    codigo_interno = generar_codigo_interno_animal(db)
    arete = datos.numero_arete.strip() if datos.numero_arete and datos.numero_arete.strip() else None
    tipo_final = (datos.tipo_ganado or datos.tipo or "Bovino").strip()

    pot_id, pot_nombre = resolver_potrero(db, datos.potrero_id, datos.ubicacion)

    animal = Animal(
        codigo_interno=codigo_interno,
        numero_arete=arete,
        nombre=datos.nombre.strip() if datos.nombre else None,
        tipo=tipo_final,
        raza=datos.raza.strip() if datos.raza else "Nelore",
        sexo=datos.sexo.strip().upper(),
        fecha_nacimiento=fecha_nac,
        peso_inicial=datos.peso_inicial,
        peso_actual=datos.peso_inicial,
        fecha_ultimo_pesaje=fecha_nac if datos.peso_inicial else None,
        estado="ACTIVO",
        procedencia="REGISTRO_MANUAL",
        madre_id=datos.madre_id,
        padre_id=datos.padre_id,
        potrero_id=pot_id,
        ubicacion=pot_nombre,
        propietario=datos.propietario.strip() if datos.propietario else None,
        observaciones=datos.observaciones,
        usuario_registro_ci=usuario_ci,
    )
    db.add(animal)
    db.flush()

    # Si se cargó peso inicial, registrar automáticamente el primer pesaje histórico
    if datos.peso_inicial and datos.peso_inicial > 0:
        primer_pesaje = PesajeGanado(
            animal_id=animal.id,
            fecha_pesaje=datos.fecha_nacimiento,
            peso=datos.peso_inicial,
            variacion_anterior=Decimal("0.00"),
            responsable="Registro Inicial",
            observaciones="Peso inicial registrado en la creación del animal.",
            usuario_ci=usuario_ci,
        )
        db.add(primer_pesaje)

    # Si se asignó arete inicial, registrar en el historial
    if arete:
        hist_arete = HistorialArete(
            animal_id=animal.id,
            arete_anterior=None,
            arete_nuevo=arete,
            fecha_cambio=obtener_fecha_bolivia(),
            motivo="Asignación inicial de arete físico.",
            usuario_ci=usuario_ci,
        )
        db.add(hist_arete)

    registrar_bitacora(
        db=db,
        modulo="GANADERIA",
        accion="REGISTRAR_ANIMAL",
        descripcion=(
            f"Se registró manualmente el animal {animal.codigo_interno} (Arete: {animal.numero_arete or 'S/N'}, "
            f"Raza: {animal.raza}, Sexo: {animal.sexo}, Ubicación: {animal.ubicacion})."
        ),
        usuario_ci=usuario_ci,
        commit=False,
    )

    db.commit()
    db.refresh(animal)
    return animal


def listar_animales(
    db: Session,
    filtro_procedencia: Optional[str] = None,  # REGISTRADOS, NACIMIENTOS, COMPRAS, VENTAS, BAJAS, TODOS
    estado: Optional[str] = None,
    sexo: Optional[str] = None,
    tipo: Optional[str] = None,
    busqueda: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[dict], int]:
    """Consulta paginada del registro principal de animales (RF-002, RF-016, RF-017)."""
    stmt = select(Animal)

    # Filtros de procedencia según RF-016
    if filtro_procedencia:
        fp = filtro_procedencia.upper().strip()
        if fp == "REGISTRADOS":
            stmt = stmt.where(Animal.procedencia == "REGISTRO_MANUAL")
        elif fp == "NACIMIENTOS":
            stmt = stmt.where(Animal.procedencia == "NACIMIENTO")
        elif fp == "COMPRAS":
            stmt = stmt.where(Animal.procedencia == "COMPRA")
        elif fp == "VENTAS":
            stmt = stmt.where(Animal.estado == "VENDIDO")
        elif fp == "BAJAS":
            stmt = stmt.where(Animal.estado.in_(["FALLECIDO", "ROBADO", "PERDIDO", "SACRIFICADO", "DESCARTADO", "BAJA"]))

    if estado and estado.strip() and estado.upper() != "TODOS":
        stmt = stmt.where(Animal.estado == estado.upper().strip())

    if sexo and sexo.strip() and sexo.upper() != "TODOS":
        stmt = stmt.where(Animal.sexo == sexo.upper().strip())

    if tipo and tipo.strip() and tipo.upper() != "TODOS":
        stmt = stmt.where(Animal.tipo == tipo.strip())

    if busqueda and busqueda.strip():
        term = f"%{busqueda.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Animal.codigo_interno).like(term),
                func.lower(Animal.numero_arete).like(term),
                func.lower(Animal.nombre).like(term),
                func.lower(Animal.raza).like(term),
                func.lower(Animal.ubicacion).like(term),
            )
        )

    # Conteo total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    # Ordenar por id descendente (más recientes primero)
    stmt = stmt.order_by(desc(Animal.id)).offset(skip).limit(limit)
    animales = list(db.execute(stmt).scalars().unique().all())

    # Formatear salida enriquecida
    filas_out = []
    for a in animales:
        edad = calcular_edad_en_meses(a.fecha_nacimiento)
        ganancia = (a.peso_actual - a.peso_inicial) if (a.peso_actual and a.peso_inicial) else Decimal("0.00")
        filas_out.append({
            "id": a.id,
            "codigo_interno": a.codigo_interno,
            "numero_arete": a.numero_arete,
            "nombre": a.nombre,
            "tipo": a.tipo,
            "tipo_ganado": a.tipo,
            "raza": a.raza,
            "sexo": a.sexo,
            "fecha_nacimiento": a.fecha_nacimiento,
            "edad_meses": edad,
            "peso_inicial": a.peso_inicial,
            "peso_actual": a.peso_actual,
            "fecha_ultimo_pesaje": a.fecha_ultimo_pesaje,
            "ganancia_peso_total": ganancia,
            "estado": a.estado,
            "procedencia": a.procedencia,
            "madre_id": a.madre_id,
            "padre_id": a.padre_id,
            "madre_arete": a.madre.numero_arete if a.madre else None,
            "padre_arete": a.padre.numero_arete if a.padre else None,
            "potrero_id": a.potrero_id,
            "ubicacion": a.ubicacion,
            "propietario": a.propietario,
            "observaciones": a.observaciones,
            "fecha_registro": a.fecha_creacion,
            "fecha_creacion": a.fecha_creacion,
            "fecha_actualizacion": a.fecha_actualizacion,
        })

    return filas_out, total


def obtener_perfil_animal(db: Session, animal_id: int) -> dict:
    """Perfil 360° individual del animal con 6 secciones completas (RF-018)."""
    animal = db.get(Animal, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal no encontrado.")

    edad = calcular_edad_en_meses(animal.fecha_nacimiento)
    ganancia = (animal.peso_actual - animal.peso_inicial) if (animal.peso_actual and animal.peso_inicial) else Decimal("0.00")

    # Madre y Padre
    madre_out = None
    if animal.madre:
        madre_out = {
            "id": animal.madre.id,
            "codigo_interno": animal.madre.codigo_interno,
            "numero_arete": animal.madre.numero_arete,
            "nombre": animal.madre.nombre,
            "tipo": animal.madre.tipo,
            "raza": animal.madre.raza,
            "sexo": animal.madre.sexo,
        }

    padre_out = None
    if animal.padre:
        padre_out = {
            "id": animal.padre.id,
            "codigo_interno": animal.padre.codigo_interno,
            "numero_arete": animal.padre.numero_arete,
            "nombre": animal.padre.nombre,
            "tipo": animal.padre.tipo,
            "raza": animal.padre.raza,
            "sexo": animal.padre.sexo,
        }

    # Historial de pesajes ordenados
    pesajes_out = [
        {
            "id": p.id,
            "animal_id": p.animal_id,
            "fecha_pesaje": p.fecha_pesaje,
            "peso": p.peso,
            "variacion_anterior": p.variacion_anterior,
            "responsable": p.responsable,
            "observaciones": p.observaciones,
            "usuario_ci": p.usuario_ci,
            "fecha_creacion": p.fecha_creacion,
        }
        for p in animal.pesajes
    ]

    # Historial de aretes
    aretes_out = [
        {
            "id": h.id,
            "animal_id": h.animal_id,
            "arete_anterior": h.arete_anterior,
            "arete_nuevo": h.arete_nuevo,
            "fecha_cambio": h.fecha_cambio,
            "motivo": h.motivo,
            "usuario_ci": h.usuario_ci,
            "fecha_creacion": h.fecha_creacion,
        }
        for h in animal.historial_aretes
    ]

    # Operaciones asociadas (compra, venta, baja, nacimiento)
    operaciones = {}
    if animal.procedencia == "COMPRA":
        detalle_compra = db.execute(
            select(CompraGanadoDetalle).where(CompraGanadoDetalle.animal_id == animal.id)
        ).scalars().first()
        if detalle_compra and detalle_compra.compra:
            operaciones["compra"] = {
                "comprobante": detalle_compra.compra.numero_comprobante,
                "proveedor": detalle_compra.compra.proveedor,
                "fecha": str(detalle_compra.compra.fecha_compra),
                "precio": float(detalle_compra.costo_total),
                "modalidad": detalle_compra.modalidad_precio,
            }

    if animal.procedencia == "NACIMIENTO":
        nacimiento = db.execute(
            select(NacimientoGanado).where(NacimientoGanado.cria_id == animal.id)
        ).scalars().first()
        if nacimiento:
            operaciones["nacimiento"] = {
                "comprobante": nacimiento.numero_comprobante,
                "fecha": str(nacimiento.fecha_nacimiento),
                "tipo_parto": nacimiento.tipo_parto,
                "peso_nacimiento": float(nacimiento.peso_nacimiento) if nacimiento.peso_nacimiento else None,
            }

    if animal.estado == "VENDIDO":
        detalle_venta = db.execute(
            select(VentaGanadoDetalle).where(VentaGanadoDetalle.animal_id == animal.id)
        ).scalars().first()
        if detalle_venta and detalle_venta.venta:
            operaciones["venta"] = {
                "comprobante": detalle_venta.venta.numero_comprobante,
                "cliente": detalle_venta.venta.cliente,
                "fecha": str(detalle_venta.venta.fecha_venta),
                "monto": float(detalle_venta.subtotal),
                "metodo_pago": detalle_venta.venta.metodo_pago,
            }

    if animal.estado in ["FALLECIDO", "ROBADO", "PERDIDO", "SACRIFICADO", "DESCARTADO", "BAJA"]:
        baja = db.execute(
            select(BajaGanado).where(BajaGanado.animal_id == animal.id)
        ).scalars().first()
        if baja:
            operaciones["baja"] = {
                "comprobante": baja.numero_comprobante,
                "motivo": baja.motivo,
                "fecha": str(baja.fecha_baja),
                "responsable": baja.responsable,
                "observaciones": baja.observaciones,
            }

    # Crías producidas (hijos)
    stmt_hijos = select(Animal).where(or_(Animal.madre_id == animal.id, Animal.padre_id == animal.id)).order_by(desc(Animal.fecha_nacimiento))
    hijos_entities = list(db.execute(stmt_hijos).scalars().all())
    hijos_out = [
        {
            "id": h.id,
            "codigo_interno": h.codigo_interno,
            "numero_arete": h.numero_arete,
            "nombre": h.nombre,
            "tipo": h.tipo,
            "raza": h.raza,
            "sexo": h.sexo,
            "fecha_nacimiento": h.fecha_nacimiento,
            "estado": h.estado,
        }
        for h in hijos_entities
    ]

    det_compra_out = None
    if animal.procedencia == "COMPRA":
        dc = db.execute(
            select(CompraGanadoDetalle).where(CompraGanadoDetalle.animal_id == animal.id)
        ).scalars().first()
        if dc:
            det_compra_out = {
                "id": dc.id,
                "compra_id": dc.compra_id,
                "animal_id": dc.animal_id,
                "modalidad_precio": dc.modalidad_precio,
                "precio_unitario": float(dc.precio_unitario),
                "peso_compra": float(dc.peso_compra) if dc.peso_compra else None,
                "subtotal": float(dc.costo_total),
            }

    det_venta_out = None
    if animal.estado == "VENDIDO":
        dv = db.execute(
            select(VentaGanadoDetalle).where(VentaGanadoDetalle.animal_id == animal.id)
        ).scalars().first()
        if dv:
            det_venta_out = {
                "id": dv.id,
                "venta_id": dv.venta_id,
                "animal_id": dv.animal_id,
                "numero_arete": dv.numero_arete,
                "modalidad_precio": dv.modalidad_precio,
                "peso_venta": float(dv.peso_venta) if dv.peso_venta else None,
                "precio_unitario": float(dv.precio_unitario),
                "subtotal": float(dv.subtotal),
            }

    det_baja_out = None
    if animal.estado in ["FALLECIDO", "ROBADO", "PERDIDO", "SACRIFICADO", "DESCARTADO", "BAJA"]:
        b = db.execute(
            select(BajaGanado).where(BajaGanado.animal_id == animal.id)
        ).scalars().first()
        if b:
            det_baja_out = {
                "id": b.id,
                "numero_acta": b.numero_comprobante,
                "animal_id": b.animal_id,
                "tipo_baja": b.motivo,
                "fecha_baja": str(b.fecha_baja),
                "causa_diagnostico": b.observaciones,
                "responsable": b.responsable,
                "estado": b.estado,
                "valor_estimado_perdida": 0,
            }

    animal_dict = {
        "id": animal.id,
        "codigo_interno": animal.codigo_interno,
        "numero_arete": animal.numero_arete,
        "nombre": animal.nombre,
        "tipo_ganado": animal.tipo,
        "tipo": animal.tipo,
        "raza": animal.raza,
        "sexo": animal.sexo,
        "fecha_nacimiento": animal.fecha_nacimiento,
        "edad_estimada_meses": edad,
        "edad_meses": edad,
        "peso_inicial": animal.peso_inicial,
        "peso_actual": animal.peso_actual,
        "fecha_ultimo_pesaje": animal.fecha_ultimo_pesaje,
        "categoria": "General",
        "ganancia_peso_total": ganancia,
        "estado": animal.estado,
        "procedencia": animal.procedencia,
        "madre_id": animal.madre_id,
        "madre_codigo": animal.madre.codigo_interno if animal.madre else None,
        "madre_arete": animal.madre.numero_arete if animal.madre else None,
        "padre_id": animal.padre_id,
        "padre_codigo": animal.padre.codigo_interno if animal.padre else None,
        "padre_arete": animal.padre.numero_arete if animal.padre else None,
        "potrero_id": animal.potrero_id,
        "ubicacion": animal.ubicacion,
        "propietario": animal.propietario,
        "observaciones": animal.observaciones,
        "fecha_registro": animal.fecha_creacion,
        "fecha_creacion": animal.fecha_creacion,
        "fecha_actualizacion": animal.fecha_actualizacion,
    }

    return {
        **animal_dict,
        "animal": animal_dict,
        "madre": madre_out,
        "padre": padre_out,
        "historial_pesajes": pesajes_out,
        "pesajes": pesajes_out,
        "historial_aretes": aretes_out,
        "detalles_operaciones": operaciones,
        "hijos": hijos_out,
        "detalles_compra": det_compra_out,
        "detalles_venta": det_venta_out,
        "detalles_baja": det_baja_out,
        "historial_movimientos": obtener_historial_movimientos_animal(db, animal.id),
    }


def actualizar_animal(db: Session, animal_id: int, datos: AnimalUpdate, usuario_ci: str) -> Animal:
    """Edición controlada de animal según RF-011 y CE-007."""
    animal = db.get(Animal, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal no encontrado.")

    # Control de cambio de número de arete
    if datos.numero_arete is not None:
        nuevo_arete = datos.numero_arete.strip() if datos.numero_arete.strip() else None
        if nuevo_arete != animal.numero_arete:
            if nuevo_arete:
                validar_unicidad_arete(db, nuevo_arete, animal_id_actual=animal.id)

            historial = HistorialArete(
                animal_id=animal.id,
                arete_anterior=animal.numero_arete,
                arete_nuevo=nuevo_arete or "RETIRADO_SIN_ARETE",
                fecha_cambio=obtener_fecha_bolivia(),
                motivo=datos.motivo_cambio_arete or "Modificación de identificación física.",
                usuario_ci=usuario_ci,
            )
            db.add(historial)
            animal.numero_arete = nuevo_arete

    if datos.nombre is not None:
        animal.nombre = datos.nombre.strip() if datos.nombre.strip() else None
    if datos.tipo is not None:
        animal.tipo = datos.tipo.strip()
    if datos.raza is not None:
        animal.raza = datos.raza.strip()
    if datos.sexo is not None:
        animal.sexo = datos.sexo.strip().upper()
    if datos.fecha_nacimiento is not None:
        if datos.fecha_nacimiento > obtener_fecha_bolivia():
            raise HTTPException(status_code=400, detail="La fecha de nacimiento no puede ser futura.")
        animal.fecha_nacimiento = datos.fecha_nacimiento
    if datos.potrero_id is not None or datos.ubicacion is not None:
        pot_id, pot_nombre = resolver_potrero(
            db,
            potrero_id=datos.potrero_id,
            ubicacion=datos.ubicacion or animal.ubicacion,
        )
        animal.potrero_id = pot_id
        animal.ubicacion = pot_nombre
    if datos.propietario is not None:
        animal.propietario = datos.propietario.strip() if datos.propietario.strip() else None
    if datos.observaciones is not None:
        animal.observaciones = datos.observaciones

    if datos.madre_id is not None:
        if datos.madre_id == animal.id:
            raise HTTPException(status_code=400, detail="Un animal no puede ser su propia madre.")
        animal.madre_id = datos.madre_id

    if datos.padre_id is not None:
        if datos.padre_id == animal.id:
            raise HTTPException(status_code=400, detail="Un animal no puede ser su propio padre.")
        animal.padre_id = datos.padre_id

    registrar_bitacora(
        db=db,
        modulo="GANADERIA",
        accion="MODIFICAR_ANIMAL",
        descripcion=f"Se actualizaron los datos del animal {animal.codigo_interno} (Arete: {animal.numero_arete or 'S/N'}).",
        usuario_ci=usuario_ci,
        commit=False,
    )

    db.commit()
    db.refresh(animal)
    return animal


# =========================================================================
# REGISTRO E HISTORIAL DE PESAJES (RF-019, RF-020, CE-008, CE-009, CE-010)
# =========================================================================
def registrar_pesaje(db: Session, animal_id: int, datos: PesajeCreate, usuario_ci: str) -> PesajeGanado:
    """Registra pesaje individual independiente y actualiza peso_actual (RF-019)."""
    animal = db.get(Animal, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal no encontrado.")

    # Calcular variación respecto al pesaje inmediatamente anterior a esta fecha
    pesaje_anterior = db.execute(
        select(PesajeGanado)
        .where(PesajeGanado.animal_id == animal_id, PesajeGanado.fecha_pesaje <= datos.fecha_pesaje)
        .order_by(desc(PesajeGanado.fecha_pesaje), desc(PesajeGanado.id))
    ).scalars().first()

    variacion = Decimal("0.00")
    if pesaje_anterior:
        variacion = datos.peso - pesaje_anterior.peso

    nuevo_pesaje = PesajeGanado(
        animal_id=animal.id,
        fecha_pesaje=datos.fecha_pesaje,
        peso=datos.peso,
        variacion_anterior=variacion,
        responsable=datos.responsable.strip() if datos.responsable else None,
        observaciones=datos.observaciones,
        usuario_ci=usuario_ci,
    )
    db.add(nuevo_pesaje)
    db.flush()

    # Si es el pesaje más reciente cronológicamente, actualizar peso_actual y fecha_ultimo_pesaje
    ultimo_pesaje_cronologico = db.execute(
        select(PesajeGanado)
        .where(PesajeGanado.animal_id == animal_id)
        .order_by(desc(PesajeGanado.fecha_pesaje), desc(PesajeGanado.id))
    ).scalars().first()

    if ultimo_pesaje_cronologico:
        animal.peso_actual = ultimo_pesaje_cronologico.peso
        animal.fecha_ultimo_pesaje = ultimo_pesaje_cronologico.fecha_pesaje

    registrar_bitacora(
        db=db,
        modulo="GANADERIA",
        accion="REGISTRAR_PESAJE",
        descripcion=(
            f"Se registró pesaje de {datos.peso} kg para el animal {animal.codigo_interno} "
            f"(Arete: {animal.numero_arete or 'S/N'}, Variación: {variacion:+.2f} kg)."
        ),
        usuario_ci=usuario_ci,
        commit=False,
    )

    db.commit()
    db.refresh(nuevo_pesaje)
    return nuevo_pesaje


def anular_pesaje(db: Session, pesaje_id: int, usuario_ci: str):
    """Eliminación controlada de un pesaje erróneo recalculando peso_actual."""
    pesaje = db.get(PesajeGanado, pesaje_id)
    if not pesaje:
        raise HTTPException(status_code=404, detail="Registro de pesaje no encontrado.")

    animal = db.get(Animal, pesaje.animal_id)
    db.delete(pesaje)
    db.flush()

    # Recalcular peso actual con el pesaje restante más reciente
    restante = db.execute(
        select(PesajeGanado)
        .where(PesajeGanado.animal_id == animal.id)
        .order_by(desc(PesajeGanado.fecha_pesaje), desc(PesajeGanado.id))
    ).scalars().first()

    if restante:
        animal.peso_actual = restante.peso
        animal.fecha_ultimo_pesaje = restante.fecha_pesaje
    else:
        animal.peso_actual = animal.peso_inicial
        animal.fecha_ultimo_pesaje = animal.fecha_nacimiento if animal.peso_inicial else None

    registrar_bitacora(
        db=db,
        modulo="GANADERIA",
        accion="ELIMINAR_PESAJE",
        descripcion=f"Se eliminó el pesaje ID {pesaje_id} del animal {animal.codigo_interno}.",
        usuario_ci=usuario_ci,
        commit=False,
    )

    db.commit()
    return {"ok": True, "message": "Pesaje eliminado y peso actual recalculado."}


# =========================================================================
# REGISTRO DE NACIMIENTOS (RF-007, RF-012)
# =========================================================================
def registrar_nacimiento(db: Session, datos: NacimientoCreate, usuario_ci: str) -> NacimientoGanado:
    """Registra el nacimiento y crea automáticamente la cría activa (si nació viva)."""
    madre = db.get(Animal, datos.madre_id)
    if not madre:
        raise HTTPException(status_code=404, detail="La madre seleccionada no existe.")
    if madre.sexo != "HEMBRA":
        raise HTTPException(status_code=400, detail="El animal asignado como madre debe ser de sexo HEMBRA.")

    if datos.padre_id:
        padre = db.get(Animal, datos.padre_id)
        if not padre:
            raise HTTPException(status_code=404, detail="El padre seleccionado no existe.")
        if padre.sexo != "MACHO":
            raise HTTPException(status_code=400, detail="El animal asignado como padre debe ser de sexo MACHO.")

    fecha_nac = datos.fecha_nacimiento or datos.fecha_parto or obtener_fecha_bolivia()
    sexo_cria = (datos.sexo_cria or datos.cria_sexo or "HEMBRA").strip().upper()
    estado_nac = "VIVO"
    if datos.condicion_cria:
        estado_nac = "VIVO" if datos.condicion_cria.upper() == "VIVA" else "MUERTO_AL_NACER"
    elif datos.estado_nacimiento:
        estado_nac = datos.estado_nacimiento.upper()

    peso_nac = datos.peso_nacimiento or datos.cria_peso_nacer
    arete_cria = (datos.numero_arete_cria or datos.cria_numero_arete or "").strip() or None
    tipo_animal = (datos.tipo_animal or datos.cria_tipo_ganado or "Bovino").strip()
    raza_cria = (datos.raza_cria or datos.cria_raza or "Nelore").strip()
    
    # Resolver potrero de la cría (si no se especifica, hereda el potrero de la madre)
    cria_pot_id = getattr(datos, "cria_potrero_id", None) or getattr(datos, "potrero_id", None) or madre.potrero_id
    cria_ubi_str = datos.cria_ubicacion or datos.ubicacion or madre.ubicacion or "Potrero 1"
    pot_id, pot_nombre = resolver_potrero(db, cria_pot_id, cria_ubi_str)

    if arete_cria:
        validar_unicidad_arete(db, arete_cria)

    numero_comprobante = generar_comprobante_ganaderia(db, "NAC-GAN")

    cria_id = None
    # Si la cría nació viva, crear el animal activo correspondiente
    if estado_nac == "VIVO":
        codigo_cria = generar_codigo_interno_animal(db)
        cria = Animal(
            codigo_interno=codigo_cria,
            numero_arete=arete_cria,
            nombre=None,
            tipo=tipo_animal,
            raza=raza_cria,
            sexo=sexo_cria,
            fecha_nacimiento=fecha_nac,
            peso_inicial=peso_nac,
            peso_actual=peso_nac,
            fecha_ultimo_pesaje=fecha_nac if peso_nac else None,
            estado="ACTIVO",
            procedencia="NACIMIENTO",
            madre_id=madre.id,
            padre_id=datos.padre_id,
            potrero_id=pot_id,
            ubicacion=pot_nombre,
            observaciones=datos.observaciones,
            usuario_registro_ci=usuario_ci,
        )
        db.add(cria)
        db.flush()
        cria_id = cria.id

        if peso_nac and peso_nac > 0:
            pesaje_inicial = PesajeGanado(
                animal_id=cria.id,
                fecha_pesaje=fecha_nac,
                peso=peso_nac,
                variacion_anterior=Decimal("0.00"),
                responsable="Parto / Nacimiento",
                observaciones="Peso al nacer.",
                usuario_ci=usuario_ci,
            )
            db.add(pesaje_inicial)

        if arete_cria:
            hist_arete = HistorialArete(
                animal_id=cria.id,
                arete_anterior=None,
                arete_nuevo=arete_cria,
                fecha_cambio=fecha_nac,
                motivo="Asignación inicial al nacimiento.",
                usuario_ci=usuario_ci,
            )
            db.add(hist_arete)

    nacimiento = NacimientoGanado(
        numero_comprobante=numero_comprobante,
        madre_id=madre.id,
        padre_id=datos.padre_id,
        cria_id=cria_id,
        fecha_nacimiento=fecha_nac,
        sexo_cria=sexo_cria,
        peso_nacimiento=peso_nac,
        tipo_parto=datos.tipo_parto or "UNICO",
        estado_nacimiento=estado_nac,
        numero_arete_cria=arete_cria,
        tipo_animal=tipo_animal,
        raza_cria=raza_cria,
        ubicacion=pot_nombre,
        observaciones=datos.observaciones,
        usuario_ci=usuario_ci,
    )
    db.add(nacimiento)

    registrar_bitacora(
        db=db,
        modulo="GANADERIA",
        accion="REGISTRAR_NACIMIENTO",
        descripcion=(
            f"Se registró el nacimiento {numero_comprobante} de la madre {madre.codigo_interno} "
            f"(Estado: {estado_nac}, Cría ID: {cria_id or 'Muerta al nacer'})."
        ),
        usuario_ci=usuario_ci,
        commit=False,
    )

    db.commit()
    db.refresh(nacimiento)
    return nacimiento


def listar_nacimientos(db: Session, skip: int = 0, limit: int = 50) -> Tuple[List[dict], int]:
    stmt = select(NacimientoGanado).order_by(desc(NacimientoGanado.id))
    total = db.scalar(select(func.count(NacimientoGanado.id))) or 0
    items = list(db.execute(stmt.offset(skip).limit(limit)).scalars().unique().all())

    out = []
    for n in items:
        out.append({
            "id": n.id,
            "numero_comprobante": n.numero_comprobante,
            "codigo_parto": n.numero_comprobante,
            "madre_id": n.madre_id,
            "madre_codigo": n.madre.codigo_interno if n.madre else None,
            "madre_arete": n.madre.numero_arete if n.madre else None,
            "padre_id": n.padre_id,
            "padre_codigo": n.padre.codigo_interno if n.padre else None,
            "padre_arete": n.padre.numero_arete if n.padre else None,
            "cria_id": n.cria_id,
            "cria_codigo": n.cria.codigo_interno if n.cria else None,
            "fecha_nacimiento": n.fecha_nacimiento,
            "fecha_parto": n.fecha_nacimiento,
            "sexo_cria": n.sexo_cria,
            "peso_nacimiento": n.peso_nacimiento,
            "tipo_parto": n.tipo_parto,
            "estado_nacimiento": n.estado_nacimiento,
            "condicion_cria": n.estado_nacimiento,
            "numero_arete_cria": n.numero_arete_cria,
            "tipo_animal": n.tipo_animal,
            "raza_cria": n.raza_cria,
            "ubicacion": n.ubicacion,
            "observaciones": n.observaciones,
            "usuario_ci": n.usuario_ci,
            "fecha_creacion": n.fecha_creacion,
        })
    return out, total


# =========================================================================
# REGISTRO DE COMPRAS EN LOTE (RF-008, RF-013)
# =========================================================================
def registrar_compra_ganado(db: Session, datos: CompraGanadoCreate, usuario_ci: str) -> CompraGanado:
    """Registra la compra de ganado e incorpora individualmente cada animal al inventario."""
    items = datos.items or datos.detalles or []
    if not items:
        raise HTTPException(status_code=400, detail="Debe ingresar al menos un animal en la compra.")

    # 1. Validar aretes de todos los animales comprados
    for idx, item in enumerate(items):
        arete = (item.numero_arete or "").strip()
        if arete:
            validar_unicidad_arete(db, arete)

    numero_comprobante = generar_comprobante_ganaderia(db, "CMP-GAN")

    # 2. Calcular montos
    costo_subtotal_animales = Decimal("0.00")
    items_calculados = []
    for item in items:
        precio_unit = item.precio_unitario or item.precio_compra or Decimal("0.00")
        peso_compra = item.peso_compra or item.peso
        if item.modalidad_precio == "POR_KG":
            if not peso_compra or peso_compra <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Si la modalidad es POR_KG, el peso de compra debe ser mayor a 0.",
                )
            costo_animal = peso_compra * precio_unit
        else:
            costo_animal = precio_unit

        costo_subtotal_animales += costo_animal
        items_calculados.append((item, costo_animal, precio_unit, peso_compra))

    costos_adic = datos.costos_adicionales or Decimal("0.00")
    transp = datos.transporte or datos.costo_transporte or Decimal("0.00")
    monto_total = costo_subtotal_animales + costos_adic + transp

    doc_ref = datos.documento_referencia or datos.numero_documento
    compra = CompraGanado(
        numero_comprobante=numero_comprobante,
        proveedor=datos.proveedor.strip(),
        fecha_compra=datos.fecha_compra,
        documento_referencia=doc_ref.strip() if doc_ref else None,
        costos_adicionales=costos_adic,
        transporte=transp,
        monto_total=monto_total,
        observaciones=datos.observaciones,
        estado="CONFIRMADO",
        usuario_ci=usuario_ci,
    )
    db.add(compra)
    db.flush()

    # 3. Crear cada animal e insertarlo en el inventario activo
    for item, costo_animal, precio_unit, peso_compra in items_calculados:
        codigo_interno = generar_codigo_interno_animal(db)
        arete = item.numero_arete.strip() if item.numero_arete and item.numero_arete.strip() else None
        fecha_nac = item.fecha_nacimiento or datos.fecha_compra
        tipo_final = (item.tipo_ganado or item.tipo or "Bovino").strip()

        pot_id, pot_nombre = resolver_potrero(
            db,
            potrero_id=getattr(item, "potrero_id", None),
            ubicacion=item.ubicacion,
        )

        animal = Animal(
            codigo_interno=codigo_interno,
            numero_arete=arete,
            nombre=None,
            tipo=tipo_final,
            raza=item.raza.strip() if item.raza else "Nelore",
            sexo=item.sexo.strip().upper(),
            fecha_nacimiento=fecha_nac,
            peso_inicial=peso_compra,
            peso_actual=peso_compra,
            fecha_ultimo_pesaje=datos.fecha_compra if peso_compra else None,
            estado="ACTIVO",
            procedencia="COMPRA",
            potrero_id=pot_id,
            ubicacion=pot_nombre,
            observaciones=item.observaciones,
            usuario_registro_ci=usuario_ci,
        )
        db.add(animal)
        db.flush()

        # Detalle de compra
        det = CompraGanadoDetalle(
            compra_id=compra.id,
            animal_id=animal.id,
            modalidad_precio=item.modalidad_precio,
            precio_unitario=precio_unit,
            peso_compra=peso_compra,
            costo_total=costo_animal,
        )
        db.add(det)

        if peso_compra and peso_compra > 0:
            pesaje_compra = PesajeGanado(
                animal_id=animal.id,
                fecha_pesaje=datos.fecha_compra,
                peso=peso_compra,
                variacion_anterior=Decimal("0.00"),
                responsable=f"Compra {compra.numero_comprobante}",
                observaciones="Peso registrado al comprar.",
                usuario_ci=usuario_ci,
            )
            db.add(pesaje_compra)

        if arete:
            hist_arete = HistorialArete(
                animal_id=animal.id,
                arete_anterior=None,
                arete_nuevo=arete,
                fecha_cambio=datos.fecha_compra,
                motivo=f"Arete registrado en compra {compra.numero_comprobante}.",
                usuario_ci=usuario_ci,
            )
            db.add(hist_arete)

    registrar_bitacora(
        db=db,
        modulo="GANADERIA",
        accion="REGISTRAR_COMPRA",
        descripcion=(
            f"Se registró la compra {numero_comprobante} del proveedor {datos.proveedor} "
            f"por {len(items)} cabezas de ganado. Importe total: Bs {monto_total:.2f}."
        ),
        usuario_ci=usuario_ci,
        commit=False,
    )

    db.commit()
    db.refresh(compra)
    return compra


def listar_compras_ganado(db: Session, skip: int = 0, limit: int = 50) -> Tuple[List[dict], int]:
    stmt = select(CompraGanado).order_by(desc(CompraGanado.id))
    total = db.scalar(select(func.count(CompraGanado.id))) or 0
    items = list(db.execute(stmt.offset(skip).limit(limit)).scalars().unique().all())

    out = []
    for c in items:
        detalles_out = [
            {
                "id": d.id,
                "animal_id": d.animal_id,
                "animal_codigo": d.animal.codigo_interno if d.animal else None,
                "animal_arete": d.animal.numero_arete if d.animal else None,
                "modalidad_precio": d.modalidad_precio,
                "precio_unitario": d.precio_unitario,
                "peso_compra": d.peso_compra,
                "costo_total": d.costo_total,
            }
            for d in c.detalles
        ]
        out.append({
            "id": c.id,
            "numero_comprobante": c.numero_comprobante,
            "proveedor": c.proveedor,
            "fecha_compra": c.fecha_compra,
            "documento_referencia": c.documento_referencia,
            "costos_adicionales": c.costos_adicionales,
            "transporte": c.transporte,
            "monto_total": c.monto_total,
            "observaciones": c.observaciones,
            "estado": c.estado,
            "motivo_anulacion": c.motivo_anulacion,
            "cantidad_animales": len(c.detalles),
            "detalles": detalles_out,
            "usuario_ci": c.usuario_ci,
            "fecha_creacion": c.fecha_creacion,
        })
    return out, total


# =========================================================================
# REGISTRO DE VENTAS COMERCIALES (RF-009, RF-014, CE-001, CE-003)
# =========================================================================
def registrar_venta_ganado(db: Session, datos: VentaGanadoCreate, usuario_ci: str) -> VentaGanado:
    """
    Registra venta comercial de ganado.
    REGLA INQUEBRANTABLE (RF-009, CE-003):
    No se puede completar una venta de un animal que no tenga número de arete registrado.
    """
    items = datos.items or datos.animales or []
    if not items:
        raise HTTPException(status_code=400, detail="Debe incluir al menos un animal en la venta.")

    animales_a_vender = []
    subtotal_bruto = Decimal("0.00")
    for item in items:
        animal = db.get(Animal, item.animal_id)
        if not animal:
            raise HTTPException(status_code=404, detail=f"Animal ID {item.animal_id} no encontrado.")

        # VALIDACIÓN ESTRICTA DE ARETE FÍSICO
        if not animal.numero_arete or not animal.numero_arete.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"BLOQUEO DE VENTA: El animal {animal.codigo_interno} no cuenta con un número de arete registrado. "
                    f"Según las reglas de negocio de SISTEMAS RAÍCES, no se puede realizar la venta comercial de un animal "
                    f"sin su identificación física única. Por favor, asigne un número de arete en su perfil antes de continuar."
                ),
            )

        # VALIDACIÓN DE ESTADO ACTIVO
        if animal.estado != "ACTIVO":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El animal {animal.codigo_interno} (Arete: {animal.numero_arete}) no está ACTIVO (Estado actual: {animal.estado}).",
            )

        precio_unit = item.precio_unitario or item.precio or Decimal("0.00")
        if item.modalidad_precio == "POR_KG":
            peso = item.peso_venta or animal.peso_actual
            if not peso or peso <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Para vender POR_KG, el animal {animal.codigo_interno} debe contar con peso registrado mayor a 0.",
                )
            subtotal_item = peso * precio_unit
        else:
            peso = item.peso_venta or animal.peso_actual
            subtotal_item = precio_unit

        subtotal_bruto += subtotal_item
        animales_a_vender.append((animal, item, peso, precio_unit, subtotal_item))

    descuentos = datos.descuentos or datos.descuento or Decimal("0.00")
    monto_total = max(Decimal("0.00"), subtotal_bruto - descuentos)
    numero_comprobante = generar_comprobante_ganaderia(db, "VNT-GAN")
    doc_ref = datos.documento_referencia or datos.numero_documento
    transp_str = str(datos.costo_transporte) if datos.costo_transporte else datos.transporte

    venta = VentaGanado(
        numero_comprobante=numero_comprobante,
        cliente=datos.cliente.strip(),
        fecha_venta=datos.fecha_venta,
        modalidad_venta=datos.modalidad_venta,
        metodo_pago=datos.metodo_pago,
        transporte=transp_str,
        descuentos=descuentos,
        monto_total=monto_total,
        documento_referencia=doc_ref.strip() if doc_ref else None,
        observaciones=datos.observaciones,
        estado="CONFIRMADO",
        usuario_ci=usuario_ci,
    )
    db.add(venta)
    db.flush()

    for animal, item, peso, precio_unit, subtotal_item in animales_a_vender:
        det = VentaGanadoDetalle(
            venta_id=venta.id,
            animal_id=animal.id,
            numero_arete=animal.numero_arete,
            modalidad_precio=item.modalidad_precio,
            peso_venta=peso,
            precio_unitario=precio_unit,
            subtotal=subtotal_item,
        )
        db.add(det)

        # Transición de estado a VENDIDO
        animal.estado = "VENDIDO"

    registrar_bitacora(
        db=db,
        modulo="GANADERIA",
        accion="REGISTRAR_VENTA",
        descripcion=(
            f"Se registró la venta {numero_comprobante} al cliente {datos.cliente} "
            f"por {len(animales_a_vender)} animales. Importe total: Bs {monto_total:.2f}."
        ),
        usuario_ci=usuario_ci,
        commit=False,
    )

    db.commit()
    db.refresh(venta)
    return venta


def anular_venta_ganado(db: Session, venta_id: int, motivo: str, usuario_ci: str):
    """Anula venta y restaura animales a estado ACTIVO."""
    venta = db.get(VentaGanado, venta_id)
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada.")
    if venta.estado == "ANULADO":
        raise HTTPException(status_code=400, detail="Esta venta ya está anulada.")

    venta.estado = "ANULADO"
    venta.motivo_anulacion = motivo.strip()

    # Restaurar estado ACTIVO en los animales vendidos
    for det in venta.detalles:
        if det.animal:
            det.animal.estado = "ACTIVO"

    registrar_bitacora(
        db=db,
        modulo="GANADERIA",
        accion="ANULAR_VENTA",
        descripcion=f"Se anuló la venta {venta.numero_comprobante}. Motivo: {motivo}. Animales restaurados a ACTIVO.",
        usuario_ci=usuario_ci,
        commit=False,
    )

    db.commit()
    return {"ok": True, "message": f"Venta {venta.numero_comprobante} anulada exitosamente."}


def listar_ventas_ganado(db: Session, skip: int = 0, limit: int = 50) -> Tuple[List[dict], int]:
    stmt = select(VentaGanado).order_by(desc(VentaGanado.id))
    total = db.scalar(select(func.count(VentaGanado.id))) or 0
    items = list(db.execute(stmt.offset(skip).limit(limit)).scalars().unique().all())

    out = []
    for v in items:
        detalles_out = [
            {
                "id": d.id,
                "animal_id": d.animal_id,
                "animal_codigo": d.animal.codigo_interno if d.animal else None,
                "numero_arete": d.numero_arete,
                "modalidad_precio": d.modalidad_precio,
                "peso_venta": d.peso_venta,
                "precio_unitario": d.precio_unitario,
                "subtotal": d.subtotal,
            }
            for d in v.detalles
        ]
        out.append({
            "id": v.id,
            "numero_comprobante": v.numero_comprobante,
            "cliente": v.cliente,
            "fecha_venta": v.fecha_venta,
            "modalidad_venta": v.modalidad_venta,
            "metodo_pago": v.metodo_pago,
            "transporte": v.transporte,
            "descuentos": v.descuentos,
            "monto_total": v.monto_total,
            "documento_referencia": v.documento_referencia,
            "observaciones": v.observaciones,
            "estado": v.estado,
            "motivo_anulacion": v.motivo_anulacion,
            "cantidad_animales": len(v.detalles),
            "detalles": detalles_out,
            "usuario_ci": v.usuario_ci,
            "fecha_creacion": v.fecha_creacion,
        })
    return out, total


# =========================================================================
# REGISTRO DE BAJAS (RF-010, RF-015, CE-001, CE-004)
# =========================================================================
def registrar_baja_ganado(db: Session, datos: BajaGanadoCreate, usuario_ci: str) -> BajaGanado:
    """
    Registra baja (fallecimiento, robo, etc.) de un animal.
    REGLA INQUEBRANTABLE (RF-010, CE-004):
    No se puede completar una baja de un animal que no tenga número de arete registrado.
    """
    animal = db.get(Animal, datos.animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal no encontrado.")

    # VALIDACIÓN OBLIGATORIA DE ARETE FÍSICO
    if not animal.numero_arete or not animal.numero_arete.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"BLOQUEO DE BAJA: El animal {animal.codigo_interno} no cuenta con un número de arete registrado. "
                f"Según las reglas de negocio de SISTEMAS RAÍCES, no se puede dar de baja a un animal sin su identificación "
                f"física previa. Por favor, asigne un número de arete antes de registrar la baja."
            ),
        )

    if animal.estado != "ACTIVO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El animal {animal.codigo_interno} no está ACTIVO (Estado actual: {animal.estado}).",
        )

    motivo_raw = datos.motivo or datos.tipo_baja or datos.tipo or "FALLECIMIENTO"
    motivo_upper = motivo_raw.strip().upper()
    if motivo_upper == "MUERTE":
        motivo_upper = "FALLECIMIENTO"

    mapa_estados = {
        "FALLECIMIENTO": "FALLECIDO",
        "ROBO": "ROBADO",
        "PERDIDA": "PERDIDO",
        "SACRIFICIO": "SACRIFICADO",
        "DESCARTE": "DESCARTADO",
    }
    estado_resultante = mapa_estados.get(motivo_upper, "BAJA")

    numero_comprobante = generar_comprobante_ganaderia(db, "BAJ-GAN")
    fecha_baja = datos.fecha_baja or datos.fecha or obtener_fecha_bolivia()
    observaciones = datos.observaciones or ""
    causa = datos.causa_diagnostico or datos.motivo_diagnostico
    if causa:
        observaciones = f"Causa/Diagnóstico: {causa}. {observaciones}".strip()

    baja = BajaGanado(
        numero_comprobante=numero_comprobante,
        animal_id=animal.id,
        numero_arete=animal.numero_arete,
        fecha_baja=fecha_baja,
        motivo=motivo_upper,
        estado_animal_resultante=estado_resultante,
        responsable=datos.responsable.strip() if datos.responsable else None,
        documento_adjunto=datos.documento_adjunto.strip() if datos.documento_adjunto else None,
        observaciones=observaciones or None,
        estado="CONFIRMADO",
        usuario_ci=usuario_ci,
    )
    db.add(baja)

    # Actualizar estado del animal
    animal.estado = estado_resultante

    registrar_bitacora(
        db=db,
        modulo="GANADERIA",
        accion="REGISTRAR_BAJA",
        descripcion=(
            f"Se registró la baja {numero_comprobante} del animal {animal.codigo_interno} "
            f"(Arete: {animal.numero_arete}). Motivo: {motivo_upper} -> Estado: {estado_resultante}."
        ),
        usuario_ci=usuario_ci,
        commit=False,
    )

    db.commit()
    db.refresh(baja)
    return baja


def anular_baja_ganado(db: Session, baja_id: int, motivo: str, usuario_ci: str):
    """Anula baja y restaura animal a estado ACTIVO."""
    baja = db.get(BajaGanado, baja_id)
    if not baja:
        raise HTTPException(status_code=404, detail="Registro de baja no encontrado.")
    if baja.estado == "ANULADO":
        raise HTTPException(status_code=400, detail="Esta baja ya se encuentra anulada.")

    baja.estado = "ANULADO"
    baja.motivo_anulacion = motivo.strip()

    if baja.animal:
        baja.animal.estado = "ACTIVO"

    registrar_bitacora(
        db=db,
        modulo="GANADERIA",
        accion="ANULAR_BAJA",
        descripcion=f"Se anuló la baja {baja.numero_comprobante} del animal {baja.numero_arete}. Motivo: {motivo}. Animal restaurado a ACTIVO.",
        usuario_ci=usuario_ci,
        commit=False,
    )

    db.commit()
    return {"ok": True, "message": f"Baja {baja.numero_comprobante} anulada exitosamente."}


def listar_bajas_ganado(db: Session, skip: int = 0, limit: int = 50) -> Tuple[List[dict], int]:
    stmt = select(BajaGanado).order_by(desc(BajaGanado.id))
    total = db.scalar(select(func.count(BajaGanado.id))) or 0
    items = list(db.execute(stmt.offset(skip).limit(limit)).scalars().unique().all())

    out = []
    for b in items:
        out.append({
            "id": b.id,
            "numero_comprobante": b.numero_comprobante,
            "animal_id": b.animal_id,
            "animal_codigo": b.animal.codigo_interno if b.animal else None,
            "numero_arete": b.numero_arete,
            "fecha_baja": b.fecha_baja,
            "motivo": b.motivo,
            "estado_animal_resultante": b.estado_animal_resultante,
            "responsable": b.responsable,
            "documento_adjunto": b.documento_adjunto,
            "observaciones": b.observaciones,
            "estado": b.estado,
            "motivo_anulacion": b.motivo_anulacion,
            "usuario_ci": b.usuario_ci,
            "fecha_creacion": b.fecha_creacion,
        })
    return out, total


# =========================================================================
# KPIS Y RESUMEN GENERAL (RF-002) - OPTIMIZADO EN 1 SOLA CONSULTA
# =========================================================================
def obtener_kpis_ganaderia(db: Session) -> GanaderiaKPIsOut:
    """Calcula métricas clave del hato ganadero de forma ultra rápida en 1 consulta SQL agrupada."""
    bajas_estados = ["FALLECIDO", "ROBADO", "PERDIDO", "SACRIFICADO", "DESCARTADO", "BAJA"]
    stmt = select(
        func.count(Animal.id).label("total_reg"),
        func.count(Animal.id).filter(Animal.estado == "ACTIVO").label("total_act"),
        func.count(Animal.id).filter(Animal.estado == "VENDIDO").label("total_ven"),
        func.count(Animal.id).filter(Animal.estado.in_(bajas_estados)).label("total_baj"),
        func.count(Animal.id).filter(Animal.estado == "ACTIVO", func.upper(Animal.sexo) == "MACHO").label("machos"),
        func.count(Animal.id).filter(Animal.estado == "ACTIVO", func.upper(Animal.sexo) == "HEMBRA").label("hembras"),
        func.avg(Animal.peso_actual).filter(Animal.estado == "ACTIVO", Animal.peso_actual.isnot(None)).label("peso_prom"),
    )
    res = db.execute(stmt).one()
    
    total_reg = res.total_reg or 0
    total_act = res.total_act or 0
    total_ven = res.total_ven or 0
    total_baj = res.total_baj or 0
    machos = res.machos or 0
    hembras = res.hembras or 0
    peso_prom = res.peso_prom
    peso_prom_dec = Decimal(str(round(peso_prom, 2))) if peso_prom else Decimal("0.00")

    total_nac = db.scalar(select(func.count(NacimientoGanado.id))) or 0
    total_cmp = db.scalar(select(func.count(CompraGanado.id)).where(CompraGanado.estado == "CONFIRMADO")) or 0

    return GanaderiaKPIsOut(
        total_hato=total_reg,
        activos=total_act,
        machos=machos,
        hembras=hembras,
        vendidos=total_ven,
        fallecidos_bajas=total_baj,
        total_registrados=total_reg,
        total_activos=total_act,
        total_vendidos=total_ven,
        total_bajas=total_baj,
        total_nacimientos=total_nac,
        total_compras=total_cmp,
        machos_activos=machos,
        hembras_activas=hembras,
        peso_promedio_activo=peso_prom_dec,
    )


# =========================================================================
# GESTIÓN DE POTREROS Y MOVIMIENTO DE GANADO (SPEC-002)
# =========================================================================

def generar_codigo_potrero(db: Session, tipo_area: str = "POTRERO") -> str:
    prefijo = "COR" if (tipo_area or "").upper() == "CORRAL" else "POT"
    total = db.scalar(select(func.count(Potrero.id)).where(Potrero.codigo.like(f"{prefijo}-%"))) or 0
    correlativo = total + 1
    codigo = f"{prefijo}-{correlativo:04d}"
    while db.scalar(select(Potrero.id).where(Potrero.codigo == codigo)):
        correlativo += 1
        codigo = f"{prefijo}-{correlativo:04d}"
    return codigo


def punto_en_poligono(lat: float, lng: float, coords: list) -> bool:
    """Algoritmo Ray-Casting (Punto en Polígono). coords: [[[lng, lat], ...]]"""
    if not coords:
        return False
    ring = coords[0] if isinstance(coords[0][0], (list, tuple)) else coords
    n = len(ring)
    inside = False
    p1x, p1y = float(ring[0][0]), float(ring[0][1])  # lng, lat
    for i in range(1, n + 1):
        p2x, p2y = float(ring[i % n][0]), float(ring[i % n][1])
        if min(p1y, p2y) < lat <= max(p1y, p2y):
            if lng <= max(p1x, p2x):
                xinters = (lat - p1y) * (p2x - p1x) / (p2y - p1y) + p1x if p1y != p2y else p1x
                if p1x == p2x or lng <= xinters:
                    inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def calcular_centroide_poligono(coords: list) -> Tuple[Decimal, Decimal]:
    """Calcula el centroide aproximado de un polígono GeoJSON."""
    ring = coords[0] if isinstance(coords[0][0], (list, tuple)) else coords
    sum_lat = 0.0
    sum_lng = 0.0
    k = len(ring)
    if k == 0:
        return Decimal("-17.923267"), Decimal("-62.246458")
    for pt in ring:
        sum_lng += float(pt[0])
        sum_lat += float(pt[1])
    return (
        Decimal(str(round(sum_lat / k, 6))),
        Decimal(str(round(sum_lng / k, 6))),
    )


def calcular_superficie_ha(coords: list) -> Decimal:
    """Cálculo aproximado de superficie en hectáreas a partir de coordenadas lat/lng esferoidales."""
    ring = coords[0] if isinstance(coords[0][0], (list, tuple)) else coords
    if len(ring) < 3:
        return Decimal("1.00")
    area_sq_m = 0.0
    R = 6378137.0
    j = len(ring) - 1
    for i in range(len(ring)):
        p1 = ring[i]
        p2 = ring[j]
        lat1 = math.radians(float(p1[1]))
        lat2 = math.radians(float(p2[1]))
        lng1 = math.radians(float(p1[0]))
        lng2 = math.radians(float(p2[0]))
        area_sq_m += (lng2 - lng1) * (2.0 + math.sin(lat1) + math.sin(lat2))
        j = i
    area_sq_m = abs(area_sq_m * R * R / 4.0)
    ha = area_sq_m / 10000.0
    return Decimal(str(round(ha, 2)))


def calcular_posicion_animal_en_potrero(potrero: Potrero, animal_id: int) -> Tuple[float, float]:
    """Calcula una posición [lat, lng] determinista dentro del polígono del potrero."""
    try:
        geo = json.loads(potrero.poligono_geojson)
        coords = geo.get("coordinates", [])
        ring = coords[0] if isinstance(coords[0][0], (list, tuple)) else coords
        lngs = [float(pt[0]) for pt in ring]
        lats = [float(pt[1]) for pt in ring]
        min_lng, max_lng = min(lngs), max(lngs)
        min_lat, max_lat = min(lats), max(lats)

        rng = random.Random(potrero.id * 100003 + animal_id)
        for _ in range(25):
            cand_lat = min_lat + (max_lat - min_lat) * rng.random()
            cand_lng = min_lng + (max_lng - min_lng) * rng.random()
            if punto_en_poligono(cand_lat, cand_lng, coords):
                return round(cand_lat, 6), round(cand_lng, 6)
    except Exception:
        pass

    c_lat = float(potrero.centroide_lat or -17.923267)
    c_lng = float(potrero.centroide_lng or -62.246458)
    jitter = ((animal_id % 13) - 6) * 0.0001
    return round(c_lat + jitter, 6), round(c_lng + jitter, 6)


def listar_potreros(db: Session) -> List[dict]:
    """Lista todos los potreros activos con totales agregados de animales en 1 sola consulta."""
    potreros = db.execute(
        select(Potrero).where(Potrero.estado == "ACTIVO").order_by(Potrero.nombre)
    ).scalars().all()

    counts_query = (
        select(
            Animal.potrero_id,
            func.count(Animal.id).label("total"),
            func.count(Animal.id).filter(Animal.sexo == "MACHO").label("machos"),
            func.count(Animal.id).filter(Animal.sexo == "HEMBRA").label("hembras"),
        )
        .where(Animal.estado == "ACTIVO", Animal.potrero_id.is_not(None))
        .group_by(Animal.potrero_id)
    )
    counts_map = {
        row.potrero_id: {"total": row.total, "machos": row.machos, "hembras": row.hembras}
        for row in db.execute(counts_query).all()
    }

    resultado = []
    for p in potreros:
        c = counts_map.get(p.id, {"total": 0, "machos": 0, "hembras": 0})
        resultado.append({
            "id": p.id,
            "codigo": p.codigo,
            "nombre": p.nombre,
            "tipo_area": p.tipo_area,
            "superficie_ha": p.superficie_ha,
            "capacidad_cabezas": p.capacidad_cabezas,
            "color_hex": p.color_hex,
            "poligono_geojson": p.poligono_geojson,
            "centroide_lat": p.centroide_lat,
            "centroide_lng": p.centroide_lng,
            "estado": p.estado,
            "total_animales": c["total"],
            "total_machos": c["machos"],
            "total_hembras": c["hembras"],
            "observaciones": p.observaciones,
            "fecha_creacion": p.fecha_creacion,
            "fecha_actualizacion": p.fecha_actualizacion,
        })
    return resultado


def obtener_potrero(db: Session, potrero_id: int) -> dict:
    """Devuelve los datos de un potrero junto con todos sus animales activos."""
    p = db.get(Potrero, potrero_id)
    if not p:
        raise HTTPException(status_code=404, detail="Potrero no encontrado.")

    animales_query = (
        select(Animal)
        .where(Animal.potrero_id == potrero_id, Animal.estado == "ACTIVO")
        .order_by(Animal.codigo_interno)
    )
    animales = db.execute(animales_query).scalars().all()

    animales_out = []
    total_machos = 0
    total_hembras = 0
    for an in animales:
        if an.sexo == "MACHO":
            total_machos += 1
        elif an.sexo == "HEMBRA":
            total_hembras += 1
        animales_out.append({
            "id": an.id,
            "codigo_interno": an.codigo_interno,
            "numero_arete": an.numero_arete,
            "nombre": an.nombre,
            "tipo": an.tipo,
            "tipo_ganado": an.tipo,
            "raza": an.raza,
            "sexo": an.sexo,
            "fecha_nacimiento": an.fecha_nacimiento,
            "edad_meses": calcular_edad_en_meses(an.fecha_nacimiento),
            "peso_inicial": an.peso_inicial,
            "peso_actual": an.peso_actual,
            "fecha_ultimo_pesaje": an.fecha_ultimo_pesaje,
            "ganancia_peso_total": (an.peso_actual - an.peso_inicial) if (an.peso_actual and an.peso_inicial) else Decimal("0.00"),
            "estado": an.estado,
            "procedencia": an.procedencia,
            "madre_id": an.madre_id,
            "padre_id": an.padre_id,
            "madre_arete": None,
            "padre_arete": None,
            "potrero_id": an.potrero_id,
            "ubicacion": an.ubicacion,
            "propietario": an.propietario,
            "observaciones": an.observaciones,
            "fecha_registro": an.fecha_creacion,
            "fecha_creacion": an.fecha_creacion,
            "fecha_actualizacion": an.fecha_actualizacion,
        })

    return {
        "id": p.id,
        "codigo": p.codigo,
        "nombre": p.nombre,
        "tipo_area": p.tipo_area,
        "superficie_ha": p.superficie_ha,
        "capacidad_cabezas": p.capacidad_cabezas,
        "color_hex": p.color_hex,
        "poligono_geojson": p.poligono_geojson,
        "centroide_lat": p.centroide_lat,
        "centroide_lng": p.centroide_lng,
        "estado": p.estado,
        "total_animales": len(animales),
        "total_machos": total_machos,
        "total_hembras": total_hembras,
        "observaciones": p.observaciones,
        "fecha_creacion": p.fecha_creacion,
        "fecha_actualizacion": p.fecha_actualizacion,
        "animales": animales_out,
    }


def crear_potrero(db: Session, datos: PotreroCreate, usuario_ci: Optional[str]) -> Potrero:
    """Crea un nuevo potrero o corral con su polígono y capacidad."""
    nombre_limpio = datos.nombre.strip()
    existente = db.execute(
        select(Potrero).where(
            func.lower(Potrero.nombre) == nombre_limpio.lower(),
            Potrero.estado == "ACTIVO"
        )
    ).scalars().first()
    if existente:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un potrero o corral activo con el nombre '{nombre_limpio}'."
        )

    try:
        geo = json.loads(datos.poligono_geojson)
        coords = geo.get("coordinates", [])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"El formato GeoJSON es inválido: {e}")

    c_lat, c_lng = calcular_centroide_poligono(coords)
    superficie = datos.superficie_ha or calcular_superficie_ha(coords)
    codigo = generar_codigo_potrero(db, datos.tipo_area)

    potrero = Potrero(
        codigo=codigo,
        nombre=nombre_limpio,
        tipo_area=(datos.tipo_area or "POTRERO").upper(),
        superficie_ha=superficie,
        capacidad_cabezas=datos.capacidad_cabezas or 50,
        color_hex=datos.color_hex or "#10b981",
        poligono_geojson=datos.poligono_geojson,
        centroide_lat=datos.centroide_lat or c_lat,
        centroide_lng=datos.centroide_lng or c_lng,
        estado="ACTIVO",
        observaciones=datos.observaciones,
        usuario_registro_ci=usuario_ci,
    )
    db.add(potrero)
    db.flush()

    registrar_bitacora(
        db=db,
        modulo="GANADERIA",
        accion="CREAR_POTRERO",
        descripcion=f"Se creó el {potrero.tipo_area.lower()} '{potrero.nombre}' ({potrero.codigo}) con capacidad para {potrero.capacidad_cabezas} cabezas.",
        usuario_ci=usuario_ci,
        commit=False,
    )
    db.commit()
    db.refresh(potrero)
    return potrero


def actualizar_potrero(db: Session, potrero_id: int, datos: PotreroUpdate, usuario_ci: Optional[str]) -> Potrero:
    """Actualiza datos y vértices de un potrero existente."""
    potrero = db.get(Potrero, potrero_id)
    if not potrero:
        raise HTTPException(status_code=404, detail="Potrero no encontrado.")

    if datos.nombre and datos.nombre.strip() != potrero.nombre:
        nombre_limpio = datos.nombre.strip()
        existente = db.execute(
            select(Potrero).where(
                func.lower(Potrero.nombre) == nombre_limpio.lower(),
                Potrero.id != potrero_id,
                Potrero.estado == "ACTIVO"
            )
        ).scalars().first()
        if existente:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe otro potrero o corral activo con el nombre '{nombre_limpio}'."
            )
        potrero.nombre = nombre_limpio

        db.execute(
            text("UPDATE animal SET ubicacion = :nuevo_nombre WHERE potrero_id = :pot_id"),
            {"nuevo_nombre": nombre_limpio, "pot_id": potrero_id}
        )

    if datos.tipo_area:
        potrero.tipo_area = datos.tipo_area.upper()
    if datos.capacidad_cabezas is not None:
        potrero.capacidad_cabezas = datos.capacidad_cabezas
    if datos.color_hex:
        potrero.color_hex = datos.color_hex
    if datos.observaciones is not None:
        potrero.observaciones = datos.observaciones

    if datos.poligono_geojson and datos.poligono_geojson != potrero.poligono_geojson:
        try:
            geo = json.loads(datos.poligono_geojson)
            coords = geo.get("coordinates", [])
            c_lat, c_lng = calcular_centroide_poligono(coords)
            potrero.poligono_geojson = datos.poligono_geojson
            potrero.centroide_lat = datos.centroide_lat or c_lat
            potrero.centroide_lng = datos.centroide_lng or c_lng
            if datos.superficie_ha is not None:
                potrero.superficie_ha = datos.superficie_ha
            else:
                potrero.superficie_ha = calcular_superficie_ha(coords)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"GeoJSON inválido: {e}")

    potrero.fecha_actualizacion = obtener_ahora_bolivia()
    registrar_bitacora(
        db=db,
        modulo="GANADERIA",
        accion="ACTUALIZAR_POTRERO",
        descripcion=f"Se actualizaron los datos del potrero '{potrero.nombre}' ({potrero.codigo}).",
        usuario_ci=usuario_ci,
        commit=False,
    )
    db.commit()
    db.refresh(potrero)
    return potrero


def desactivar_potrero(db: Session, potrero_id: int, usuario_ci: Optional[str]) -> Potrero:
    """Desactiva un potrero únicamente si no contiene animales activos (RF-014)."""
    potrero = db.get(Potrero, potrero_id)
    if not potrero:
        raise HTTPException(status_code=404, detail="Potrero no encontrado.")

    animales_activos = db.scalar(
        select(func.count(Animal.id)).where(Animal.potrero_id == potrero_id, Animal.estado == "ACTIVO")
    ) or 0
    if animales_activos > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No es posible desactivar '{potrero.nombre}' porque contiene {animales_activos} animal(es) activo(s). Debe trasladarlos a otro potrero o corral primero."
        )

    potrero.estado = "INACTIVO"
    potrero.fecha_actualizacion = obtener_ahora_bolivia()
    registrar_bitacora(
        db=db,
        modulo="GANADERIA",
        accion="DESACTIVAR_POTRERO",
        descripcion=f"Se desactivó el potrero '{potrero.nombre}' ({potrero.codigo}).",
        usuario_ci=usuario_ci,
        commit=False,
    )
    db.commit()
    db.refresh(potrero)
    return potrero


def obtener_mapa_distribucion(db: Session) -> dict:
    """
    Retorna en 1 sola consulta optimizada los potreros activos y todos los animales activos
    con sus coordenadas internas calculadas (RF-015, RF-016).
    """
    potreros_list = listar_potreros(db)
    potreros_dict = {p["id"]: p for p in potreros_list}

    animales = db.execute(
        select(Animal)
        .where(Animal.estado == "ACTIVO", Animal.potrero_id.is_not(None))
        .order_by(Animal.codigo_interno)
    ).scalars().all()

    puntos_animales = []
    for an in animales:
        pot = potreros_dict.get(an.potrero_id)
        if not pot:
            continue
        class DummyPotrero:
            pass
        dp = DummyPotrero()
        dp.id = pot["id"]
        dp.poligono_geojson = pot["poligono_geojson"]
        dp.centroide_lat = pot["centroide_lat"]
        dp.centroide_lng = pot["centroide_lng"]

        lat, lng = calcular_posicion_animal_en_potrero(dp, an.id)
        puntos_animales.append({
            "id": an.id,
            "codigo_interno": an.codigo_interno,
            "numero_arete": an.numero_arete,
            "nombre": an.nombre,
            "tipo": an.tipo,
            "raza": an.raza,
            "sexo": an.sexo,
            "peso_actual": an.peso_actual,
            "potrero_id": an.potrero_id,
            "potrero_nombre": pot["nombre"],
            "lat": lat,
            "lng": lng,
        })

    return {
        "potreros": potreros_list,
        "animales": puntos_animales,
        "total_cabezas_activas": len(puntos_animales),
    }


def registrar_movimiento_ganado(db: Session, datos: MovimientoGanadoCreate, usuario_ci: Optional[str]) -> MovimientoGanado:
    """
    Registra un traslado atómico de uno o varios animales entre potreros (RF-018 - RF-028).
    Sincroniza animal.potrero_id y animal.ubicacion bidireccionalmente.
    """
    if datos.potrero_origen_id == datos.potrero_destino_id:
        raise HTTPException(
            status_code=400,
            detail="El potrero de destino no puede ser igual al potrero de origen."
        )

    pot_origen = db.get(Potrero, datos.potrero_origen_id)
    pot_destino = db.get(Potrero, datos.potrero_destino_id)
    if not pot_origen or pot_origen.estado != "ACTIVO":
        raise HTTPException(status_code=404, detail="El potrero de origen no existe o no está activo.")
    if not pot_destino or pot_destino.estado != "ACTIVO":
        raise HTTPException(status_code=404, detail="El potrero de destino no existe o no está activo.")

    if not datos.animales_ids:
        raise HTTPException(status_code=400, detail="Debe seleccionar al menos un animal para el traslado.")

    animales = db.execute(
        select(Animal).where(Animal.id.in_(datos.animales_ids))
    ).scalars().all()

    if len(animales) != len(datos.animales_ids):
        raise HTTPException(status_code=400, detail="Uno o más animales seleccionados no existen en la base de datos.")

    for an in animales:
        if an.estado != "ACTIVO":
            raise HTTPException(
                status_code=400,
                detail=f"El animal {an.codigo_interno} ({an.numero_arete or 'S/N'}) está en estado '{an.estado}' y no puede ser trasladado."
            )

    fecha_mov = datos.fecha_movimiento or obtener_fecha_bolivia()
    comprobante = generar_comprobante_ganaderia(db, "MOV-GAN")

    movimiento = MovimientoGanado(
        numero_comprobante=comprobante,
        fecha_movimiento=fecha_mov,
        potrero_origen_id=pot_origen.id,
        potrero_destino_id=pot_destino.id,
        tipo_operacion=datos.tipo_operacion,
        cantidad_animales=len(animales),
        motivo=datos.motivo,
        responsable=datos.responsable,
        observaciones=datos.observaciones,
        estado="CONFIRMADO",
        usuario_ci=usuario_ci,
    )
    db.add(movimiento)
    db.flush()

    for an in animales:
        pot_ant_id = an.potrero_id or pot_origen.id
        detalle = MovimientoGanadoDetalle(
            movimiento_id=movimiento.id,
            animal_id=an.id,
            numero_arete=an.numero_arete,
            codigo_interno=an.codigo_interno,
            potrero_origen_id=pot_ant_id,
            potrero_destino_id=pot_destino.id,
        )
        db.add(detalle)
        an.potrero_id = pot_destino.id
        an.ubicacion = pot_destino.nombre

    registrar_bitacora(
        db=db,
        modulo="GANADERIA",
        accion="REGISTRAR_MOVIMIENTO",
        descripcion=(
            f"Comprobante {comprobante}: Traslado de {len(animales)} cabezas desde '{pot_origen.nombre}' "
            f"hasta '{pot_destino.nombre}'. Motivo: {datos.motivo or 'No especificado'}."
        ),
        usuario_ci=usuario_ci,
        commit=False,
    )

    db.commit()
    db.refresh(movimiento)
    return movimiento


def listar_movimientos(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    potrero_id: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> Tuple[List[dict], int]:
    """Historial paginado de movimientos de ganado."""
    stmt = select(MovimientoGanado)
    if potrero_id:
        stmt = stmt.where(
            or_(
                MovimientoGanado.potrero_origen_id == potrero_id,
                MovimientoGanado.potrero_destino_id == potrero_id,
            )
        )
    if fecha_desde:
        stmt = stmt.where(MovimientoGanado.fecha_movimiento >= fecha_desde)
    if fecha_hasta:
        stmt = stmt.where(MovimientoGanado.fecha_movimiento <= fecha_hasta)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    movs = db.execute(
        stmt.order_by(desc(MovimientoGanado.fecha_movimiento), desc(MovimientoGanado.id))
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    items = []
    for m in movs:
        detalles_out = []
        for d in (m.detalles or []):
            an = d.animal
            detalles_out.append({
                "id": d.id,
                "movimiento_id": d.movimiento_id,
                "animal_id": d.animal_id,
                "numero_arete": d.numero_arete,
                "codigo_interno": d.codigo_interno,
                "potrero_origen_id": d.potrero_origen_id,
                "potrero_destino_id": d.potrero_destino_id,
                "animal_nombre": an.nombre if an else None,
                "animal_raza": an.raza if an else None,
                "animal_sexo": an.sexo if an else None,
                "animal_peso_actual": an.peso_actual if an else None,
            })
        items.append({
            "id": m.id,
            "numero_comprobante": m.numero_comprobante,
            "fecha_movimiento": m.fecha_movimiento,
            "potrero_origen_id": m.potrero_origen_id,
            "potrero_origen_nombre": m.potrero_origen.nombre if m.potrero_origen else None,
            "potrero_destino_id": m.potrero_destino_id,
            "potrero_destino_nombre": m.potrero_destino.nombre if m.potrero_destino else None,
            "tipo_operacion": m.tipo_operacion,
            "cantidad_animales": m.cantidad_animales,
            "motivo": m.motivo,
            "responsable": m.responsable,
            "observaciones": m.observaciones,
            "estado": m.estado,
            "motivo_anulacion": m.motivo_anulacion,
            "usuario_ci": m.usuario_ci,
            "fecha_creacion": m.fecha_creacion,
            "detalles": detalles_out,
        })
    return items, total


def obtener_movimiento(db: Session, movimiento_id: int) -> dict:
    """Obtiene un movimiento con su comprobante y lista de animales."""
    m = db.get(MovimientoGanado, movimiento_id)
    if not m:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado.")

    detalles_out = []
    for d in (m.detalles or []):
        an = d.animal
        detalles_out.append({
            "id": d.id,
            "movimiento_id": d.movimiento_id,
            "animal_id": d.animal_id,
            "numero_arete": d.numero_arete,
            "codigo_interno": d.codigo_interno,
            "potrero_origen_id": d.potrero_origen_id,
            "potrero_destino_id": d.potrero_destino_id,
            "animal_nombre": an.nombre if an else None,
            "animal_raza": an.raza if an else None,
            "animal_sexo": an.sexo if an else None,
            "animal_peso_actual": an.peso_actual if an else None,
        })

    return {
        "id": m.id,
        "numero_comprobante": m.numero_comprobante,
        "fecha_movimiento": m.fecha_movimiento,
        "potrero_origen_id": m.potrero_origen_id,
        "potrero_origen_nombre": m.potrero_origen.nombre if m.potrero_origen else None,
        "potrero_destino_id": m.potrero_destino_id,
        "potrero_destino_nombre": m.potrero_destino.nombre if m.potrero_destino else None,
        "tipo_operacion": m.tipo_operacion,
        "cantidad_animales": m.cantidad_animales,
        "motivo": m.motivo,
        "responsable": m.responsable,
        "observaciones": m.observaciones,
        "estado": m.estado,
        "motivo_anulacion": m.motivo_anulacion,
        "usuario_ci": m.usuario_ci,
        "fecha_creacion": m.fecha_creacion,
        "detalles": detalles_out,
    }


def anular_movimiento_ganado(db: Session, movimiento_id: int, motivo: str, usuario_ci: Optional[str]) -> MovimientoGanado:
    """Anula un movimiento y devuelve los animales a su potrero anterior (RF-036)."""
    m = db.get(MovimientoGanado, movimiento_id)
    if not m:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado.")
    if m.estado == "ANULADO":
        raise HTTPException(status_code=400, detail="Este movimiento ya fue anulado anteriormente.")

    pot_origen = db.get(Potrero, m.potrero_origen_id)
    if not pot_origen or pot_origen.estado != "ACTIVO":
        raise HTTPException(
            status_code=400,
            detail=f"No se puede anular el movimiento porque el potrero de origen '{pot_origen.nombre if pot_origen else 'Desconocido'}' está inactivo."
        )

    for det in (m.detalles or []):
        an = db.get(Animal, det.animal_id)
        if not an:
            continue
        if an.potrero_id != m.potrero_destino_id:
            raise HTTPException(
                status_code=400,
                detail=f"No se puede anular el movimiento porque el animal {an.codigo_interno} ya no se encuentra en el potrero de destino (ubicación actual: {an.ubicacion})."
            )
        an.potrero_id = pot_origen.id
        an.ubicacion = pot_origen.nombre

    m.estado = "ANULADO"
    m.motivo_anulacion = motivo

    registrar_bitacora(
        db=db,
        modulo="GANADERIA",
        accion="ANULAR_MOVIMIENTO",
        descripcion=f"Se anuló el comprobante {m.numero_comprobante} de traslado de ganado. Motivo: {motivo}.",
        usuario_ci=usuario_ci,
        commit=False,
    )
    db.commit()
    db.refresh(m)
    return m


def obtener_historial_movimientos_animal(db: Session, animal_id: int) -> List[dict]:
    """Cronología de traslados de un animal particular para su Ficha Perfil 360° (RF-034)."""
    detalles = db.execute(
        select(MovimientoGanadoDetalle)
        .join(MovimientoGanado, MovimientoGanado.id == MovimientoGanadoDetalle.movimiento_id)
        .where(MovimientoGanadoDetalle.animal_id == animal_id, MovimientoGanado.estado == "CONFIRMADO")
        .order_by(desc(MovimientoGanado.fecha_movimiento), desc(MovimientoGanado.id))
    ).scalars().all()

    resultado = []
    for d in detalles:
        mov = d.movimiento
        po = db.get(Potrero, d.potrero_origen_id)
        pd = db.get(Potrero, d.potrero_destino_id)
        resultado.append({
            "movimiento_id": mov.id,
            "numero_comprobante": mov.numero_comprobante,
            "fecha_movimiento": mov.fecha_movimiento,
            "potrero_origen": po.nombre if po else "Origen",
            "potrero_destino": pd.nombre if pd else "Destino",
            "tipo_operacion": mov.tipo_operacion,
            "motivo": mov.motivo,
            "responsable": mov.responsable,
            "observaciones": mov.observaciones,
        })
    return resultado

