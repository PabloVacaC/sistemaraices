from datetime import date
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel


class ResumenContableKPIs(BaseModel):
    total_egresos_global: Decimal
    total_nomina_pagada: Decimal
    total_anticipos_pagados: Decimal
    total_sueldos_pagados: Decimal
    total_compras_inventario: Decimal
    total_gastos_menores: Decimal
    total_compromisos_pendientes: Decimal
    cantidad_transacciones: int
    promedio_diario_egresos: Decimal

    class Config:
        from_attributes = True


class DesglosePorArea(BaseModel):
    area_id: Optional[int] = None
    area_nombre: str
    total_nomina: Decimal
    total_gastos_menores: Decimal
    total_compras: Decimal
    total_egresos: Decimal
    porcentaje: float

    class Config:
        from_attributes = True


class MovimientoContable(BaseModel):
    id: str
    fecha: date
    tipo_categoria: str  # 'NOMINA_ANTICIPO', 'NOMINA_SUELDO', 'COMPRA_INVENTARIO', 'GASTO_OPERATIVO'
    tipo_label: str
    numero_comprobante: str
    beneficiario_proveedor: str
    concepto: str
    area_nombre: str
    metodo_pago: str
    monto: Decimal
    usuario_registro_ci: Optional[str] = None

    class Config:
        from_attributes = True


class ContabilidadReporteMensual(BaseModel):
    mes: int
    anio: int
    mes_nombre: str
    rango_fechas: str
    kpis: ResumenContableKPIs
    desglose_areas: List[DesglosePorArea]
    movimientos: List[MovimientoContable]
    metodos_pago_resumen: Dict[str, Decimal]

    class Config:
        from_attributes = True


class MesComparativoAnual(BaseModel):
    mes: int
    mes_nombre: str
    total_nomina: Decimal
    total_compras: Decimal
    total_gastos: Decimal
    total_global: Decimal

    class Config:
        from_attributes = True


class ContabilidadReporteAnual(BaseModel):
    anio: int
    kpis: ResumenContableKPIs
    meses: List[MesComparativoAnual]
    desglose_areas: List[DesglosePorArea]
    metodos_pago_resumen: Dict[str, Decimal]

    class Config:
        from_attributes = True

