from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


# =========================================================================
# FASE 1: PREPARACIÓN
# =========================================================================

class ActividadPreparacionCreate(BaseModel):
    tipo_actividad: str = Field(..., description="ARADO, RASTRA, ROLO, SUBSOLADO, OTRO")
    fecha: date
    completada: bool = False
    observaciones: Optional[str] = None


class ActividadPreparacionUpdate(BaseModel):
    tipo_actividad: Optional[str] = None
    fecha: Optional[date] = None
    completada: Optional[bool] = None
    observaciones: Optional[str] = None


class ActividadPreparacionOut(BaseModel):
    id: int
    ciclo_agricola_id: int
    tipo_actividad: str
    fecha: date
    completada: bool
    observaciones: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# =========================================================================
# FASE 2: SIEMBRA
# =========================================================================

class SiembraUpdate(BaseModel):
    cultivo: str
    variedad_hibrido: Optional[str] = None
    fecha_siembra: date
    superficie_sembrada_ha: Decimal = Field(..., ge=0)
    observaciones: Optional[str] = None


# =========================================================================
# FASE 3: FUMIGACIÓN Y MANEJO
# =========================================================================

class ActividadManejoCreate(BaseModel):
    fecha: date
    tipo_actividad: str = Field(..., description="FUMIGACION, HERBICIDA, INSECTICIDA, FUNGICIDA, FERTILIZACION, APLICACION_FOLIAR, OTRO")
    producto_utilizado: str
    cantidad_aplicada: Decimal = Field(..., ge=0)
    unidad_medida: str = Field("LT", description="LT, KG, DOSIS, etc.")
    dosis_por_ha: Optional[Decimal] = None
    superficie_aplicada_ha: Optional[Decimal] = None
    observaciones: Optional[str] = None


class ActividadManejoOut(BaseModel):
    id: int
    ciclo_agricola_id: int
    fecha: date
    tipo_actividad: str
    producto_utilizado: str
    cantidad_aplicada: Decimal
    unidad_medida: str
    dosis_por_ha: Optional[Decimal] = None
    superficie_aplicada_ha: Optional[Decimal] = None
    observaciones: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# =========================================================================
# FASE 4: COSECHA
# =========================================================================

class CosechaCreate(BaseModel):
    fecha_cosecha: date
    fecha_fin_cosecha: Optional[date] = None
    cultivo_cosechado: str
    superficie_cosechada_ha: Decimal = Field(..., gt=0)
    cantidad_producida: Decimal = Field(..., ge=0)
    unidad_medida: str = Field("TN", description="TN, KG, QQ")
    observaciones: Optional[str] = None


class CosechaOut(BaseModel):
    id: int
    ciclo_agricola_id: int
    fecha_cosecha: date
    fecha_fin_cosecha: Optional[date] = None
    cultivo_cosechado: str
    superficie_cosechada_ha: Decimal
    cantidad_producida: Decimal
    unidad_medida: str
    rendimiento_calculado_ha: Decimal
    observaciones: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# =========================================================================
# CICLO AGRÍCOLA
# =========================================================================

class CicloAgricolaCreate(BaseModel):
    cultivo: str = Field(..., description="Soya, Maíz, Sorgo, Trigo, etc.")
    variedad_hibrido: Optional[str] = None
    campana: str = Field(..., description="Ej: Verano 2025/2026, Invierno 2026")
    fecha_inicio: date
    superficie_utilizada_ha: Decimal = Field(..., ge=0)
    observaciones: Optional[str] = None


class CicloCambioFasePayload(BaseModel):
    fase: str = Field(..., description="PREPARACION, SIEMBRA, MANEJO, COSECHA, FINALIZADO")


class CicloAgricolaOut(BaseModel):
    id: int
    area_agricola_id: int
    cultivo: str
    variedad_hibrido: Optional[str] = None
    campana: str
    fecha_inicio: date
    superficie_utilizada_ha: Decimal
    fase_actual: str
    estado: str
    fecha_cierre: Optional[date] = None
    total_cosechado: Optional[Decimal] = None
    unidad_cosecha: Optional[str] = "TN"
    rendimiento_promedio_ha: Optional[Decimal] = None
    observaciones: Optional[str] = None
    actividades_preparacion: List[ActividadPreparacionOut] = []
    actividades_manejo: List[ActividadManejoOut] = []
    cosechas: List[CosechaOut] = []
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# =========================================================================
# ÁREA AGRÍCOLA (PARCELA / LOTE)
# =========================================================================

class AreaAgricolaCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    superficie_ha: Decimal = Field(..., ge=0)
    poligono_geojson: Optional[str] = None
    color_hex: Optional[str] = "#10B981"
    observaciones: Optional[str] = None


class AreaAgricolaUpdate(BaseModel):
    nombre: Optional[str] = None
    superficie_ha: Optional[Decimal] = None
    poligono_geojson: Optional[str] = None
    color_hex: Optional[str] = None
    estado: Optional[str] = None
    observaciones: Optional[str] = None


class AreaAgricolaOut(BaseModel):
    id: int
    codigo: str
    nombre: str
    superficie_ha: Decimal
    poligono_geojson: Optional[str] = None
    centroide_lat: Optional[Decimal] = None
    centroide_lng: Optional[Decimal] = None
    color_hex: str
    estado: str
    observaciones: Optional[str] = None
    ciclo_activo: Optional[CicloAgricolaOut] = None
    total_ciclos_historicos: int = 0
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


# =========================================================================
# INDICADORES (KPIS)
# =========================================================================

class AgriculturaKPIsOut(BaseModel):
    total_areas: int
    superficie_total_ha: Decimal
    ciclos_activos: int
    hectareas_en_produccion: Decimal
    distribucion_fases: Dict[str, int]
    rendimiento_promedio_ultimas_campanas: Decimal
