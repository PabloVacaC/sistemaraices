from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# =========================================================================
# CATÁLOGO DE VACUNAS
# =========================================================================

class SanidadVacunaBase(BaseModel):
    codigo: str = Field(..., max_length=50)
    nombre: str = Field(..., max_length=100)
    nombre_comercial: Optional[str] = Field(None, max_length=100)
    enfermedad_objetivo: str = Field(..., max_length=150)
    especie: str = Field("BOVINO", max_length=50)
    dosis_defecto_ml: Optional[Decimal] = None
    via_administracion: str = Field("SUBCUTANEA", max_length=50)
    dias_retiro_carne: int = Field(0, ge=0)
    dias_retiro_leche: int = Field(0, ge=0)
    requiere_refuerzo: bool = False
    dias_refuerzo: Optional[int] = Field(None, ge=1)
    estado: str = Field("ACTIVO", max_length=20)
    observaciones: Optional[str] = None


class SanidadVacunaCreate(SanidadVacunaBase):
    pass


class SanidadVacunaUpdate(BaseModel):
    nombre: Optional[str] = None
    nombre_comercial: Optional[str] = None
    enfermedad_objetivo: Optional[str] = None
    dosis_defecto_ml: Optional[Decimal] = None
    via_administracion: Optional[str] = None
    dias_retiro_carne: Optional[int] = None
    dias_retiro_leche: Optional[int] = None
    requiere_refuerzo: Optional[bool] = None
    dias_refuerzo: Optional[int] = None
    estado: Optional[str] = None
    observaciones: Optional[str] = None


class SanidadVacunaOut(SanidadVacunaBase):
    id: int
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# CATÁLOGO DE MEDICAMENTOS Y FÁRMACOS
# =========================================================================

class SanidadMedicamentoBase(BaseModel):
    codigo: str = Field(..., max_length=50)
    nombre: str = Field(..., max_length=100)
    nombre_comercial: Optional[str] = Field(None, max_length=100)
    tipo_farmaco: str = Field("ANTIBIOTICO", max_length=50)
    principio_activo: Optional[str] = Field(None, max_length=150)
    concentracion: Optional[str] = Field(None, max_length=100)
    unidad_medida: str = Field("ML", max_length=20)
    via_administracion: str = Field("INTRAMUSCULAR", max_length=50)
    dias_retiro_carne: int = Field(0, ge=0)
    dias_retiro_leche: int = Field(0, ge=0)
    almacen_id: Optional[int] = None
    estado: str = Field("ACTIVO", max_length=20)
    observaciones: Optional[str] = None


class SanidadMedicamentoCreate(SanidadMedicamentoBase):
    pass


class SanidadMedicamentoUpdate(BaseModel):
    nombre: Optional[str] = None
    nombre_comercial: Optional[str] = None
    tipo_farmaco: Optional[str] = None
    principio_activo: Optional[str] = None
    concentracion: Optional[str] = None
    unidad_medida: Optional[str] = None
    via_administracion: Optional[str] = None
    dias_retiro_carne: Optional[int] = None
    dias_retiro_leche: Optional[int] = None
    almacen_id: Optional[int] = None
    estado: Optional[str] = None
    observaciones: Optional[str] = None


class SanidadMedicamentoOut(SanidadMedicamentoBase):
    id: int
    fecha_creacion: datetime
    almacen_nombre: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# SEGUIMIENTOS CLÍNICOS / EVOLUCIÓN
# =========================================================================

class SanidadSeguimientoCreate(BaseModel):
    fecha_seguimiento: date
    estado_salud: str = Field("FAVORABLE", max_length=30)  # FAVORABLE, ESTABLE, DESFAVORABLE, RECUPERADO
    temperatura_c: Optional[Decimal] = None
    peso_actual_kg: Optional[Decimal] = None
    observaciones: Optional[str] = None


class SanidadSeguimientoOut(BaseModel):
    id: int
    detalle_id: int
    fecha_seguimiento: date
    estado_salud: str
    temperatura_c: Optional[Decimal] = None
    peso_actual_kg: Optional[Decimal] = None
    observaciones: Optional[str] = None
    usuario_ci: Optional[str] = None
    usuario_nombre: Optional[str] = None
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# DETALLES DE OPERACIÓN POR ANIMAL
# =========================================================================

class AnimalOperacionItemPayload(BaseModel):
    animal_id: int
    dosis_aplicada: Optional[Decimal] = None
    unidad_medida: Optional[str] = "ML"
    estado_aplicacion: Optional[str] = "APLICADO"  # APLICADO, PENDIENTE, RECHAZADO
    reaccion_adversa: Optional[str] = None
    observaciones: Optional[str] = None


class SanidadOperacionDetalleOut(BaseModel):
    id: int
    operacion_id: int
    animal_id: int
    numero_arete: Optional[str] = None
    codigo_interno: str
    animal_nombre: Optional[str] = None
    animal_raza: Optional[str] = None
    animal_sexo: Optional[str] = None
    dosis_aplicada: Optional[Decimal] = None
    unidad_medida: str
    fecha_fin_retiro_carne: Optional[date] = None
    fecha_fin_retiro_leche: Optional[date] = None
    en_retiro_carne: bool = False
    en_retiro_leche: bool = False
    dias_restantes_retiro_carne: int = 0
    dias_restantes_retiro_leche: int = 0
    estado_aplicacion: str
    reaccion_adversa: Optional[str] = None
    observaciones: Optional[str] = None
    seguimientos: List[SanidadSeguimientoOut] = []

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# OPERACIÓN SANITARIA (VACUNACIÓN / TRATAMIENTO)
# =========================================================================

class SanidadOperacionCreate(BaseModel):
    tipo_operacion: str = Field(..., max_length=40)  # VACUNACION_INDIVIDUAL, VACUNACION_GRUPAL, TRATAMIENTO_INDIVIDUAL, TRATAMIENTO_GRUPAL, PREVENTIVO
    fecha_aplicacion: date
    fecha_programada: Optional[date] = None
    potrero_origen_id: Optional[int] = None
    vacuna_id: Optional[int] = None
    medicamento_id: Optional[int] = None
    lote_producto: Optional[str] = None
    fecha_vencimiento_producto: Optional[date] = None
    diagnostico: Optional[str] = None
    sintomas: Optional[str] = None
    trabajador_id: Optional[int] = None
    veterinario_nombre: Optional[str] = None
    costo_total_estimado: Optional[Decimal] = None
    descontar_inventario: bool = False
    trasladar_a_cuarentena: bool = False
    potrero_cuarentena_id: Optional[int] = None
    observaciones: Optional[str] = None
    animales: List[AnimalOperacionItemPayload] = Field(..., min_length=1)


class SanidadOperacionOut(BaseModel):
    id: int
    numero_comprobante: str
    tipo_operacion: str
    fecha_aplicacion: date
    fecha_programada: Optional[date] = None
    potrero_origen_id: Optional[int] = None
    potrero_origen_nombre: Optional[str] = None
    vacuna_id: Optional[int] = None
    vacuna_nombre: Optional[str] = None
    medicamento_id: Optional[int] = None
    medicamento_nombre: Optional[str] = None
    producto_aplicado: str = ""
    lote_producto: Optional[str] = None
    fecha_vencimiento_producto: Optional[date] = None
    diagnostico: Optional[str] = None
    sintomas: Optional[str] = None
    cantidad_animales: int
    trabajador_id: Optional[int] = None
    trabajador_nombre: Optional[str] = None
    veterinario_nombre: Optional[str] = None
    costo_total_estimado: Optional[Decimal] = None
    descontar_inventario: bool
    movimiento_almacen_id: Optional[int] = None
    traslado_cuarentena_id: Optional[int] = None
    estado: str
    motivo_anulacion: Optional[str] = None
    observaciones: Optional[str] = None
    usuario_ci: Optional[str] = None
    usuario_nombre: Optional[str] = None
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)


class SanidadOperacionDetalladaOut(SanidadOperacionOut):
    detalles: List[SanidadOperacionDetalleOut] = []


class AnulacionSanidadIn(BaseModel):
    motivo_anulacion: str = Field(..., min_length=5, max_length=500)


# =========================================================================
# ALERTAS DE RETIRO Y KPIS
# =========================================================================

class AlertaRetiroOut(BaseModel):
    animal_id: int
    codigo_interno: str
    numero_arete: Optional[str] = None
    potrero_id: Optional[int] = None
    potrero_nombre: Optional[str] = None
    tipo_retiro: str  # CARNE, LECHE, AMBOS
    fecha_fin_retiro_carne: Optional[date] = None
    fecha_fin_retiro_leche: Optional[date] = None
    dias_restantes_carne: int = 0
    dias_restantes_leche: int = 0
    producto_origen: str
    numero_comprobante: str
    fecha_aplicacion: date


class SanidadKPIsOut(BaseModel):
    total_vacunaciones_mes: int = 0
    total_tratamientos_activos: int = 0
    animales_en_retiro_carne: int = 0
    animales_en_retiro_leche: int = 0
    vacunas_catalogo_activas: int = 0
    medicamentos_catalogo_activos: int = 0
    alertas_retiro_proximas: List[AlertaRetiroOut] = []


class HistorialSanitarioAnimalOut(BaseModel):
    animal_id: int
    codigo_interno: str
    numero_arete: Optional[str] = None
    en_retiro_carne: bool = False
    en_retiro_leche: bool = False
    fecha_fin_retiro_carne: Optional[date] = None
    fecha_fin_retiro_leche: Optional[date] = None
    dias_restantes_retiro_carne: int = 0
    dias_restantes_retiro_leche: int = 0
    vacunaciones: List[SanidadOperacionDetalleOut] = []
    tratamientos: List[SanidadOperacionDetalleOut] = []
