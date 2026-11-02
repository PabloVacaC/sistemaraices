from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


# --- DESCUENTOS SALARIALES DINÁMICOS ---
class DescuentoCreate(BaseModel):
    trabajador_id: int
    periodo_id: int
    fecha: date = Field(default_factory=date.today)
    importe: Decimal = Field(..., gt=0, description="Monto en bolivianos del descuento")
    concepto: str = Field(..., min_length=2, max_length=150, description="Concepto o motivo del descuento")
    observaciones: Optional[str] = None


class DescuentoOut(BaseModel):
    id: int
    numero_comprobante: str
    trabajador_id: int
    trabajador_nombre: Optional[str] = None
    periodo_id: int
    fecha: date
    importe: Decimal
    concepto: str
    observaciones: Optional[str] = None
    estado: str
    usuario_id: Optional[str] = None
    usuario_nombre: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# --- AJUSTE MANUAL DE DÍAS TRABAJADOS ---
class ActualizarDiasTrabajadosIn(BaseModel):
    trabajador_id: int
    periodo_id: int
    dias_trabajados: int = Field(..., ge=0, le=30, description="Días trabajados computables (0 a 30)")
    observaciones: Optional[str] = None


# --- FILA DE LA PLANILLA (13 COLUMNAS EXACTAS DE RF-9) ---
class PlanillaFilaOut(BaseModel):
    # Col 1: Numeración consecutiva visual
    nro: int
    # Identificadores del trabajador
    trabajador_id: int
    # Col 2: Nombre completo
    nombre_completo: str
    ci: Optional[str] = None
    # Col 3: Cargo
    cargo: str
    # Col 4: Área
    area: str
    # Col 5: Fecha de ingreso
    fecha_ingreso: date
    # Col 6: Haber básico histórico del período
    haber_basico: Decimal
    # Col 7: Días trabajados del período (0..30)
    dias_trabajados: int
    dias_manual: bool = False
    # Col 8: Total ganado = (Haber básico / 30) * Días trabajados
    total_ganado: Decimal
    # Col 9: Pago de quincena
    pago_quincena: Decimal
    estado_quincena: str  # LIQUIDADA, PENDIENTE
    quincena_sugerida: Decimal
    supera_quincena: bool = False
    excedente_quincena: Decimal = Decimal("0.00")
    quincena_referencia: Decimal = Decimal("1000.00")
    anticipos_antes_dia_18: Decimal = Decimal("0.00")
    diferencia_quincena: Decimal = Decimal("0.00")
    # Col 10: Pago de anticipos válidos del período
    pago_anticipos: Decimal
    anticipos_count: int = 0
    # Desglose de anticipos por ciclo salarial (spec.md)
    reposicion_ebert: Decimal = Decimal("0.00")
    reposicion_antes_sueldo: Decimal = Decimal("0.00")
    # Desglose de Descuentos
    total_descuentos: Decimal = Decimal("0.00")
    descuentos_count: int = 0
    # Col 11: Total de anticipos y descuentos = Pago Anticipos + Total Descuentos
    total_anticipos_descuentos: Decimal
    # Col 12: Anticipos para el período siguiente (días 1 al 5)
    anticipos_periodo_siguiente: Decimal = Decimal("0.00")
    # Col 13: Líquido pagable = Total ganado - Total anticipos y descuentos - Pago quincena
    liquido_pagable: Decimal
    # Campos de gestión y auditoría
    monto_pagado_total: Decimal = Decimal("0.00")
    saldo_pendiente_real: Decimal = Decimal("0.00")
    estado_liquidacion: str = "PENDIENTE"  # PENDIENTE, PARCIAL, LIQUIDADO
    liquidacion_id: Optional[int] = None
    liquidacion_comprobante: Optional[str] = None
    pago_liquidacion: Decimal = Decimal("0.00")
    fecha_liquidacion: Optional[date] = None
    liquidacion_metodo_pago: Optional[str] = None
    liquidacion_observaciones: Optional[str] = None
    liquidacion_ajustes: Decimal = Decimal("0.00")
    liquidacion_usuario_id: Optional[str] = None


class PlanillaResumenTotales(BaseModel):
    total_haber_basico: Decimal
    total_ganado: Decimal
    total_quincena: Decimal
    total_anticipos: Decimal
    total_descuentos: Decimal
    total_anticipos_descuentos: Decimal
    total_anticipos_periodo_siguiente: Decimal
    total_liquido_pagable: Decimal
    total_trabajadores: int
    trabajadores_liquidados: int
    trabajadores_pendientes: int
    # 8 Indicadores Clave de Ciclo Salarial (spec.md)
    reposicion_ebert: Decimal = Decimal("0.00")
    solicitud_quincena: Decimal = Decimal("0.00")
    reposicion_antes_sueldo: Decimal = Decimal("0.00")
    liquido_sueldo: Decimal = Decimal("0.00")
    solicitud_sueldo: Decimal = Decimal("0.00")
    solicitud_total_mes: Decimal = Decimal("0.00")
    total_saldo_pendiente: Decimal = Decimal("0.00")


class PlanillaCierreOut(BaseModel):
    id: int
    periodo_id: int
    entregado_quincena: Decimal
    solicitud_quincena: Decimal
    diferencia_quincena: Decimal
    entregado_sueldo: Decimal
    solicitud_sueldo: Decimal
    diferencia_sueldo: Decimal
    otros_gastos: Decimal
    otros_gastos_detalle: Optional[str] = None
    total_diferencia: Decimal
    observaciones: Optional[str] = None
    usuario_ci: Optional[str] = None
    usuario_nombre: Optional[str] = None
    fecha_cierre: datetime

    class Config:
        from_attributes = True


class PlanillaMensualOut(BaseModel):
    periodo_id: int
    periodo_descripcion: str
    mes: int
    anio: int
    fecha_inicio: date
    fecha_fin: date
    fecha_pago_estimada: Optional[date] = None
    fecha_limite_pago: Optional[date] = None
    estado_periodo: str  # ABIERTO, CERRADO
    filas: List[PlanillaFilaOut]
    totales: PlanillaResumenTotales
    cierre: Optional[PlanillaCierreOut] = None


class CerrarPlanillaRequest(BaseModel):
    observaciones: Optional[str] = None
    confirmar_pendientes: bool = False
    entregado_quincena: Decimal = Decimal("0.00")
    solicitud_quincena: Decimal = Decimal("0.00")
    entregado_sueldo: Decimal = Decimal("0.00")
    solicitud_sueldo: Decimal = Decimal("0.00")
    otros_gastos: Decimal = Decimal("0.00")
    otros_gastos_detalle: Optional[str] = None

