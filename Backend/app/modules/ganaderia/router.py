from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.entities import Usuario
from app.modules.ganaderia import service
from app.modules.ganaderia.schemas import (
    AnimalCreate,
    AnimalUpdate,
    AnimalOut,
    AnimalPerfilOut,
    PesajeCreate,
    PesajeOut,
    NacimientoCreate,
    NacimientoOut,
    CompraGanadoCreate,
    CompraGanadoOut,
    VentaGanadoCreate,
    VentaGanadoOut,
    BajaGanadoCreate,
    BajaGanadoOut,
    AnulacionOperacionIn,
    GanaderiaKPIsOut,
    PotreroCreate,
    PotreroUpdate,
    PotreroOut,
    PotreroDetalleOut,
    MovimientoGanadoCreate,
    MovimientoGanadoOut,
    MapaDistribucionOut,
)

router = APIRouter(prefix="/ganaderia", tags=["Módulo de Ganadería"])


# =========================================================================
# KPIS Y RESUMEN GENERAL
# =========================================================================
@router.get("/kpis", response_model=GanaderiaKPIsOut)
def obtener_kpis(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Consulta indicadores clave del hato ganadero para tarjetas ejecutivas."""
    return service.obtener_kpis_ganaderia(db)


# =========================================================================
# ANIMALES (REGISTRO, CONSULTA, PERFIL, EDICIÓN)
# =========================================================================
@router.get("/animales", response_model=List[AnimalOut])
def listar_animales(
    response: Response,
    filtro_procedencia: Optional[str] = Query(None, description="REGISTRADOS, NACIMIENTOS, COMPRAS, VENTAS, BAJAS, TODOS"),
    estado: Optional[str] = Query(None, description="ACTIVO, VENDIDO, FALLECIDO, etc."),
    sexo: Optional[str] = Query(None, description="MACHO, HEMBRA"),
    tipo: Optional[str] = Query(None, description="Bovino, Ovino, etc."),
    busqueda: Optional[str] = Query(None, description="Búsqueda por número de arete, código interno o nombre"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Consulta paginada del listado principal de animales con filtros y búsqueda rápida."""
    items, total = service.listar_animales(
        db=db,
        filtro_procedencia=filtro_procedencia,
        estado=estado,
        sexo=sexo,
        tipo=tipo,
        busqueda=busqueda,
        skip=skip,
        limit=limit,
    )
    response.headers["X-Total-Count"] = str(total)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
    return items


@router.post("/animales", response_model=AnimalOut, status_code=status.HTTP_201_CREATED)
def registrar_animal(
    datos: AnimalCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra manualmente un animal individual generando su código interno único."""
    animal = service.registrar_animal_manual(db, datos, usuario_ci=current_user.ci)
    edad = service.calcular_edad_en_meses(animal.fecha_nacimiento)
    return {
        "id": animal.id,
        "codigo_interno": animal.codigo_interno,
        "numero_arete": animal.numero_arete,
        "nombre": animal.nombre,
        "tipo": animal.tipo,
        "raza": animal.raza,
        "sexo": animal.sexo,
        "fecha_nacimiento": animal.fecha_nacimiento,
        "edad_meses": edad,
        "peso_inicial": animal.peso_inicial,
        "peso_actual": animal.peso_actual,
        "fecha_ultimo_pesaje": animal.fecha_ultimo_pesaje,
        "ganancia_peso_total": 0,
        "estado": animal.estado,
        "procedencia": animal.procedencia,
        "madre_id": animal.madre_id,
        "padre_id": animal.padre_id,
        "potrero_id": animal.potrero_id,
        "ubicacion": animal.ubicacion,
        "propietario": animal.propietario,
        "observaciones": animal.observaciones,
        "fecha_creacion": animal.fecha_creacion,
        "fecha_actualizacion": animal.fecha_actualizacion,
    }


@router.get("/animales/{animal_id}", response_model=AnimalPerfilOut)
def obtener_perfil_animal(
    animal_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Consulta el perfil integral 360° del animal con genealogía, pesajes e historial."""
    return service.obtener_perfil_animal(db, animal_id)


@router.put("/animales/{animal_id}", response_model=AnimalOut)
def actualizar_animal(
    animal_id: int,
    datos: AnimalUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Edición controlada de datos del animal. Si cambia el arete, se audita en el historial."""
    animal = service.actualizar_animal(db, animal_id, datos, usuario_ci=current_user.ci)
    edad = service.calcular_edad_en_meses(animal.fecha_nacimiento)
    ganancia = (animal.peso_actual - animal.peso_inicial) if (animal.peso_actual and animal.peso_inicial) else 0
    return {
        "id": animal.id,
        "codigo_interno": animal.codigo_interno,
        "numero_arete": animal.numero_arete,
        "nombre": animal.nombre,
        "tipo": animal.tipo,
        "raza": animal.raza,
        "sexo": animal.sexo,
        "fecha_nacimiento": animal.fecha_nacimiento,
        "edad_meses": edad,
        "peso_inicial": animal.peso_inicial,
        "peso_actual": animal.peso_actual,
        "fecha_ultimo_pesaje": animal.fecha_ultimo_pesaje,
        "ganancia_peso_total": ganancia,
        "estado": animal.estado,
        "procedencia": animal.procedencia,
        "madre_id": animal.madre_id,
        "padre_id": animal.padre_id,
        "madre_arete": animal.madre.numero_arete if animal.madre else None,
        "padre_arete": animal.padre.numero_arete if animal.padre else None,
        "potrero_id": animal.potrero_id,
        "ubicacion": animal.ubicacion,
        "propietario": animal.propietario,
        "observaciones": animal.observaciones,
        "fecha_creacion": animal.fecha_creacion,
        "fecha_actualizacion": animal.fecha_actualizacion,
    }


# =========================================================================
# PESAJES DE GANADO (RF-019, RF-020)
# =========================================================================
@router.post("/animales/{animal_id}/pesajes", response_model=PesajeOut, status_code=status.HTTP_201_CREATED)
def registrar_pesaje(
    animal_id: int,
    datos: PesajeCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra pesaje de báscula para un animal y actualiza su peso actual de forma atómica."""
    return service.registrar_pesaje(db, animal_id, datos, usuario_ci=current_user.ci)


@router.delete("/pesajes/{pesaje_id}")
def anular_pesaje(
    pesaje_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Eliminación controlada de un pesaje erróneo recalculando el peso actual."""
    return service.anular_pesaje(db, pesaje_id, usuario_ci=current_user.ci)


# =========================================================================
# NACIMIENTOS (RF-007, RF-012)
# =========================================================================
@router.get("/nacimientos", response_model=List[NacimientoOut])
def listar_nacimientos(
    response: Response,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Consulta el registro histórico de partos y nacimientos."""
    items, total = service.listar_nacimientos(db, skip=skip, limit=limit)
    response.headers["X-Total-Count"] = str(total)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
    return items


@router.post("/nacimientos", response_model=NacimientoOut, status_code=status.HTTP_201_CREATED)
def registrar_nacimiento(
    datos: NacimientoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra un nacimiento incorporando automáticamente la cría viva al inventario."""
    n = service.registrar_nacimiento(db, datos, usuario_ci=current_user.ci)
    return {
        "id": n.id,
        "numero_comprobante": n.numero_comprobante,
        "codigo_parto": n.numero_comprobante,
        "madre_id": n.madre_id,
        "madre_codigo": n.madre.codigo_interno if n.madre else None,
        "madre_arete": n.madre.numero_arete if n.madre else None,
        "padre_id": n.padre_id,
        "padre_codigo": n.padre.codigo_interno if n.padre else None,
        "padre_arete": n.padre.numero_arete if n.padre else None,
        "cria_id": n.cria_id,
        "cria_codigo": n.cria.codigo_interno if n.cria else None,
        "fecha_nacimiento": n.fecha_nacimiento,
        "fecha_parto": n.fecha_nacimiento,
        "sexo_cria": n.sexo_cria,
        "peso_nacimiento": n.peso_nacimiento,
        "tipo_parto": n.tipo_parto,
        "estado_nacimiento": n.estado_nacimiento,
        "condicion_cria": n.estado_nacimiento,
        "numero_arete_cria": n.numero_arete_cria,
        "tipo_animal": n.tipo_animal,
        "raza_cria": n.raza_cria,
        "ubicacion": n.ubicacion,
        "observaciones": n.observaciones,
        "usuario_ci": n.usuario_ci,
        "fecha_creacion": n.fecha_creacion,
    }


# =========================================================================
# COMPRAS DE GANADO (RF-008, RF-013)
# =========================================================================
@router.get("/compras", response_model=List[CompraGanadoOut])
def listar_compras(
    response: Response,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Consulta el listado de compras de ganado."""
    items, total = service.listar_compras_ganado(db, skip=skip, limit=limit)
    response.headers["X-Total-Count"] = str(total)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
    return items


@router.post("/compras", response_model=CompraGanadoOut, status_code=status.HTTP_201_CREATED)
def registrar_compra(
    datos: CompraGanadoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra una compra e incorpora individualmente cada animal al inventario."""
    compra = service.registrar_compra_ganado(db, datos, usuario_ci=current_user.ci)
    detalles_out = [
        {
            "id": d.id,
            "animal_id": d.animal_id,
            "animal_codigo": d.animal.codigo_interno if d.animal else None,
            "animal_arete": d.animal.numero_arete if d.animal else None,
            "modalidad_precio": d.modalidad_precio,
            "precio_unitario": d.precio_unitario,
            "peso_compra": d.peso_compra,
            "costo_total": d.costo_total,
        }
        for d in compra.detalles
    ]
    return {
        "id": compra.id,
        "numero_comprobante": compra.numero_comprobante,
        "proveedor": compra.proveedor,
        "fecha_compra": compra.fecha_compra,
        "documento_referencia": compra.documento_referencia,
        "costos_adicionales": compra.costos_adicionales,
        "transporte": compra.transporte,
        "monto_total": compra.monto_total,
        "observaciones": compra.observaciones,
        "estado": compra.estado,
        "motivo_anulacion": compra.motivo_anulacion,
        "cantidad_animales": len(compra.detalles),
        "detalles": detalles_out,
        "usuario_ci": compra.usuario_ci,
        "fecha_creacion": compra.fecha_creacion,
    }


# =========================================================================
# VENTAS DE GANADO (RF-009, RF-014, CE-003)
# =========================================================================
@router.get("/ventas", response_model=List[VentaGanadoOut])
def listar_ventas(
    response: Response,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Consulta el listado de ventas comerciales de ganado."""
    items, total = service.listar_ventas_ganado(db, skip=skip, limit=limit)
    response.headers["X-Total-Count"] = str(total)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
    return items


@router.post("/ventas", response_model=VentaGanadoOut, status_code=status.HTTP_201_CREATED)
def registrar_venta(
    datos: VentaGanadoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Registra venta de ganado. Bloquea si algún animal no tiene número de arete asignado.
    """
    venta = service.registrar_venta_ganado(db, datos, usuario_ci=current_user.ci)
    detalles_out = [
        {
            "id": d.id,
            "animal_id": d.animal_id,
            "animal_codigo": d.animal.codigo_interno if d.animal else None,
            "numero_arete": d.numero_arete,
            "modalidad_precio": d.modalidad_precio,
            "peso_venta": d.peso_venta,
            "precio_unitario": d.precio_unitario,
            "subtotal": d.subtotal,
        }
        for d in venta.detalles
    ]
    return {
        "id": venta.id,
        "numero_comprobante": venta.numero_comprobante,
        "cliente": venta.cliente,
        "fecha_venta": venta.fecha_venta,
        "modalidad_venta": venta.modalidad_venta,
        "metodo_pago": venta.metodo_pago,
        "transporte": venta.transporte,
        "descuentos": venta.descuentos,
        "monto_total": venta.monto_total,
        "documento_referencia": venta.documento_referencia,
        "observaciones": venta.observaciones,
        "estado": venta.estado,
        "motivo_anulacion": venta.motivo_anulacion,
        "cantidad_animales": len(venta.detalles),
        "detalles": detalles_out,
        "usuario_ci": venta.usuario_ci,
        "fecha_creacion": venta.fecha_creacion,
    }


@router.post("/ventas/{venta_id}/anular")
def anular_venta(
    venta_id: int,
    datos: AnulacionOperacionIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Anula venta y devuelve los animales vendidos al estado ACTIVO."""
    return service.anular_venta_ganado(db, venta_id, datos.motivo, usuario_ci=current_user.ci)


# =========================================================================
# BAJAS DE GANADO (RF-010, RF-015, CE-004)
# =========================================================================
@router.get("/bajas", response_model=List[BajaGanadoOut])
def listar_bajas(
    response: Response,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Consulta el listado de bajas, muertes o pérdidas de ganado."""
    items, total = service.listar_bajas_ganado(db, skip=skip, limit=limit)
    response.headers["X-Total-Count"] = str(total)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
    return items


@router.post("/bajas", response_model=BajaGanadoOut, status_code=status.HTTP_201_CREATED)
def registrar_baja(
    datos: BajaGanadoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Registra baja de un animal. Bloquea si el animal no cuenta con número de arete asignado.
    """
    baja = service.registrar_baja_ganado(db, datos, usuario_ci=current_user.ci)
    return {
        "id": baja.id,
        "numero_comprobante": baja.numero_comprobante,
        "animal_id": baja.animal_id,
        "animal_codigo": baja.animal.codigo_interno if baja.animal else None,
        "numero_arete": baja.numero_arete,
        "fecha_baja": baja.fecha_baja,
        "motivo": baja.motivo,
        "estado_animal_resultante": baja.estado_animal_resultante,
        "responsable": baja.responsable,
        "documento_adjunto": baja.documento_adjunto,
        "observaciones": baja.observaciones,
        "estado": baja.estado,
        "motivo_anulacion": baja.motivo_anulacion,
        "usuario_ci": baja.usuario_ci,
        "fecha_creacion": baja.fecha_creacion,
    }


@router.post("/bajas/{baja_id}/anular")
def anular_baja(
    baja_id: int,
    datos: AnulacionOperacionIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Anula baja y restaura el animal al estado ACTIVO."""
    return service.anular_baja_ganado(db, baja_id, datos.motivo, usuario_ci=current_user.ci)


# =========================================================================
# POTREROS Y CORRALES (SPEC-002)
# =========================================================================
@router.get("/potreros", response_model=List[PotreroOut])
def listar_potreros(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista todos los potreros y corrales activos con estadísticas agregadas."""
    return service.listar_potreros(db)


@router.post("/potreros", response_model=PotreroOut, status_code=status.HTTP_201_CREATED)
def crear_potrero(
    datos: PotreroCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Crea un nuevo potrero o corral con su polígono delimitado y capacidad."""
    potrero = service.crear_potrero(db, datos, usuario_ci=current_user.ci)
    return {
        "id": potrero.id,
        "codigo": potrero.codigo,
        "nombre": potrero.nombre,
        "tipo_area": potrero.tipo_area,
        "superficie_ha": potrero.superficie_ha,
        "capacidad_cabezas": potrero.capacidad_cabezas,
        "color_hex": potrero.color_hex,
        "poligono_geojson": potrero.poligono_geojson,
        "centroide_lat": potrero.centroide_lat,
        "centroide_lng": potrero.centroide_lng,
        "estado": potrero.estado,
        "total_animales": 0,
        "total_machos": 0,
        "total_hembras": 0,
        "observaciones": potrero.observaciones,
        "fecha_creacion": potrero.fecha_creacion,
        "fecha_actualizacion": potrero.fecha_actualizacion,
    }


@router.get("/potreros/{potrero_id}", response_model=PotreroDetalleOut)
def obtener_potrero(
    potrero_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene el detalle de un potrero y la lista de todos sus animales presentes."""
    return service.obtener_potrero(db, potrero_id)


@router.put("/potreros/{potrero_id}", response_model=PotreroOut)
def actualizar_potrero(
    potrero_id: int,
    datos: PotreroUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Actualiza datos y/o vértices de un potrero o corral existente."""
    p = service.actualizar_potrero(db, potrero_id, datos, usuario_ci=current_user.ci)
    # Contar animales activos
    animales = service.obtener_potrero(db, potrero_id)
    return {
        "id": p.id,
        "codigo": p.codigo,
        "nombre": p.nombre,
        "tipo_area": p.tipo_area,
        "superficie_ha": p.superficie_ha,
        "capacidad_cabezas": p.capacidad_cabezas,
        "color_hex": p.color_hex,
        "poligono_geojson": p.poligono_geojson,
        "centroide_lat": p.centroide_lat,
        "centroide_lng": p.centroide_lng,
        "estado": p.estado,
        "total_animales": animales["total_animales"],
        "total_machos": animales["total_machos"],
        "total_hembras": animales["total_hembras"],
        "observaciones": p.observaciones,
        "fecha_creacion": p.fecha_creacion,
        "fecha_actualizacion": p.fecha_actualizacion,
    }


@router.patch("/potreros/{potrero_id}/desactivar", response_model=PotreroOut)
def desactivar_potrero(
    potrero_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Desactiva un potrero (únicamente si tiene 0 animales activos)."""
    p = service.desactivar_potrero(db, potrero_id, usuario_ci=current_user.ci)
    return {
        "id": p.id,
        "codigo": p.codigo,
        "nombre": p.nombre,
        "tipo_area": p.tipo_area,
        "superficie_ha": p.superficie_ha,
        "capacidad_cabezas": p.capacidad_cabezas,
        "color_hex": p.color_hex,
        "poligono_geojson": p.poligono_geojson,
        "centroide_lat": p.centroide_lat,
        "centroide_lng": p.centroide_lng,
        "estado": p.estado,
        "total_animales": 0,
        "total_machos": 0,
        "total_hembras": 0,
        "observaciones": p.observaciones,
        "fecha_creacion": p.fecha_creacion,
        "fecha_actualizacion": p.fecha_actualizacion,
    }


@router.get("/mapa-distribucion", response_model=MapaDistribucionOut)
def obtener_mapa_distribucion(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Devuelve en 1 sola consulta optimizada los potreros delimitados y animales activos con coordenadas calculadas."""
    return service.obtener_mapa_distribucion(db)


# =========================================================================
# MOVIMIENTOS DE GANADO (SPEC-002)
# =========================================================================
@router.post("/movimientos", response_model=MovimientoGanadoOut, status_code=status.HTTP_201_CREATED)
def registrar_movimiento(
    datos: MovimientoGanadoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra un movimiento (por arrastre en mapa o lote) y actualiza la ubicación del ganado."""
    mov = service.registrar_movimiento_ganado(db, datos, usuario_ci=current_user.ci)
    return service.obtener_movimiento(db, mov.id)


@router.get("/movimientos", response_model=List[MovimientoGanadoOut])
def listar_movimientos(
    response: Response,
    potrero_id: Optional[int] = Query(None, description="Filtrar por potrero origen o destino"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Historial paginado de movimientos con filtros."""
    items, total = service.listar_movimientos(db=db, skip=skip, limit=limit, potrero_id=potrero_id)
    response.headers["X-Total-Count"] = str(total)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
    return items


@router.get("/movimientos/{movimiento_id}", response_model=MovimientoGanadoOut)
def obtener_movimiento(
    movimiento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Consulta el comprobante y detalle de un movimiento específico."""
    return service.obtener_movimiento(db, movimiento_id)


@router.post("/movimientos/{movimiento_id}/anular", response_model=MovimientoGanadoOut)
def anular_movimiento(
    movimiento_id: int,
    datos: AnulacionOperacionIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Anula un movimiento revirtiendo la ubicación de los animales de forma atómica y segura."""
    service.anular_movimiento_ganado(db, movimiento_id, datos.motivo, usuario_ci=current_user.ci)
    return service.obtener_movimiento(db, movimiento_id)


@router.get("/animales/{animal_id}/historial-movimientos")
def obtener_historial_movimientos_animal(
    animal_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Cronología de traslados de un animal particular para su Ficha Perfil 360°."""
    return service.obtener_historial_movimientos_animal(db, animal_id)

