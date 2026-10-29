from datetime import date, datetime
import calendar
from typing import List, Optional, Dict, Any
from decimal import Decimal
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_

from app.models.entities import (
    Trabajador,
    Area,
    PeriodoSalarial,
    Anticipo,
    Liquidacion,
    PagoLiquidacion,
    Almacen,
    CompraAlmacen,
    GastoMenor,
)
from app.modules.contabilidad.schemas import (
    ResumenContableKPIs,
    DesglosePorArea,
    MovimientoContable,
    ContabilidadReporteMensual,
    MesComparativoAnual,
    ContabilidadReporteAnual,
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


def obtener_anios_disponibles(db: Session) -> List[int]:
    """Obtiene rápidamente los años con actividad financiera usando índices B-tree"""
    anios_set = {date.today().year}

    # Períodos salariales
    periodos = db.execute(select(PeriodoSalarial.anio).distinct()).scalars().all()
    anios_set.update(p for p in periodos if p)

    # Compras (Index Scan en fecha_compra)
    min_compra = db.scalar(select(func.min(CompraAlmacen.fecha_compra)))
    max_compra = db.scalar(select(func.max(CompraAlmacen.fecha_compra)))
    if min_compra and max_compra:
        for y in range(min_compra.year, max_compra.year + 1):
            anios_set.add(y)

    # Gastos menores (Index Scan en fecha_gasto)
    min_gasto = db.scalar(select(func.min(GastoMenor.fecha_gasto)))
    max_gasto = db.scalar(select(func.max(GastoMenor.fecha_gasto)))
    if min_gasto and max_gasto:
        for y in range(min_gasto.year, max_gasto.year + 1):
            anios_set.add(y)

    return sorted(list(anios_set), reverse=True)


def obtener_reporte_contable_mensual(
    db: Session, mes: int, anio: int, area_id: Optional[int] = None
) -> ContabilidadReporteMensual:
    """Genera la consolidación contable total de un mes específico con proyecciones SQL directas de alto rendimiento"""
    last_day = calendar.monthrange(anio, mes)[1]
    start_date = date(anio, mes, 1)
    end_date = date(anio, mes, last_day)

    # 1. Diccionario de Áreas registradas
    areas = db.execute(select(Area.id, Area.nombre)).all()
    areas_dict = {a.id: a.nombre for a in areas}

    # 2. Consultar Anticipos del mes (Proyección de columnas directas)
    stmt_ant = (
        select(
            Anticipo.id,
            Anticipo.numero_comprobante,
            Anticipo.fecha_entrega,
            Anticipo.importe,
            Anticipo.metodo_pago,
            Anticipo.observaciones,
            Anticipo.usuario_id,
            Trabajador.area_id,
            Trabajador.nombres,
            Trabajador.apellidos,
            Area.nombre.label("area_nombre"),
        )
        .join(Trabajador, Anticipo.trabajador_id == Trabajador.id)
        .outerjoin(Area, Trabajador.area_id == Area.id)
        .where(
            Anticipo.estado == "PAGADO",
            Anticipo.fecha_entrega >= start_date,
            Anticipo.fecha_entrega <= end_date,
        )
    )
    if area_id is not None:
        stmt_ant = stmt_ant.where(Trabajador.area_id == area_id)
    anticipos = db.execute(stmt_ant).all()

    # 3. Consultar Pagos de Sueldo / Liquidación del mes
    stmt_pagos = (
        select(
            PagoLiquidacion.id,
            PagoLiquidacion.numero_comprobante,
            PagoLiquidacion.fecha_pago,
            PagoLiquidacion.monto,
            PagoLiquidacion.tipo_pago,
            PagoLiquidacion.metodo_pago,
            PagoLiquidacion.observaciones,
            PagoLiquidacion.usuario_id,
            Trabajador.area_id,
            Trabajador.nombres,
            Trabajador.apellidos,
            Area.nombre.label("area_nombre"),
        )
        .join(Liquidacion, PagoLiquidacion.liquidacion_id == Liquidacion.id)
        .join(Trabajador, Liquidacion.trabajador_id == Trabajador.id)
        .outerjoin(Area, Trabajador.area_id == Area.id)
        .where(
            PagoLiquidacion.estado == "CONFIRMADO",
            Liquidacion.estado != "ANULADO",
            PagoLiquidacion.fecha_pago >= start_date,
            PagoLiquidacion.fecha_pago <= end_date,
        )
    )
    if area_id is not None:
        stmt_pagos = stmt_pagos.where(Trabajador.area_id == area_id)
    pagos_sueldos = db.execute(stmt_pagos).all()

    # 4. Consultar Compras de Almacén del mes (Sin cascadas innecesarias)
    stmt_compras = (
        select(
            CompraAlmacen.id,
            CompraAlmacen.numero_comprobante,
            CompraAlmacen.fecha_compra,
            CompraAlmacen.precio_total,
            CompraAlmacen.proveedor,
            CompraAlmacen.observaciones,
            CompraAlmacen.usuario_registro_ci,
            Almacen.nombre.label("producto_nombre"),
        )
        .join(Almacen, CompraAlmacen.almacen_id == Almacen.id)
        .where(
            CompraAlmacen.estado == "COMPLETADO",
            CompraAlmacen.fecha_compra >= start_date,
            CompraAlmacen.fecha_compra <= end_date,
        )
    )
    compras = db.execute(stmt_compras).all()
    if area_id is not None:
        area_obj = areas_dict.get(area_id, "").lower()
        if "almacen" not in area_obj and "administra" not in area_obj and "general" not in area_obj:
            compras = []

    # 5. Consultar Gastos Menores del mes
    stmt_gastos = (
        select(
            GastoMenor.id,
            GastoMenor.numero_comprobante,
            GastoMenor.fecha_gasto,
            GastoMenor.importe_total,
            GastoMenor.nombre,
            GastoMenor.metodo_pago,
            GastoMenor.descripcion,
            GastoMenor.proveedor,
            GastoMenor.usuario_registro_ci,
            GastoMenor.area_id,
            Area.nombre.label("area_nombre"),
        )
        .outerjoin(Area, GastoMenor.area_id == Area.id)
        .where(
            GastoMenor.estado.in_(["APROBADO", "REGISTRADO"]),
            GastoMenor.fecha_gasto >= start_date,
            GastoMenor.fecha_gasto <= end_date,
        )
    )
    if area_id is not None:
        stmt_gastos = stmt_gastos.where(GastoMenor.area_id == area_id)
    gastos_menores = db.execute(stmt_gastos).all()

    # --- CÁLCULOS DE TOTALES ---
    total_anticipos = sum((a.importe for a in anticipos), Decimal("0.00"))
    total_sueldos = sum((p.monto for p in pagos_sueldos), Decimal("0.00"))
    total_nomina = total_anticipos + total_sueldos
    total_compras = sum((c.precio_total for c in compras), Decimal("0.00"))
    total_gastos = sum((g.importe_total for g in gastos_menores), Decimal("0.00"))

    total_egresos = total_nomina + total_compras + total_gastos

    # Compromisos pendientes del período
    stmt_pendientes = (
        select(func.sum(Liquidacion.saldo_pendiente))
        .join(PeriodoSalarial, Liquidacion.periodo_id == PeriodoSalarial.id)
        .where(
            PeriodoSalarial.mes == mes,
            PeriodoSalarial.anio == anio,
            Liquidacion.estado.in_(["PENDIENTE", "PARCIAL"]),
        )
    )
    total_compromisos_pendientes = db.scalar(stmt_pendientes) or Decimal("0.00")

    cantidad_transacciones = len(anticipos) + len(pagos_sueldos) + len(compras) + len(gastos_menores)
    promedio_diario = (total_egresos / Decimal(last_day)).quantize(Decimal("0.01")) if last_day > 0 else Decimal("0.00")

    kpis = ResumenContableKPIs(
        total_egresos_global=total_egresos,
        total_nomina_pagada=total_nomina,
        total_anticipos_pagados=total_anticipos,
        total_sueldos_pagados=total_sueldos,
        total_compras_inventario=total_compras,
        total_gastos_menores=total_gastos,
        total_compromisos_pendientes=total_compromisos_pendientes,
        cantidad_transacciones=cantidad_transacciones,
        promedio_diario_egresos=promedio_diario,
    )

    # --- MÉTODOS DE PAGO RESUMEN ---
    metodos_pago = defaultdict(lambda: Decimal("0.00"))
    for a in anticipos:
        metodos_pago[a.metodo_pago or "EFECTIVO"] += a.importe
    for p in pagos_sueldos:
        metodos_pago[p.metodo_pago or "EFECTIVO"] += p.monto
    for g in gastos_menores:
        metodos_pago[g.metodo_pago or "EFECTIVO"] += g.importe_total
    for c in compras:
        metodos_pago["TRANSFERENCIA/CHEQUE"] += c.precio_total

    # --- DESGLOSE POR ÁREA / CENTRO DE COSTOS ---
    area_nomina = defaultdict(lambda: Decimal("0.00"))
    area_gastos = defaultdict(lambda: Decimal("0.00"))
    area_compras = defaultdict(lambda: Decimal("0.00"))

    for a in anticipos:
        area_nomina[a.area_id] += a.importe

    for p in pagos_sueldos:
        area_nomina[p.area_id] += p.monto

    for g in gastos_menores:
        area_gastos[g.area_id] += g.importe_total

    if compras:
        admin_area_id = next(
            (aid for aid, name in areas_dict.items() if "admin" in name.lower() or "direc" in name.lower()),
            None
        )
        area_compras[admin_area_id] += total_compras

    todas_areas_ids = set(areas_dict.keys())
    todas_areas_ids.update(area_nomina.keys())
    todas_areas_ids.update(area_gastos.keys())
    todas_areas_ids.update(area_compras.keys())

    desglose_areas = []
    for aid in todas_areas_ids:
        anom = area_nomina[aid]
        agas = area_gastos[aid]
        acom = area_compras[aid]
        atotal = anom + agas + acom
        if atotal > 0:
            porc = float((atotal / total_egresos * Decimal(100)).quantize(Decimal("0.1"))) if total_egresos > 0 else 0.0
            desglose_areas.append(
                DesglosePorArea(
                    area_id=aid,
                    area_nombre=areas_dict.get(aid, "General / Sin Área"),
                    total_nomina=anom,
                    total_gastos_menores=agas,
                    total_compras=acom,
                    total_egresos=atotal,
                    porcentaje=porc,
                )
            )

    desglose_areas.sort(key=lambda x: x.total_egresos, reverse=True)

    # --- LISTA UNIFICADA DE MOVIMIENTOS CONTABLES ---
    movimientos: List[MovimientoContable] = []

    for a in anticipos:
        trab_nom = f"{a.nombres} {a.apellidos}".strip() if a.nombres else "Trabajador"
        movimientos.append(
            MovimientoContable(
                id=f"ANT-{a.id}",
                fecha=a.fecha_entrega,
                tipo_categoria="NOMINA_ANTICIPO",
                tipo_label="Anticipo Salarial",
                numero_comprobante=a.numero_comprobante,
                beneficiario_proveedor=trab_nom,
                concepto=f"Adelanto de sueldo: {a.observaciones or 'Gastos personales'}",
                area_nombre=a.area_nombre or "General",
                metodo_pago=a.metodo_pago or "EFECTIVO",
                monto=a.importe,
                usuario_registro_ci=a.usuario_id,
            )
        )

    for p in pagos_sueldos:
        trab_nom = f"{p.nombres} {p.apellidos}".strip() if p.nombres else "Trabajador"
        label_tipo = "Liquidación de Sueldo" if p.tipo_pago == "LIQUIDACION_FINAL" else "Pago de Quincena"
        movimientos.append(
            MovimientoContable(
                id=f"PAG-{p.id}",
                fecha=p.fecha_pago,
                tipo_categoria="NOMINA_SUELDO",
                tipo_label=label_tipo,
                numero_comprobante=p.numero_comprobante,
                beneficiario_proveedor=trab_nom,
                concepto=f"Pago de nómina ({p.tipo_pago}): {p.observaciones or 'Sueldo cancelado'}",
                area_nombre=p.area_nombre or "General",
                metodo_pago=p.metodo_pago or "EFECTIVO",
                monto=p.monto,
                usuario_registro_ci=p.usuario_id,
            )
        )

    for c in compras:
        movimientos.append(
            MovimientoContable(
                id=f"CMP-{c.id}",
                fecha=c.fecha_compra,
                tipo_categoria="COMPRA_INVENTARIO",
                tipo_label="Compra de Insumo / Almacén",
                numero_comprobante=c.numero_comprobante,
                beneficiario_proveedor=c.proveedor or "Proveedor Comercial",
                concepto=f"Adquisición para inventario: {c.producto_nombre}. {c.observaciones or ''}".strip(),
                area_nombre="Almacén Central / Administración",
                metodo_pago="TRANSFERENCIA/CHEQUE",
                monto=c.precio_total,
                usuario_registro_ci=c.usuario_registro_ci,
            )
        )

    for g in gastos_menores:
        movimientos.append(
            MovimientoContable(
                id=f"GAS-{g.id}",
                fecha=g.fecha_gasto,
                tipo_categoria="GASTO_OPERATIVO",
                tipo_label="Gasto Menor / Operativo",
                numero_comprobante=g.numero_comprobante,
                beneficiario_proveedor=g.proveedor or "Caja Chica / Operaciones",
                concepto=f"{g.nombre}: {g.descripcion or 'Gasto operativo autorizado'}",
                area_nombre=g.area_nombre or "General",
                metodo_pago=g.metodo_pago or "EFECTIVO",
                monto=g.importe_total,
                usuario_registro_ci=g.usuario_registro_ci,
            )
        )

    # Orden cronológico descendente (lo más reciente primero)
    movimientos.sort(key=lambda x: str(x.fecha), reverse=True)

    mes_nombre = MESES_ESPANOL.get(mes, f"Mes {mes}")
    rango_fechas = f"01/{mes:02d}/{anio} al {last_day:02d}/{mes:02d}/{anio}"

    return ContabilidadReporteMensual(
        mes=mes,
        anio=anio,
        mes_nombre=mes_nombre,
        rango_fechas=rango_fechas,
        kpis=kpis,
        desglose_areas=desglose_areas,
        movimientos=movimientos,
        metodos_pago_resumen=dict(metodos_pago),
    )


def obtener_reporte_contable_anual(
    db: Session, anio: int, area_id: Optional[int] = None
) -> ContabilidadReporteAnual:
    """Consolida la contabilidad completa anual en solo 4 consultas directas optimizadas"""
    start_year = date(anio, 1, 1)
    end_year = date(anio, 12, 31)

    # 1. Áreas
    areas = db.execute(select(Area.id, Area.nombre)).all()
    areas_dict = {a.id: a.nombre for a in areas}

    # 2. Consultas anuales unificadas
    stmt_ant = (
        select(Anticipo.importe, Anticipo.fecha_entrega, Anticipo.metodo_pago, Trabajador.area_id)
        .join(Trabajador, Anticipo.trabajador_id == Trabajador.id)
        .where(
            Anticipo.estado == "PAGADO",
            Anticipo.fecha_entrega >= start_year,
            Anticipo.fecha_entrega <= end_year,
        )
    )
    if area_id is not None:
        stmt_ant = stmt_ant.where(Trabajador.area_id == area_id)
    anticipos = db.execute(stmt_ant).all()

    stmt_pagos = (
        select(PagoLiquidacion.monto, PagoLiquidacion.fecha_pago, PagoLiquidacion.metodo_pago, Trabajador.area_id)
        .join(Liquidacion, PagoLiquidacion.liquidacion_id == Liquidacion.id)
        .join(Trabajador, Liquidacion.trabajador_id == Trabajador.id)
        .where(
            PagoLiquidacion.estado == "CONFIRMADO",
            Liquidacion.estado != "ANULADO",
            PagoLiquidacion.fecha_pago >= start_year,
            PagoLiquidacion.fecha_pago <= end_year,
        )
    )
    if area_id is not None:
        stmt_pagos = stmt_pagos.where(Trabajador.area_id == area_id)
    pagos_sueldos = db.execute(stmt_pagos).all()

    stmt_compras = (
        select(CompraAlmacen.precio_total, CompraAlmacen.fecha_compra)
        .where(
            CompraAlmacen.estado == "COMPLETADO",
            CompraAlmacen.fecha_compra >= start_year,
            CompraAlmacen.fecha_compra <= end_year,
        )
    )
    compras = db.execute(stmt_compras).all()
    if area_id is not None:
        area_obj = areas_dict.get(area_id, "").lower()
        if "almacen" not in area_obj and "administra" not in area_obj and "general" not in area_obj:
            compras = []

    stmt_gastos = (
        select(GastoMenor.importe_total, GastoMenor.fecha_gasto, GastoMenor.metodo_pago, GastoMenor.area_id)
        .where(
            GastoMenor.estado.in_(["APROBADO", "REGISTRADO"]),
            GastoMenor.fecha_gasto >= start_year,
            GastoMenor.fecha_gasto <= end_year,
        )
    )
    if area_id is not None:
        stmt_gastos = stmt_gastos.where(GastoMenor.area_id == area_id)
    gastos_menores = db.execute(stmt_gastos).all()

    # --- AGREGACIÓN EN MEMORIA POR MES (1 AL 12) ---
    mes_nomina = defaultdict(lambda: Decimal("0.00"))
    mes_anticipos = defaultdict(lambda: Decimal("0.00"))
    mes_sueldos = defaultdict(lambda: Decimal("0.00"))
    mes_compras = defaultdict(lambda: Decimal("0.00"))
    mes_gastos = defaultdict(lambda: Decimal("0.00"))

    metodos_pago_anual = defaultdict(lambda: Decimal("0.00"))
    areas_anual = defaultdict(lambda: {"nomina": Decimal("0.00"), "gastos": Decimal("0.00"), "compras": Decimal("0.00"), "nombre": ""})

    for a in anticipos:
        m = a.fecha_entrega.month
        mes_nomina[m] += a.importe
        mes_anticipos[m] += a.importe
        metodos_pago_anual[a.metodo_pago or "EFECTIVO"] += a.importe
        areas_anual[a.area_id]["nomina"] += a.importe

    for p in pagos_sueldos:
        m = p.fecha_pago.month
        mes_nomina[m] += p.monto
        mes_sueldos[m] += p.monto
        metodos_pago_anual[p.metodo_pago or "EFECTIVO"] += p.monto
        areas_anual[p.area_id]["nomina"] += p.monto

    for c in compras:
        m = c.fecha_compra.month
        mes_compras[m] += c.precio_total
        metodos_pago_anual["TRANSFERENCIA/CHEQUE"] += c.precio_total

    for g in gastos_menores:
        m = g.fecha_gasto.month
        mes_gastos[m] += g.importe_total
        metodos_pago_anual[g.metodo_pago or "EFECTIVO"] += g.importe_total
        areas_anual[g.area_id]["gastos"] += g.importe_total

    # Asignar compras a Administración/General
    total_compras_anual = sum(mes_compras.values(), Decimal("0.00"))
    if total_compras_anual > 0:
        admin_area_id = next(
            (aid for aid, name in areas_dict.items() if "admin" in name.lower() or "direc" in name.lower()),
            None
        )
        areas_anual[admin_area_id]["compras"] += total_compras_anual

    # Construir listado de los 12 meses
    meses_comparativo: List[MesComparativoAnual] = []
    total_nomina_anual = Decimal("0.00")
    total_anticipos_anual = Decimal("0.00")
    total_sueldos_anual = Decimal("0.00")
    total_gastos_anual = Decimal("0.00")

    for m in range(1, 13):
        nom = mes_nomina[m]
        com = mes_compras[m]
        gas = mes_gastos[m]
        tot = nom + com + gas
        meses_comparativo.append(
            MesComparativoAnual(
                mes=m,
                mes_nombre=MESES_ESPANOL.get(m, f"Mes {m}"),
                total_nomina=nom,
                total_compras=com,
                total_gastos=gas,
                total_global=tot,
            )
        )
        total_nomina_anual += nom
        total_anticipos_anual += mes_anticipos[m]
        total_sueldos_anual += mes_sueldos[m]
        total_gastos_anual += gas

    total_egresos_anual = total_nomina_anual + total_compras_anual + total_gastos_anual
    cantidad_transacciones_anual = len(anticipos) + len(pagos_sueldos) + len(compras) + len(gastos_menores)
    promedio_diario = (total_egresos_anual / Decimal(365)).quantize(Decimal("0.01")) if total_egresos_anual > 0 else Decimal("0.00")

    kpis_anual = ResumenContableKPIs(
        total_egresos_global=total_egresos_anual,
        total_nomina_pagada=total_nomina_anual,
        total_anticipos_pagados=total_anticipos_anual,
        total_sueldos_pagados=total_sueldos_anual,
        total_compras_inventario=total_compras_anual,
        total_gastos_menores=total_gastos_anual,
        total_compromisos_pendientes=Decimal("0.00"),
        cantidad_transacciones=cantidad_transacciones_anual,
        promedio_diario_egresos=promedio_diario,
    )

    # Desglose por áreas anual
    desglose_areas_anual = []
    for aid, vals in areas_anual.items():
        tot = vals["nomina"] + vals["gastos"] + vals["compras"]
        if tot > 0:
            porc = float((tot / total_egresos_anual * Decimal(100)).quantize(Decimal("0.1"))) if total_egresos_anual > 0 else 0.0
            desglose_areas_anual.append(
                DesglosePorArea(
                    area_id=aid,
                    area_nombre=areas_dict.get(aid, "General / Sin Área"),
                    total_nomina=vals["nomina"],
                    total_gastos_menores=vals["gastos"],
                    total_compras=vals["compras"],
                    total_egresos=tot,
                    porcentaje=porc,
                )
            )

    desglose_areas_anual.sort(key=lambda x: x.total_egresos, reverse=True)

    return ContabilidadReporteAnual(
        anio=anio,
        kpis=kpis_anual,
        meses=meses_comparativo,
        desglose_areas=desglose_areas_anual,
        metodos_pago_resumen=dict(metodos_pago_anual),
    )
