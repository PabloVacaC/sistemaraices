from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.entities import Usuario
from app.modules.inventario.schemas import (
    ProductoAlmacenOut,
    ProductoAlmacenDetalleOut,
    ProductoConPrimeraCompraCreate,
    CompraAlmacenOut,
    CompraPosteriorCreate,
    MovimientoAlmacenOut,
    SalidaAlmacenCreate,
    AjusteStockCreate,
    AnulacionOperacionCreate,
    GastoMenorOut,
    GastoMenorCreate,
    GastoMenorUpdate,
    ReporteAlmacenResumen,
    ReporteGastosResumen,
)
from app.modules.inventario import service

router = APIRouter(prefix="/inventario", tags=["Módulo de Inventario: Almacén y Gastos Menores"])


# =========================================================================
# RUTAS DE ALMACÉN: PRODUCTOS
# =========================================================================

@router.get("/almacen/productos", response_model=List[ProductoAlmacenOut])
def listar_productos(
    busqueda: Optional[str] = Query(None, description="Búsqueda por nombre o código"),
    estado_stock: Optional[str] = Query(None, description="Filtro de stock: TODOS, NORMAL, BAJO, AGOTADO"),
    unidad_control: Optional[str] = Query(None, description="Filtro por unidad de control"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.listar_productos(
        db, busqueda=busqueda, estado_stock=estado_stock, unidad_control=unidad_control
    )


@router.get("/almacen/productos/buscar", response_model=List[dict])
def buscar_productos_autocomplete(
    q: str = Query(..., min_length=1, description="Texto de autocompletado"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.buscar_productos_autocomplete(db, q=q)


@router.get("/almacen/productos/{id}", response_model=ProductoAlmacenDetalleOut)
def obtener_producto_detalle(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.obtener_producto_por_id(db, producto_id=id)


@router.post("/almacen/productos", response_model=ProductoAlmacenOut, status_code=status.HTTP_201_CREATED)
def crear_producto_con_primera_compra(
    payload: ProductoConPrimeraCompraCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.crear_producto_con_primera_compra(db, payload, usuario_ci=current_user.ci)


# =========================================================================
# RUTAS DE COMPRAS Y SALIDAS
# =========================================================================

@router.post("/almacen/compras", response_model=CompraAlmacenOut, status_code=status.HTTP_201_CREATED)
def registrar_compra_posterior(
    payload: CompraPosteriorCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.registrar_compra_posterior(db, payload, usuario_ci=current_user.ci)


@router.post("/almacen/salidas", response_model=MovimientoAlmacenOut, status_code=status.HTTP_201_CREATED)
def registrar_salida_almacen(
    payload: SalidaAlmacenCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.registrar_salida_almacen(db, payload, usuario_ci=current_user.ci)


@router.post("/almacen/ajustes", response_model=MovimientoAlmacenOut, status_code=status.HTTP_201_CREATED)
def registrar_ajuste_stock(
    payload: AjusteStockCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.registrar_ajuste_stock(db, payload, usuario_ci=current_user.ci)


@router.patch("/almacen/movimientos/{id}/anular")
def anular_movimiento(
    id: int,
    payload: AnulacionOperacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.anular_movimiento(db, movimiento_id=id, motivo=payload.motivo, usuario_ci=current_user.ci)


@router.get("/almacen/movimientos", response_model=List[MovimientoAlmacenOut])
def listar_movimientos(
    almacen_id: Optional[int] = Query(None),
    tipo_movimiento: Optional[str] = Query(None),
    trabajador_id: Optional[int] = Query(None),
    area_id: Optional[int] = Query(None),
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.listar_movimientos(
        db,
        almacen_id=almacen_id,
        tipo_movimiento=tipo_movimiento,
        trabajador_id=trabajador_id,
        area_id=area_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )


@router.get("/almacen/reportes/resumen", response_model=ReporteAlmacenResumen)
def obtener_reporte_almacen(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.obtener_reporte_almacen(db)


# =========================================================================
# RUTAS DE GASTOS MENORES
# =========================================================================

@router.get("/gastos", response_model=List[GastoMenorOut])
def listar_gastos_menores(
    busqueda: Optional[str] = Query(None),
    area_id: Optional[int] = Query(None),
    trabajador_id: Optional[int] = Query(None),
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.listar_gastos_menores(
        db,
        busqueda=busqueda,
        area_id=area_id,
        trabajador_id=trabajador_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado=estado,
    )


@router.post("/gastos", response_model=GastoMenorOut, status_code=status.HTTP_201_CREATED)
def crear_gasto_menor(
    payload: GastoMenorCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.crear_gasto_menor(db, payload, usuario_ci=current_user.ci)


@router.put("/gastos/{id}", response_model=GastoMenorOut)
def actualizar_gasto_menor(
    id: int,
    payload: GastoMenorUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.actualizar_gasto_menor(db, gasto_id=id, datos=payload, usuario_ci=current_user.ci)


@router.patch("/gastos/{id}/anular")
def anular_gasto_menor(
    id: int,
    payload: AnulacionOperacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.anular_gasto_menor(db, gasto_id=id, motivo=payload.motivo, usuario_ci=current_user.ci)


@router.get("/gastos/reportes/resumen", response_model=ReporteGastosResumen)
def obtener_reporte_gastos(
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return service.obtener_reporte_gastos(db, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

