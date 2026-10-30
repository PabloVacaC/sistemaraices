from datetime import date
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field

# Constante de referencia para la primera quincena (configurable)
IMPORTE_REFERENCIA_QUINCENA = Decimal("1000.00")


# --- PERÍODOS SALARIALES ---
class PeriodoSalarialOut(BaseModel):
    id: int
    mes: int
    anio: int
    fecha_inicio: date
    fecha_fin: date
    fecha_pago_estimada: date
    estado: str
    descripcion: str

    class Config:
        from_attributes = True


class PeriodoSalarialCreate(BaseModel):
    mes: int = Field(..., ge=1, le=12)
    anio: int = Field(..., ge=2020, le=2100)
    fecha_inicio: date
    fecha_fin: date
    fecha_pago_estimada: date
    descripcion: str


# --- ANTICIPOS ---
class AnticipoCreate(BaseModel):
    trabajador_id: int
    periodo_id: int
    importe: Decimal = Field(..., gt=0)
    metodo_pago: str = "EFECTIVO"
    fecha_entrega: date = Field(default_factory=date.today)
    observaciones: Optional[str] = None


class AnticipoOut(BaseModel):
    id: int
    numero_comprobante: str
    trabajador_id: int
    periodo_id: int
    fecha_solicitud: date
    fecha_entrega: date
    importe: Decimal
    metodo_pago: str
    estado: str
    observaciones: Optional[str] = None
    motivo_anulacion: Optional[str] = None
    usuario_id: Optional[str] = None
    usuario_nombre: Optional[str] = None

    class Config:
        from_attributes = True


# --- PAGOS DE LIQUIDACIÓN / PAGOS PARCIALES ---
class PagoLiquidacionCreate(BaseModel):
    liquidacion_id: int
    monto: Decimal = Field(..., ge=0)
    tipo_pago: str = "PAGO_PARCIAL"  # PAGO_QUINCENA, PAGO_PARCIAL, LIQUIDACION_FINAL, REVISION_QUINCENA
    metodo_pago: str = "EFECTIVO"
    fecha_pago: date = Field(default_factory=date.today)
    observaciones: Optional[str] = None


class PagoParcialDirectoCreate(BaseModel):
    trabajador_id: int
    periodo_id: int
    monto: Decimal = Field(..., ge=0)
    tipo_pago: str = "PAGO_QUINCENA"  # PAGO_QUINCENA, PAGO_PARCIAL, REVISION_QUINCENA
    metodo_pago: str = "EFECTIVO"
    fecha_pago: date = Field(default_factory=date.today)
    observaciones: Optional[str] = None


class PagoLiquidacionOut(BaseModel):
    id: int
    numero_comprobante: str
    liquidacion_id: int
    fecha_pago: date
    monto: Decimal
    tipo_pago: str = "PAGO_PARCIAL"
    metodo_pago: str
    observaciones: Optional[str] = None
    estado: str
    motivo_anulacion: Optional[str] = None
    usuario_id: Optional[str] = None
    usuario_nombre: Optional[str] = None

    class Config:
        from_attributes = True


# --- LIQUIDACIONES ---
class LiquidacionCreate(BaseModel):
    trabajador_id: int
    periodo_id: int
    fecha_liquidacion: date = Field(default_factory=date.today)
    ajustes: Decimal = Decimal("0.00")
    observaciones: Optional[str] = None
    # Si desea registrar un pago inmediato al crear la liquidación:
    pago_inmediato: bool = False
    monto_pago_inmediato: Optional[Decimal] = None
    metodo_pago_inmediato: str = "EFECTIVO"


class LiquidacionOut(BaseModel):
    id: int
    numero_comprobante: str
    trabajador_id: int
    periodo_id: int
    fecha_liquidacion: date
    sueldo_base: Decimal
    ajustes: Decimal
    total_anticipos: Decimal
    monto_neto: Decimal
    monto_pagado: Decimal
    saldo_pendiente: Decimal
    estado: str
    observaciones: Optional[str] = None
    motivo_anulacion: Optional[str] = None
    usuario_id: Optional[str] = None
    usuario_nombre: Optional[str] = None
    pago_inmediato_monto: Optional[Decimal] = None
    pago_inmediato_comprobante: Optional[str] = None
    total_pagos_previos: Optional[Decimal] = Decimal("0.00")
    pago_quincena_previo: Optional[Decimal] = Decimal("0.00")
    pagos: List[PagoLiquidacionOut] = []

    class Config:
        from_attributes = True


# --- RESUMEN SALARIAL DEL TRABAJADOR ---
class ResumenSalarialTrabajador(BaseModel):
    trabajador_id: int
    nombre_completo: str
    ci: Optional[str] = None
    cargo: str
    area: str
    sueldo_base: Decimal
    periodo_id: int
    periodo_descripcion: str
    quincena_referencia: Decimal = IMPORTE_REFERENCIA_QUINCENA
    anticipos: List[AnticipoOut] = []
    total_anticipos: Decimal
    anticipos_antes_dia_18: Decimal = Decimal("0.00")
    diferencia_quincena: Decimal = Decimal("0.00")
    monto_sugerido_quincena: Decimal = Decimal("0.00")
    pago_quincena_realizado: Decimal = Decimal("0.00")
    quincena_pagada: bool = False
    anticipos_posteriores_dia_18: Decimal = Decimal("0.00")
    total_pagos_parciales: Decimal = Decimal("0.00")
    saldo_salarial_pendiente: Decimal = Decimal("0.00")
    supera_quincena: bool = False
    excedente_quincena: Decimal = Decimal("0.00")
    fecha_ultimo_anticipo: Optional[date] = None
    liquidacion: Optional[LiquidacionOut] = None
    total_pagos_anteriores: Decimal
    saldo_pendiente_liquidacion: Decimal
    estado_liquidacion: str


# --- RESUMEN DE PAGOS PARCIALES POR TRABAJADOR (TABLA PAGOS PARCIALES) ---
class ResumenTrabajadorPagosParcialesOut(BaseModel):
    trabajador_id: int
    nombre_completo: str
    ci: Optional[str] = None
    cargo: str
    area: str
    sueldo_base: Decimal
    quincena_referencia: Decimal = IMPORTE_REFERENCIA_QUINCENA
    anticipos_antes_dia_18: Decimal
    diferencia_quincena: Decimal
    pago_quincena_realizado: Decimal
    quincena_pagada: bool = False
    anticipos_posteriores_dia_18: Decimal
    total_anticipos_periodo: Decimal
    total_pagos_parciales: Decimal
    saldo_salarial_pendiente: Decimal
    estado_periodo: str
    supera_quincena: bool
    excedente_quincena: Decimal
    monto_sugerido_quincena: Decimal
    fecha_ultimo_anticipo: Optional[date] = None
    liquidacion_id: Optional[int] = None
    liquidacion_comprobante: Optional[str] = None


# --- COMPROBANTE DETALLADO HISTÓRICO DE ANTICIPO ---
class ComprobanteAnticipoDetalladoOut(BaseModel):
    empresa_nombre: str = "SISTEMAS RAÍCES"
    numero_comprobante: str
    trabajador_id: int
    trabajador_nombre: str
    trabajador_ci: Optional[str] = None
    trabajador_cargo: Optional[str] = None
    trabajador_area: Optional[str] = None
    periodo_id: int
    periodo_descripcion: str
    fecha_anticipo: date
    importe_actual: Decimal
    metodo_entrega: str
    usuario_nombre: Optional[str] = None
    usuario_ci: Optional[str] = None
    motivo: Optional[str] = None
    total_anticipos_anteriores: Decimal
    anticipos_historicos: List[AnticipoOut] = []
    anticipos_periodo: List[AnticipoOut] = []
    total_acumulado: Decimal
    sueldo_base: Decimal
    quincena_referencia: Decimal = IMPORTE_REFERENCIA_QUINCENA
    diferencia_quincena: Decimal
    saldo_salarial_estimado: Decimal
    supera_quincena: bool = False
    excedente_quincena: Decimal = Decimal("0.00")
    quincena_pagada: bool = False
    estado_quincena: str = "PENDIENTE"
    pago_quincena_realizado: Optional[Decimal] = Decimal("0.00")
    total_pagos_realizados: Optional[Decimal] = Decimal("0.00")


# --- INDICADORES DEL PANEL GENERAL ---
class PanelResumenPagos(BaseModel):
    total_anticipos_mes: Decimal
    total_sueldos_pagados_mes: Decimal
    liquidaciones_pendientes_count: int
    liquidaciones_parciales_count: int
    liquidaciones_completadas_count: int
    trabajadores_con_pendientes_count: int
    total_dinero_entregado: Decimal
    total_dinero_pendiente: Decimal
    total_trabajadores_activos: int = 0
    trabajadores_liquidados_count: int = 0
    periodo_completamente_liquidado: bool = False
    resumen_estado_mes: str = ""


# --- ANULACIÓN ---
class AnulacionRequest(BaseModel):
    motivo: str = Field(..., min_length=3)
