from datetime import date, time, datetime
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field


# =========================================================================
# SCHEMAS: ALMACÉN
# =========================================================================

class CompraAlmacenOut(BaseModel):
    id: int
    numero_comprobante: str
    almacen_id: int
    cantidad_comprada: Decimal
    unidad_compra: str
    equivalencia_unidad: Decimal
    cantidad_en_unidad_control: Decimal
    precio_total: Decimal
    precio_unitario: Decimal
    precio_unitario_anterior: Optional[Decimal] = None
    variacion_porcentual: Optional[Decimal] = None
    fecha_compra: date
    proveedor: Optional[str] = None
    numero_factura: Optional[str] = None
    observaciones: Optional[str] = None
    usuario_registro_ci: Optional[str] = None
    usuario_registro_nombre: Optional[str] = None
    estado: str
    motivo_anulacion: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class MovimientoAlmacenOut(BaseModel):
    id: int
    numero_comprobante: str
    almacen_id: int
    compra_id: Optional[int] = None
    movimiento_original_id: Optional[int] = None
    trabajador_id: Optional[int] = None
    trabajador_nombre: Optional[str] = None
    area_id: Optional[int] = None
    area_nombre: Optional[str] = None
    vehiculo_maquinaria: Optional[str] = None
    usuario_registro_ci: Optional[str] = None
    usuario_registro_nombre: Optional[str] = None
    tipo_movimiento: str
    cantidad: Decimal
    cantidad_entrada: Decimal
    cantidad_salida: Decimal
    stock_anterior: Decimal
    stock_resultante: Decimal
    motivo: str
    observaciones: Optional[str] = None
    fecha_movimiento: date
    hora_movimiento: time
    estado: str
    motivo_anulacion: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class ProductoAlmacenOut(BaseModel):
    id: int
    codigo: str
    nombre: str
    foto: Optional[str] = None
    descripcion: Optional[str] = None
    unidad_control: str
    stock_actual: Decimal
    stock_minimo: Decimal
    estado_stock: str
    precio_ultima_compra: Decimal
    fecha_ultima_compra: Optional[date] = None
    precio_anterior: Optional[Decimal] = None
    variacion_porcentual: Optional[Decimal] = None
    usuario_registro_ci: Optional[str] = None
    usuario_registro_nombre: Optional[str] = None
    estado: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class ProductoAlmacenDetalleOut(ProductoAlmacenOut):
    compras: List[CompraAlmacenOut] = []
    movimientos: List[MovimientoAlmacenOut] = []


class ProductoConPrimeraCompraCreate(BaseModel):
    # Datos del producto
    nombre: str = Field(..., min_length=2, max_length=150)
    descripcion: Optional[str] = None
    foto: Optional[str] = None
    unidad_control: Optional[str] = Field(default="Unidades", max_length=50)
    stock_minimo: Decimal = Field(default=Decimal("0.00"), ge=0)

    # Datos obligatorios de la primera compra
    cantidad_comprada: Decimal = Field(..., gt=0)
    unidad_compra: Optional[str] = Field(default="Unidades")
    equivalencia_unidad: Optional[Decimal] = Field(default=Decimal("1.00"), gt=0)
    precio_total: Decimal = Field(..., ge=0)
    fecha_compra: date = Field(default_factory=date.today)
    proveedor: Optional[str] = None
    numero_factura: Optional[str] = None
    observaciones: Optional[str] = None


class CompraPosteriorCreate(BaseModel):
    almacen_id: int
    cantidad_comprada: Decimal = Field(..., gt=0)
    unidad_compra: Optional[str] = Field(default="Unidades")
    equivalencia_unidad: Optional[Decimal] = Field(default=Decimal("1.00"), gt=0)
    precio_total: Decimal = Field(..., ge=0)
    fecha_compra: date = Field(default_factory=date.today)
    proveedor: Optional[str] = None
    numero_factura: Optional[str] = None
    observaciones: Optional[str] = None


class SalidaAlmacenCreate(BaseModel):
    almacen_id: int
    cantidad: Decimal = Field(..., gt=0)
    trabajador_id: int
    area_id: int
    motivo: str = Field(..., min_length=3)
    vehiculo_maquinaria: Optional[str] = None
    fecha_movimiento: date = Field(default_factory=date.today)
    observaciones: Optional[str] = None


class AjusteStockCreate(BaseModel):
    almacen_id: int
    tipo_ajuste: str = Field(..., pattern="^(POSITIVO|NEGATIVO)$")
    cantidad: Decimal = Field(..., gt=0)
    motivo: str = Field(..., min_length=3)
    observaciones: Optional[str] = None


class AnulacionOperacionCreate(BaseModel):
    motivo: str = Field(..., min_length=3)


# =========================================================================
# SCHEMAS: GASTOS MENORES
# =========================================================================

class GastoMenorOut(BaseModel):
    id: int
    numero_comprobante: str
    nombre: str
    descripcion: Optional[str] = None
    foto_comprobante: Optional[str] = None
    importe_total: Decimal
    fecha_gasto: date
    area_id: Optional[int] = None
    area_nombre: Optional[str] = None
    trabajador_responsable_id: Optional[int] = None
    trabajador_nombre: Optional[str] = None
    metodo_pago: str
    proveedor: Optional[str] = None
    numero_comprobante_fiscal: Optional[str] = None
    usuario_registro_ci: Optional[str] = None
    usuario_registro_nombre: Optional[str] = None
    estado: str
    motivo_anulacion: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class GastoMenorCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=150)
    descripcion: Optional[str] = None
    foto_comprobante: Optional[str] = None
    importe_total: Decimal = Field(..., gt=0)
    fecha_gasto: date = Field(default_factory=date.today)
    area_id: Optional[int] = None
    trabajador_responsable_id: Optional[int] = None
    metodo_pago: str = "EFECTIVO"
    proveedor: Optional[str] = None
    numero_comprobante_fiscal: Optional[str] = None


class GastoMenorUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    foto_comprobante: Optional[str] = None
    importe_total: Optional[Decimal] = Field(default=None, gt=0)
    fecha_gasto: Optional[date] = None
    area_id: Optional[int] = None
    trabajador_responsable_id: Optional[int] = None
    metodo_pago: Optional[str] = None
    proveedor: Optional[str] = None
    numero_comprobante_fiscal: Optional[str] = None
    motivo_edicion: str = Field(..., min_length=3)


# =========================================================================
# SCHEMAS: REPORTES Y RESÚMENES
# =========================================================================

class ReporteAlmacenResumen(BaseModel):
    total_productos: int
    productos_normal: int
    productos_stock_bajo: int
    productos_agotados: int
    total_entradas_mes: Decimal
    total_salidas_mes: Decimal
    valor_estimado_inventario: Decimal


class ReporteGastosResumen(BaseModel):
    total_gastos_mes: Decimal
    cantidad_gastos_mes: int
    total_por_area: List[dict] = []
    total_por_metodo: List[dict] = []

