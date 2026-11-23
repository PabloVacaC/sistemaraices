from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


# --- ESQUEMAS DE PESAJE ---
class PesajeCreate(BaseModel):
    fecha_pesaje: date
    peso: Decimal = Field(..., gt=0, description="Peso registrado en kilogramos (debe ser mayor a 0)")
    responsable: Optional[str] = None
    observaciones: Optional[str] = None


class PesajeOut(BaseModel):
    id: int
    animal_id: int
    fecha_pesaje: date
    peso: Decimal
    variacion_anterior: Optional[Decimal] = None
    responsable: Optional[str] = None
    observaciones: Optional[str] = None
    usuario_ci: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# --- ESQUEMAS DE HISTORIAL DE ARETE ---
class HistorialAreteOut(BaseModel):
    id: int
    animal_id: int
    arete_anterior: Optional[str] = None
    arete_nuevo: str
    fecha_cambio: date
    motivo: Optional[str] = None
    usuario_ci: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# --- ESQUEMAS DE ANIMAL ---
class AnimalCreate(BaseModel):
    numero_arete: Optional[str] = Field(None, description="Número de arete físico único (opcional inicialmente)")
    nombre: Optional[str] = None
    tipo: Optional[str] = Field("Bovino", description="Tipo de animal (Bovino, Ovino, Caprino, Equino, etc.)")
    tipo_ganado: Optional[str] = None
    raza: str = Field("Nelore", description="Raza del animal")
    sexo: str = Field(..., description="Sexo del animal: MACHO o HEMBRA")
    fecha_nacimiento: Optional[date] = None
    edad_estimada_meses: Optional[int] = None
    categoria: Optional[str] = None
    peso_inicial: Optional[Decimal] = Field(None, ge=0)
    potrero_id: Optional[int] = None
    ubicacion: str = Field("Potrero 1", description="Ubicación física o potrero")
    propietario: Optional[str] = None
    madre_id: Optional[int] = None
    padre_id: Optional[int] = None
    observaciones: Optional[str] = None


class AnimalUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    tipo_ganado: Optional[str] = None
    raza: Optional[str] = None
    sexo: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    edad_estimada_meses: Optional[int] = None
    categoria: Optional[str] = None
    potrero_id: Optional[int] = None
    ubicacion: Optional[str] = None
    propietario: Optional[str] = None
    madre_id: Optional[int] = None
    padre_id: Optional[int] = None
    observaciones: Optional[str] = None
    # Cambio de arete controlado
    numero_arete: Optional[str] = None
    motivo_cambio_arete: Optional[str] = None


class AnimalFamiliarOut(BaseModel):
    id: int
    codigo_interno: str
    numero_arete: Optional[str] = None
    nombre: Optional[str] = None
    tipo: str
    raza: str
    sexo: str

    class Config:
        from_attributes = True


class AnimalOut(BaseModel):
    id: int
    codigo_interno: str
    numero_arete: Optional[str] = None
    nombre: Optional[str] = None
    tipo: str
    tipo_ganado: Optional[str] = None
    raza: str
    sexo: str
    fecha_nacimiento: date
    edad_meses: Optional[int] = None
    peso_inicial: Optional[Decimal] = None
    peso_actual: Optional[Decimal] = None
    fecha_ultimo_pesaje: Optional[date] = None
    ganancia_peso_total: Optional[Decimal] = None
    estado: str
    procedencia: str
    madre_id: Optional[int] = None
    padre_id: Optional[int] = None
    madre_arete: Optional[str] = None
    padre_arete: Optional[str] = None
    potrero_id: Optional[int] = None
    ubicacion: str
    propietario: Optional[str] = None
    observaciones: Optional[str] = None
    fecha_registro: Optional[datetime] = None
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


class AnimalPerfilOut(AnimalOut):
    madre: Optional[AnimalFamiliarOut] = None
    padre: Optional[AnimalFamiliarOut] = None
    historial_pesajes: List[PesajeOut] = []
    pesajes: List[PesajeOut] = []
    historial_aretes: List[HistorialAreteOut] = []
    detalles_operaciones: Optional[dict] = None
    hijos: List[dict] = []
    detalles_compra: Optional[dict] = None
    detalles_venta: Optional[dict] = None
    detalles_baja: Optional[dict] = None
    animal: Optional[dict] = None


# --- ESQUEMAS DE NACIMIENTO ---
class NacimientoCreate(BaseModel):
    madre_id: int = Field(..., description="ID del animal madre (obligatorio)")
    padre_id: Optional[int] = Field(None, description="ID del animal padre (opcional)")
    fecha_nacimiento: Optional[date] = None
    fecha_parto: Optional[date] = None
    sexo_cria: Optional[str] = None
    cria_sexo: Optional[str] = None
    peso_nacimiento: Optional[Decimal] = Field(None, ge=0)
    cria_peso_nacer: Optional[Decimal] = Field(None, ge=0)
    tipo_parto: str = Field("UNICO", description="UNICO, GEMELAR, DISTOCICO")
    estado_nacimiento: Optional[str] = Field("VIVO", description="VIVO o MUERTO_AL_NACER")
    condicion_cria: Optional[str] = None
    numero_arete_cria: Optional[str] = None
    cria_numero_arete: Optional[str] = None
    tipo_animal: str = "Bovino"
    cria_tipo_ganado: Optional[str] = None
    raza_cria: str = "Nelore"
    cria_raza: Optional[str] = None
    potrero_id: Optional[int] = None
    cria_potrero_id: Optional[int] = None
    ubicacion: str = "Potrero 1"
    cria_ubicacion: Optional[str] = None
    observaciones: Optional[str] = None


class NacimientoUpdate(BaseModel):
    padre_id: Optional[int] = None
    fecha_nacimiento: Optional[date] = None
    sexo_cria: Optional[str] = None
    peso_nacimiento: Optional[Decimal] = None
    tipo_parto: Optional[str] = None
    estado_nacimiento: Optional[str] = None
    numero_arete_cria: Optional[str] = None
    ubicacion: Optional[str] = None
    observaciones: Optional[str] = None


class NacimientoOut(BaseModel):
    id: int
    numero_comprobante: str
    codigo_parto: Optional[str] = None
    madre_id: int
    madre_codigo: Optional[str] = None
    madre_arete: Optional[str] = None
    padre_id: Optional[int] = None
    padre_codigo: Optional[str] = None
    padre_arete: Optional[str] = None
    cria_id: Optional[int] = None
    cria_codigo: Optional[str] = None
    fecha_nacimiento: date
    fecha_parto: Optional[date] = None
    sexo_cria: str
    peso_nacimiento: Optional[Decimal] = None
    tipo_parto: str
    estado_nacimiento: str
    condicion_cria: Optional[str] = None
    numero_arete_cria: Optional[str] = None
    tipo_animal: str
    raza_cria: str
    ubicacion: str
    observaciones: Optional[str] = None
    usuario_ci: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# --- ESQUEMAS DE COMPRA ---
class CompraItemCreate(BaseModel):
    tipo: Optional[str] = "Bovino"
    tipo_ganado: Optional[str] = None
    raza: str = "Nelore"
    sexo: str = "HEMBRA"
    fecha_nacimiento: Optional[date] = None
    edad_estimada_meses: Optional[int] = None
    numero_arete: Optional[str] = None
    peso: Optional[Decimal] = Field(None, ge=0)
    peso_compra: Optional[Decimal] = Field(None, ge=0)
    modalidad_precio: str = Field("POR_ANIMAL", description="POR_ANIMAL o POR_KG")
    precio_unitario: Optional[Decimal] = None
    precio_compra: Optional[Decimal] = None
    potrero_id: Optional[int] = None
    ubicacion: str = "Potrero 1"
    observaciones: Optional[str] = None


class CompraGanadoCreate(BaseModel):
    proveedor: str
    fecha_compra: date
    documento_referencia: Optional[str] = None
    numero_documento: Optional[str] = None
    costos_adicionales: Decimal = Decimal("0.00")
    transporte: Decimal = Decimal("0.00")
    costo_transporte: Decimal = Decimal("0.00")
    observaciones: Optional[str] = None
    items: Optional[List[CompraItemCreate]] = None
    detalles: Optional[List[CompraItemCreate]] = None


class CompraDetalleItemOut(BaseModel):
    id: int
    animal_id: int
    animal_codigo: Optional[str] = None
    animal_arete: Optional[str] = None
    modalidad_precio: str
    precio_unitario: Decimal
    peso_compra: Optional[Decimal] = None
    costo_total: Decimal

    class Config:
        from_attributes = True


class CompraGanadoOut(BaseModel):
    id: int
    numero_comprobante: str
    proveedor: str
    fecha_compra: date
    documento_referencia: Optional[str] = None
    costos_adicionales: Decimal
    transporte: Decimal
    monto_total: Decimal
    observaciones: Optional[str] = None
    estado: str
    motivo_anulacion: Optional[str] = None
    cantidad_animales: int = 0
    detalles: List[CompraDetalleItemOut] = []
    usuario_ci: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# --- ESQUEMAS DE VENTA ---
class VentaItemCreate(BaseModel):
    animal_id: int = Field(..., description="ID del animal a vender (debe contar con arete)")
    modalidad_precio: str = Field("POR_ANIMAL", description="POR_ANIMAL o POR_KG")
    precio: Optional[Decimal] = None
    precio_unitario: Optional[Decimal] = None
    peso_venta: Optional[Decimal] = Field(None, ge=0)


class VentaGanadoCreate(BaseModel):
    cliente: str
    fecha_venta: date
    modalidad_venta: str = "POR_ANIMAL"
    metodo_pago: str = "EFECTIVO"
    documento_referencia: Optional[str] = None
    numero_documento: Optional[str] = None
    transporte: Optional[str] = None
    costo_transporte: Decimal = Decimal("0.00")
    descuentos: Decimal = Decimal("0.00")
    descuento: Decimal = Decimal("0.00")
    observaciones: Optional[str] = None
    items: Optional[List[VentaItemCreate]] = None
    animales: Optional[List[VentaItemCreate]] = None


class VentaDetalleItemOut(BaseModel):
    id: int
    animal_id: int
    animal_codigo: Optional[str] = None
    numero_arete: str
    modalidad_precio: str
    peso_venta: Optional[Decimal] = None
    precio_unitario: Decimal
    subtotal: Decimal

    class Config:
        from_attributes = True


class VentaGanadoOut(BaseModel):
    id: int
    numero_comprobante: str
    cliente: str
    fecha_venta: date
    modalidad_venta: str
    metodo_pago: str
    transporte: Optional[str] = None
    descuentos: Decimal
    monto_total: Decimal
    documento_referencia: Optional[str] = None
    observaciones: Optional[str] = None
    estado: str
    motivo_anulacion: Optional[str] = None
    cantidad_animales: int = 0
    detalles: List[VentaDetalleItemOut] = []
    usuario_ci: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# --- ESQUEMAS DE BAJA ---
class BajaGanadoCreate(BaseModel):
    animal_id: int = Field(..., description="ID del animal (debe contar con arete registrado)")
    fecha: Optional[date] = None
    fecha_baja: Optional[date] = None
    motivo: Optional[str] = None
    tipo: Optional[str] = None
    tipo_baja: Optional[str] = None
    motivo_diagnostico: Optional[str] = None
    causa_diagnostico: Optional[str] = None
    necropsia_realizada: Optional[bool] = False
    destino_canal: Optional[str] = None
    destino_cuerpo: Optional[str] = None
    valor_estimado_perdida: Optional[Decimal] = Decimal("0.00")
    responsable: Optional[str] = None
    documento_adjunto: Optional[str] = None
    observaciones: Optional[str] = None


class BajaGanadoOut(BaseModel):
    id: int
    numero_comprobante: str
    animal_id: int
    animal_codigo: Optional[str] = None
    numero_arete: str
    fecha_baja: date
    motivo: str
    estado_animal_resultante: str
    responsable: Optional[str] = None
    documento_adjunto: Optional[str] = None
    observaciones: Optional[str] = None
    estado: str
    motivo_anulacion: Optional[str] = None
    usuario_ci: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# --- ESQUEMAS DE AUDITORÍA Y ANULACIÓN ---
class AnulacionOperacionIn(BaseModel):
    motivo: str = Field(..., min_length=3, description="Justificación obligatoria de la anulación")


# --- KPIS RESUMEN ---
class GanaderiaKPIsOut(BaseModel):
    total_hato: int = 0
    activos: int = 0
    machos: int = 0
    hembras: int = 0
    vendidos: int = 0
    fallecidos_bajas: int = 0
    total_registrados: int = 0
    total_activos: int = 0
    total_vendidos: int = 0
    total_bajas: int = 0
    total_nacimientos: int = 0
    total_compras: int = 0
    machos_activos: int = 0
    hembras_activas: int = 0
    peso_promedio_activo: Optional[Decimal] = Decimal("0.00")


# =========================================================================
# ESQUEMAS PARA GESTIÓN DE POTREROS Y MOVIMIENTO DE GANADO (SPEC-002)
# =========================================================================

class PotreroBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    tipo_area: str = Field("POTRERO", description="POTRERO, CORRAL, CUARENTENA, MATERNIDAD, OTRO")
    superficie_ha: Optional[Decimal] = Field(None, ge=0)
    capacidad_cabezas: int = Field(50, ge=1)
    color_hex: str = Field("#10b981", max_length=20)
    poligono_geojson: str = Field(..., description="GeoJSON Polygon o MultiPolygon")
    centroide_lat: Optional[Decimal] = None
    centroide_lng: Optional[Decimal] = None
    observaciones: Optional[str] = None


class PotreroCreate(PotreroBase):
    pass


class PotreroUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo_area: Optional[str] = None
    superficie_ha: Optional[Decimal] = None
    capacidad_cabezas: Optional[int] = None
    color_hex: Optional[str] = None
    poligono_geojson: Optional[str] = None
    centroide_lat: Optional[Decimal] = None
    centroide_lng: Optional[Decimal] = None
    observaciones: Optional[str] = None


class PotreroOut(BaseModel):
    id: int
    codigo: str
    nombre: str
    tipo_area: str
    superficie_ha: Optional[Decimal] = None
    capacidad_cabezas: int
    color_hex: str
    poligono_geojson: str
    centroide_lat: Optional[Decimal] = None
    centroide_lng: Optional[Decimal] = None
    estado: str
    total_animales: int = 0
    total_machos: int = 0
    total_hembras: int = 0
    observaciones: Optional[str] = None
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


class PotreroDetalleOut(PotreroOut):
    animales: List[AnimalOut] = []


class MovimientoGanadoCreate(BaseModel):
    potrero_origen_id: int
    potrero_destino_id: int
    animales_ids: List[int] = Field(..., min_length=1)
    fecha_movimiento: Optional[date] = None
    tipo_operacion: str = Field("MANUAL", description="ARRASTRE_MAPA, MANUAL_INDIVIDUAL, MANUAL_GRUPAL")
    motivo: Optional[str] = None
    responsable: Optional[str] = None
    observaciones: Optional[str] = None


class MovimientoGanadoDetalleOut(BaseModel):
    id: int
    movimiento_id: int
    animal_id: int
    numero_arete: Optional[str] = None
    codigo_interno: str
    potrero_origen_id: int
    potrero_destino_id: int
    animal_nombre: Optional[str] = None
    animal_raza: Optional[str] = None
    animal_sexo: Optional[str] = None
    animal_peso_actual: Optional[Decimal] = None

    class Config:
        from_attributes = True


class MovimientoGanadoOut(BaseModel):
    id: int
    numero_comprobante: str
    fecha_movimiento: date
    potrero_origen_id: int
    potrero_origen_nombre: Optional[str] = None
    potrero_destino_id: int
    potrero_destino_nombre: Optional[str] = None
    tipo_operacion: str
    cantidad_animales: int
    motivo: Optional[str] = None
    responsable: Optional[str] = None
    observaciones: Optional[str] = None
    estado: str
    motivo_anulacion: Optional[str] = None
    usuario_ci: Optional[str] = None
    fecha_creacion: datetime
    detalles: List[MovimientoGanadoDetalleOut] = []

    class Config:
        from_attributes = True


class AnimalPuntoMapa(BaseModel):
    id: int
    codigo_interno: str
    numero_arete: Optional[str] = None
    nombre: Optional[str] = None
    tipo: str
    raza: str
    sexo: str
    peso_actual: Optional[Decimal] = None
    potrero_id: int
    potrero_nombre: str
    lat: float
    lng: float

    class Config:
        from_attributes = True


class MapaDistribucionOut(BaseModel):
    potreros: List[PotreroOut] = []
    animales: List[AnimalPuntoMapa] = []
    total_cabezas_activas: int = 0

