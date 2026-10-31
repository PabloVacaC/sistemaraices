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

    dia_18 = date(periodo.anio, periodo.mes, 18)

    items: List[PlanillaItemOut] = []

    # Totales acumuladores
    total_sueldo_base = Decimal("0.00")
    total_anticipos_antes_18 = Decimal("0.00")
    total_anticipos_post_18 = Decimal("0.00")
    total_anticipos = Decimal("0.00")
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

        if liq:
            # Si ya tiene liquidación, se preserva el sueldo base histórico congelado (RF-4 y RF-5)
            s_base = liq.sueldo_base
            ajustes = liq.ajustes or Decimal("0.00")
            tot_ant_aplicado = liq.total_anticipos or tot_ant
            monto_bruto = s_base + ajustes
            liq_pagable = liq.monto_neto

            pagos_confirmados = [p for p in liq.pagos if p.estado == "CONFIRMADO"]
            pago_q = sum(
                (p.monto for p in pagos_confirmados if getattr(p, "tipo_pago", "") in ("PAGO_QUINCENA", "REVISION_QUINCENA")),
                Decimal("0.00"),
            )
            monto_pagado_total = sum((p.monto for p in pagos_confirmados), Decimal("0.00"))
            saldo_pend = liq.saldo_pendiente
            estado_p = liq.estado

            quincena_liq = any(
                getattr(p, "tipo_pago", "") in ("PAGO_QUINCENA", "REVISION_QUINCENA")
                for p in pagos_confirmados
            ) or (liq.estado == "LIQUIDADO")

            liq_id = liq.id
            liq_comp = liq.numero_comprobante
            obs = liq.observaciones
        else:
            s_base = t.sueldoBase
            ajustes = Decimal("0.00")
            tot_ant_aplicado = tot_ant
            monto_bruto = s_base
            liq_pagable = s_base - tot_ant
            pago_q = Decimal("0.00")
            monto_pagado_total = Decimal("0.00")
            saldo_pend = liq_pagable
            estado_p = "PENDIENTE" if tot_ant > 0 else "SIN_MOVIMIENTOS"
            quincena_liq = False
            liq_id = None
            liq_comp = None
            obs = None

        if estado_p == "LIQUIDADO" or (saldo_pend <= Decimal("0.00") and monto_pagado_total > Decimal("0.00")):
            count_liquidados += 1
        elif estado_p == "PARCIAL" or monto_pagado_total > Decimal("0.00"):
            count_parciales += 1
        else:
            count_pendientes += 1

        total_sueldo_base += s_base
        total_anticipos_antes_18 += ant_antes_18
        total_anticipos_post_18 += ant_post_18
        total_anticipos += tot_ant_aplicado
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
                anticipos_antes_18=ant_antes_18,
                pago_quincena=pago_q,
                anticipos_post_18=ant_post_18,
                total_anticipos=tot_ant_aplicado,
                ajustes=ajustes,
                total_ganado_bruto=monto_bruto,
                liquido_pagable=liq_pagable,
                total_pagado=monto_pagado_total,
                saldo_pendiente=saldo_pend,
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
        total_anticipos_antes_18=total_anticipos_antes_18,
        total_anticipos_post_18=total_anticipos_post_18,
        total_anticipos=total_anticipos,
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
