from datetime import date, datetime, timezone, timedelta
import calendar
from typing import List, Optional, Dict, Any
from collections import defaultdict
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, and_, or_, desc, text
from fastapi import HTTPException, status

from app.models.entities import (
    Trabajador,
    PeriodoSalarial,
    Anticipo,
    AnticipoRider,
    Liquidacion,
    PagoLiquidacion,
    Descuento,
    Usuario,
    PlanillaDetalle,
)
from app.modules.pagos.schemas import (
    AnticipoCreate,
    LiquidacionCreate,
    PagoLiquidacionCreate,
    PagoParcialDirectoCreate,
    ResumenSalarialTrabajador,
    ResumenTrabajadorPagosParcialesOut,
    ComprobanteAnticipoDetalladoOut,
    PanelResumenPagos,
    AnticipoOut,
    LiquidacionOut,
    PagoLiquidacionOut,
    PeriodoSalarialCreate,
    IMPORTE_REFERENCIA_QUINCENA,
)
from app.modules.bitacora.service import registrar_bitacora


# =========================================================================
# UTILIDADES DE GENERACIÓN DE COMPROBANTES ÚNICOS
# =========================================================================
def generar_numero_comprobante(db: Session, prefijo: str) -> str:
    """
    Genera números correlativos únicos y seguros tipo: ANT-202610-0001, LIQ-202610-0001, PAG-202610-0001
    Aplica bloqueo transaccional a nivel de PostgreSQL (pg_advisory_xact_lock) para evitar
    condiciones de carrera y colisiones de comprobantes concurrentes.
    Usa hora de Bolivia (UTC-4) para evitar saltos prematuros de mes en servidores en la nube.
    """
    # Zona horaria Bolivia (UTC-4)
    now = datetime.now(timezone(timedelta(hours=-4)))
    ym = now.strftime("%Y%m")
    prefix_ym = f"{prefijo}-{ym}-"

    # Bloqueo transaccional de concurrencia en PostgreSQL (se libera automáticamente al hacer commit o rollback)
    try:
        bind = db.get_bind()
        if bind and bind.dialect.name == "postgresql":
            db.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
                {"lock_key": prefix_ym},
            )
    except Exception:
        pass

    max_code = None
    if prefijo == "ANT":
        max_code = db.scalar(
            select(func.max(Anticipo.numero_comprobante)).where(
                Anticipo.numero_comprobante.like(f"{prefix_ym}%")
            )
        )
    elif prefijo == "LIQ":
        max_code = db.scalar(
            select(func.max(Liquidacion.numero_comprobante)).where(
                Liquidacion.numero_comprobante.like(f"{prefix_ym}%")
            )
        )
    elif prefijo == "PAG":
        max_code = db.scalar(
            select(func.max(PagoLiquidacion.numero_comprobante)).where(
                PagoLiquidacion.numero_comprobante.like(f"{prefix_ym}%")
            )
        )
    elif prefijo == "DESC":
        max_code = db.scalar(
            select(func.max(Descuento.numero_comprobante)).where(
                Descuento.numero_comprobante.like(f"{prefix_ym}%")
            )
        )
    elif prefijo in ("RID", "ARID"):
        max_code = db.scalar(
            select(func.max(AnticipoRider.numero_comprobante)).where(
                AnticipoRider.numero_comprobante.like(f"{prefix_ym}%")
            )
        )

    correlativo = 1
    if max_code and len(max_code) >= len(prefix_ym):
        try:
            ultimo_num = int(max_code.split("-")[-1])
            correlativo = ultimo_num + 1
        except (ValueError, IndexError):
            correlativo = 1

    # Bucle de salvaguarda para garantizar unicidad absoluta
    while True:
        candidato = f"{prefix_ym}{correlativo:04d}"
        existe = False
        if prefijo == "ANT":
            existe = db.scalar(select(Anticipo.id).where(Anticipo.numero_comprobante == candidato)) is not None
        elif prefijo == "LIQ":
            existe = db.scalar(select(Liquidacion.id).where(Liquidacion.numero_comprobante == candidato)) is not None
        elif prefijo == "PAG":
            existe = db.scalar(select(PagoLiquidacion.id).where(PagoLiquidacion.numero_comprobante == candidato)) is not None
        elif prefijo == "DESC":
            existe = db.scalar(select(Descuento.id).where(Descuento.numero_comprobante == candidato)) is not None
        elif prefijo in ("RID", "ARID"):
            existe = db.scalar(select(AnticipoRider.id).where(AnticipoRider.numero_comprobante == candidato)) is not None

        if not existe:
            return candidato
        correlativo += 1


# =========================================================================
# HELPERS DE SINCRONIZACIÓN SALARIAL (PLANILLA VS PAGOS)
# =========================================================================
def calcular_dias_trabajados_base(trabajador: Trabajador, periodo: PeriodoSalarial) -> int:
    """Calcula los días comerciales estándar (base 30) según ingreso o cese en el mes."""
    if trabajador.fecha_ingreso > periodo.fecha_fin:
        return 0

    if (
        trabajador.fecha_ingreso.year == periodo.anio
        and trabajador.fecha_ingreso.month == periodo.mes
    ):
        dia_ingreso = trabajador.fecha_ingreso.day
        return max(1, min(30, 30 - dia_ingreso + 1))

    if (
        trabajador.fecha_inactividad
        and trabajador.fecha_inactividad.year == periodo.anio
        and trabajador.fecha_inactividad.month == periodo.mes
    ):
        return max(1, min(30, trabajador.fecha_inactividad.day))

    if (
        trabajador.fecha_inactividad
        and trabajador.fecha_inactividad < date(periodo.anio, periodo.mes, 1)
        and not trabajador.estado
    ):
        return 0

    return 30


def calcular_sueldo_proporcional(haber_basico: Decimal, dias: int) -> Decimal:
    """Calcula el total ganado proporcional a los días trabajados en base a 30 días comerciales."""
    if dias >= 30:
        return haber_basico
    if dias <= 0:
        return Decimal("0.00")
    val = (haber_basico / Decimal("30")) * Decimal(dias)
    return round(val, 2)


def obtener_base_salarial_periodo(
    db: Session, trabajador: Trabajador, periodo: PeriodoSalarial
) -> Decimal:
    """
    Obtiene la base salarial efectiva/proporcional para el período:
    1. Si existe PlanillaDetalle registrado, usa su total_ganado (respeta días ajustados manualmente).
    2. Si no existe aún registro de planilla, calcula automáticamente según fecha de ingreso/inactividad.
    """
    stmt_det = select(PlanillaDetalle).where(
        PlanillaDetalle.trabajador_id == trabajador.id,
        PlanillaDetalle.periodo_id == periodo.id,
    )
    det = db.execute(stmt_det).scalars().first()
    if det:
        return det.total_ganado

    dias = calcular_dias_trabajados_base(trabajador, periodo)
    return calcular_sueldo_proporcional(trabajador.sueldoBase, dias)


# =========================================================================
# PERÍODOS SALARIALES Y APERTURA AUTOMÁTICA
# =========================================================================
MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

def calcular_mes_siguiente(anio: int, mes: int) -> tuple[int, int]:
    if mes == 12:
        return anio + 1, 1
    return anio, mes + 1


def asegurar_periodos_automaticos(db: Session):
    """
    Apertura Automática Inteligente de Períodos:
    Garantiza que el mes actual, el mes siguiente y el subsiguiente estén siempre
    creados y disponibles en la base de datos con sus fechas exactas (inicio, fin, pago día 5).
    """
    now = datetime.now(timezone(timedelta(hours=-4)))
    anio_hoy = now.year
    mes_hoy = now.month

    # Asegurar mes actual, siguiente y subsiguiente
    m1_anio, m1_mes = anio_hoy, mes_hoy
    m2_anio, m2_mes = calcular_mes_siguiente(m1_anio, m1_mes)
    m3_anio, m3_mes = calcular_mes_siguiente(m2_anio, m2_mes)

    objetivos = [(m1_anio, m1_mes), (m2_anio, m2_mes), (m3_anio, m3_mes)]

    nuevos_creados = False
    for a, m in objetivos:
        existe = db.scalar(
            select(PeriodoSalarial.id).where(
                PeriodoSalarial.anio == a,
                PeriodoSalarial.mes == m
            )
        )
        if not existe:
            _, ultimo_dia = calendar.monthrange(a, m)
            f_inicio = date(a, m, 1)
            f_fin = date(a, m, ultimo_dia)
            p_anio, p_mes = calcular_mes_siguiente(a, m)
            f_pago = date(p_anio, p_mes, 5)
            desc_mes = f"{MESES_ES[m]} {a}"

            nuevo = PeriodoSalarial(
                mes=m,
                anio=a,
                fecha_inicio=f_inicio,
                fecha_fin=f_fin,
                fecha_pago_estimada=f_pago,
                estado="ABIERTO",
                descripcion=desc_mes
            )
            db.add(nuevo)
            nuevos_creados = True

    if nuevos_creados:
        try:
            db.commit()
        except Exception:
            db.rollback()


def obtener_o_crear_periodo_siguiente(db: Session, periodo: PeriodoSalarial) -> Optional[PeriodoSalarial]:
    """Obtiene el período salarial del mes calendario siguiente, creándolo automáticamente si no existe."""
    sig_anio, sig_mes = calcular_mes_siguiente(periodo.anio, periodo.mes)
    periodo_sig = db.execute(
        select(PeriodoSalarial).where(
            PeriodoSalarial.anio == sig_anio,
            PeriodoSalarial.mes == sig_mes,
        )
    ).scalars().first()
    if not periodo_sig:
        asegurar_periodos_automaticos(db)
        periodo_sig = db.execute(
            select(PeriodoSalarial).where(
                PeriodoSalarial.anio == sig_anio,
                PeriodoSalarial.mes == sig_mes,
            )
        ).scalars().first()
    if not periodo_sig:
        _, ultimo_dia = calendar.monthrange(sig_anio, sig_mes)
        p_anio, p_mes = calcular_mes_siguiente(sig_anio, sig_mes)
        periodo_sig = PeriodoSalarial(
            mes=sig_mes,
            anio=sig_anio,
            fecha_inicio=date(sig_anio, sig_mes, 1),
            fecha_fin=date(sig_anio, sig_mes, ultimo_dia),
            fecha_pago_estimada=date(p_anio, p_mes, 5),
            estado="ABIERTO",
            descripcion=f"{MESES_ES[sig_mes]} {sig_anio}",
        )
        db.add(periodo_sig)
        db.commit()
        db.refresh(periodo_sig)
    return periodo_sig


def listar_periodos(db: Session) -> List[PeriodoSalarial]:
    asegurar_periodos_automaticos(db)
    stmt = select(PeriodoSalarial).order_by(
        desc(PeriodoSalarial.anio), desc(PeriodoSalarial.mes)
    )
    return list(db.execute(stmt).scalars().unique().all())


def crear_periodo(db: Session, datos: PeriodoSalarialCreate, admin_ci: Optional[str] = None) -> PeriodoSalarial:
    existente = db.execute(
        select(PeriodoSalarial).where(
            PeriodoSalarial.mes == datos.mes, PeriodoSalarial.anio == datos.anio
        )
    ).scalars().first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El período salarial {datos.mes}/{datos.anio} ya existe.",
        )

    nuevo = PeriodoSalarial(**datos.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    registrar_bitacora(
        db=db,
        modulo="PAGOS",
        accion="CREAR_PERIODO",
        descripcion=f"Se creó el período salarial {nuevo.descripcion}",
        usuario_ci=admin_ci,
    )
    return nuevo


# =========================================================================
# CÁLCULOS Y MÉTRICAS SALARIALES BASE POR PERÍODO
# =========================================================================
def calcular_metricas_trabajador_periodo(
    db: Session, trabajador: Trabajador, periodo: PeriodoSalarial
) -> Dict[str, Any]:
    """
    Calcula de manera centralizada y exacta todas las métricas salariales de un trabajador:
    - Anticipos antes y después del día 18
    - Comparativa con la quincena de referencia (Bs 1.000)
    - Monto sugerido para pago adicional de quincena
    - Pagos parciales / quincena ya realizados
    - Saldo salarial pendiente real (sin truncar negativos)
    """
    # 1. Anticipos pagados en el período
    stmt_ant = select(Anticipo).where(
        Anticipo.trabajador_id == trabajador.id,
        Anticipo.periodo_id == periodo.id,
        Anticipo.estado == "PAGADO",
    ).order_by(Anticipo.fecha_entrega, Anticipo.id)
    anticipos = list(db.execute(stmt_ant).scalars().unique().all())

    total_anticipos = sum((a.importe for a in anticipos), Decimal("0.00"))

    # 1.1 Anticipos rider pagados en el período (spec.md)
    stmt_rider = select(AnticipoRider).where(
        AnticipoRider.trabajador_id == trabajador.id,
        AnticipoRider.periodo_id == periodo.id,
        AnticipoRider.estado == "PAGADO",
    ).order_by(AnticipoRider.fecha_entrega, AnticipoRider.id)
    anticipos_rider = list(db.execute(stmt_rider).scalars().unique().all())
    total_anticipos_rider = sum((ar.importe for ar in anticipos_rider), Decimal("0.00"))

    # Corte de primera quincena: día 18 del mes del período
    dia_18_limite = date(periodo.anio, periodo.mes, 18)
    anticipos_antes_18 = sum(
        (a.importe for a in anticipos if a.fecha_entrega <= dia_18_limite),
        Decimal("0.00"),
    )
    anticipos_post_18 = total_anticipos - anticipos_antes_18
    fecha_ultimo_anticipo = anticipos[-1].fecha_entrega if anticipos else None

    # Quincena de referencia (configurable)
    quincena_ref = IMPORTE_REFERENCIA_QUINCENA
    diferencia_quincena = quincena_ref - anticipos_antes_18
    supera_quincena = anticipos_antes_18 > quincena_ref
    excedente_quincena = (anticipos_antes_18 - quincena_ref) if supera_quincena else Decimal("0.00")
    monto_sugerido_quincena = max(Decimal("0.00"), diferencia_quincena)

    # Base salarial efectiva y proporcional sincronizada con Planilla
    sueldo_base_efectivo = obtener_base_salarial_periodo(db, trabajador, periodo)

    # Descuentos aplicados en el período
    stmt_desc = select(Descuento).where(
        Descuento.trabajador_id == trabajador.id,
        Descuento.periodo_id == periodo.id,
        Descuento.estado == "CONFIRMADO",
    )
    descuentos = list(db.execute(stmt_desc).scalars().unique().all())
    total_descuentos = sum((d.importe for d in descuentos), Decimal("0.00"))

    # 2. Liquidación y pagos parciales existentes
    stmt_liq = select(Liquidacion).where(
        Liquidacion.trabajador_id == trabajador.id,
        Liquidacion.periodo_id == periodo.id,
        Liquidacion.estado != "ANULADO",
    )
    liquidacion = db.execute(stmt_liq).scalars().first()

    pago_quincena_realizado = Decimal("0.00")
    quincena_pagada = False
    total_pagos_parciales = Decimal("0.00")
    saldo_salarial_pendiente = Decimal("0.00")
    estado_periodo = "SIN_MOVIMIENTOS"

    if liquidacion:
        pagos = [p for p in liquidacion.pagos if p.estado == "CONFIRMADO"]
        pago_quincena_realizado = sum(
            (p.monto for p in pagos if getattr(p, "tipo_pago", "") in ("PAGO_QUINCENA", "REVISION_QUINCENA")),
            Decimal("0.00"),
        )
        quincena_pagada = any(getattr(p, "tipo_pago", "") in ("PAGO_QUINCENA", "REVISION_QUINCENA") for p in pagos) or (liquidacion.estado == "LIQUIDADO")
        total_pagos_parciales = sum((p.monto for p in pagos), Decimal("0.00"))
        # SALDO = SUELDO_PROPORCIONAL + AJUSTES - TOTAL_ANTICIPOS - TOTAL_ANTICIPOS_RIDER - TOTAL_DESCUENTOS - TOTAL_PAGOS_PARCIALES
        saldo_salarial_pendiente = sueldo_base_efectivo + liquidacion.ajustes - total_anticipos - total_anticipos_rider - total_descuentos - total_pagos_parciales
        estado_periodo = liquidacion.estado
    else:
        total_pagos_parciales = Decimal("0.00")
        saldo_salarial_pendiente = sueldo_base_efectivo - total_anticipos - total_anticipos_rider - total_descuentos
        if total_anticipos > 0:
            estado_periodo = "ANTICIPOS_PENDIENTES"
        else:
            estado_periodo = "PENDIENTE"

    return {
        "trabajador": trabajador,
        "periodo": periodo,
        "sueldo_base_efectivo": sueldo_base_efectivo,
        "descuentos": descuentos,
        "total_descuentos": total_descuentos,
        "anticipos": anticipos,
        "total_anticipos": total_anticipos,
        "anticipos_rider": anticipos_rider,
        "total_anticipos_rider": total_anticipos_rider,
        "anticipos_antes_18": anticipos_antes_18,
        "anticipos_post_18": anticipos_post_18,
        "fecha_ultimo_anticipo": fecha_ultimo_anticipo,
        "quincena_ref": quincena_ref,
        "diferencia_quincena": diferencia_quincena,
        "supera_quincena": supera_quincena,
        "excedente_quincena": excedente_quincena,
        "monto_sugerido_quincena": monto_sugerido_quincena,
        "liquidacion": liquidacion,
        "pago_quincena_realizado": pago_quincena_realizado,
        "quincena_pagada": quincena_pagada,
        "total_pagos_parciales": total_pagos_parciales,
        "saldo_salarial_pendiente": saldo_salarial_pendiente,
        "estado_periodo": estado_periodo,
    }


# =========================================================================
# RESUMEN SALARIAL DEL TRABAJADOR EN UN PERÍODO
# =========================================================================
def obtener_resumen_salarial(
    db: Session, trabajador_id: int, periodo_id: int
) -> ResumenSalarialTrabajador:
    trabajador = db.execute(
        select(Trabajador).where(Trabajador.id == trabajador_id)
    ).scalars().first()
    if not trabajador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trabajador con ID {trabajador_id} no encontrado.",
        )

    periodo = db.execute(
        select(PeriodoSalarial).where(PeriodoSalarial.id == periodo_id)
    ).scalars().first()
    if not periodo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Período salarial con ID {periodo_id} no encontrado.",
        )

    m = calcular_metricas_trabajador_periodo(db, trabajador, periodo)
    liq = m["liquidacion"]

    nombre_completo = f"{trabajador.nombres} {trabajador.apellidos}"
    area_nombre = trabajador.area.nombre if trabajador.area else "Sin Área"

    return ResumenSalarialTrabajador(
        trabajador_id=trabajador.id,
        nombre_completo=nombre_completo,
        ci=trabajador.ci,
        cargo=trabajador.cargo,
        area=area_nombre,
        sueldo_base=trabajador.sueldoBase,
        periodo_id=periodo.id,
        periodo_descripcion=periodo.descripcion,
        quincena_referencia=m["quincena_ref"],
        anticipos=[AnticipoOut.model_validate(a) for a in m["anticipos"]],
        total_anticipos=m["total_anticipos"],
        anticipos_antes_dia_18=m["anticipos_antes_18"],
        diferencia_quincena=m["diferencia_quincena"],
        monto_sugerido_quincena=m["monto_sugerido_quincena"],
        pago_quincena_realizado=m["pago_quincena_realizado"],
        quincena_pagada=m["quincena_pagada"],
        anticipos_posteriores_dia_18=m["anticipos_post_18"],
        total_pagos_parciales=m["total_pagos_parciales"],
        saldo_salarial_pendiente=m["saldo_salarial_pendiente"],
        supera_quincena=m["supera_quincena"],
        excedente_quincena=m["excedente_quincena"],
        fecha_ultimo_anticipo=m["fecha_ultimo_anticipo"],
        liquidacion=LiquidacionOut.model_validate(liq) if liq else None,
        total_pagos_anteriores=m["total_pagos_parciales"],
        saldo_pendiente_liquidacion=m["saldo_salarial_pendiente"],
        estado_liquidacion=m["estado_periodo"],
    )


# =========================================================================
# REGISTRO DE ANTICIPOS
# =========================================================================
def registrar_anticipo(
    db: Session, datos: AnticipoCreate, usuario_ci: Optional[str] = None
) -> Anticipo:
    trabajador = db.execute(
        select(Trabajador).where(Trabajador.id == datos.trabajador_id)
    ).scalars().first()
    if not trabajador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trabajador con ID {datos.trabajador_id} no encontrado.",
        )

    periodo = db.execute(
        select(PeriodoSalarial).where(PeriodoSalarial.id == datos.periodo_id)
    ).scalars().first()
    if not periodo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período salarial no encontrado.",
        )

    if periodo.estado == "CERRADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El período salarial se encuentra CERRADO. No se admiten nuevos anticipos.",
        )

    if not (periodo.fecha_inicio <= datos.fecha_entrega <= periodo.fecha_fin):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"La fecha de entrega ({datos.fecha_entrega}) no corresponde al período {periodo.descripcion}. "
                f"Debe estar entre {periodo.fecha_inicio} y {periodo.fecha_fin}."
            ),
        )

    # Verificar si ya existe una liquidación completamente cerrada
    liq_existente = db.execute(
        select(Liquidacion).where(
            Liquidacion.trabajador_id == datos.trabajador_id,
            Liquidacion.periodo_id == datos.periodo_id,
            Liquidacion.estado == "LIQUIDADO",
        )
    ).scalars().first()
    if liq_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El período ya ha sido completamente LIQUIDADO para este trabajador. No se pueden registrar más anticipos.",
        )

    # Validar saldo salarial disponible (RF-27: advertencia si supera, pero permite confirmar con confirmar_excedente=True)
    m_prev = calcular_metricas_trabajador_periodo(db, trabajador, periodo)
    saldo_disponible = m_prev["saldo_salarial_pendiente"]

    if datos.importe > saldo_disponible and trabajador.sueldoBase > 0:
        if not getattr(datos, "confirmar_excedente", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"ADVERTENCIA_EXCEDENTE: El anticipo solicitado (Bs {datos.importe}) supera el saldo salarial disponible "
                    f"(Bs {saldo_disponible}) en Bs {datos.importe - saldo_disponible}."
                ),
            )

    anticipos_previos = db.scalar(
        select(func.sum(Anticipo.importe)).where(
            Anticipo.trabajador_id == datos.trabajador_id,
            Anticipo.periodo_id == datos.periodo_id,
            Anticipo.estado == "PAGADO",
        )
    ) or Decimal("0.00")

    total_con_nuevo = anticipos_previos + datos.importe

    nro_comprobante = generar_numero_comprobante(db, "ANT")

    nuevo_anticipo = Anticipo(
        numero_comprobante=nro_comprobante,
        trabajador_id=datos.trabajador_id,
        periodo_id=datos.periodo_id,
        fecha_solicitud=date.today(),
        fecha_entrega=datos.fecha_entrega,
        importe=datos.importe,
        metodo_pago=datos.metodo_pago.upper(),
        es_periodo_siguiente=getattr(datos, "es_periodo_siguiente", False) or False,
        estado="PAGADO",
        observaciones=datos.observaciones,
        usuario_id=usuario_ci,
    )

    db.add(nuevo_anticipo)
    db.flush()

    # Si ya existía una liquidación abierta (ej. PENDIENTE o PARCIAL), actualizar su balance
    liq_abierta = db.execute(
        select(Liquidacion).where(
            Liquidacion.trabajador_id == datos.trabajador_id,
            Liquidacion.periodo_id == datos.periodo_id,
            Liquidacion.estado.in_(["PENDIENTE", "PARCIAL"]),
        )
    ).scalars().first()
    if liq_abierta:
        liq_abierta.total_anticipos = total_con_nuevo
        liq_abierta.monto_neto = liq_abierta.sueldo_base + liq_abierta.ajustes - liq_abierta.total_anticipos
        liq_abierta.saldo_pendiente = liq_abierta.monto_neto - liq_abierta.monto_pagado
        if liq_abierta.saldo_pendiente <= 0 and liq_abierta.monto_pagado > 0:
            liq_abierta.estado = "LIQUIDADO"
        elif liq_abierta.monto_pagado > 0:
            liq_abierta.estado = "PARCIAL"

    db.commit()
    db.refresh(nuevo_anticipo)

    registrar_bitacora(
        db=db,
        modulo="ANTICIPOS",
        accion="REGISTRAR",
        descripcion=(
            f"Se registró anticipo {nro_comprobante} por Bs {datos.importe} "
            f"para {trabajador.nombres} {trabajador.apellidos} ({periodo.descripcion})"
        ),
        usuario_ci=usuario_ci,
    )

    return nuevo_anticipo


def listar_anticipos(
    db: Session,
    periodo_id: Optional[int] = None,
    trabajador_id: Optional[int] = None,
    area_id: Optional[int] = None,
) -> List[Anticipo]:
    stmt = select(Anticipo).join(Trabajador).order_by(desc(Anticipo.fecha_entrega), desc(Anticipo.id))

    if periodo_id:
        stmt = stmt.where(Anticipo.periodo_id == periodo_id)
    if trabajador_id:
        stmt = stmt.where(Anticipo.trabajador_id == trabajador_id)
    if area_id:
        stmt = stmt.where(Trabajador.area_id == area_id)

    return list(db.execute(stmt).scalars().unique().all())


# =========================================================================
# COMPROBANTE HISTÓRICO DETALLADO DE ANTICIPO (INMUTABLE)
# =========================================================================
def obtener_comprobante_anticipo_detallado(
    db: Session, anticipo_id: int
) -> ComprobanteAnticipoDetalladoOut:
    """
    Obtiene el comprobante de anticipo con desglose histórico hasta el momento exacto
    de su emisión. Anticipos futuros no alteran ni modifican el comprobante emitido.
    """
    anticipo = db.execute(select(Anticipo).where(Anticipo.id == anticipo_id)).scalars().first()
    if not anticipo:
        raise HTTPException(status_code=404, detail="Anticipo no encontrado.")

    trabajador = anticipo.trabajador
    periodo = anticipo.periodo

    # Recuperar anticipos del período
    stmt = (
        select(Anticipo)
        .where(
            Anticipo.trabajador_id == anticipo.trabajador_id,
            Anticipo.periodo_id == anticipo.periodo_id,
            Anticipo.estado != "ANULADO",
        )
        .order_by(Anticipo.fecha_entrega, Anticipo.id)
    )
    todos = list(db.execute(stmt).scalars().unique().all())

    # Filtrar solo registros hasta este anticipo (cronológico / ID)
    historicos_hasta_este = [
        a for a in todos
        if (a.fecha_entrega < anticipo.fecha_entrega) or (a.fecha_entrega == anticipo.fecha_entrega and a.id <= anticipo.id)
    ]
    anteriores = [a for a in historicos_hasta_este if a.id != anticipo.id]
    total_anteriores = sum((a.importe for a in anteriores), Decimal("0.00"))
    total_acumulado = total_anteriores + anticipo.importe

    # Métricas de quincena al momento de emitir este comprobante
    dia_18 = date(periodo.anio, periodo.mes, 18)
    anticipos_quincena = sum(
        (a.importe for a in historicos_hasta_este if a.fecha_entrega <= dia_18),
        Decimal("0.00"),
    )
    diferencia_quincena = IMPORTE_REFERENCIA_QUINCENA - anticipos_quincena
    supera_quincena = anticipos_quincena > IMPORTE_REFERENCIA_QUINCENA
    excedente_quincena = (anticipos_quincena - IMPORTE_REFERENCIA_QUINCENA) if supera_quincena else Decimal("0.00")

    # Estado de la quincena y pagos salariales del período
    stmt_liq = (
        select(Liquidacion)
        .options(joinedload(Liquidacion.pagos))
        .where(
            Liquidacion.trabajador_id == trabajador.id,
            Liquidacion.periodo_id == periodo.id,
            Liquidacion.estado != "ANULADO",
        )
    )
    liq = db.execute(stmt_liq).scalars().first()
    quincena_pagada = False
    pago_quincena_realizado = Decimal("0.00")
    total_pagos_realizados = Decimal("0.00")
    ajustes_liq = Decimal("0.00")

    if liq:
        pagos_confirmados = [p for p in liq.pagos if p.estado == "CONFIRMADO"]
        ajustes_liq = liq.ajustes or Decimal("0.00")

        pagos_quincena = [
            p for p in pagos_confirmados
            if getattr(p, "tipo_pago", "") in ("PAGO_QUINCENA", "REVISION_QUINCENA")
        ]
        if pagos_quincena:
            quincena_pagada = True
            pago_quincena_realizado = sum((p.monto for p in pagos_quincena), Decimal("0.00"))
        elif liq.estado == "LIQUIDADO":
            quincena_pagada = True

        total_pagos_realizados = sum((p.monto for p in pagos_confirmados), Decimal("0.00"))
        if pago_quincena_realizado == Decimal("0.00") and quincena_pagada and total_pagos_realizados > Decimal("0.00"):
            pago_quincena_realizado = total_pagos_realizados

    estado_quincena = "LIQUIDADA" if quincena_pagada else "PENDIENTE"

    # Base salarial efectiva y descuentos aplicados al momento del comprobante
    base_sal = obtener_base_salarial_periodo(db, trabajador, periodo)
    stmt_desc = select(Descuento).where(
        Descuento.trabajador_id == trabajador.id,
        Descuento.periodo_id == periodo.id,
        Descuento.estado == "CONFIRMADO",
    )
    total_descuentos = sum((d.importe for d in db.execute(stmt_desc).scalars().unique().all()), Decimal("0.00"))

    # El saldo salarial estimado tras este anticipo debe descontar los anticipos acumulados,
    # los descuentos aplicados y los pagos salariales ya ejecutados (quincena / parciales)
    saldo_estimado = max(
        Decimal("0.00"),
        base_sal + ajustes_liq - total_acumulado - total_descuentos - total_pagos_realizados,
    )

    anticipos_periodo = [AnticipoOut.model_validate(a) for a in historicos_hasta_este]

    return ComprobanteAnticipoDetalladoOut(
        empresa_nombre="SISTEMAS RAÍCES",
        numero_comprobante=anticipo.numero_comprobante,
        trabajador_id=trabajador.id,
        trabajador_nombre=f"{trabajador.nombres} {trabajador.apellidos}",
        trabajador_ci=trabajador.ci,
        trabajador_cargo=trabajador.cargo,
        trabajador_area=trabajador.area.nombre if trabajador.area else "Sin Área",
        periodo_id=periodo.id,
        periodo_descripcion=periodo.descripcion,
        fecha_anticipo=anticipo.fecha_entrega,
        importe_actual=anticipo.importe,
        metodo_entrega=anticipo.metodo_pago,
        usuario_nombre=anticipo.usuario_nombre,
        usuario_ci=anticipo.usuario_id,
        motivo=anticipo.observaciones,
        total_anticipos_anteriores=total_anteriores,
        anticipos_historicos=[AnticipoOut.model_validate(a) for a in anteriores],
        anticipos_periodo=anticipos_periodo,
        total_acumulado=total_acumulado,
        sueldo_base=trabajador.sueldoBase,
        quincena_referencia=IMPORTE_REFERENCIA_QUINCENA,
        diferencia_quincena=diferencia_quincena,
        saldo_salarial_estimado=saldo_estimado,
        supera_quincena=supera_quincena,
        excedente_quincena=excedente_quincena,
        quincena_pagada=quincena_pagada,
        estado_quincena=estado_quincena,
        pago_quincena_realizado=pago_quincena_realizado,
        total_pagos_realizados=total_pagos_realizados,
    )


# =========================================================================
# SUBMÓDULO DE PAGOS PARCIALES (LISTA DE CONTROL DE QUINCENA)
# =========================================================================
def listar_resumen_pagos_parciales(
    db: Session, periodo_id: int
) -> List[ResumenTrabajadorPagosParcialesOut]:
    """Genera la lista consolidada de todos los trabajadores para gestión de quincena y pagos parciales en lote (O(1) consultas)"""
    periodo = db.execute(
        select(PeriodoSalarial).where(PeriodoSalarial.id == periodo_id)
    ).scalars().first()
    if not periodo:
        raise HTTPException(status_code=404, detail="Período no encontrado.")

    # 1. Cargar trabajadores activos con su área en 1 consulta única
    trabajadores = list(
        db.execute(
            select(Trabajador)
            .options(joinedload(Trabajador.area))
            .where(Trabajador.estado.is_(True))
            .order_by(Trabajador.apellidos, Trabajador.nombres)
        ).scalars().unique().all()
    )

    if not trabajadores:
        return []

    # 2. Cargar TODOS los anticipos del período en 1 consulta única indexada
    anticipos_periodo = list(
        db.execute(
            select(Anticipo)
            .where(Anticipo.periodo_id == periodo_id, Anticipo.estado == "PAGADO")
            .order_by(Anticipo.fecha_entrega, Anticipo.id)
        ).scalars().unique().all()
    )
    anticipos_por_trab = defaultdict(list)
    for a in anticipos_periodo:
        anticipos_por_trab[a.trabajador_id].append(a)

    # 3. Cargar TODAS las liquidaciones con sus pagos en 1 consulta única
    liquidaciones_periodo = list(
        db.execute(
            select(Liquidacion)
            .options(joinedload(Liquidacion.pagos))
            .where(Liquidacion.periodo_id == periodo_id, Liquidacion.estado != "ANULADO")
        ).scalars().unique().all()
    )
    liquidaciones_por_trab = {liq.trabajador_id: liq for liq in liquidaciones_periodo}

    # 4. Cargar detalles de planilla y descuentos para sincronización salarial exacta
    detalles_periodo = list(
        db.execute(
            select(PlanillaDetalle).where(PlanillaDetalle.periodo_id == periodo_id)
        ).scalars().unique().all()
    )
    detalles_por_trab = {d.trabajador_id: d for d in detalles_periodo}

    descuentos_periodo = list(
        db.execute(
            select(Descuento).where(
                Descuento.periodo_id == periodo_id,
                Descuento.estado == "CONFIRMADO"
            )
        ).scalars().unique().all()
    )
    descuentos_por_trab = defaultdict(list)
    for d in descuentos_periodo:
        descuentos_por_trab[d.trabajador_id].append(d)

    # 5. Cálculo en memoria ultrarrápido
    dia_18_limite = date(periodo.anio, periodo.mes, 18)
    quincena_ref = IMPORTE_REFERENCIA_QUINCENA

    resultados = []
    for t in trabajadores:
        ants = anticipos_por_trab.get(t.id, [])
        total_anticipos = sum((a.importe for a in ants), Decimal("0.00"))
        anticipos_antes_18 = sum(
            (a.importe for a in ants if a.fecha_entrega <= dia_18_limite),
            Decimal("0.00"),
        )
        anticipos_post_18 = total_anticipos - anticipos_antes_18
        fecha_ultimo_anticipo = ants[-1].fecha_entrega if ants else None

        diferencia_quincena = quincena_ref - anticipos_antes_18
        supera_quincena = anticipos_antes_18 > quincena_ref
        excedente_quincena = (anticipos_antes_18 - quincena_ref) if supera_quincena else Decimal("0.00")
        monto_sugerido_quincena = max(Decimal("0.00"), diferencia_quincena)

        # Base salarial efectiva y descuentos
        det = detalles_por_trab.get(t.id)
        if det:
            base_sueldo = det.total_ganado
        else:
            dias = calcular_dias_trabajados_base(t, periodo)
            base_sueldo = calcular_sueldo_proporcional(t.sueldoBase, dias)

        descs = descuentos_por_trab.get(t.id, [])
        total_descuentos = sum((d.importe for d in descs), Decimal("0.00"))

        liq = liquidaciones_por_trab.get(t.id)
        if liq:
            pagos_confirmados = [p for p in liq.pagos if p.estado == "CONFIRMADO"]
            pago_quincena_realizado = sum(
                (p.monto for p in pagos_confirmados if getattr(p, "tipo_pago", "") in ("PAGO_QUINCENA", "REVISION_QUINCENA")),
                Decimal("0.00"),
            )
            quincena_pagada = any(getattr(p, "tipo_pago", "") in ("PAGO_QUINCENA", "REVISION_QUINCENA") for p in pagos_confirmados)
            total_pagos_parciales = sum((p.monto for p in pagos_confirmados), Decimal("0.00"))
            saldo_salarial_pendiente = base_sueldo + liq.ajustes - total_anticipos - total_descuentos - total_pagos_parciales
            estado_periodo = liq.estado
        else:
            pago_quincena_realizado = Decimal("0.00")
            quincena_pagada = False
            total_pagos_parciales = Decimal("0.00")
            saldo_salarial_pendiente = base_sueldo - total_anticipos - total_descuentos
            estado_periodo = "ANTICIPOS_PENDIENTES" if total_anticipos > 0 else "PENDIENTE"

        resultados.append(
            ResumenTrabajadorPagosParcialesOut(
                trabajador_id=t.id,
                nombre_completo=f"{t.nombres} {t.apellidos}",
                ci=t.ci,
                cargo=t.cargo,
                area=t.area.nombre if t.area else "Sin Área",
                sueldo_base=t.sueldoBase,
                quincena_referencia=quincena_ref,
                anticipos_antes_dia_18=anticipos_antes_18,
                diferencia_quincena=diferencia_quincena,
                pago_quincena_realizado=pago_quincena_realizado,
                quincena_pagada=quincena_pagada,
                anticipos_posteriores_dia_18=anticipos_post_18,
                total_anticipos_periodo=total_anticipos,
                total_descuentos=total_descuentos,
                total_pagos_parciales=total_pagos_parciales,
                saldo_salarial_pendiente=saldo_salarial_pendiente,
                estado_periodo=estado_periodo,
                supera_quincena=supera_quincena,
                excedente_quincena=excedente_quincena,
                monto_sugerido_quincena=monto_sugerido_quincena,
                fecha_ultimo_anticipo=fecha_ultimo_anticipo,
                liquidacion_id=liq.id if liq else None,
                liquidacion_comprobante=liq.numero_comprobante if liq else None,
            )
        )

    return resultados


def registrar_pago_parcial_directo(
    db: Session, datos: PagoParcialDirectoCreate, usuario_ci: Optional[str] = None
) -> PagoLiquidacion:
    """
    Registra directamente un pago de quincena o pago parcial para un trabajador en un período.
    Permite montos >= 0 (por ejemplo, Bs 0 para revisión de quincena ya superada).
    No duplica anticipos ni pagos.
    """
    trabajador = db.execute(
        select(Trabajador).where(Trabajador.id == datos.trabajador_id)
    ).scalars().first()
    if not trabajador:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado.")

    periodo = db.execute(
        select(PeriodoSalarial).where(PeriodoSalarial.id == datos.periodo_id)
    ).scalars().first()
    if not periodo:
        raise HTTPException(status_code=404, detail="Período no encontrado.")

    if periodo.estado == "CERRADO":
        raise HTTPException(status_code=400, detail="El período salarial está CERRADO.")

    limite_max_pago = periodo.fecha_fin if datos.tipo_pago in ("PAGO_QUINCENA", "REVISION_QUINCENA") else periodo.fecha_limite_pago
    if not (periodo.fecha_inicio <= datos.fecha_pago <= limite_max_pago):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"La fecha de pago ({datos.fecha_pago}) no corresponde a la ventana permitida del período {periodo.descripcion}. "
                f"Debe estar entre {periodo.fecha_inicio} y {limite_max_pago}."
            ),
        )

    m = calcular_metricas_trabajador_periodo(db, trabajador, periodo)

    # Validar regla: una sola quincena por trabajador en el período
    if datos.tipo_pago in ("PAGO_QUINCENA", "REVISION_QUINCENA") and m["quincena_pagada"]:
        raise HTTPException(
            status_code=400,
            detail="Ya se registró el pago de quincena para este trabajador en el período actual.",
        )

    if datos.monto > 0 and m["saldo_salarial_pendiente"] > 0 and datos.monto > m["saldo_salarial_pendiente"]:
        raise HTTPException(
            status_code=400,
            detail=f"El monto (Bs {datos.monto}) supera el saldo salarial pendiente del trabajador (Bs {m['saldo_salarial_pendiente']}).",
        )

    # Buscar o inicializar la liquidación del trabajador en este período
    liq = m["liquidacion"]
    if not liq:
        nro_liq = generar_numero_comprobante(db, "LIQ")
        liq = Liquidacion(
            numero_comprobante=nro_liq,
            trabajador_id=trabajador.id,
            periodo_id=periodo.id,
            fecha_liquidacion=datos.fecha_pago,
            sueldo_base=m["sueldo_base_efectivo"],
            ajustes=Decimal("0.00"),
            total_anticipos=m["total_anticipos"],
            monto_neto=m["sueldo_base_efectivo"] - m["total_anticipos"] - m["total_descuentos"],
            monto_pagado=Decimal("0.00"),
            saldo_pendiente=m["sueldo_base_efectivo"] - m["total_anticipos"] - m["total_descuentos"],
            estado="PENDIENTE",
            observaciones="Liquidación iniciada por control de pagos parciales",
            usuario_id=usuario_ci,
        )
        db.add(liq)
        db.flush()
    elif liq.estado == "LIQUIDADO" and datos.monto > 0:
        raise HTTPException(
            status_code=400,
            detail="El trabajador ya se encuentra completamente LIQUIDADO en este período.",
        )

    nro_pag = generar_numero_comprobante(db, "PAG")
    nuevo_pago = PagoLiquidacion(
        numero_comprobante=nro_pag,
        liquidacion_id=liq.id,
        fecha_pago=datos.fecha_pago,
        monto=datos.monto,
        tipo_pago=datos.tipo_pago,
        metodo_pago=datos.metodo_pago.upper(),
        observaciones=datos.observaciones,
        estado="CONFIRMADO",
        usuario_id=usuario_ci,
    )
    db.add(nuevo_pago)

    # Actualizar balances de la liquidación de forma atómica
    liq.monto_pagado += datos.monto
    liq.total_anticipos = m["total_anticipos"]
    liq.monto_neto = liq.sueldo_base + liq.ajustes - liq.total_anticipos - m["total_descuentos"]
    liq.saldo_pendiente = liq.monto_neto - liq.monto_pagado

    if liq.saldo_pendiente <= 0 and liq.monto_pagado > 0:
        liq.estado = "LIQUIDADO"
    elif liq.monto_pagado > 0:
        liq.estado = "PARCIAL"

    db.commit()
    db.refresh(nuevo_pago)

    registrar_bitacora(
        db=db,
        modulo="PAGOS_PARCIALES",
        accion="REGISTRAR",
        descripcion=(
            f"Se registró {datos.tipo_pago} {nro_pag} por Bs {datos.monto} para "
            f"{trabajador.nombres} {trabajador.apellidos} ({periodo.descripcion})"
        ),
        usuario_ci=usuario_ci,
    )

    return nuevo_pago


# =========================================================================
# REGISTRO DE LIQUIDACIÓN DE SUELDO (DÍA 5 O CIERRE FINAL)
# =========================================================================
def registrar_liquidacion(
    db: Session, datos: LiquidacionCreate, usuario_ci: Optional[str] = None
) -> Liquidacion:
    trabajador = db.execute(
        select(Trabajador).where(Trabajador.id == datos.trabajador_id)
    ).scalars().first()
    if not trabajador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trabajador con ID {datos.trabajador_id} no encontrado.",
        )

    periodo = db.execute(
        select(PeriodoSalarial).where(PeriodoSalarial.id == datos.periodo_id)
    ).scalars().first()
    if not periodo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período salarial no encontrado.",
        )

    if periodo.estado == "CERRADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El período salarial se encuentra CERRADO. No se pueden registrar o actualizar liquidaciones.",
        )

    if not (periodo.fecha_inicio <= datos.fecha_liquidacion <= periodo.fecha_limite_pago):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"La fecha de liquidación ({datos.fecha_liquidacion}) no corresponde a la ventana permitida del período {periodo.descripcion}. "
                f"Debe estar entre {periodo.fecha_inicio} y {periodo.fecha_limite_pago}."
            ),
        )

    m = calcular_metricas_trabajador_periodo(db, trabajador, periodo)
    existente = m["liquidacion"]

    if existente and existente.estado == "LIQUIDADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Ya existe una liquidación activa finalizada ({existente.numero_comprobante}) "
                f"para este trabajador en el período {periodo.descripcion} con estado LIQUIDADO."
            ),
        )

    sueldo_base = m["sueldo_base_efectivo"]
    ajustes = datos.ajustes or Decimal("0.00")
    total_anticipos = m["total_anticipos"]
    total_anticipos_rider = m.get("total_anticipos_rider", Decimal("0.00"))
    total_descuentos = m["total_descuentos"]
    total_pagos_previos = m["total_pagos_parciales"]

    # Monto neto restando anticipos, anticipos rider y descuentos
    monto_neto = sueldo_base + ajustes - total_anticipos - total_anticipos_rider - total_descuentos
    saldo_final_restante = monto_neto - total_pagos_previos

    if existente:
        liq = existente
        liq.fecha_liquidacion = datos.fecha_liquidacion
        liq.ajustes = ajustes
        liq.total_anticipos = total_anticipos
        liq.monto_neto = monto_neto
        if datos.observaciones:
            liq.observaciones = datos.observaciones
    else:
        nro_liq = generar_numero_comprobante(db, "LIQ")
        liq = Liquidacion(
            numero_comprobante=nro_liq,
            trabajador_id=datos.trabajador_id,
            periodo_id=datos.periodo_id,
            fecha_liquidacion=datos.fecha_liquidacion,
            sueldo_base=sueldo_base,
            ajustes=ajustes,
            total_anticipos=total_anticipos,
            monto_neto=monto_neto,
            monto_pagado=total_pagos_previos,
            saldo_pendiente=saldo_final_restante,
            estado="PENDIENTE",
            observaciones=datos.observaciones,
            usuario_id=usuario_ci,
        )
        db.add(liq)
        db.flush()

    # Procesar pago inmediato si se solicitó (Liquidación final)
    pago_creado = None
    excedente_sig = Decimal("0.00")
    if datos.pago_inmediato:
        monto_a_pagar = datos.monto_pago_inmediato if datos.monto_pago_inmediato is not None else saldo_final_restante
        if monto_a_pagar < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El monto de pago no puede ser negativo.",
            )

        # Si el monto a entregar supera el saldo de liquidación, se cubre el saldo actual
        # y el excedente se transfiere automáticamente al mes siguiente como Anticipo Rider (spec.md)
        if monto_a_pagar > saldo_final_restante:
            excedente_sig = monto_a_pagar - max(Decimal("0.00"), saldo_final_restante)

        if monto_a_pagar > 0:
            nro_pag = generar_numero_comprobante(db, "PAG")
            obs_pago = "Liquidación final de sueldo"
            if excedente_sig > 0:
                obs_pago += f" (Incluye Bs {excedente_sig} como anticipo para el siguiente mes)"

            pago_obj = PagoLiquidacion(
                numero_comprobante=nro_pag,
                liquidacion_id=liq.id,
                fecha_pago=datos.fecha_liquidacion,
                monto=monto_a_pagar,
                tipo_pago="LIQUIDACION_FINAL",
                metodo_pago=datos.metodo_pago_inmediato.upper(),
                observaciones=obs_pago,
                estado="CONFIRMADO",
                usuario_id=usuario_ci,
            )
            db.add(pago_obj)
            liq.monto_pagado += monto_a_pagar
            pago_creado = pago_obj

            # Transferencia automática al siguiente mes como Anticipo Rider (spec.md)
            if excedente_sig > 0:
                periodo_sig = obtener_o_crear_periodo_siguiente(db, periodo)
                if periodo_sig:
                    ar_sig = db.execute(
                        select(AnticipoRider).where(
                            AnticipoRider.periodo_id == periodo_sig.id,
                            AnticipoRider.trabajador_id == datos.trabajador_id,
                            AnticipoRider.es_periodo_siguiente.is_(True),
                            AnticipoRider.estado == "PAGADO",
                        )
                    ).scalars().first()
                    if ar_sig:
                        ar_sig.importe = excedente_sig
                        ar_sig.fecha_entrega = datos.fecha_liquidacion
                        ar_sig.observaciones = (
                            f"Anticipo que se le pagó el día del sueldo (Excedente liquidación {periodo.descripcion})"
                        )
                    else:
                        nro_rid = generar_numero_comprobante(db, "RID")
                        nuevo_rider_sig = AnticipoRider(
                            numero_comprobante=nro_rid,
                            trabajador_id=datos.trabajador_id,
                            periodo_id=periodo_sig.id,
                            fecha_solicitud=date.today(),
                            fecha_entrega=datos.fecha_liquidacion,
                            importe=excedente_sig,
                            metodo_pago=datos.metodo_pago_inmediato.upper() if datos.metodo_pago_inmediato else "EFECTIVO",
                            es_periodo_siguiente=True,
                            estado="PAGADO",
                            observaciones=f"Anticipo que se le pagó el día del sueldo (Excedente liquidación {periodo.descripcion})",
                            usuario_id=usuario_ci,
                        )
                        db.add(nuevo_rider_sig)

                    registrar_bitacora(
                        db=db,
                        modulo="ANTICIPOS_RIDER",
                        accion="REGISTRAR",
                        descripcion=(
                            f"Se generó anticipo rider por Bs {excedente_sig} en {periodo_sig.descripcion} "
                            f"por excedente de liquidación de {periodo.descripcion} para {trabajador.nombres} {trabajador.apellidos}"
                        ),
                        usuario_ci=usuario_ci,
                    )

    liq.saldo_pendiente = max(Decimal("0.00"), liq.monto_neto - liq.monto_pagado)
    if liq.monto_pagado >= liq.monto_neto:
        liq.estado = "LIQUIDADO"
    elif liq.monto_pagado > 0:
        liq.estado = "PARCIAL"
    else:
        liq.estado = "PENDIENTE"

    db.commit()
    db.refresh(liq)

    setattr(liq, "pago_inmediato_monto", pago_creado.monto if pago_creado else (Decimal("0.00") if not datos.pago_inmediato else monto_a_pagar))
    setattr(liq, "pago_inmediato_comprobante", pago_creado.numero_comprobante if pago_creado else None)
    setattr(liq, "total_pagos_previos", total_pagos_previos)
    setattr(liq, "pago_quincena_previo", m.get("pago_quincena_realizado", Decimal("0.00")))
    setattr(liq, "excedente_siguiente_mes", excedente_sig)

    registrar_bitacora(
        db=db,
        modulo="LIQUIDACIONES",
        accion="REGISTRAR",
        descripcion=(
            f"Se liquidó sueldo ({liq.numero_comprobante}) para {trabajador.nombres} {trabajador.apellidos} "
            f"({periodo.descripcion}): Neto Bs {liq.monto_neto}, Pagado Bs {liq.monto_pagado}, Saldo Bs {liq.saldo_pendiente}"
        ),
        usuario_ci=usuario_ci,
    )

    return liq


def listar_liquidaciones(
    db: Session,
    periodo_id: Optional[int] = None,
    trabajador_id: Optional[int] = None,
    estado: Optional[str] = None,
    area_id: Optional[int] = None,
) -> List[Liquidacion]:
    stmt = select(Liquidacion).join(Trabajador).order_by(desc(Liquidacion.fecha_liquidacion), desc(Liquidacion.id))

    if periodo_id:
        stmt = stmt.where(Liquidacion.periodo_id == periodo_id)
    if trabajador_id:
        stmt = stmt.where(Liquidacion.trabajador_id == trabajador_id)
    if estado:
        stmt = stmt.where(Liquidacion.estado == estado.upper())
    if area_id:
        stmt = stmt.where(Trabajador.area_id == area_id)

    return list(db.execute(stmt).scalars().unique().all())


# =========================================================================
# REGISTRO DE PAGOS A UNA LIQUIDACIÓN
# =========================================================================
def registrar_pago_liquidacion(
    db: Session, datos: PagoLiquidacionCreate, usuario_ci: Optional[str] = None
) -> PagoLiquidacion:
    liq = db.execute(
        select(Liquidacion).where(Liquidacion.id == datos.liquidacion_id)
    ).scalars().first()
    if not liq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Liquidación con ID {datos.liquidacion_id} no encontrada.",
        )

    if liq.estado == "ANULADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La liquidación se encuentra ANULADA. No se pueden registrar pagos.",
        )

    if liq.periodo.estado == "CERRADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El período salarial se encuentra CERRADO. No se admiten nuevos pagos.",
        )

    if not (liq.periodo.fecha_inicio <= datos.fecha_pago <= liq.periodo.fecha_limite_pago):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"La fecha de pago ({datos.fecha_pago}) no corresponde a la ventana permitida del período {liq.periodo.descripcion}. "
                f"Debe estar entre {liq.periodo.fecha_inicio} y {liq.periodo.fecha_limite_pago}."
            ),
        )

    if liq.estado == "LIQUIDADO" or liq.saldo_pendiente <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La liquidación ya se encuentra completamente pagada (Saldo Bs 0.00).",
        )

    if datos.monto <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El monto a pagar debe ser mayor a cero.",
        )

    if datos.monto > liq.saldo_pendiente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El monto ingresado (Bs {datos.monto}) supera el saldo pendiente de liquidación "
                f"(Bs {liq.saldo_pendiente})."
            ),
        )

    nro_pag = generar_numero_comprobante(db, "PAG")

    nuevo_pago = PagoLiquidacion(
        numero_comprobante=nro_pag,
        liquidacion_id=liq.id,
        fecha_pago=datos.fecha_pago,
        monto=datos.monto,
        tipo_pago=datos.tipo_pago,
        metodo_pago=datos.metodo_pago.upper(),
        observaciones=datos.observaciones,
        estado="CONFIRMADO",
        usuario_id=usuario_ci,
    )
    db.add(nuevo_pago)

    # Actualizar liquidación atómicamente
    liq.monto_pagado += datos.monto
    liq.saldo_pendiente -= datos.monto
    if liq.saldo_pendiente <= 0:
        liq.estado = "LIQUIDADO"
    else:
        liq.estado = "PARCIAL"

    db.commit()
    db.refresh(nuevo_pago)

    trab_nombre = f"{liq.trabajador.nombres} {liq.trabajador.apellidos}" if liq.trabajador else ""
    registrar_bitacora(
        db=db,
        modulo="PAGOS_LIQUIDACION",
        accion="REGISTRAR",
        descripcion=(
            f"Se registró pago {nro_pag} por Bs {datos.monto} para {trab_nombre} "
            f"(Liquidación: {liq.numero_comprobante}, Nuevo Saldo: Bs {liq.saldo_pendiente})"
        ),
        usuario_ci=usuario_ci,
    )

    return nuevo_pago


# =========================================================================
# HISTORIAL COMPLETO DE MOVIMIENTOS DE UN TRABAJADOR
# =========================================================================
def obtener_historial_trabajador(db: Session, trabajador_id: int):
    trabajador = db.execute(
        select(Trabajador).where(Trabajador.id == trabajador_id)
    ).scalars().first()
    if not trabajador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trabajador no encontrado",
        )

    stmt_ant = select(Anticipo).where(Anticipo.trabajador_id == trabajador_id)
    anticipos = db.execute(stmt_ant).scalars().unique().all()

    stmt_liq = select(Liquidacion).where(Liquidacion.trabajador_id == trabajador_id)
    liquidaciones = db.execute(stmt_liq).scalars().unique().all()

    movimientos = []
    for a in anticipos:
        movimientos.append({
            "id": a.id,
            "tipo": "ANTICIPO",
            "numero_comprobante": a.numero_comprobante,
            "fecha": a.fecha_entrega,
            "periodo": a.periodo.descripcion if a.periodo else "",
            "monto": a.importe,
            "metodo_pago": a.metodo_pago,
            "estado": a.estado,
            "observaciones": a.observaciones,
            "usuario_id": a.usuario_id,
            "usuario_nombre": a.usuario_nombre,
        })

    for l in liquidaciones:
        pagos_confirmados = [x for x in l.pagos if x.estado == "CONFIRMADO"]
        quincena_monto = sum(
            (x.monto for x in pagos_confirmados if getattr(x, "tipo_pago", "") in ("PAGO_QUINCENA", "REVISION_QUINCENA")),
            Decimal("0.00"),
        )
        for p in l.pagos:
            movimientos.append({
                "id": p.id,
                "tipo": "PAGO_LIQUIDACION",
                "tipo_pago": getattr(p, "tipo_pago", "PAGO_PARCIAL"),
                "numero_comprobante": p.numero_comprobante,
                "liquidacion_comprobante": l.numero_comprobante,
                "fecha": p.fecha_pago,
                "periodo": l.periodo.descripcion if l.periodo else "",
                "monto": p.monto,
                "metodo_pago": p.metodo_pago,
                "estado": p.estado,
                "observaciones": p.observaciones,
                "usuario_id": p.usuario_id,
                "usuario_nombre": p.usuario_nombre,
                "sueldo_base": l.sueldo_base,
                "total_anticipos": l.total_anticipos,
                "quincena_descontada": quincena_monto,
                "saldo_pendiente": l.saldo_pendiente,
            })

    movimientos.sort(key=lambda x: str(x["fecha"]), reverse=True)
    return {
        "trabajador": {
            "id": trabajador.id,
            "ci": trabajador.ci,
            "nombre_completo": f"{trabajador.nombres} {trabajador.apellidos}",
            "cargo": trabajador.cargo,
            "sueldo_base": trabajador.sueldoBase,
            "area": trabajador.area.nombre if trabajador.area else "",
            "estado": trabajador.estado,
        },
        "movimientos": movimientos,
    }


# =========================================================================
# INDICADORES DEL PANEL GENERAL DE PAGOS
# =========================================================================
def obtener_panel_general(db: Session, periodo_id: Optional[int] = None) -> PanelResumenPagos:
    # 1. Total anticipos
    stmt_ant = select(func.sum(Anticipo.importe)).where(Anticipo.estado == "PAGADO")
    if periodo_id:
        stmt_ant = stmt_ant.where(Anticipo.periodo_id == periodo_id)
    total_anticipos = db.scalar(stmt_ant) or Decimal("0.00")

    # 2. Total pagos de sueldos (pagos de liquidaciones confirmados)
    stmt_pagos = select(func.sum(PagoLiquidacion.monto)).join(Liquidacion).where(
        PagoLiquidacion.estado == "CONFIRMADO",
        Liquidacion.estado != "ANULADO",
    )
    if periodo_id:
        stmt_pagos = stmt_pagos.where(Liquidacion.periodo_id == periodo_id)
    total_sueldos_pagados = db.scalar(stmt_pagos) or Decimal("0.00")

    # 3. Conteo de liquidaciones por estado
    stmt_liq_base = select(Liquidacion).where(Liquidacion.estado != "ANULADO")
    if periodo_id:
        stmt_liq_base = stmt_liq_base.where(Liquidacion.periodo_id == periodo_id)
    liqs = db.execute(stmt_liq_base).scalars().unique().all()
    liquidaciones_por_trab = {l.trabajador_id: l for l in liqs}

    liq_pendientes = sum(1 for l in liqs if l.estado == "PENDIENTE")
    liq_parciales = sum(1 for l in liqs if l.estado == "PARCIAL")
    liq_completadas = sum(1 for l in liqs if l.estado == "LIQUIDADO")

    # 4. Trabajadores activos y balance pendiente exacto del período
    trabajadores_activos = list(
        db.execute(select(Trabajador).where(Trabajador.estado.is_(True))).scalars().unique().all()
    )
    total_activos_count = len(trabajadores_activos)

    # Anticipos por trabajador en el período
    stmt_ants_trab = select(Anticipo.trabajador_id, func.sum(Anticipo.importe)).where(
        Anticipo.estado == "PAGADO"
    )
    if periodo_id:
        stmt_ants_trab = stmt_ants_trab.where(Anticipo.periodo_id == periodo_id)
    stmt_ants_trab = stmt_ants_trab.group_by(Anticipo.trabajador_id)
    anticipos_dict = dict(db.execute(stmt_ants_trab).all())

    # Cargar detalles de planilla y descuentos para sincronización exacta
    detalles_dict = {}
    descuentos_dict = defaultdict(Decimal)
    periodo_obj = None
    if periodo_id:
        periodo_obj = db.execute(select(PeriodoSalarial).where(PeriodoSalarial.id == periodo_id)).scalars().first()
        det_list = db.execute(select(PlanillaDetalle).where(PlanillaDetalle.periodo_id == periodo_id)).scalars().unique().all()
        detalles_dict = {d.trabajador_id: d for d in det_list}
        desc_list = db.execute(select(Descuento).where(Descuento.periodo_id == periodo_id, Descuento.estado == "CONFIRMADO")).scalars().unique().all()
        for d in desc_list:
            descuentos_dict[d.trabajador_id] += d.importe

    total_dinero_pendiente = Decimal("0.00")
    trabajadores_con_pendientes_count = 0
    trabajadores_liquidados_count = 0

    for t in trabajadores_activos:
        liq = liquidaciones_por_trab.get(t.id)
        if liq:
            if liq.estado == "LIQUIDADO":
                trabajadores_liquidados_count += 1
            else:
                total_dinero_pendiente += liq.saldo_pendiente
                if liq.saldo_pendiente > 0:
                    trabajadores_con_pendientes_count += 1
        else:
            t_ants = anticipos_dict.get(t.id, Decimal("0.00"))
            t_descs = descuentos_dict.get(t.id, Decimal("0.00"))
            det = detalles_dict.get(t.id)
            if det:
                base_sal = det.total_ganado
            elif periodo_obj:
                dias = calcular_dias_trabajados_base(t, periodo_obj)
                base_sal = calcular_sueldo_proporcional(t.sueldoBase, dias)
            else:
                base_sal = t.sueldoBase
            saldo = base_sal - t_ants - t_descs
            if saldo > 0:
                total_dinero_pendiente += saldo
                trabajadores_con_pendientes_count += 1

    total_dinero_entregado = total_anticipos + total_sueldos_pagados
    periodo_completamente_liquidado = (
        total_activos_count > 0 and trabajadores_liquidados_count == total_activos_count
    )

    if periodo_completamente_liquidado:
        resumen_estado_mes = "Nómina salarial completamente liquidada. Todos los colaboradores recibieron su sueldo restante."
    elif total_dinero_entregado == Decimal("0.00"):
        resumen_estado_mes = f"Período salarial nuevo. {total_activos_count} trabajadores comienzan en cero, pendientes de adelantos o liquidación."
    else:
        resumen_estado_mes = f"{trabajadores_con_pendientes_count} de {total_activos_count} trabajadores tienen saldo pendiente por liquidar."

    return PanelResumenPagos(
        total_anticipos_mes=total_anticipos,
        total_sueldos_pagados_mes=total_sueldos_pagados,
        liquidaciones_pendientes_count=liq_pendientes,
        liquidaciones_parciales_count=liq_parciales,
        liquidaciones_completadas_count=liq_completadas,
        trabajadores_con_pendientes_count=trabajadores_con_pendientes_count,
        total_dinero_entregado=total_dinero_entregado,
        total_dinero_pendiente=total_dinero_pendiente,
        total_trabajadores_activos=total_activos_count,
        trabajadores_liquidados_count=trabajadores_liquidados_count,
        periodo_completamente_liquidado=periodo_completamente_liquidado,
        resumen_estado_mes=resumen_estado_mes,
    )


# =========================================================================
# ANULACIÓN DE MOVIMIENTOS
# =========================================================================
def anular_anticipo(db: Session, anticipo_id: int, motivo: str, usuario_ci: Optional[str] = None):
    anticipo = db.execute(select(Anticipo).where(Anticipo.id == anticipo_id)).scalars().first()
    if not anticipo:
        raise HTTPException(status_code=404, detail="Anticipo no encontrado.")
    if anticipo.estado == "ANULADO":
        raise HTTPException(status_code=400, detail="El anticipo ya se encuentra anulado.")

    anticipo.estado = "ANULADO"
    anticipo.motivo_anulacion = motivo
    db.flush()

    # Recalcular liquidación activa si existe
    liq = db.execute(
        select(Liquidacion).where(
            Liquidacion.trabajador_id == anticipo.trabajador_id,
            Liquidacion.periodo_id == anticipo.periodo_id,
            Liquidacion.estado != "ANULADO",
        )
    ).scalars().first()
    if liq:
        total_anticipos_restantes = db.scalar(
            select(func.sum(Anticipo.importe)).where(
                Anticipo.trabajador_id == anticipo.trabajador_id,
                Anticipo.periodo_id == anticipo.periodo_id,
                Anticipo.estado == "PAGADO",
            )
        ) or Decimal("0.00")
        liq.total_anticipos = total_anticipos_restantes
        liq.monto_neto = liq.sueldo_base + liq.ajustes - liq.total_anticipos
        liq.saldo_pendiente = liq.monto_neto - liq.monto_pagado
        if liq.saldo_pendiente <= 0 and liq.monto_pagado > 0:
            liq.estado = "LIQUIDADO"
        elif liq.monto_pagado > 0:
            liq.estado = "PARCIAL"
        else:
            liq.estado = "PENDIENTE"

    db.commit()

    registrar_bitacora(
        db=db,
        modulo="ANTICIPOS",
        accion="ANULAR",
        descripcion=f"Se anuló el anticipo {anticipo.numero_comprobante}. Motivo: {motivo}",
        usuario_ci=usuario_ci,
    )
    return {"mensaje": f"Anticipo {anticipo.numero_comprobante} anulado exitosamente."}


def anular_liquidacion(db: Session, liquidacion_id: int, motivo: str, usuario_ci: Optional[str] = None):
    liq = db.execute(select(Liquidacion).where(Liquidacion.id == liquidacion_id)).scalars().first()
    if not liq:
        raise HTTPException(status_code=404, detail="Liquidación no encontrada.")
    if liq.estado == "ANULADO":
        raise HTTPException(status_code=400, detail="La liquidación ya se encuentra anulada.")

    # Anular pagos asociados
    for p in liq.pagos:
        p.estado = "ANULADO"
        p.motivo_anulacion = f"Anulación de liquidación madre {liq.numero_comprobante}"

    liq.estado = "ANULADO"
    liq.motivo_anulacion = motivo
    db.commit()

    registrar_bitacora(
        db=db,
        modulo="LIQUIDACIONES",
        accion="ANULAR",
        descripcion=f"Se anuló la liquidación {liq.numero_comprobante} y sus pagos asociados. Motivo: {motivo}",
        usuario_ci=usuario_ci,
    )
    return {"mensaje": f"Liquidación {liq.numero_comprobante} anulada exitosamente."}


def anular_pago_liquidacion(db: Session, pago_id: int, motivo: str, usuario_ci: Optional[str] = None):
    pago = db.execute(select(PagoLiquidacion).where(PagoLiquidacion.id == pago_id)).scalars().first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado.")
    if pago.estado == "ANULADO":
        raise HTTPException(status_code=400, detail="El pago ya se encuentra anulado.")

    pago.estado = "ANULADO"
    pago.motivo_anulacion = motivo
    db.flush()

    liq = pago.liquidacion
    if liq and liq.estado != "ANULADO":
        pagos_activos = db.scalar(
            select(func.sum(PagoLiquidacion.monto)).where(
                PagoLiquidacion.liquidacion_id == liq.id,
                PagoLiquidacion.estado == "CONFIRMADO",
            )
        ) or Decimal("0.00")
        liq.monto_pagado = pagos_activos
        liq.saldo_pendiente = liq.monto_neto - liq.monto_pagado
        if liq.saldo_pendiente <= 0 and liq.monto_pagado > 0:
            liq.estado = "LIQUIDADO"
        elif liq.monto_pagado > 0:
            liq.estado = "PARCIAL"
        else:
            liq.estado = "PENDIENTE"

    db.commit()

    registrar_bitacora(
        db=db,
        modulo="PAGOS_LIQUIDACION",
        accion="ANULAR",
        descripcion=f"Se anuló el pago {pago.numero_comprobante}. Motivo: {motivo}",
        usuario_ci=usuario_ci,
    )
    return {"mensaje": f"Pago {pago.numero_comprobante} anulado exitosamente."}
