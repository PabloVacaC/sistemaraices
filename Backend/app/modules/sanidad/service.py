from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, desc

from app.models.entities import (
    SanidadVacuna,
    SanidadMedicamento,
    SanidadOperacion,
    SanidadOperacionDetalle,
    SanidadSeguimiento,
    Animal,
    Potrero,
    Trabajador,
    Usuario,
    Almacen,
    MovimientoAlmacen,
    MovimientoGanado,
    MovimientoGanadoDetalle,
    Bitacora,
)
from app.modules.sanidad.schemas import (
    SanidadVacunaCreate,
    SanidadVacunaUpdate,
    SanidadMedicamentoCreate,
    SanidadMedicamentoUpdate,
    SanidadOperacionCreate,
    SanidadSeguimientoCreate,
    AnulacionSanidadIn,
    SanidadOperacionOut,
    SanidadOperacionDetalleOut,
    SanidadSeguimientoOut,
    AlertaRetiroOut,
    SanidadKPIsOut,
    HistorialSanitarioAnimalOut,
)


def get_today_bolivia() -> date:
    # GMT-4 (Bolivia)
    return (datetime.utcnow() - timedelta(hours=4)).date()


def registrar_bitacora(
    db: Session,
    usuario_ci: Optional[str],
    accion: str,
    tabla: str,
    registro_id: Optional[str] = None,
    detalles: Optional[str] = None,
):
    try:
        desc = f"[{tabla} id={registro_id}] {detalles}" if registro_id else (detalles or accion)
        b = Bitacora(
            usuario_ci=usuario_ci,
            accion=accion,
            modulo="Ganadería / Sanidad",
            descripcion=desc,
        )
        db.add(b)
    except Exception as e:
        print(f"Error al registrar bitácora de sanidad: {e}")


# =========================================================================
# CATÁLOGO DE VACUNAS
# =========================================================================

def listar_vacunas(db: Session, solo_activas: bool = False) -> List[SanidadVacuna]:
    query = select(SanidadVacuna).order_by(SanidadVacuna.nombre)
    if solo_activas:
        query = query.where(SanidadVacuna.estado == "ACTIVO")
    return list(db.execute(query).scalars().all())


def crear_vacuna(db: Session, payload: SanidadVacunaCreate, usuario_ci: Optional[str]) -> SanidadVacuna:
    existente = db.execute(select(SanidadVacuna).where(SanidadVacuna.codigo == payload.codigo.strip())).scalars().first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una vacuna con el código '{payload.codigo}'."
        )

    vacuna = SanidadVacuna(
        codigo=payload.codigo.strip().upper(),
        nombre=payload.nombre.strip(),
        nombre_comercial=payload.nombre_comercial.strip() if payload.nombre_comercial else None,
        enfermedad_objetivo=payload.enfermedad_objetivo.strip(),
        especie=payload.especie.strip().upper(),
        dosis_defecto_ml=payload.dosis_defecto_ml,
        via_administracion=payload.via_administracion.strip().upper(),
        dias_retiro_carne=payload.dias_retiro_carne,
        dias_retiro_leche=payload.dias_retiro_leche,
        requiere_refuerzo=payload.requiere_refuerzo,
        dias_refuerzo=payload.dias_refuerzo,
        estado=payload.estado.strip().upper(),
        observaciones=payload.observaciones,
    )
    db.add(vacuna)
    db.commit()
    db.refresh(vacuna)

    registrar_bitacora(
        db, usuario_ci, "CREAR_VACUNA", "sanidad_vacuna", vacuna.id,
        f"Registrada vacuna '{vacuna.nombre}' ({vacuna.codigo})"
    )
    return vacuna


def actualizar_vacuna(db: Session, vacuna_id: int, payload: SanidadVacunaUpdate, usuario_ci: Optional[str]) -> SanidadVacuna:
    vacuna = db.get(SanidadVacuna, vacuna_id)
    if not vacuna:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacuna no encontrada.")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        if v is not None:
            if isinstance(v, str):
                v = v.strip()
            setattr(vacuna, k, v)

    db.commit()
    db.refresh(vacuna)
    registrar_bitacora(
        db, usuario_ci, "ACTUALIZAR_VACUNA", "sanidad_vacuna", vacuna.id,
        f"Actualizada vacuna '{vacuna.nombre}' ({vacuna.codigo})"
    )
    return vacuna


def desactivar_vacuna(db: Session, vacuna_id: int, usuario_ci: Optional[str]) -> SanidadVacuna:
    vacuna = db.get(SanidadVacuna, vacuna_id)
    if not vacuna:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacuna no encontrada.")

    vacuna.estado = "INACTIVO" if vacuna.estado == "ACTIVO" else "ACTIVO"
    db.commit()
    db.refresh(vacuna)
    registrar_bitacora(
        db, usuario_ci, "CAMBIAR_ESTADO_VACUNA", "sanidad_vacuna", vacuna.id,
        f"Nuevo estado: {vacuna.estado}"
    )
    return vacuna


# =========================================================================
# CATÁLOGO DE MEDICAMENTOS Y FÁRMACOS
# =========================================================================

def listar_medicamentos(db: Session, solo_activos: bool = False):
    query = select(SanidadMedicamento).order_by(SanidadMedicamento.nombre)
    if solo_activos:
        query = query.where(SanidadMedicamento.estado == "ACTIVO")
    meds = db.execute(query).scalars().all()
    resultado = []
    for m in meds:
        almacen_nom = m.almacen.nombre if m.almacen else None
        resultado.append({
            "id": m.id,
            "codigo": m.codigo,
            "nombre": m.nombre,
            "nombre_comercial": m.nombre_comercial,
            "tipo_farmaco": m.tipo_farmaco,
            "principio_activo": m.principio_activo,
            "concentracion": m.concentracion,
            "unidad_medida": m.unidad_medida,
            "via_administracion": m.via_administracion,
            "dias_retiro_carne": m.dias_retiro_carne,
            "dias_retiro_leche": m.dias_retiro_leche,
            "almacen_id": m.almacen_id,
            "almacen_nombre": almacen_nom,
            "estado": m.estado,
            "observaciones": m.observaciones,
            "fecha_creacion": m.fecha_creacion,
        })
    return resultado


def crear_medicamento(db: Session, payload: SanidadMedicamentoCreate, usuario_ci: Optional[str]) -> SanidadMedicamento:
    existente = db.execute(select(SanidadMedicamento).where(SanidadMedicamento.codigo == payload.codigo.strip())).scalars().first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un medicamento con el código '{payload.codigo}'."
        )

    if payload.almacen_id:
        alm = db.get(Almacen, payload.almacen_id)
        if not alm:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El producto de almacén vinculado no existe.")

    med = SanidadMedicamento(
        codigo=payload.codigo.strip().upper(),
        nombre=payload.nombre.strip(),
        nombre_comercial=payload.nombre_comercial.strip() if payload.nombre_comercial else None,
        tipo_farmaco=payload.tipo_farmaco.strip().upper(),
        principio_activo=payload.principio_activo.strip() if payload.principio_activo else None,
        concentracion=payload.concentracion.strip() if payload.concentracion else None,
        unidad_medida=payload.unidad_medida.strip().upper(),
        via_administracion=payload.via_administracion.strip().upper(),
        dias_retiro_carne=payload.dias_retiro_carne,
        dias_retiro_leche=payload.dias_retiro_leche,
        almacen_id=payload.almacen_id,
        estado=payload.estado.strip().upper(),
        observaciones=payload.observaciones,
    )
    db.add(med)
    db.commit()
    db.refresh(med)

    registrar_bitacora(
        db, usuario_ci, "CREAR_MEDICAMENTO", "sanidad_medicamento", med.id,
        f"Registrado medicamento '{med.nombre}' ({med.codigo})"
    )
    return med


def actualizar_medicamento(db: Session, medicamento_id: int, payload: SanidadMedicamentoUpdate, usuario_ci: Optional[str]) -> SanidadMedicamento:
    med = db.get(SanidadMedicamento, medicamento_id)
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento no encontrado.")

    data = payload.model_dump(exclude_unset=True)
    if "almacen_id" in data and data["almacen_id"] is not None:
        alm = db.get(Almacen, data["almacen_id"])
        if not alm:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El producto de almacén vinculado no existe.")

    for k, v in data.items():
        if v is not None:
            if isinstance(v, str):
                v = v.strip()
            setattr(med, k, v)

    db.commit()
    db.refresh(med)
    registrar_bitacora(
        db, usuario_ci, "ACTUALIZAR_MEDICAMENTO", "sanidad_medicamento", med.id,
        f"Actualizado medicamento '{med.nombre}' ({med.codigo})"
    )
    return med


def desactivar_medicamento(db: Session, medicamento_id: int, usuario_ci: Optional[str]) -> SanidadMedicamento:
    med = db.get(SanidadMedicamento, medicamento_id)
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento no encontrado.")

    med.estado = "INACTIVO" if med.estado == "ACTIVO" else "ACTIVO"
    db.commit()
    db.refresh(med)
    registrar_bitacora(
        db, usuario_ci, "CAMBIAR_ESTADO_MEDICAMENTO", "sanidad_medicamento", med.id,
        f"Nuevo estado: {med.estado}"
    )
    return med


# =========================================================================
# OPERACIONES SANITARIAS (VACUNACIÓN / TRATAMIENTOS)
# =========================================================================

def generar_numero_comprobante_sanidad(db: Session, tipo_operacion: str) -> str:
    prefijo = "VAC" if "VACUNA" in tipo_operacion.upper() else "TRAT"
    today_str = get_today_bolivia().strftime("%Y%m%d")
    base_prefix = f"SAN-{prefijo}-{today_str}-"

    last_op = db.execute(
        select(SanidadOperacion.numero_comprobante)
        .where(SanidadOperacion.numero_comprobante.like(f"{base_prefix}%"))
        .order_by(desc(SanidadOperacion.id))
    ).scalars().first()

    if last_op:
        try:
            sec = int(last_op.split("-")[-1]) + 1
        except Exception:
            sec = 1
    else:
        sec = 1
    return f"{base_prefix}{sec:04d}"


def crear_operacion_sanitaria(
    db: Session,
    payload: SanidadOperacionCreate,
    usuario_ci: Optional[str],
) -> SanidadOperacion:
    # 1. Validaciones
    if not payload.vacuna_id and not payload.medicamento_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe seleccionar una Vacuna o un Medicamento para la operación sanitaria."
        )

    vacuna: Optional[SanidadVacuna] = None
    medicamento: Optional[SanidadMedicamento] = None
    dias_carne = 0
    dias_leche = 0

    if payload.vacuna_id:
        vacuna = db.get(SanidadVacuna, payload.vacuna_id)
        if not vacuna:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La vacuna seleccionada no existe.")
        dias_carne = vacuna.dias_retiro_carne or 0
        dias_leche = vacuna.dias_retiro_leche or 0

    if payload.medicamento_id:
        medicamento = db.get(SanidadMedicamento, payload.medicamento_id)
        if not medicamento:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El medicamento seleccionado no existe.")
        dias_carne = medicamento.dias_retiro_carne or 0
        dias_leche = medicamento.dias_retiro_leche or 0

    # 2. Calcular fechas de fin de retiro
    fecha_fin_retiro_carne = payload.fecha_aplicacion + timedelta(days=dias_carne) if dias_carne > 0 else None
    fecha_fin_retiro_leche = payload.fecha_aplicacion + timedelta(days=dias_leche) if dias_leche > 0 else None

    # 3. Validar animales
    animal_ids = [item.animal_id for item in payload.animales]
    if len(animal_ids) != len(set(animal_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puede incluir el mismo animal más de una vez en la misma operación.")

    animales_db = db.execute(select(Animal).where(Animal.id.in_(animal_ids))).scalars().all()
    if len(animales_db) != len(animal_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uno o más animales seleccionados no existen en el sistema.")

    animales_map = {a.id: a for a in animales_db}

    # 4. Generar comprobante
    comprobante = generar_numero_comprobante_sanidad(db, payload.tipo_operacion)

    # 5. Descuento opcional en Almacén / Inventario (RF-010 / HU-03)
    movimiento_almacen_id = None
    if payload.descontar_inventario and medicamento and medicamento.almacen_id:
        almacen_item = db.get(Almacen, medicamento.almacen_id)
        if almacen_item:
            # Calcular total dosis administradas
            total_dosis = sum([Decimal(str(item.dosis_aplicada or 0)) for item in payload.animales])
            if total_dosis > 0:
                if almacen_item.stock_actual < total_dosis:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Stock insuficiente en almacén para '{almacen_item.nombre}'. Stock actual: {almacen_item.stock_actual}, Dosis requeridas: {total_dosis}"
                    )
                almacen_item.stock_actual -= total_dosis

                # Registrar movimiento de salida en almacén
                mov_alm = MovimientoAlmacen(
                    numero_comprobante=f"SAL-SAN-{comprobante}",
                    almacen_id=almacen_item.id,
                    trabajador_id=payload.trabajador_id,
                    usuario_registro_ci=usuario_ci,
                    cantidad=total_dosis,
                    tipo_movimiento="SALIDA",
                    motivo=f"Aplicación sanitaria comprobante {comprobante}",
                    observaciones=f"Dosis administradas a {len(payload.animales)} cabezas de ganado.",
                )
                db.add(mov_alm)
                db.flush()
                movimiento_almacen_id = mov_alm.id

    # 6. Traslado opcional a Cuarentena (RF-014 / HU-06)
    traslado_cuarentena_id = None
    if payload.trasladar_a_cuarentena and payload.animales:
        # Buscar potrero/corral de cuarentena
        potrero_dest = None
        if payload.potrero_cuarentena_id:
            potrero_dest = db.get(Potrero, payload.potrero_cuarentena_id)
        if not potrero_dest:
            potrero_dest = db.execute(
                select(Potrero).where(
                    and_(
                        Potrero.estado == "ACTIVO",
                        or_(
                            Potrero.nombre.ilike("%cuarentena%"),
                            Potrero.nombre.ilike("%aislamiento%"),
                            Potrero.tipo_area == "CORRAL",
                        )
                    )
                )
            ).scalars().first()

        if potrero_dest:
            mov_comprobante = f"MOV-CUAR-{comprobante}"
            primer_origen_id = payload.potrero_origen_id or (animales_db[0].potrero_id if animales_db[0].potrero_id else potrero_dest.id)

            mov_ganado = MovimientoGanado(
                numero_comprobante=mov_comprobante,
                fecha_movimiento=payload.fecha_aplicacion,
                potrero_origen_id=primer_origen_id,
                potrero_destino_id=potrero_dest.id,
                tipo_operacion="MANUAL_GRUPAL",
                cantidad_animales=len(animales_db),
                motivo="CUARENTENA / AISLAMIENTO SANITARIO",
                responsable=payload.veterinario_nombre or (f"Trabajador #{payload.trabajador_id}" if payload.trabajador_id else None),
                observaciones=f"Traslado preventivo por operación sanitaria {comprobante}. Diagnóstico: {payload.diagnostico or 'Tratamiento clínico'}",
                estado="CONFIRMADO",
                usuario_ci=usuario_ci,
            )
            db.add(mov_ganado)
            db.flush()
            traslado_cuarentena_id = mov_ganado.id

            for an in animales_db:
                orig_id = an.potrero_id or primer_origen_id
                det_mov = MovimientoGanadoDetalle(
                    movimiento_id=mov_ganado.id,
                    animal_id=an.id,
                    numero_arete=an.numero_arete,
                    codigo_interno=an.codigo_interno,
                    potrero_origen_id=orig_id,
                    potrero_destino_id=potrero_dest.id,
                )
                db.add(det_mov)
                an.potrero_id = potrero_dest.id
                an.ubicacion = potrero_dest.nombre

    # 7. Crear Cabecera SanidadOperacion
    operacion = SanidadOperacion(
        numero_comprobante=comprobante,
        tipo_operacion=payload.tipo_operacion,
        fecha_aplicacion=payload.fecha_aplicacion,
        fecha_programada=payload.fecha_programada,
        potrero_origen_id=payload.potrero_origen_id,
        vacuna_id=payload.vacuna_id,
        medicamento_id=payload.medicamento_id,
        lote_producto=payload.lote_producto.strip() if payload.lote_producto else None,
        fecha_vencimiento_producto=payload.fecha_vencimiento_producto,
        diagnostico=payload.diagnostico.strip() if payload.diagnostico else None,
        sintomas=payload.sintomas.strip() if payload.sintomas else None,
        cantidad_animales=len(payload.animales),
        trabajador_id=payload.trabajador_id,
        veterinario_nombre=payload.veterinario_nombre.strip() if payload.veterinario_nombre else None,
        costo_total_estimado=payload.costo_total_estimado,
        descontar_inventario=payload.descontar_inventario,
        movimiento_almacen_id=movimiento_almacen_id,
        traslado_cuarentena_id=traslado_cuarentena_id,
        estado="EJECUTADO",
        observaciones=payload.observaciones,
        usuario_ci=usuario_ci,
    )
    db.add(operacion)
    db.flush()

    # 8. Crear Detalles por Animal
    for item in payload.animales:
        an = animales_map[item.animal_id]
        detalle = SanidadOperacionDetalle(
            operacion_id=operacion.id,
            animal_id=an.id,
            numero_arete=an.numero_arete,
            codigo_interno=an.codigo_interno,
            dosis_aplicada=item.dosis_aplicada or (vacuna.dosis_defecto_ml if vacuna else None),
            unidad_medida=item.unidad_medida or (medicamento.unidad_medida if medicamento else "ML"),
            fecha_fin_retiro_carne=fecha_fin_retiro_carne,
            fecha_fin_retiro_leche=fecha_fin_retiro_leche,
            estado_aplicacion=item.estado_aplicacion or "APLICADO",
            reaccion_adversa=item.reaccion_adversa,
            observaciones=item.observaciones,
        )
        db.add(detalle)

    db.commit()
    db.refresh(operacion)

    producto_desc = vacuna.nombre if vacuna else (medicamento.nombre if medicamento else "Fármaco")
    registrar_bitacora(
        db, usuario_ci, "CREAR_OPERACION_SANIDAD", "sanidad_operacion", operacion.id,
        f"Comprobante {comprobante}: {payload.tipo_operacion} con '{producto_desc}' para {len(payload.animales)} cabezas."
    )
    return operacion


def listar_operaciones_sanitarias(
    db: Session,
    tipo_operacion: Optional[str] = None,
    potrero_id: Optional[int] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    busqueda: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
):
    query = select(SanidadOperacion).order_by(desc(SanidadOperacion.fecha_aplicacion), desc(SanidadOperacion.id))

    if tipo_operacion and tipo_operacion.upper() != "TODOS":
        query = query.where(SanidadOperacion.tipo_operacion == tipo_operacion.upper())
    if potrero_id:
        query = query.where(SanidadOperacion.potrero_origen_id == potrero_id)
    if estado and estado.upper() != "TODOS":
        query = query.where(SanidadOperacion.estado == estado.upper())
    if fecha_desde:
        query = query.where(SanidadOperacion.fecha_aplicacion >= fecha_desde)
    if fecha_hasta:
        query = query.where(SanidadOperacion.fecha_aplicacion <= fecha_hasta)
    if busqueda and busqueda.strip():
        txt = f"%{busqueda.strip()}%"
        query = query.where(
            or_(
                SanidadOperacion.numero_comprobante.ilike(txt),
                SanidadOperacion.diagnostico.ilike(txt),
                SanidadOperacion.veterinario_nombre.ilike(txt),
                SanidadOperacion.observaciones.ilike(txt),
            )
        )

    ops = db.execute(query.offset(skip).limit(limit)).scalars().all()
    resultado = []
    for op in ops:
        prod_nombre = ""
        if op.vacuna:
            prod_nombre = f"Vacuna: {op.vacuna.nombre}"
        elif op.medicamento:
            prod_nombre = f"Med: {op.medicamento.nombre}"

        trab_nom = None
        if op.trabajador:
            trab_nom = f"{op.trabajador.nombres} {op.trabajador.apellidos}".strip()

        usr_nom = None
        if op.usuario:
            usr_nom = f"{op.usuario.nombre} {op.usuario.apellido}".strip()

        resultado.append({
            "id": op.id,
            "numero_comprobante": op.numero_comprobante,
            "tipo_operacion": op.tipo_operacion,
            "fecha_aplicacion": op.fecha_aplicacion,
            "fecha_programada": op.fecha_programada,
            "potrero_origen_id": op.potrero_origen_id,
            "potrero_origen_nombre": op.potrero_origen.nombre if op.potrero_origen else None,
            "vacuna_id": op.vacuna_id,
            "vacuna_nombre": op.vacuna.nombre if op.vacuna else None,
            "medicamento_id": op.medicamento_id,
            "medicamento_nombre": op.medicamento.nombre if op.medicamento else None,
            "producto_aplicado": prod_nombre,
            "lote_producto": op.lote_producto,
            "fecha_vencimiento_producto": op.fecha_vencimiento_producto,
            "diagnostico": op.diagnostico,
            "sintomas": op.sintomas,
            "cantidad_animales": op.cantidad_animales,
            "trabajador_id": op.trabajador_id,
            "trabajador_nombre": trab_nom,
            "veterinario_nombre": op.veterinario_nombre,
            "costo_total_estimado": op.costo_total_estimado,
            "descontar_inventario": op.descontar_inventario,
            "movimiento_almacen_id": op.movimiento_almacen_id,
            "traslado_cuarentena_id": op.traslado_cuarentena_id,
            "estado": op.estado,
            "motivo_anulacion": op.motivo_anulacion,
            "observaciones": op.observaciones,
            "usuario_ci": op.usuario_ci,
            "usuario_nombre": usr_nom,
            "fecha_creacion": op.fecha_creacion,
        })
    return resultado


def obtener_operacion_por_id(db: Session, operacion_id: int):
    op = db.get(SanidadOperacion, operacion_id)
    if not op:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operación sanitaria no encontrada.")

    today = get_today_bolivia()
    detalles_out = []
    for d in op.detalles:
        an = d.animal
        en_ret_carne = bool(d.fecha_fin_retiro_carne and d.fecha_fin_retiro_carne >= today and op.estado != "ANULADO")
        en_ret_leche = bool(d.fecha_fin_retiro_leche and d.fecha_fin_retiro_leche >= today and op.estado != "ANULADO")
        dias_carne = (d.fecha_fin_retiro_carne - today).days if en_ret_carne else 0
        dias_leche = (d.fecha_fin_retiro_leche - today).days if en_ret_leche else 0

        seguimientos_out = []
        for s in d.seguimientos:
            s_usr_nom = f"{s.usuario.nombre} {s.usuario.apellido}".strip() if s.usuario else None
            seguimientos_out.append({
                "id": s.id,
                "detalle_id": s.detalle_id,
                "fecha_seguimiento": s.fecha_seguimiento,
                "estado_salud": s.estado_salud,
                "temperatura_c": s.temperatura_c,
                "peso_actual_kg": s.peso_actual_kg,
                "observaciones": s.observaciones,
                "usuario_ci": s.usuario_ci,
                "usuario_nombre": s_usr_nom,
                "fecha_creacion": s.fecha_creacion,
            })

        detalles_out.append({
            "id": d.id,
            "operacion_id": d.operacion_id,
            "animal_id": d.animal_id,
            "numero_arete": d.numero_arete,
            "codigo_interno": d.codigo_interno,
            "animal_nombre": an.nombre if an else None,
            "animal_raza": an.raza if an else None,
            "animal_sexo": an.sexo if an else None,
            "dosis_aplicada": d.dosis_aplicada,
            "unidad_medida": d.unidad_medida,
            "fecha_fin_retiro_carne": d.fecha_fin_retiro_carne,
            "fecha_fin_retiro_leche": d.fecha_fin_retiro_leche,
            "en_retiro_carne": en_ret_carne,
            "en_retiro_leche": en_ret_leche,
            "dias_restantes_retiro_carne": dias_carne,
            "dias_restantes_retiro_leche": dias_leche,
            "estado_aplicacion": d.estado_aplicacion,
            "reaccion_adversa": d.reaccion_adversa,
            "observaciones": d.observaciones,
            "seguimientos": seguimientos_out,
        })

    prod_nombre = ""
    if op.vacuna:
        prod_nombre = f"Vacuna: {op.vacuna.nombre}"
    elif op.medicamento:
        prod_nombre = f"Med: {op.medicamento.nombre}"

    trab_nom = f"{op.trabajador.nombres} {op.trabajador.apellidos}".strip() if op.trabajador else None
    usr_nom = f"{op.usuario.nombre} {op.usuario.apellido}".strip() if op.usuario else None

    return {
        "id": op.id,
        "numero_comprobante": op.numero_comprobante,
        "tipo_operacion": op.tipo_operacion,
        "fecha_aplicacion": op.fecha_aplicacion,
        "fecha_programada": op.fecha_programada,
        "potrero_origen_id": op.potrero_origen_id,
        "potrero_origen_nombre": op.potrero_origen.nombre if op.potrero_origen else None,
        "vacuna_id": op.vacuna_id,
        "vacuna_nombre": op.vacuna.nombre if op.vacuna else None,
        "medicamento_id": op.medicamento_id,
        "medicamento_nombre": op.medicamento.nombre if op.medicamento else None,
        "producto_aplicado": prod_nombre,
        "lote_producto": op.lote_producto,
        "fecha_vencimiento_producto": op.fecha_vencimiento_producto,
        "diagnostico": op.diagnostico,
        "sintomas": op.sintomas,
        "cantidad_animales": op.cantidad_animales,
        "trabajador_id": op.trabajador_id,
        "trabajador_nombre": trab_nom,
        "veterinario_nombre": op.veterinario_nombre,
        "costo_total_estimado": op.costo_total_estimado,
        "descontar_inventario": op.descontar_inventario,
        "movimiento_almacen_id": op.movimiento_almacen_id,
        "traslado_cuarentena_id": op.traslado_cuarentena_id,
        "estado": op.estado,
        "motivo_anulacion": op.motivo_anulacion,
        "observaciones": op.observaciones,
        "usuario_ci": op.usuario_ci,
        "usuario_nombre": usr_nom,
        "fecha_creacion": op.fecha_creacion,
        "detalles": detalles_out,
    }


def anular_operacion_sanitaria(
    db: Session,
    operacion_id: int,
    payload: AnulacionSanidadIn,
    usuario_ci: Optional[str],
) -> SanidadOperacion:
    op = db.get(SanidadOperacion, operacion_id)
    if not op:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operación sanitaria no encontrada.")

    if op.estado == "ANULADO":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La operación sanitaria ya se encuentra anulada.")

    op.estado = "ANULADO"
    op.motivo_anulacion = payload.motivo_anulacion.strip()

    # Revertir descuento de almacén si existió
    if op.movimiento_almacen_id and op.descontar_inventario and op.medicamento and op.medicamento.almacen_id:
        alm = db.get(Almacen, op.medicamento.almacen_id)
        if alm:
            total_dosis = sum([Decimal(str(d.dosis_aplicada or 0)) for d in op.detalles])
            alm.stock_actual += total_dosis
            reversion = MovimientoAlmacen(
                numero_comprobante=f"REV-SAN-{op.numero_comprobante}",
                almacen_id=alm.id,
                trabajador_id=op.trabajador_id,
                usuario_registro_ci=usuario_ci,
                cantidad=total_dosis,
                tipo_movimiento="ENTRADA",
                motivo=f"Reversión por anulación de operación {op.numero_comprobante}",
                observaciones=payload.motivo_anulacion,
            )
            db.add(reversion)

    db.commit()
    db.refresh(op)

    registrar_bitacora(
        db, usuario_ci, "ANULAR_OPERACION_SANIDAD", "sanidad_operacion", op.id,
        f"Anulada operación {op.numero_comprobante}. Motivo: {payload.motivo_anulacion}"
    )
    return op


def registrar_seguimiento_clinico(
    db: Session,
    detalle_id: int,
    payload: SanidadSeguimientoCreate,
    usuario_ci: Optional[str],
) -> SanidadSeguimiento:
    det = db.get(SanidadOperacionDetalle, detalle_id)
    if not det:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detalle de tratamiento no encontrado.")

    seg = SanidadSeguimiento(
        detalle_id=det.id,
        fecha_seguimiento=payload.fecha_seguimiento,
        estado_salud=payload.estado_salud.strip().upper(),
        temperatura_c=payload.temperatura_c,
        peso_actual_kg=payload.peso_actual_kg,
        observaciones=payload.observaciones,
        usuario_ci=usuario_ci,
    )
    db.add(seg)
    db.commit()
    db.refresh(seg)

    registrar_bitacora(
        db, usuario_ci, "SEGUIMIENTO_CLINICO", "sanidad_seguimiento", seg.id,
        f"Animal {det.codigo_interno}: evolución {seg.estado_salud} ({seg.fecha_seguimiento})"
    )
    return seg


# =========================================================================
# HISTORIAL SANITARIO INDIVIDUAL DE ANIMAL (PERFIL 360 - SPEC-001)
# =========================================================================

def obtener_historial_sanitario_animal(db: Session, animal_id: int) -> HistorialSanitarioAnimalOut:
    an = db.get(Animal, animal_id)
    if not an:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal no encontrado.")

    today = get_today_bolivia()
    detalles = db.execute(
        select(SanidadOperacionDetalle)
        .join(SanidadOperacion)
        .where(
            and_(
                SanidadOperacionDetalle.animal_id == animal_id,
                SanidadOperacion.estado != "ANULADO"
            )
        )
        .order_by(desc(SanidadOperacion.fecha_aplicacion))
    ).scalars().all()

    en_ret_carne = False
    en_ret_leche = False
    max_fin_carne: Optional[date] = None
    max_fin_leche: Optional[date] = None

    vacs = []
    trats = []

    for d in detalles:
        op = d.operacion
        is_carne = bool(d.fecha_fin_retiro_carne and d.fecha_fin_retiro_carne >= today)
        is_leche = bool(d.fecha_fin_retiro_leche and d.fecha_fin_retiro_leche >= today)

        if is_carne:
            en_ret_carne = True
            if not max_fin_carne or d.fecha_fin_retiro_carne > max_fin_carne:
                max_fin_carne = d.fecha_fin_retiro_carne

        if is_leche:
            en_ret_leche = True
            if not max_fin_leche or d.fecha_fin_retiro_leche > max_fin_leche:
                max_fin_leche = d.fecha_fin_retiro_leche

        dias_carne = (d.fecha_fin_retiro_carne - today).days if is_carne else 0
        dias_leche = (d.fecha_fin_retiro_leche - today).days if is_leche else 0

        seguimientos_out = []
        for s in d.seguimientos:
            s_usr_nom = f"{s.usuario.nombre} {s.usuario.apellido}".strip() if s.usuario else None
            seguimientos_out.append({
                "id": s.id,
                "detalle_id": s.detalle_id,
                "fecha_seguimiento": s.fecha_seguimiento,
                "estado_salud": s.estado_salud,
                "temperatura_c": s.temperatura_c,
                "peso_actual_kg": s.peso_actual_kg,
                "observaciones": s.observaciones,
                "usuario_ci": s.usuario_ci,
                "usuario_nombre": s_usr_nom,
                "fecha_creacion": s.fecha_creacion,
            })

        det_dict = {
            "id": d.id,
            "operacion_id": d.operacion_id,
            "animal_id": d.animal_id,
            "numero_arete": d.numero_arete,
            "codigo_interno": d.codigo_interno,
            "animal_nombre": an.nombre,
            "animal_raza": an.raza,
            "animal_sexo": an.sexo,
            "dosis_aplicada": d.dosis_aplicada,
            "unidad_medida": d.unidad_medida,
            "fecha_fin_retiro_carne": d.fecha_fin_retiro_carne,
            "fecha_fin_retiro_leche": d.fecha_fin_retiro_leche,
            "en_retiro_carne": is_carne,
            "en_retiro_leche": is_leche,
            "dias_restantes_retiro_carne": dias_carne,
            "dias_restantes_retiro_leche": dias_leche,
            "estado_aplicacion": d.estado_aplicacion,
            "reaccion_adversa": d.reaccion_adversa,
            "observaciones": d.observaciones,
            "seguimientos": seguimientos_out,
        }

        if "VACUNA" in op.tipo_operacion:
            vacs.append(det_dict)
        else:
            trats.append(det_dict)

    dias_max_carne = (max_fin_carne - today).days if max_fin_carne else 0
    dias_max_leche = (max_fin_leche - today).days if max_fin_leche else 0

    return HistorialSanitarioAnimalOut(
        animal_id=an.id,
        codigo_interno=an.codigo_interno,
        numero_arete=an.numero_arete,
        en_retiro_carne=en_ret_carne,
        en_retiro_leche=en_ret_leche,
        fecha_fin_retiro_carne=max_fin_carne,
        fecha_fin_retiro_leche=max_fin_leche,
        dias_restantes_retiro_carne=dias_max_carne,
        dias_restantes_retiro_leche=dias_max_leche,
        vacunaciones=vacs,
        tratamientos=trats,
    )


# =========================================================================
# ALERTAS DE RETIRO Y KPIS GENERALES (RF-017 / D-03)
# =========================================================================

def obtener_alertas_retiro(db: Session) -> List[AlertaRetiroOut]:
    today = get_today_bolivia()
    detalles = db.execute(
        select(SanidadOperacionDetalle)
        .join(SanidadOperacion)
        .join(Animal)
        .where(
            and_(
                SanidadOperacion.estado != "ANULADO",
                Animal.estado == "ACTIVO",
                or_(
                    SanidadOperacionDetalle.fecha_fin_retiro_carne >= today,
                    SanidadOperacionDetalle.fecha_fin_retiro_leche >= today,
                )
            )
        )
        .order_by(
            SanidadOperacionDetalle.fecha_fin_retiro_carne.asc(),
            SanidadOperacionDetalle.fecha_fin_retiro_leche.asc()
        )
    ).scalars().all()

    alertas: List[AlertaRetiroOut] = []
    # Agrupar por animal para mostrar el retiro más exigente
    vistos = set()
    for d in detalles:
        if d.animal_id in vistos:
            continue
        vistos.add(d.animal_id)

        an = d.animal
        op = d.operacion
        prod_desc = op.vacuna.nombre if op.vacuna else (op.medicamento.nombre if op.medicamento else "Fármaco")

        has_carne = bool(d.fecha_fin_retiro_carne and d.fecha_fin_retiro_carne >= today)
        has_leche = bool(d.fecha_fin_retiro_leche and d.fecha_fin_retiro_leche >= today)
        tipo = "AMBOS" if (has_carne and has_leche) else ("CARNE" if has_carne else "LECHE")

        dias_c = (d.fecha_fin_retiro_carne - today).days if has_carne else 0
        dias_l = (d.fecha_fin_retiro_leche - today).days if has_leche else 0

        alertas.append(AlertaRetiroOut(
            animal_id=an.id,
            codigo_interno=an.codigo_interno,
            numero_arete=an.numero_arete,
            potrero_id=an.potrero_id,
            potrero_nombre=an.potrero.nombre if an.potrero else an.ubicacion,
            tipo_retiro=tipo,
            fecha_fin_retiro_carne=d.fecha_fin_retiro_carne,
            fecha_fin_retiro_leche=d.fecha_fin_retiro_leche,
            dias_restantes_carne=dias_c,
            dias_restantes_leche=dias_l,
            producto_origen=prod_desc,
            numero_comprobante=op.numero_comprobante,
            fecha_aplicacion=op.fecha_aplicacion,
        ))
    return alertas


def obtener_kpis_sanidad(db: Session) -> SanidadKPIsOut:
    today = get_today_bolivia()
    primer_dia_mes = today.replace(day=1)

    # 1. Total vacunaciones en el mes actual
    total_vacs = db.execute(
        select(func.count(SanidadOperacion.id)).where(
            and_(
                SanidadOperacion.estado == "EJECUTADO",
                SanidadOperacion.tipo_operacion.like("%VACUNA%"),
                SanidadOperacion.fecha_aplicacion >= primer_dia_mes,
            )
        )
    ).scalar() or 0

    # 2. Total tratamientos activos
    total_trats = db.execute(
        select(func.count(SanidadOperacion.id)).where(
            and_(
                SanidadOperacion.estado == "EJECUTADO",
                SanidadOperacion.tipo_operacion.like("%TRATAMIENTO%"),
                SanidadOperacion.fecha_aplicacion >= today - timedelta(days=30),
            )
        )
    ).scalar() or 0

    # 3. Alertas de retiro
    alertas = obtener_alertas_retiro(db)
    animales_carne = len([a for a in alertas if a.tipo_retiro in ("CARNE", "AMBOS")])
    animales_leche = len([a for a in alertas if a.tipo_retiro in ("LECHE", "AMBOS")])

    # 4. Catálogos activos
    vacs_activas = db.execute(select(func.count(SanidadVacuna.id)).where(SanidadVacuna.estado == "ACTIVO")).scalar() or 0
    meds_activos = db.execute(select(func.count(SanidadMedicamento.id)).where(SanidadMedicamento.estado == "ACTIVO")).scalar() or 0

    return SanidadKPIsOut(
        total_vacunaciones_mes=total_vacs,
        total_tratamientos_activos=total_trats,
        animales_en_retiro_carne=animales_carne,
        animales_en_retiro_leche=animales_leche,
        vacunas_catalogo_activas=vacs_activas,
        medicamentos_catalogo_activos=meds_activos,
        alertas_retiro_proximas=alertas[:10],
    )
