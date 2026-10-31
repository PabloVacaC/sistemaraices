import calendar
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import Session, joinedload

from app.models.entities import (
    PeriodoSalarial,
    Trabajador,
    Liquidacion,
    PagoLiquidacion,
    Anticipo,
    Bitacora,
)
from app.modules.pagos.service import generar_numero_comprobante
from app.modules.planillas.schemas import (
    PlanillaItemOut,
    PlanillaPeriodoHeaderOut,
    PlanillaResumenOut,
    CierrePlanillaRequest,
    ReaperturaPlanillaRequest,
    PeriodoPlanillaListItem,
)

MESES_ESPANOL = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


def registrar_bitacora(
    db: Session,
    modulo: str,
    accion: str,
    descripcion: str,
    usuario_ci: Optional[str] = None,
):
    try:
        entrada = Bitacora(
            modulo=modulo,
            accion=accion,
            descripcion=descripcion,
            usuario_ci=usuario_ci,
        )
        db.add(entrada)
        db.commit()
    except Exception as e:
        print(f"Error registrando en bitácora ({modulo} - {accion}): {e}")


def asegurar_periodo_actual(db: Session, usuario_ci: Optional[str] = None) -> PeriodoSalarial:
    """
    Garantiza que exista el período salarial del mes en curso. Si no existe,
    lo crea automáticamente con fechas y descripción estándar (RF-2 y RF-6).
    """
    hoy = date.today()
    mes_actual = hoy.month
    anio_actual = hoy.year

    periodo = db.execute(
        select(PeriodoSalarial).where(
            PeriodoSalarial.mes == mes_actual,
            PeriodoSalarial.anio == anio_actual,
        )
    ).scalars().first()

    if not periodo:
        nombre_mes = MESES_ESPANOL.get(mes_actual, f"Mes {mes_actual}")
        ultimo_dia = calendar.monthrange(anio_actual, mes_actual)[1]
        fecha_inicio = date(anio_actual, mes_actual, 1)
        fecha_fin = date(anio_actual, mes_actual, ultimo_dia)

        # Fecha estimada de pago: día 5 del mes siguiente
        if mes_actual == 12:
            fecha_pago = date(anio_actual + 1, 1, 5)
        else:
            fecha_pago = date(anio_actual, mes_actual + 1, 5)

        periodo = PeriodoSalarial(
            mes=mes_actual,
            anio=anio_actual,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            fecha_pago_estimada=fecha_pago,
            estado="ABIERTO",
            descripcion=f"{nombre_mes} {anio_actual}",
        )
        db.add(periodo)
        db.commit()
        db.refresh(periodo)

        registrar_bitacora(
            db=db,
            modulo="PLANILLA",
            accion="GENERAR_PERIODO_AUTOMATICO",
            descripcion=f"Se habilitó automáticamente el período salarial de {periodo.descripcion}.",
            usuario_ci=usuario_ci,
        )

    return periodo


def obtener_planilla_consolidada(db: Session, periodo_id: int) -> PlanillaResumenOut:
    """
    Genera la matriz consolidada de la planilla salarial para un período determinado.
    Conserva los haberes históricos si el período está cerrado o tiene liquidación fijada,
    retiene trabajadores inactivos que tuvieron movimientos en el período y consolida en O(1) consultas.
    """
    periodo = db.execute(
        select(PeriodoSalarial).where(PeriodoSalarial.id == periodo_id)
    ).scalars().first()
    if not periodo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Período salarial con ID {periodo_id} no encontrado.",
        )

    # 1. Obtener liquidaciones existentes para el período
    liquidaciones = list(
        db.execute(
            select(Liquidacion)
            .options(joinedload(Liquidacion.pagos))
            .where(
                Liquidacion.periodo_id == periodo.id,
                Liquidacion.estado != "ANULADO",
            )
        ).scalars().unique().all()
    )
    liq_por_trabajador: Dict[int, Liquidacion] = {l.trabajador_id: l for l in liquidaciones}

    # 2. Obtener anticipos pagados del período
    anticipos = list(
        db.execute(
            select(Anticipo).where(
                Anticipo.periodo_id == periodo.id,
                Anticipo.estado == "PAGADO",
            )
        ).scalars().unique().all()
    )
    anticipos_por_trabajador: Dict[int, List[Anticipo]] = {}
    for a in anticipos:
        anticipos_por_trabajador.setdefault(a.trabajador_id, []).append(a)

    # 3. Conjunto de trabajadores a incluir (Activos + Inactivos con movimientos en el período)
    ids_con_movimiento = set(liq_por_trabajador.keys()) | set(anticipos_por_trabajador.keys())
    stmt_trabajadores = (
        select(Trabajador)
        .options(joinedload(Trabajador.area))
        .where(
            or_(
                Trabajador.estado.is_(True),
                Trabajador.id.in_(ids_con_movimiento if ids_con_movimiento else [-1]),
            )
        )
        .order_by(Trabajador.apellidos, Trabajador.nombres)
    )
    trabajadores = list(db.execute(stmt_trabajadores).scalars().unique().all())

    # 4. Anticipos del día 1 al 5 del período siguiente (informativos para esta planilla, RF-Problema 2)
    if periodo.mes == 12:
        sig_mes, sig_anio = 1, periodo.anio + 1
    else:
        sig_mes, sig_anio = periodo.mes + 1, periodo.anio

    periodo_siguiente = db.execute(
        select(PeriodoSalarial).where(
            PeriodoSalarial.mes == sig_mes,
            PeriodoSalarial.anio == sig_anio,
        )
    ).scalars().first()

    anticipos_sig_map: Dict[int, Decimal] = {}
    if periodo_siguiente:
        dia_5_sig = date(sig_anio, sig_mes, 5)
        ants_sig = db.execute(
            select(Anticipo).where(
                Anticipo.periodo_id == periodo_siguiente.id,
                Anticipo.fecha_entrega <= dia_5_sig,
                Anticipo.estado == "PAGADO",
            )
        ).scalars().unique().all()
        for a in ants_sig:
            anticipos_sig_map[a.trabajador_id] = (
                anticipos_sig_map.get(a.trabajador_id, Decimal("0.00")) + a.importe
            )

    dia_18 = date(periodo.anio, periodo.mes, 18)

    items: List[PlanillaItemOut] = []

    # Totales acumuladores
    total_sueldo_base = Decimal("0.00")
    total_ganado_sum = Decimal("0.00")
    total_anticipos_antes_18 = Decimal("0.00")
    total_anticipos_post_18 = Decimal("0.00")
    total_anticipos = Decimal("0.00")
    total_anticipos_sig = Decimal("0.00")
    total_pagos_quincena = Decimal("0.00")
    total_ajustes = Decimal("0.00")
    total_ganado_bruto = Decimal("0.00")
    total_liquido_pagable = Decimal("0.00")
    total_pagado = Decimal("0.00")
    total_saldo_pendiente = Decimal("0.00")

    count_liquidados = 0
    count_parciales = 0
    count_pendientes = 0

    for t in trabajadores:
        liq = liq_por_trabajador.get(t.id)
        ants_t = anticipos_por_trabajador.get(t.id, [])

        # Desglose de anticipos por corte día 18
        ant_antes_18 = sum((a.importe for a in ants_t if a.fecha_entrega <= dia_18), Decimal("0.00"))
        ant_post_18 = sum((a.importe for a in ants_t if a.fecha_entrega > dia_18), Decimal("0.00"))
        tot_ant = ant_antes_18 + ant_post_18

        # Días trabajados calculados automáticamente (base mes comercial 30 días)
        if liq and liq.dias_trabajados:
            dias_t = liq.dias_trabajados
        elif t.fecha_ingreso and t.fecha_ingreso.year == periodo.anio and t.fecha_ingreso.month == periodo.mes:
            # Ingresó en el curso de este mes: computa desde día de ingreso hasta el día 30
            dias_t = max(1, min(30, 30 - t.fecha_ingreso.day + 1))
        else:
            dias_t = 30

        s_base = liq.sueldo_base if liq else t.sueldoBase
        # Total Ganado = (Haber Básico / 30) * Días Trabajados
        total_ganado = round((s_base / Decimal("30.00")) * Decimal(dias_t), 2)

        ajustes = (liq.ajustes or Decimal("0.00")) if liq else Decimal("0.00")
        tot_ant_aplicado = (liq.total_anticipos or tot_ant) if liq else tot_ant
        monto_bruto = total_ganado + ajustes

        # Líquido pagable = Total Ganado + Ajustes - Total Anticipos (SIN max(0), puede ser negativo)
        liq_pagable = monto_bruto - tot_ant_aplicado

        if liq:
            pagos_confirmados = [p for p in liq.pagos if p.estado == "CONFIRMADO"]
            pago_q = sum(
                (p.monto for p in pagos_confirmados if getattr(p, "tipo_pago", "") in ("PAGO_QUINCENA", "REVISION_QUINCENA")),
                Decimal("0.00"),
            )
            monto_pagado_total = sum((p.monto for p in pagos_confirmados), Decimal("0.00"))
            # Saldo pendiente real (sin ocultar negativos)
            saldo_pend = liq_pagable - monto_pagado_total
            estado_p = liq.estado

            quincena_liq = any(
                getattr(p, "tipo_pago", "") in ("PAGO_QUINCENA", "REVISION_QUINCENA")
                for p in pagos_confirmados
            ) or (liq.estado == "LIQUIDADO")

            liq_id = liq.id
            liq_comp = liq.numero_comprobante
            obs = liq.observaciones
        else:
            pago_q = Decimal("0.00")
            monto_pagado_total = Decimal("0.00")
            saldo_pend = liq_pagable
            estado_p = "PENDIENTE" if tot_ant > 0 else "SIN_MOVIMIENTOS"
            quincena_liq = False
            liq_id = None
            liq_comp = None
            obs = None

        ant_sig = anticipos_sig_map.get(t.id, Decimal("0.00"))
        es_negativo = saldo_pend < Decimal("0.00")

        if estado_p == "LIQUIDADO" or (saldo_pend <= Decimal("0.00") and monto_pagado_total > Decimal("0.00")):
            count_liquidados += 1
        elif estado_p == "PARCIAL" or monto_pagado_total > Decimal("0.00"):
            count_parciales += 1
        else:
            count_pendientes += 1

        total_sueldo_base += s_base
        total_ganado_sum += total_ganado
        total_anticipos_antes_18 += ant_antes_18
        total_anticipos_post_18 += ant_post_18
        total_anticipos += tot_ant_aplicado
        total_anticipos_sig += ant_sig
        total_pagos_quincena += pago_q
        total_ajustes += ajustes
        total_ganado_bruto += monto_bruto
        total_liquido_pagable += liq_pagable
        total_pagado += monto_pagado_total
        total_saldo_pendiente += saldo_pend

        nombre_completo = f"{t.nombres} {t.apellidos}".strip()
        area_nombre = t.area.nombre if t.area else "Sin Área"

        items.append(
            PlanillaItemOut(
                trabajador_id=t.id,
                ci=t.ci,
                nombre_completo=nombre_completo,
                cargo=t.cargo,
                area=area_nombre,
                fecha_ingreso=t.fecha_ingreso,
                estado_trabajador=t.estado,
                sueldo_base=s_base,
                dias_trabajados=dias_t,
                total_ganado=total_ganado,
                anticipos_antes_18=ant_antes_18,
                pago_quincena=pago_q,
                anticipos_post_18=ant_post_18,
                total_anticipos=tot_ant_aplicado,
                anticipos_siguiente_periodo=ant_sig,
                ajustes=ajustes,
                total_ganado_bruto=monto_bruto,
                liquido_pagable=liq_pagable,
                total_pagado=monto_pagado_total,
                saldo_pendiente=saldo_pend,
                es_saldo_negativo=es_negativo,
                estado_pago=estado_p,
                quincena_liquidada=quincena_liq,
                liquidacion_id=liq_id,
                numero_comprobante_liq=liq_comp,
                observaciones=obs,
            )
        )

    # Evaluación de advertencias para el cierre de planilla (RF-9 y RF-10)
    advertencias = []
    if total_saldo_pendiente > Decimal("0.00"):
        advertencias.append(
            f"Existen {count_pendientes + count_parciales} trabajadores con saldo salarial pendiente de liquidar "
            f"por un total acumulado de Bs {total_saldo_pendiente:,.2f}."
        )

    if count_liquidados < len(trabajadores):
        advertencias.append(
            f"Faltan {len(trabajadores) - count_liquidados} trabajadores por liquidar completamente su sueldo."
        )

    header = PlanillaPeriodoHeaderOut(
        id=periodo.id,
        mes=periodo.mes,
        anio=periodo.anio,
        descripcion=periodo.descripcion,
        fecha_inicio=periodo.fecha_inicio,
        fecha_fin=periodo.fecha_fin,
        fecha_pago_estimada=periodo.fecha_pago_estimada,
        estado=periodo.estado,
        fecha_cierre=periodo.fecha_cierre,
        cerrado_por=periodo.cerrado_por,
        cerrado_por_nombre=periodo.cerrado_por_nombre,
        observaciones_cierre=periodo.observaciones_cierre,
    )

    return PlanillaResumenOut(
        periodo=header,
        total_trabajadores=len(trabajadores),
        total_sueldo_base=total_sueldo_base,
        total_ganado=total_ganado_sum,
        total_anticipos_antes_18=total_anticipos_antes_18,
        total_anticipos_post_18=total_anticipos_post_18,
        total_anticipos=total_anticipos,
        total_anticipos_siguiente_periodo=total_anticipos_sig,
        total_pagos_quincena=total_pagos_quincena,
        total_ajustes=total_ajustes,
        total_ganado_bruto=total_ganado_bruto,
        total_liquido_pagable=total_liquido_pagable,
        total_pagado=total_pagado,
        total_saldo_pendiente=total_saldo_pendiente,
        trabajadores_liquidados=count_liquidados,
        trabajadores_parciales=count_parciales,
        trabajadores_pendientes=count_pendientes,
        es_cerrable=(periodo.estado == "ABIERTO"),
        advertencias_cierre=advertencias,
        items=items,
    )


def actualizar_dias_trabajados(
    db: Session,
    periodo_id: int,
    trabajador_id: int,
    dias: int,
    usuario_ci: Optional[str] = None,
) -> PlanillaItemOut:
    """
    Ajusta interactivamente los días trabajados de un trabajador en la planilla (base mes comercial 30 días),
    recalculando Total Ganado, Líquido Pagable y Saldo Salarial en tiempo real.
    """
    periodo = db.execute(
        select(PeriodoSalarial).where(PeriodoSalarial.id == periodo_id)
    ).scalars().first()
    if not periodo:
        raise HTTPException(status_code=404, detail="Período salarial no encontrado.")

    if periodo.estado == "CERRADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden modificar los días trabajados de una planilla CERRADA.",
        )

    trabajador = db.execute(
        select(Trabajador).where(Trabajador.id == trabajador_id)
    ).scalars().first()
    if not trabajador:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado.")

    liq = db.execute(
        select(Liquidacion).where(
            Liquidacion.trabajador_id == trabajador.id,
            Liquidacion.periodo_id == periodo.id,
            Liquidacion.estado != "ANULADO",
        )
    ).scalars().first()

    anticipos_tot = db.scalar(
        select(func.sum(Anticipo.importe)).where(
            Anticipo.trabajador_id == trabajador.id,
            Anticipo.periodo_id == periodo.id,
            Anticipo.estado == "PAGADO",
        )
    ) or Decimal("0.00")

    sueldo_base = liq.sueldo_base if liq else trabajador.sueldoBase
    total_ganado = round((sueldo_base / Decimal("30.00")) * Decimal(dias), 2)
    ajustes = liq.ajustes if liq else Decimal("0.00")
    monto_neto = total_ganado + ajustes - anticipos_tot
    monto_pagado = liq.monto_pagado if liq else Decimal("0.00")
    saldo_pendiente = monto_neto - monto_pagado

    if not liq:
        nro_comp = generar_numero_comprobante(db, "LIQ")
        liq = Liquidacion(
            numero_comprobante=nro_comp,
            trabajador_id=trabajador.id,
            periodo_id=periodo.id,
            fecha_liquidacion=date.today(),
            sueldo_base=sueldo_base,
            dias_trabajados=dias,
            remuneracion_mensual=total_ganado,
            ajustes=ajustes,
            total_anticipos=anticipos_tot,
            monto_neto=monto_neto,
            monto_pagado=monto_pagado,
            saldo_pendiente=saldo_pendiente,
            estado="PENDIENTE",
            observaciones=f"Ajuste de días trabajados a {dias} días",
            usuario_id=usuario_ci,
        )
        db.add(liq)
    else:
        liq.dias_trabajados = dias
        liq.remuneracion_mensual = total_ganado
        liq.monto_neto = monto_neto
        liq.saldo_pendiente = saldo_pendiente
        if liq.saldo_pendiente <= Decimal("0.00") and liq.monto_pagado > Decimal("0.00"):
            liq.estado = "LIQUIDADO"
        elif liq.monto_pagado > Decimal("0.00"):
            liq.estado = "PARCIAL"

    db.commit()
    db.refresh(liq)

    registrar_bitacora(
        db=db,
        modulo="PLANILLA",
        accion="AJUSTAR_DIAS",
        descripcion=f"Se ajustaron los días trabajados de {trabajador.nombres} {trabajador.apellidos} a {dias} días (Total Ganado: Bs {total_ganado}).",
        usuario_ci=usuario_ci,
    )

    resumen = obtener_planilla_consolidada(db, periodo.id)
    item_actualizado = next((it for it in resumen.items if it.trabajador_id == trabajador.id), None)
    if not item_actualizado:
        raise HTTPException(status_code=500, detail="Error al recuperar ítem actualizado.")
    return item_actualizado


def cerrar_planilla(
    db: Session,
    periodo_id: int,
    request: CierrePlanillaRequest,
    usuario_ci: Optional[str] = None,
) -> PlanillaResumenOut:
    """
    Ejecuta el cierre formal de la planilla salarial mensual:
    - Valida si existen pagos pendientes y exige confirmación explícita (RF-9 y RF-10).
    - Congela las liquidaciones de todos los trabajadores para preservar inmutabilidad (RF-11 y RF-12).
    - Cambia el estado del período a CERRADO y sella fecha y usuario de cierre.
    """
    periodo = db.execute(
        select(PeriodoSalarial).where(PeriodoSalarial.id == periodo_id)
    ).scalars().first()
    if not periodo:
        raise HTTPException(status_code=404, detail="Período salarial no encontrado.")

    if periodo.estado == "CERRADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La planilla de este período salarial ya se encuentra CERRADA.",
        )

    # 1. Obtener la consolidación para validar saldos pendientes
    resumen = obtener_planilla_consolidada(db, periodo_id)

    if resumen.total_saldo_pendiente > Decimal("0.00") and not request.confirmar_con_pendientes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"No se puede cerrar la planilla sin confirmación: Existen {resumen.trabajadores_pendientes + resumen.trabajadores_parciales} "
                f"trabajadores con saldos salariales pendientes por Bs {resumen.total_saldo_pendiente:,.2f}. "
                f"Debe activar la confirmación explícita para proceder."
            ),
        )

    # 2. Asegurar que cada trabajador tenga un registro formal de liquidación congelado
    for item in resumen.items:
        if not item.liquidacion_id:
            nro_comprobante = generar_numero_comprobante(db, "LIQ")
            estado_calc = "LIQUIDADO" if item.saldo_pendiente <= Decimal("0.00") and item.total_pagado > Decimal("0.00") else ("PARCIAL" if item.total_pagado > Decimal("0.00") else "PENDIENTE")
            nueva_liq = Liquidacion(
                numero_comprobante=nro_comprobante,
                trabajador_id=item.trabajador_id,
                periodo_id=periodo.id,
                fecha_liquidacion=date.today(),
                sueldo_base=item.sueldo_base,
                dias_trabajados=item.dias_trabajados,
                remuneracion_mensual=item.total_ganado,
                ajustes=item.ajustes,
                total_anticipos=item.total_anticipos,
                monto_neto=item.liquido_pagable,
                monto_pagado=item.total_pagado,
                saldo_pendiente=item.saldo_pendiente,
                estado=estado_calc,
                observaciones=request.observaciones or "Cierre formal de planilla mensual",
                usuario_id=usuario_ci,
            )
            db.add(nueva_liq)

    # 3. Marcar el período como CERRADO
    periodo.estado = "CERRADO"
    periodo.fecha_cierre = datetime.now()
    periodo.cerrado_por = usuario_ci
    periodo.observaciones_cierre = request.observaciones or "Planilla cerrada satisfactoriamente."

    db.commit()
    db.refresh(periodo)

    registrar_bitacora(
        db=db,
        modulo="PLANILLA",
        accion="CERRAR_PLANILLA",
        descripcion=(
            f"Se cerró la planilla salarial {periodo.descripcion}. "
            f"Trabajadores: {resumen.total_trabajadores}, Total Pagado: Bs {resumen.total_pagado:,.2f}, "
            f"Saldo Pendiente: Bs {resumen.total_saldo_pendiente:,.2f}."
        ),
        usuario_ci=usuario_ci,
    )

    return obtener_planilla_consolidada(db, periodo.id)


def reabrir_planilla(
    db: Session,
    periodo_id: int,
    request: ReaperturaPlanillaRequest,
    usuario_ci: Optional[str] = None,
) -> PlanillaResumenOut:
    """
    Reabre administrativamente una planilla cerrada, registrando auditoría estricta.
    """
    periodo = db.execute(
        select(PeriodoSalarial).where(PeriodoSalarial.id == periodo_id)
    ).scalars().first()
    if not periodo:
        raise HTTPException(status_code=404, detail="Período salarial no encontrado.")

    if periodo.estado != "CERRADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La planilla no se encuentra cerrada.",
        )

    periodo.estado = "ABIERTO"
    nota_reapertura = (
        f"[Reapertura {datetime.now().strftime('%Y-%m-%d %H:%M')} por CI {usuario_ci or 'N/A'}]: {request.motivo}"
    )
    if periodo.observaciones_cierre:
        periodo.observaciones_cierre += f"\n{nota_reapertura}"
    else:
        periodo.observaciones_cierre = nota_reapertura

    db.commit()
    db.refresh(periodo)

    registrar_bitacora(
        db=db,
        modulo="PLANILLA",
        accion="REABRIR_PLANILLA",
        descripcion=f"Reapertura administrativa de la planilla {periodo.descripcion}. Motivo: {request.motivo}",
        usuario_ci=usuario_ci,
    )

    return obtener_planilla_consolidada(db, periodo.id)


def listar_resumen_periodos(db: Session) -> List[PeriodoPlanillaListItem]:
    """
    Retorna la lista de todos los períodos ordenados cronológicamente descendente
    con avance porcentual y saldos para alimentar el selector de planillas.
    """
    periodos = list(
        db.execute(
            select(PeriodoSalarial).order_by(
                desc(PeriodoSalarial.anio), desc(PeriodoSalarial.mes)
            )
        ).scalars().unique().all()
    )

    resultado: List[PeriodoPlanillaListItem] = []
    for p in periodos:
        # Consulta rápida de liquidaciones y totales
        liqs = db.execute(
            select(
                func.count(Liquidacion.id),
                func.sum(Liquidacion.sueldo_base),
                func.sum(Liquidacion.monto_pagado),
                func.sum(Liquidacion.saldo_pendiente),
            ).where(Liquidacion.periodo_id == p.id, Liquidacion.estado != "ANULADO")
        ).first()

        cant = liqs[0] or 0
        s_base = liqs[1] or Decimal("0.00")
        pagado = liqs[2] or Decimal("0.00")
        pendiente = liqs[3] or Decimal("0.00")

        total_neto = pagado + pendiente
        porcentaje = round(float(pagado / total_neto * 100), 1) if total_neto > Decimal("0.00") else 0.0

        resultado.append(
            PeriodoPlanillaListItem(
                id=p.id,
                mes=p.mes,
                anio=p.anio,
                descripcion=p.descripcion,
                estado=p.estado,
                fecha_inicio=p.fecha_inicio,
                fecha_fin=p.fecha_fin,
                fecha_cierre=p.fecha_cierre,
                total_trabajadores=cant,
                total_sueldo_base=s_base,
                total_pagado=pagado,
                total_saldo_pendiente=pendiente,
                porcentaje_avance=porcentaje,
            )
        )

    return resultado
