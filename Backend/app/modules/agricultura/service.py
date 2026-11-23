import json
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.entities import (
    AreaAgricola,
    CicloAgricola,
    ActividadPreparacion,
    ActividadManejo,
    CosechaRegistro,
    Bitacora,
)
from app.modules.agricultura.schemas import (
    AreaAgricolaCreate,
    AreaAgricolaUpdate,
    CicloAgricolaCreate,
    ActividadPreparacionCreate,
    ActividadPreparacionUpdate,
    SiembraUpdate,
    ActividadManejoCreate,
    CosechaCreate,
    AgriculturaKPIsOut,
)


# =========================================================================
# UTILITARIOS GEOGRÁFICOS Y DE CÓDIGO
# =========================================================================

def generar_codigo_area(db: Session) -> str:
    """Genera un código secuencial único como AGR-0001, AGR-0002."""
    ultimo = db.execute(
        select(AreaAgricola.codigo)
        .order_by(desc(AreaAgricola.id))
        .limit(1)
    ).scalar_one_or_none()

    if not ultimo or not ultimo.startswith("AGR-"):
        return "AGR-0001"

    try:
        numero = int(ultimo.split("-")[1]) + 1
        return f"AGR-{numero:04d}"
    except (ValueError, IndexError):
        return f"AGR-{db.query(func.count(AreaAgricola.id)).scalar() + 1:04d}"


def calcular_centroide_geojson(geojson_str: Optional[str]) -> Tuple[Optional[Decimal], Optional[Decimal]]:
    """Calcula el centroide aproximado a partir de la lista de coordenadas en JSON."""
    if not geojson_str:
        return None, None
    try:
        coords = json.loads(geojson_str)
        if isinstance(coords, list) and len(coords) >= 3:
            lats = [c[0] for c in coords if len(c) >= 2]
            lngs = [c[1] for c in coords if len(c) >= 2]
            if lats and lngs:
                avg_lat = Decimal(str(round(sum(lats) / len(lats), 6)))
                avg_lng = Decimal(str(round(sum(lngs) / len(lngs), 6)))
                return avg_lat, avg_lng
    except Exception:
        pass
    return None, None


def registrar_bitacora(
    db: Session,
    accion: str,
    descripcion: str,
    usuario_ci: Optional[str] = None
) -> None:
    """Registra evento en la bitácora central de auditoría."""
    try:
        now = datetime.now()
        bitacora = Bitacora(
            modulo="AGRICULTURA",
            accion=accion,
            descripcion=descripcion,
            usuario_ci=usuario_ci,
            fecha=now.date(),
            hora=now.time(),
        )
        db.add(bitacora)
    except Exception as e:
        print(f"Error al registrar bitácora de agricultura: {e}")


# =========================================================================
# ÁREAS AGRÍCOLAS (PARCELAS)
# =========================================================================

def listar_areas(db: Session) -> List[dict]:
    """Lista todas las áreas agrícolas activas con su ciclo activo y conteo histórico."""
    areas = db.execute(
        select(AreaAgricola)
        .where(AreaAgricola.estado == "ACTIVO")
        .order_by(AreaAgricola.nombre)
    ).scalars().all()

    resultado = []
    for a in areas:
        c_activo = a.ciclo_activo
        total_historicos = len([c for c in a.ciclos if c.estado != "ACTIVO"])
        resultado.append({
            "id": a.id,
            "codigo": a.codigo,
            "nombre": a.nombre,
            "superficie_ha": a.superficie_ha,
            "poligono_geojson": a.poligono_geojson,
            "centroide_lat": a.centroide_lat,
            "centroide_lng": a.centroide_lng,
            "color_hex": a.color_hex,
            "estado": a.estado,
            "observaciones": a.observaciones,
            "ciclo_activo": c_activo,
            "total_ciclos_historicos": total_historicos,
            "fecha_creacion": a.fecha_creacion,
            "fecha_actualizacion": a.fecha_actualizacion,
        })
    return resultado


def obtener_area(db: Session, area_id: int) -> dict:
    """Consulta una parcela agrícola por ID."""
    area = db.get(AreaAgricola, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Área agrícola no encontrada.")

    return {
        "id": area.id,
        "codigo": area.codigo,
        "nombre": area.nombre,
        "superficie_ha": area.superficie_ha,
        "poligono_geojson": area.poligono_geojson,
        "centroide_lat": area.centroide_lat,
        "centroide_lng": area.centroide_lng,
        "color_hex": area.color_hex,
        "estado": area.estado,
        "observaciones": area.observaciones,
        "ciclo_activo": area.ciclo_activo,
        "total_ciclos_historicos": len([c for c in area.ciclos if c.estado != "ACTIVO"]),
        "fecha_creacion": area.fecha_creacion,
        "fecha_actualizacion": area.fecha_actualizacion,
    }


def crear_area(db: Session, datos: AreaAgricolaCreate, usuario_ci: Optional[str] = None) -> AreaAgricola:
    """Crea una nueva parcela agrícola con cálculo de centroide."""
    codigo = generar_codigo_area(db)
    c_lat, c_lng = calcular_centroide_geojson(datos.poligono_geojson)

    area = AreaAgricola(
        codigo=codigo,
        nombre=datos.nombre.strip(),
        superficie_ha=datos.superficie_ha,
        poligono_geojson=datos.poligono_geojson,
        centroide_lat=c_lat,
        centroide_lng=c_lng,
        color_hex=datos.color_hex or "#10B981",
        estado="ACTIVO",
        observaciones=datos.observaciones,
    )
    db.add(area)
    db.commit()
    db.refresh(area)

    registrar_bitacora(
        db,
        accion="CREAR_AREA_AGRICOLA",
        descripcion=f"Se delimitó el área agrícola '{area.nombre}' ({area.codigo}) con {area.superficie_ha} ha.",
        usuario_ci=usuario_ci,
    )
    db.commit()
    return area


def actualizar_area(db: Session, area_id: int, datos: AreaAgricolaUpdate, usuario_ci: Optional[str] = None) -> AreaAgricola:
    """Actualiza datos de un área agrícola."""
    area = db.get(AreaAgricola, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Área agrícola no encontrada.")

    if datos.nombre is not None:
        area.nombre = datos.nombre.strip()
    if datos.superficie_ha is not None:
        area.superficie_ha = datos.superficie_ha
    if datos.poligono_geojson is not None:
        area.poligono_geojson = datos.poligono_geojson
        c_lat, c_lng = calcular_centroide_geojson(datos.poligono_geojson)
        area.centroide_lat = c_lat
        area.centroide_lng = c_lng
    if datos.color_hex is not None:
        area.color_hex = datos.color_hex
    if datos.estado is not None:
        area.estado = datos.estado
    if datos.observaciones is not None:
        area.observaciones = datos.observaciones

    db.commit()
    db.refresh(area)

    registrar_bitacora(
        db,
        accion="ACTUALIZAR_AREA_AGRICOLA",
        descripcion=f"Se actualizó la parcela agrícola '{area.nombre}' ({area.codigo}).",
        usuario_ci=usuario_ci,
    )
    db.commit()
    return area


def eliminar_area(db: Session, area_id: int, usuario_ci: Optional[str] = None) -> dict:
    """Desactiva lógicamente una parcela agrícola."""
    area = db.get(AreaAgricola, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Área agrícola no encontrada.")

    area.estado = "INACTIVO"
    db.commit()

    registrar_bitacora(
        db,
        accion="DESACTIVAR_AREA_AGRICOLA",
        descripcion=f"Se desactivó el área agrícola '{area.nombre}' ({area.codigo}).",
        usuario_ci=usuario_ci,
    )
    db.commit()
    return {"mensaje": f"Área {area.codigo} desactivada exitosamente."}


def obtener_historial_area(db: Session, area_id: int) -> List[CicloAgricola]:
    """Obtiene todos los ciclos pasados y finalizados de un área agrícola."""
    area = db.get(AreaAgricola, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Área agrícola no encontrada.")

    return list(area.ciclos)


# =========================================================================
# GESTIÓN DE CICLOS AGRÍCOLAS
# =========================================================================

def iniciar_ciclo(
    db: Session,
    area_id: int,
    datos: CicloAgricolaCreate,
    usuario_ci: Optional[str] = None
) -> CicloAgricola:
    """Inicia un nuevo ciclo agrícola para un área, verificando que no tenga uno activo."""
    area = db.get(AreaAgricola, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Área agrícola no encontrada.")

    # Verificar si ya tiene ciclo activo
    if area.ciclo_activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El área '{area.nombre}' ya tiene un ciclo activo en campaña '{area.ciclo_activo.campana}' ({area.ciclo_activo.cultivo}). Debe finalizarlo antes de crear otro."
        )

    # Crear ciclo
    ciclo = CicloAgricola(
        area_agricola_id=area_id,
        cultivo=datos.cultivo.strip(),
        variedad_hibrido=datos.variedad_hibrido.strip() if datos.variedad_hibrido else None,
        campana=datos.campana.strip(),
        fecha_inicio=datos.fecha_inicio,
        superficie_utilizada_ha=datos.superficie_utilizada_ha or area.superficie_ha,
        fase_actual="PREPARACION",
        estado="ACTIVO",
        observaciones=datos.observaciones,
        usuario_ci=usuario_ci,
    )
    db.add(ciclo)
    db.flush()

    # Pre-crear las 3 labores estándar de preparación
    labores = [
        ("ARADO", False),
        ("RASTRA", False),
        ("ROLO", False),
    ]
    for tipo, comp in labores:
        act = ActividadPreparacion(
            ciclo_agricola_id=ciclo.id,
            tipo_actividad=tipo,
            fecha=datos.fecha_inicio,
            completada=comp,
            observaciones=f"Labor estándar de preparación de cama de siembra ({tipo.lower()})."
        )
        db.add(act)

    # Actualizar color del área a Ámbar (Fase Preparación)
    area.color_hex = "#F59E0B"

    db.commit()
    db.refresh(ciclo)

    registrar_bitacora(
        db,
        accion="INICIAR_CICLO_AGRICOLA",
        descripcion=f"Se inició ciclo agrícola para '{area.nombre}': Cultivo {ciclo.cultivo}, Campaña {ciclo.campana}.",
        usuario_ci=usuario_ci,
    )
    db.commit()
    return ciclo


def obtener_ciclo(db: Session, ciclo_id: int) -> CicloAgricola:
    """Consulta el detalle integral de un ciclo agrícola."""
    ciclo = db.get(CicloAgricola, ciclo_id)
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo agrícola no encontrado.")
    return ciclo


def cambiar_fase_ciclo(
    db: Session,
    ciclo_id: int,
    nueva_fase: str,
    usuario_ci: Optional[str] = None
) -> CicloAgricola:
    """Actualiza manualmente la fase del ciclo agrícola."""
    fases_validas = ["PREPARACION", "SIEMBRA", "MANEJO", "COSECHA", "FINALIZADO"]
    if nueva_fase not in fases_validas:
        raise HTTPException(status_code=400, detail=f"Fase inválida. Opciones: {fases_validas}")

    ciclo = db.get(CicloAgricola, ciclo_id)
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo agrícola no encontrado.")

    ciclo.fase_actual = nueva_fase

    # Actualizar color del área según la fase
    colores_fase = {
        "PREPARACION": "#F59E0B",
        "SIEMBRA": "#3B82F6",
        "MANEJO": "#10B981",
        "COSECHA": "#8B5CF6",
        "FINALIZADO": "#64748B",
    }
    if ciclo.area:
        ciclo.area.color_hex = colores_fase.get(nueva_fase, "#10B981")

    db.commit()
    db.refresh(ciclo)

    registrar_bitacora(
        db,
        accion="CAMBIO_FASE_AGRICOLA",
        descripcion=f"El ciclo {ciclo.cultivo} ({ciclo.campana}) avanzó a la fase {nueva_fase}.",
        usuario_ci=usuario_ci,
    )
    db.commit()
    return ciclo


# =========================================================================
# FASE 1: PREPARACIÓN
# =========================================================================

def registrar_actividad_preparacion(
    db: Session,
    ciclo_id: int,
    datos: ActividadPreparacionCreate
) -> ActividadPreparacion:
    """Registra una labor adicional en la fase de preparación."""
    ciclo = db.get(CicloAgricola, ciclo_id)
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo agrícola no encontrado.")

    act = ActividadPreparacion(
        ciclo_agricola_id=ciclo_id,
        tipo_actividad=datos.tipo_actividad.strip().upper(),
        fecha=datos.fecha,
        completada=datos.completada,
        observaciones=datos.observaciones,
    )
    db.add(act)
    db.commit()
    db.refresh(act)
    return act


def actualizar_actividad_preparacion(
    db: Session,
    ciclo_id: int,
    act_id: int,
    datos: ActividadPreparacionUpdate
) -> ActividadPreparacion:
    """Actualiza el estado (completado/pendiente) u observaciones de una labor de preparación."""
    act = db.get(ActividadPreparacion, act_id)
    if not act or act.ciclo_agricola_id != ciclo_id:
        raise HTTPException(status_code=404, detail="Actividad de preparación no encontrada.")

    if datos.tipo_actividad is not None:
        act.tipo_actividad = datos.tipo_actividad.strip().upper()
    if datos.fecha is not None:
        act.fecha = datos.fecha
    if datos.completada is not None:
        act.completada = datos.completada
    if datos.observaciones is not None:
        act.observaciones = datos.observaciones

    db.commit()
    db.refresh(act)
    return act


# =========================================================================
# FASE 2: SIEMBRA
# =========================================================================

def actualizar_siembra(
    db: Session,
    ciclo_id: int,
    datos: SiembraUpdate,
    usuario_ci: Optional[str] = None
) -> CicloAgricola:
    """Registra los datos de siembra y avanza automáticamente a Fase de Manejo / Fumigación."""
    ciclo = db.get(CicloAgricola, ciclo_id)
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo agrícola no encontrado.")

    ciclo.cultivo = datos.cultivo.strip()
    if datos.variedad_hibrido:
        ciclo.variedad_hibrido = datos.variedad_hibrido.strip()
    ciclo.superficie_utilizada_ha = datos.superficie_sembrada_ha
    ciclo.fecha_inicio = datos.fecha_siembra
    if datos.observaciones:
        ciclo.observaciones = ((ciclo.observaciones or "") + f" [Siembra: {datos.observaciones}]").strip()

    # Avanza de fase
    ciclo.fase_actual = "MANEJO"
    if ciclo.area:
        ciclo.area.color_hex = "#10B981"  # Verde esmeralda (desarrollo)

    db.commit()
    db.refresh(ciclo)

    registrar_bitacora(
        db,
        accion="REGISTRO_SIEMBRA",
        descripcion=f"Se registró siembra de {ciclo.cultivo} ({datos.variedad_hibrido or 'S/V'}) en {ciclo.superficie_utilizada_ha} ha.",
        usuario_ci=usuario_ci,
    )
    db.commit()
    return ciclo


# =========================================================================
# FASE 3: FUMIGACIÓN Y MANEJO
# =========================================================================

def registrar_actividad_manejo(
    db: Session,
    ciclo_id: int,
    datos: ActividadManejoCreate,
    usuario_ci: Optional[str] = None
) -> ActividadManejo:
    """Registra una fumigación, fertilización o aplicación foliar."""
    ciclo = db.get(CicloAgricola, ciclo_id)
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo agrícola no encontrado.")

    act = ActividadManejo(
        ciclo_agricola_id=ciclo_id,
        fecha=datos.fecha,
        tipo_actividad=datos.tipo_actividad.strip().upper(),
        producto_utilizado=datos.producto_utilizado.strip(),
        cantidad_aplicada=datos.cantidad_aplicada,
        unidad_medida=datos.unidad_medida.strip().upper(),
        dosis_por_ha=datos.dosis_por_ha,
        superficie_aplicada_ha=datos.superficie_aplicada_ha,
        observaciones=datos.observaciones,
    )
    db.add(act)

    # Si estaba en siembra o preparación, situarlo en fase Manejo
    if ciclo.fase_actual in ["PREPARACION", "SIEMBRA"]:
        ciclo.fase_actual = "MANEJO"
        if ciclo.area:
            ciclo.area.color_hex = "#10B981"

    db.commit()
    db.refresh(act)

    registrar_bitacora(
        db,
        accion="REGISTRO_MANEJO_AGRICOLA",
        descripcion=f"Labor de {act.tipo_actividad}: {act.producto_utilizado} ({act.cantidad_aplicada} {act.unidad_medida}) en ciclo {ciclo.cultivo}.",
        usuario_ci=usuario_ci,
    )
    db.commit()
    return act


def eliminar_actividad_manejo(db: Session, ciclo_id: int, act_id: int) -> dict:
    """Elimina una actividad de manejo registrada."""
    act = db.get(ActividadManejo, act_id)
    if not act or act.ciclo_agricola_id != ciclo_id:
        raise HTTPException(status_code=404, detail="Actividad de manejo no encontrada.")

    db.delete(act)
    db.commit()
    return {"mensaje": "Actividad de manejo eliminada correctamente."}


# =========================================================================
# FASE 4: COSECHA Y FINALIZACIÓN
# =========================================================================

def registrar_cosecha(
    db: Session,
    ciclo_id: int,
    datos: CosechaCreate,
    usuario_ci: Optional[str] = None
) -> CosechaRegistro:
    """Registra una jornada de cosecha y calcula el rendimiento por hectárea."""
    ciclo = db.get(CicloAgricola, ciclo_id)
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo agrícola no encontrado.")

    # Cálculo automático de rendimiento por hectárea
    sup = datos.superficie_cosechada_ha
    rendimiento = round(datos.cantidad_producida / sup, 2) if sup > 0 else Decimal("0.00")

    cosecha = CosechaRegistro(
        ciclo_agricola_id=ciclo_id,
        fecha_cosecha=datos.fecha_cosecha,
        fecha_fin_cosecha=datos.fecha_fin_cosecha,
        cultivo_cosechado=datos.cultivo_cosechado.strip(),
        superficie_cosechada_ha=sup,
        cantidad_producida=datos.cantidad_producida,
        unidad_medida=datos.unidad_medida.strip().upper(),
        rendimiento_calculado_ha=rendimiento,
        observaciones=datos.observaciones,
    )
    db.add(cosecha)

    # Actualizar fase a COSECHA y color púrpura
    ciclo.fase_actual = "COSECHA"
    if ciclo.area:
        ciclo.area.color_hex = "#8B5CF6"

    db.commit()
    db.refresh(cosecha)

    registrar_bitacora(
        db,
        accion="REGISTRO_COSECHA",
        descripcion=f"Se registró cosecha de {cosecha.cultivo_cosechado}: {cosecha.cantidad_producida} {cosecha.unidad_medida} ({rendimiento} {cosecha.unidad_medida}/ha).",
        usuario_ci=usuario_ci,
    )
    db.commit()
    return cosecha


def finalizar_ciclo(
    db: Session,
    ciclo_id: int,
    usuario_ci: Optional[str] = None
) -> CicloAgricola:
    """Cierra y consolida definitivamente la campaña agrícola."""
    ciclo = db.get(CicloAgricola, ciclo_id)
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo agrícola no encontrado.")

    # Consolidar totales de cosecha
    cosechas = ciclo.cosechas
    total_cant = Decimal("0.00")
    total_sup = Decimal("0.00")
    unidad = "TN"

    if cosechas:
        for c in cosechas:
            total_cant += c.cantidad_producida
            total_sup += c.superficie_cosechada_ha
            unidad = c.unidad_medida
        rend_prom = round(total_cant / total_sup, 2) if total_sup > 0 else Decimal("0.00")
    else:
        rend_prom = Decimal("0.00")

    ciclo.estado = "FINALIZADO"
    ciclo.fase_actual = "FINALIZADO"
    ciclo.fecha_cierre = date.today()
    ciclo.total_cosechado = total_cant
    ciclo.unidad_cosecha = unidad
    ciclo.rendimiento_promedio_ha = rend_prom

    # Restaurar color del área a estado de descanso / sin ciclo activo
    if ciclo.area:
        ciclo.area.color_hex = "#94A3B8"

    db.commit()
    db.refresh(ciclo)

    registrar_bitacora(
        db,
        accion="FINALIZAR_CICLO_AGRICOLA",
        descripcion=f"Se finalizó la campaña '{ciclo.campana}' de {ciclo.cultivo}. Rendimiento final: {rend_prom} {unidad}/ha.",
        usuario_ci=usuario_ci,
    )
    db.commit()
    return ciclo


# =========================================================================
# INDICADORES EJECUTIVOS (KPIS)
# =========================================================================

def obtener_kpis(db: Session) -> AgriculturaKPIsOut:
    """Calcula los indicadores globales de la gestión agrícola."""
    areas = db.execute(
        select(AreaAgricola).where(AreaAgricola.estado == "ACTIVO")
    ).scalars().all()

    total_areas = len(areas)
    superficie_total = sum((a.superficie_ha for a in areas), Decimal("0.00"))

    ciclos_activos_query = db.execute(
        select(CicloAgricola).where(CicloAgricola.estado == "ACTIVO")
    ).scalars().all()

    ciclos_activos = len(ciclos_activos_query)
    hectareas_prod = sum((c.superficie_utilizada_ha for c in ciclos_activos_query), Decimal("0.00"))

    dist_fases = {
        "PREPARACION": 0,
        "SIEMBRA": 0,
        "MANEJO": 0,
        "COSECHA": 0,
        "FINALIZADO": 0,
    }
    for c in ciclos_activos_query:
        if c.fase_actual in dist_fases:
            dist_fases[c.fase_actual] += 1

    # Rendimiento promedio de los últimos ciclos finalizados
    finalizados = db.execute(
        select(CicloAgricola.rendimiento_promedio_ha)
        .where(CicloAgricola.estado == "FINALIZADO", CicloAgricola.rendimiento_promedio_ha.is_not(None))
        .order_by(desc(CicloAgricola.id))
        .limit(10)
    ).scalars().all()

    if finalizados:
        rend_prom = round(sum(finalizados) / len(finalizados), 2)
    else:
        rend_prom = Decimal("0.00")

    return AgriculturaKPIsOut(
        total_areas=total_areas,
        superficie_total_ha=round(superficie_total, 2),
        ciclos_activos=ciclos_activos,
        hectareas_en_produccion=round(hectareas_prod, 2),
        distribucion_fases=dist_fases,
        rendimiento_promedio_ultimas_campanas=rend_prom,
    )
