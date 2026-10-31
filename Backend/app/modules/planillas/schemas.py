from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class PlanillaItemOut(BaseModel):
    trabajador_id: int
    ci: Optional[str] = None
    nombre_completo: str
    cargo: str
    area: str
    fecha_ingreso: Optional[date] = None
    estado_trabajador: bool = True

    # Valores económicos del período
    sueldo_base: Decimal = Decimal("0.00")
    dias_trabajados: int = 30
    total_ganado: Decimal = Decimal("0.00")  # (sueldo_base / 30) * dias_trabajados
    anticipos_antes_18: Decimal = Decimal("0.00")
    pago_quincena: Decimal = Decimal("0.00")
    anticipos_post_18: Decimal = Decimal("0.00")
    total_anticipos: Decimal = Decimal("0.00")
    anticipos_siguiente_periodo: Decimal = Decimal("0.00")  # Entregados entre día 1 y 5 del mes siguiente
    ajustes: Decimal = Decimal("0.00")
    total_ganado_bruto: Decimal = Decimal("0.00")  # total_ganado + ajustes
    liquido_pagable: Decimal = Decimal("0.00")     # total_ganado + ajustes - total_anticipos (puede ser negativo)
    total_pagado: Decimal = Decimal("0.00")        # suma de pagos recibidos
    saldo_pendiente: Decimal = Decimal("0.00")     # liquido_pagable - total_pagado (puede ser negativo)
    es_saldo_negativo: bool = False                # Indicador de saldo por regularizar

    # Estado y trazabilidad
    estado_pago: str = "PENDIENTE"  # LIQUIDADO, PARCIAL, PENDIENTE, SIN_MOVIMIENTOS
    quincena_liquidada: bool = False
    liquidacion_id: Optional[int] = None
    numero_comprobante_liq: Optional[str] = None
    observaciones: Optional[str] = None


class PlanillaPeriodoHeaderOut(BaseModel):
    id: int
    mes: int
    anio: int
    descripcion: str
    fecha_inicio: date
    fecha_fin: date
    fecha_pago_estimada: date
    estado: str  # ABIERTO, CERRADO
    fecha_cierre: Optional[datetime] = None
    cerrado_por: Optional[str] = None
    cerrado_por_nombre: Optional[str] = None
    observaciones_cierre: Optional[str] = None


class PlanillaResumenOut(BaseModel):
    periodo: PlanillaPeriodoHeaderOut

    # Totales consolidados de la planilla
    total_trabajadores: int = 0
    total_sueldo_base: Decimal = Decimal("0.00")
    total_ganado: Decimal = Decimal("0.00")
    total_anticipos_antes_18: Decimal = Decimal("0.00")
    total_anticipos_post_18: Decimal = Decimal("0.00")
    total_anticipos: Decimal = Decimal("0.00")
    total_anticipos_siguiente_periodo: Decimal = Decimal("0.00")
    total_pagos_quincena: Decimal = Decimal("0.00")
    total_ajustes: Decimal = Decimal("0.00")
    total_ganado_bruto: Decimal = Decimal("0.00")
    total_liquido_pagable: Decimal = Decimal("0.00")
    total_pagado: Decimal = Decimal("0.00")
    total_saldo_pendiente: Decimal = Decimal("0.00")

    # Contadores de estado
    trabajadores_liquidados: int = 0
    trabajadores_parciales: int = 0
    trabajadores_pendientes: int = 0

    # Estado operativo
    es_cerrable: bool = True
    advertencias_cierre: List[str] = []

    # Lista detallada de trabajadores en la planilla
    items: List[PlanillaItemOut] = []


class ActualizarDiasTrabajadosRequest(BaseModel):
    dias_trabajados: int = Field(..., ge=1, le=30, description="Días efectivamente trabajados en base mes comercial 30")


class CierrePlanillaRequest(BaseModel):
    confirmar_con_pendientes: bool = False
    observaciones: Optional[str] = None


class ReaperturaPlanillaRequest(BaseModel):
    motivo: str = Field(..., min_length=5, description="Motivo justificado para la reapertura administrativa")


class PeriodoPlanillaListItem(BaseModel):
    id: int
    mes: int
    anio: int
    descripcion: str
    estado: str
    fecha_inicio: date
    fecha_fin: date
    fecha_cierre: Optional[datetime] = None
    total_trabajadores: int = 0
    total_sueldo_base: Decimal = Decimal("0.00")
    total_pagado: Decimal = Decimal("0.00")
    total_saldo_pendiente: Decimal = Decimal("0.00")
    porcentaje_avance: float = 0.0

