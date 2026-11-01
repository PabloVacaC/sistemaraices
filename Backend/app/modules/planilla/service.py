from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, and_, or_, desc
from fastapi import HTTPException, status

from app.models.entities import (
    Trabajador,
    PeriodoSalarial,
    Anticipo,
    Liquidacion,
    PagoLiquidacion,
    Descuento,
    PlanillaDetalle,
    Usuario,
)
from app.modules.pagos.service import (
    generar_numero_comprobante,
    IMPORTE_REFERENCIA_QUINCENA,
)
from app.modules.planilla.schemas import (
    DescuentoCreate,
    DescuentoOut,
    ActualizarDiasTrabajadosIn,
    PlanillaFilaOut,
    PlanillaResumenTotales,
    PlanillaMensualOut,
    CerrarPlanillaRequest,
)
from app.modules.bitacora.service import registrar_bitacora


# =========================================================================
# CÁLCULO DE DÍAS TRABAJADOS (RF-15 A RF-21, CL-1, CL-2, CL-3)
# =========================================================================
def calcular_dias_trabajados_automaticos(trabajador: Trabajador, periodo: PeriodoSalarial) -> int:
    """
    Calcula los días trabajados en base a 30 días comerciales estándar:
    - Mes completo: 30 días (RF-19, CL-2).
    - Ingreso en el mes: 30 - fecha_ingreso.dia + 1 (RF-18, CL-1).
    - Desactivación en el mes: fecha_inactividad.dia (RF-20, CL-3).
    - Fuera de vigencia: 0 días.
    """
    inicio_mes = date(periodo.anio, periodo.mes, 1)
    
    # Si ingresó después del período actual
    if trabajador.fecha_ingreso > periodo.fecha_fin:
        return 0

    # Si ingresó durante el mes del período
    if (
        trabajador.fecha_ingreso.year == periodo.anio
        and trabajador.fecha_ingreso.month == periodo.mes
    ):
        dia_ingreso = trabajador.fecha_ingreso.day
        # Fórmula RF-18: proporcional desde fecha de ingreso hasta fin de mes base 30
        dias = 30 - dia_ingreso + 1
        return max(1, min(30, dias))

    # Si se desvinculó o inactivó durante este mes (RF-20, CL-3)
    if (
        trabajador.fecha_inactividad
        and trabajador.fecha_inactividad.year == periodo.anio
        and trabajador.fecha_inactividad.month == periodo.mes
    ):
        dia_fin = trabajador.fecha_inactividad.day
        return max(1, min(30, dia_fin))

    # Si fue inactivado antes de este mes
    if trabajador.fecha_inactividad and trabajador.fecha_inactividad < inicio_mes and not trabajador.estado:
        return 0

    # Mes completo normal
    return 30


def calcular_total_ganado(haber_basico: Decimal, dias_trabajados: int) -> Decimal:
    """Fórmula RF-17: Total ganado = (Haber básico / 30) × Días trabajados"""
    if dias_trabajados >= 30:
        return haber_basico
    if dias_trabajados <= 0:
        return Decimal("0.00")
    
    val = (haber_basico / Decimal("30")) * Decimal(dias_trabajados)
    return round(val, 2)


# =========================================================================
# GESTIÓN Y CARGA DE LA PLANILLA MENSUAL
# =========================================================================
def obtener_o_generar_planilla(db: Session, periodo_id: int) -> PlanillaMensualOut:
    """
    Genera o consulta la planilla tabular completa (13 columnas de RF-9)
    optimizada con O(1) consultas agrupadas, garantizando persistencia y
    conservación de importes históricos.
    """
    periodo = db.execute(
        select(PeriodoSalarial).where(PeriodoSalarial.id == periodo_id)
    ).scalars().first()
    if not periodo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Período salarial con ID {periodo_id} no encontrado.",
        )

    # 1. Cargar todos los trabajadores activos o que tuvieron actividad en este período
    # (RF-12: activos o con registro histórico en este período)
    inicio_mes = date(periodo.anio, periodo.mes, 1)
    stmt_trab = (
        select(Trabajador)
        .options(joinedload(Trabajador.area))
        .where(
            or_(
                Trabajador.estado.is_(True),
                and_(
                    Trabajador.fecha_inactividad.isnot(None),
                    Trabajador.fecha_inactividad >= inicio_mes,
                ),
            )
        )
        .order_by(Trabajador.apellidos, Trabajador.nombres)
    )
    trabajadores = list(db.execute(stmt_trab).scalars().unique().all())

    # 2. Cargar detalles históricos guardados en PlanillaDetalle
    stmt_det = select(PlanillaDetalle).where(PlanillaDetalle.periodo_id == periodo_id)
    detalles_guardados = {
        d.trabajador_id: d
        for d in db.execute(stmt_det).scalars().unique().all()
    }

    # 3. Cargar todos los anticipos del período
    stmt_ants = select(Anticipo).where(
        Anticipo.periodo_id == periodo_id,
        Anticipo.estado == "PAGADO",
    ).order_by(Anticipo.fecha_entrega)
    anticipos_todos = list(db.execute(stmt_ants).scalars().unique().all())

    anticipos_por_trab = {}
    for a in anticipos_todos:
        anticipos_por_trab.setdefault(a.trabajador_id, []).append(a)

    # 4. Cargar descuentos del período
    stmt_desc = select(Descuento).where(
        Descuento.periodo_id == periodo_id,
        Descuento.estado == "CONFIRMADO",
    ).order_by(Descuento.fecha)
    descuentos_todos = list(db.execute(stmt_desc).scalars().unique().all())
    descuentos_por_trab = {}
    for d in descuentos_todos:
        descuentos_por_trab.setdefault(d.trabajador_id, []).append(d)

    # 5. Cargar liquidaciones y pagos salariales
    stmt_liqs = (
        select(Liquidacion)
        .options(joinedload(Liquidacion.pagos))
        .where(
            Liquidacion.periodo_id == periodo_id,
            Liquidacion.estado != "ANULADO",
        )
    )
    liquidaciones_todos = list(db.execute(stmt_liqs).scalars().unique().all())
    liquidaciones_por_trab = {l.trabajador_id: l for l in liquidaciones_todos}

    dia_18 = date(periodo.anio, periodo.mes, 18)
    filas_out: List[PlanillaFilaOut] = []

    # Variables de totales acumulados
    tot_haber = Decimal("0.00")
    tot_ganado = Decimal("0.00")
    tot_quincena = Decimal("0.00")
    tot_anticipos = Decimal("0.00")
    tot_descuentos = Decimal("0.00")
    tot_ant_desc = Decimal("0.00")
    tot_ant_sig = Decimal("0.00")
    tot_liquido = Decimal("0.00")
    count_liquidados = 0
    count_pendientes = 0

    # Construir filas de la planilla
    nro_consecutivo = 1
    nuevos_detalles_creados = False
    for t in trabajadores:
        # Si ingresó después del fin del período, no incluirlo
        if t.fecha_ingreso > periodo.fecha_fin:
            continue

        det = detalles_guardados.get(t.id)

        # Haber básico histórico (RF-6, RF-21)
        if det:
            haber_basico = det.haber_basico
            dias = det.dias_trabajados
            dias_manual = det.dias_manual
            total_ganado = det.total_ganado
        else:
            haber_basico = t.sueldoBase
            dias = calcular_dias_trabajados_automaticos(t, periodo)
            dias_manual = False
            total_ganado = calcular_total_ganado(haber_basico, dias)

            # Persistir automáticamente el detalle inicial en la BD
            nuevo_det = PlanillaDetalle(
                periodo_id=periodo_id,
                trabajador_id=t.id,
                haber_basico=haber_basico,
                dias_trabajados=dias,
                dias_manual=False,
                total_ganado=total_ganado,
            )
            db.add(nuevo_det)
            detalles_guardados[t.id] = nuevo_det
            nuevos_detalles_creados = True

        # Anticipos del período
        ants_t = anticipos_por_trab.get(t.id, [])
        monto_anticipos = sum((a.importe for a in ants_t), Decimal("0.00"))

        # Anticipos antes del corte de quincena (Día 18)
        ants_pre_18 = sum(
            (a.importe for a in ants_t if a.fecha_entrega <= dia_18),
            Decimal("0.00"),
        )
        quincena_sugerida = max(Decimal("0.00"), IMPORTE_REFERENCIA_QUINCENA - ants_pre_18)
        supera_quincena = ants_pre_18 > IMPORTE_REFERENCIA_QUINCENA
        excedente_quincena = (ants_pre_18 - IMPORTE_REFERENCIA_QUINCENA) if supera_quincena else Decimal("0.00")
        diferencia_quincena = max(Decimal("0.00"), IMPORTE_REFERENCIA_QUINCENA - ants_pre_18)

        # Anticipos para el período siguiente (deprecado / no utilizado)
        monto_anticipos_sig = Decimal("0.00")

        # Descuentos del período (RF-29 a RF-32)
        descs_t = descuentos_por_trab.get(t.id, [])
        monto_descuentos = sum((d.importe for d in descs_t), Decimal("0.00"))

        # Col 11: Total anticipos y descuentos
        total_anticipos_descuentos = monto_anticipos + monto_descuentos

        # Liquidación y Pagos
        liq = liquidaciones_por_trab.get(t.id)
        pagos_confirmados = [p for p in liq.pagos if p.estado == "CONFIRMADO"] if liq else []

        pagos_quincena = [
            p for p in pagos_confirmados
            if getattr(p, "tipo_pago", "") in ("PAGO_QUINCENA", "REVISION_QUINCENA")
        ]
        monto_quincena = sum((p.monto for p in pagos_quincena), Decimal("0.00"))
        estado_quincena = "LIQUIDADA" if (pagos_quincena or (liq and liq.estado == "LIQUIDADO")) else "PENDIENTE"

        total_pagado = sum((p.monto for p in pagos_confirmados), Decimal("0.00"))

        # Col 13: Líquido Pagable (RF-46)
        # Líquido pagable = total ganado − total de anticipos y descuentos − pago de quincena
        liquido_pagable = total_ganado - total_anticipos_descuentos - monto_quincena

        # Saldo pendiente real de liquidar
        saldo_pendiente_real = max(
            Decimal("0.00"),
            total_ganado + (liq.ajustes if liq else Decimal("0.00")) - total_anticipos_descuentos - total_pagado,
        ) if liquido_pagable > 0 else Decimal("0.00")

        estado_liq = liq.estado if liq else ("LIQUIDADO" if (total_pagado >= total_ganado and total_ganado > 0) else "PENDIENTE")

        if estado_liq == "LIQUIDADO":
            count_liquidados += 1
        else:
            count_pendientes += 1

        # Acumuladores de totales
        tot_haber += haber_basico
        tot_ganado += total_ganado
        tot_quincena += monto_quincena
        tot_anticipos += monto_anticipos
        tot_descuentos += monto_descuentos
        tot_ant_desc += total_anticipos_descuentos
        tot_ant_sig += monto_anticipos_sig
        tot_liquido += liquido_pagable

        nombre_completo = f"{t.nombres} {t.apellidos}".strip()
        area_nombre = t.area.nombre if t.area else "Sin Área"

        fila = PlanillaFilaOut(
            nro=nro_consecutivo,
            trabajador_id=t.id,
            nombre_completo=nombre_completo,
            ci=t.ci,
            cargo=t.cargo,
            area=area_nombre,
            fecha_ingreso=t.fecha_ingreso,
            haber_basico=haber_basico,
            dias_trabajados=dias,
            dias_manual=dias_manual,
            total_ganado=total_ganado,
            pago_quincena=monto_quincena,
            estado_quincena=estado_quincena,
            quincena_sugerida=quincena_sugerida,
            supera_quincena=supera_quincena,
            excedente_quincena=excedente_quincena,
            quincena_referencia=IMPORTE_REFERENCIA_QUINCENA,
            anticipos_antes_dia_18=ants_pre_18,
            diferencia_quincena=diferencia_quincena,
            pago_anticipos=monto_anticipos,
            anticipos_count=len(ants_t),
            total_descuentos=monto_descuentos,
            descuentos_count=len(descs_t),
            total_anticipos_descuentos=total_anticipos_descuentos,
            anticipos_periodo_siguiente=monto_anticipos_sig,
            liquido_pagable=liquido_pagable,
            monto_pagado_total=total_pagado,
            saldo_pendiente_real=saldo_pendiente_real,
            estado_liquidacion=estado_liq,
            liquidacion_id=liq.id if liq else None,
            liquidacion_comprobante=liq.numero_comprobante if liq else None,
        )
        filas_out.append(fila)
        nro_consecutivo += 1

    db.commit()

    totales_resumen = PlanillaResumenTotales(
        total_haber_basico=tot_haber,
        total_ganado=tot_ganado,
        total_quincena=tot_quincena,
        total_anticipos=tot_anticipos,
        total_descuentos=tot_descuentos,
        total_anticipos_descuentos=tot_ant_desc,
        total_anticipos_periodo_siguiente=tot_ant_sig,
        total_liquido_pagable=tot_liquido,
        total_trabajadores=len(filas_out),
        trabajadores_liquidados=count_liquidados,
        trabajadores_pendientes=count_pendientes,
    )

    return PlanillaMensualOut(
        periodo_id=periodo.id,
        periodo_descripcion=periodo.descripcion,
        mes=periodo.mes,
        anio=periodo.anio,
        fecha_inicio=periodo.fecha_inicio,
        fecha_fin=periodo.fecha_fin,
        fecha_pago_estimada=periodo.fecha_pago_estimada,
        fecha_limite_pago=periodo.fecha_limite_pago,
        estado_periodo=periodo.estado,
        filas=filas_out,
        totales=totales_resumen,
    )


# =========================================================================
# ACTUALIZACIÓN DE DÍAS TRABAJADOS (RF-16)
# =========================================================================
def actualizar_dias_trabajados(
    db: Session, datos: ActualizarDiasTrabajadosIn, usuario_ci: Optional[str] = None
) -> PlanillaFilaOut:
    """Modifica manualmente los días trabajados en una planilla abierta y recalcula."""
    periodo = db.execute(
        select(PeriodoSalarial).where(PeriodoSalarial.id == datos.periodo_id)
    ).scalars().first()
    if not periodo:
        raise HTTPException(status_code=404, detail="Período no encontrado.")

    if periodo.estado == "CERRADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La planilla de este período está CERRADA. No se admiten modificaciones ordinarias.",
        )

    trabajador = db.execute(
        select(Trabajador).where(Trabajador.id == datos.trabajador_id)
    ).scalars().first()
    if not trabajador:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado.")

    det = db.execute(
        select(PlanillaDetalle).where(
            PlanillaDetalle.periodo_id == datos.periodo_id,
            PlanillaDetalle.trabajador_id == datos.trabajador_id,
        )
    ).scalars().first()

    haber = det.haber_basico if det else trabajador.sueldoBase
    nuevo_total_ganado = calcular_total_ganado(haber, datos.dias_trabajados)

    if det:
        det.dias_trabajados = datos.dias_trabajados
        det.dias_manual = True
        det.total_ganado = nuevo_total_ganado
        if datos.observaciones:
            det.observaciones = datos.observaciones
    else:
        det = PlanillaDetalle(
            periodo_id=datos.periodo_id,
            trabajador_id=datos.trabajador_id,
            haber_basico=haber,
            dias_trabajados=datos.dias_trabajados,
            dias_manual=True,
            total_ganado=nuevo_total_ganado,
            observaciones=datos.observaciones,
        )
        db.add(det)

    db.commit()
    db.refresh(det)

    registrar_bitacora(
        db=db,
        modulo="PLANILLA",
        accion="MODIFICAR_DIAS",
        descripcion=(
            f"Se ajustaron los días trabajados a {datos.dias_trabajados} (Total ganado: Bs {nuevo_total_ganado}) "
            f"para {trabajador.nombres} {trabajador.apellidos} en {periodo.descripcion}"
        ),
        usuario_ci=usuario_ci,
    )

    # Devolver la planilla actualizada del trabajador
    planilla_completa = obtener_o_generar_planilla(db, datos.periodo_id)
    for f in planilla_completa.filas:
        if f.trabajador_id == datos.trabajador_id:
            return f

    raise HTTPException(status_code=500, detail="Error al recuperar fila de planilla.")


# =========================================================================
# GESTIÓN INTERACTIVA DE DESCUENTOS (RF-29 A RF-32)
# =========================================================================
def listar_descuentos(
    db: Session, periodo_id: int, trabajador_id: Optional[int] = None
) -> List[DescuentoOut]:
    """Lista los descuentos de un período con filtro opcional por trabajador."""
    stmt = select(Descuento).where(
        Descuento.periodo_id == periodo_id,
        Descuento.estado == "CONFIRMADO",
    )
    if trabajador_id:
        stmt = stmt.where(Descuento.trabajador_id == trabajador_id)
    stmt = stmt.order_by(desc(Descuento.fecha), desc(Descuento.id))

    descs = list(db.execute(stmt).scalars().unique().all())
    return [
        DescuentoOut(
            id=d.id,
            numero_comprobante=d.numero_comprobante,
            trabajador_id=d.trabajador_id,
            trabajador_nombre=f"{d.trabajador.nombres} {d.trabajador.apellidos}" if d.trabajador else None,
            periodo_id=d.periodo_id,
            fecha=d.fecha,
            importe=d.importe,
            concepto=d.concepto,
            observaciones=d.observaciones,
            estado=d.estado,
            usuario_id=d.usuario_id,
            usuario_nombre=d.usuario_nombre,
            fecha_creacion=d.fecha_creacion,
        )
        for d in descs
    ]


def registrar_descuento(
    db: Session, datos: DescuentoCreate, usuario_ci: Optional[str] = None
) -> DescuentoOut:
    """Registra una deducción salarial independiente (RF-29) con comprobante DESC-YYYYMM-XXXX."""
    periodo = db.execute(
        select(PeriodoSalarial).where(PeriodoSalarial.id == datos.periodo_id)
    ).scalars().first()
    if not periodo:
        raise HTTPException(status_code=404, detail="Período no encontrado.")
    if periodo.estado == "CERRADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La planilla de este período se encuentra CERRADA. No se admiten nuevos descuentos.",
        )

    if not (periodo.fecha_inicio <= datos.fecha <= periodo.fecha_fin):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"La fecha del descuento ({datos.fecha}) no corresponde al período {periodo.descripcion}. "
                f"Debe estar entre {periodo.fecha_inicio} y {periodo.fecha_fin}."
            ),
        )

    trabajador = db.execute(
        select(Trabajador).where(Trabajador.id == datos.trabajador_id)
    ).scalars().first()
    if not trabajador:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado.")

    nro_comprobante = generar_numero_comprobante(db, "DESC")

    nuevo_desc = Descuento(
        numero_comprobante=nro_comprobante,
        trabajador_id=datos.trabajador_id,
        periodo_id=datos.periodo_id,
        fecha=datos.fecha,
        importe=datos.importe,
        concepto=datos.concepto.strip(),
        observaciones=datos.observaciones,
        estado="CONFIRMADO",
        usuario_id=usuario_ci,
    )
    db.add(nuevo_desc)
    db.commit()
    db.refresh(nuevo_desc)

    registrar_bitacora(
        db=db,
        modulo="DESCUENTOS",
        accion="REGISTRAR",
        descripcion=(
            f"Se registró descuento {nro_comprobante} por Bs {datos.importe} "
            f"({datos.concepto}) para {trabajador.nombres} {trabajador.apellidos}"
        ),
        usuario_ci=usuario_ci,
    )

    return DescuentoOut(
        id=nuevo_desc.id,
        numero_comprobante=nuevo_desc.numero_comprobante,
        trabajador_id=nuevo_desc.trabajador_id,
        trabajador_nombre=f"{trabajador.nombres} {trabajador.apellidos}",
        periodo_id=nuevo_desc.periodo_id,
        fecha=nuevo_desc.fecha,
        importe=nuevo_desc.importe,
        concepto=nuevo_desc.concepto,
        observaciones=nuevo_desc.observaciones,
        estado=nuevo_desc.estado,
        usuario_id=nuevo_desc.usuario_id,
        usuario_nombre=nuevo_desc.usuario_nombre,
        fecha_creacion=nuevo_desc.fecha_creacion,
    )


def anular_descuento(
    db: Session, descuento_id: int, motivo: str, usuario_ci: Optional[str] = None
) -> DescuentoOut:
    """Anulación justificada de descuento salarial (RF-74)."""
    desc_obj = db.execute(
        select(Descuento).where(Descuento.id == descuento_id)
    ).scalars().first()
    if not desc_obj:
        raise HTTPException(status_code=404, detail="Descuento no encontrado.")

    periodo = desc_obj.periodo
    if periodo and periodo.estado == "CERRADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden anular movimientos de una planilla CERRADA.",
        )

    if desc_obj.estado == "ANULADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este descuento ya se encuentra anulado.",
        )

    desc_obj.estado = "ANULADO"
    desc_obj.motivo_anulacion = motivo.strip()
    db.commit()
    db.refresh(desc_obj)

    registrar_bitacora(
        db=db,
        modulo="DESCUENTOS",
        accion="ANULAR",
        descripcion=f"Se anuló el descuento {desc_obj.numero_comprobante}. Motivo: {motivo}",
        usuario_ci=usuario_ci,
    )

    return DescuentoOut(
        id=desc_obj.id,
        numero_comprobante=desc_obj.numero_comprobante,
        trabajador_id=desc_obj.trabajador_id,
        trabajador_nombre=f"{desc_obj.trabajador.nombres} {desc_obj.trabajador.apellidos}" if desc_obj.trabajador else None,
        periodo_id=desc_obj.periodo_id,
        fecha=desc_obj.fecha,
        importe=desc_obj.importe,
        concepto=desc_obj.concepto,
        observaciones=desc_obj.observaciones,
        estado=desc_obj.estado,
        usuario_id=desc_obj.usuario_id,
        usuario_nombre=desc_obj.usuario_nombre,
        fecha_creacion=desc_obj.fecha_creacion,
    )


# =========================================================================
# CIERRE FORMAL DE PLANILLA MENSUAL (RF-7, RF-8, RF-76, CL-15, CL-16)
# =========================================================================
def cerrar_planilla_periodo(
    db: Session, periodo_id: int, req: CerrarPlanillaRequest, usuario_ci: Optional[str] = None
) -> Dict[str, Any]:
    """Cierra formalmente una planilla mensual bloqueando modificaciones ordinarias."""
    periodo = db.execute(
        select(PeriodoSalarial).where(PeriodoSalarial.id == periodo_id)
    ).scalars().first()
    if not periodo:
        raise HTTPException(status_code=404, detail="Período no encontrado.")

    if periodo.estado == "CERRADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La planilla de este período ya se encuentra CERRADA.",
        )

    # Validar pendientes
    resumen = obtener_o_generar_planilla(db, periodo_id)
    pendientes = resumen.totales.trabajadores_pendientes

    if pendientes > 0 and not req.confirmar_pendientes:
        return {
            "requiere_confirmacion": True,
            "mensaje": f"Existen {pendientes} trabajadores con saldo salarial o liquidación pendiente en esta planilla. ¿Deseas confirmar el cierre de todas formas?",
            "trabajadores_pendientes": pendientes,
            "periodo_id": periodo_id,
        }

    # Proceder al cierre formal
    periodo.estado = "CERRADO"
    db.commit()
    db.refresh(periodo)

    registrar_bitacora(
        db=db,
        modulo="PLANILLA",
        accion="CERRAR_PLANILLA",
        descripcion=(
            f"Se cerró formalmente la planilla {periodo.descripcion} (ID: {periodo.id}). "
            f"Observaciones: {req.observaciones or 'Cierre mensual ordinario'}"
        ),
        usuario_ci=usuario_ci,
    )

    return {
        "success": True,
        "mensaje": f"Planilla {periodo.descripcion} cerrada exitosamente. Los registros han quedado bloqueados.",
        "periodo_id": periodo.id,
        "estado": periodo.estado,
    }
