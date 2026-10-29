from datetime import date, datetime
from typing import List, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, desc
from fastapi import HTTPException, status

from app.models.entities import (
    Almacen,
    CompraAlmacen,
    MovimientoAlmacen,
    GastoMenor,
    Trabajador,
    Area,
    Usuario,
)
from app.modules.inventario.schemas import (
    ProductoConPrimeraCompraCreate,
    CompraPosteriorCreate,
    SalidaAlmacenCreate,
    AjusteStockCreate,
    GastoMenorCreate,
    GastoMenorUpdate,
    ReporteAlmacenResumen,
    ReporteGastosResumen,
)
from app.modules.bitacora.service import registrar_bitacora


# =========================================================================
# GENERADORES DE COMPROBANTES Y CÓDIGOS CORRELATIVOS ÚNICOS
# =========================================================================

def generar_codigo_producto(db: Session) -> str:
    total = db.scalar(select(func.count(Almacen.id))) or 0
    correlativo = total + 1
    # Asegurar unicidad si se han borrado registros
    while db.scalar(select(Almacen.id).where(Almacen.codigo == f"PRD-{correlativo:04d}")):
        correlativo += 1
    return f"PRD-{correlativo:04d}"


def generar_comprobante(db: Session, prefijo: str) -> str:
    """Genera comprobantes correlativos tipo: CMP-202610-0001, MOV-202610-0001, GAS-202610-0001"""
    now = datetime.now()
    ym = now.strftime("%Y%m")

    total = 0
    if prefijo == "CMP":
        total = db.scalar(
            select(func.count(CompraAlmacen.id)).where(CompraAlmacen.numero_comprobante.like(f"CMP-{ym}-%"))
        ) or 0
        correlativo = total + 1
        while db.scalar(select(CompraAlmacen.id).where(CompraAlmacen.numero_comprobante == f"CMP-{ym}-{correlativo:04d}")):
            correlativo += 1
    elif prefijo == "MOV":
        total = db.scalar(
            select(func.count(MovimientoAlmacen.id)).where(MovimientoAlmacen.numero_comprobante.like(f"MOV-{ym}-%"))
        ) or 0
        correlativo = total + 1
        while db.scalar(select(MovimientoAlmacen.id).where(MovimientoAlmacen.numero_comprobante == f"MOV-{ym}-{correlativo:04d}")):
            correlativo += 1
    elif prefijo == "GAS":
        total = db.scalar(
            select(func.count(GastoMenor.id)).where(GastoMenor.numero_comprobante.like(f"GAS-{ym}-%"))
        ) or 0
        correlativo = total + 1
        while db.scalar(select(GastoMenor.id).where(GastoMenor.numero_comprobante == f"GAS-{ym}-{correlativo:04d}")):
            correlativo += 1
    else:
        correlativo = 1

    return f"{prefijo}-{ym}-{correlativo:04d}"


# =========================================================================
# SERVICIOS DE ALMACÉN: PRODUCTOS Y PRIMERA COMPRA
# =========================================================================

def crear_producto_con_primera_compra(
    db: Session,
    datos: ProductoConPrimeraCompraCreate,
    usuario_ci: Optional[str] = None,
) -> Almacen:
    # 1. Validar nombre no vacío y no duplicado
    nombre_limpio = datos.nombre.strip()
    if not nombre_limpio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre del producto no puede estar vacío ni contener solo espacios.",
        )

    existente = db.execute(
        select(Almacen).where(
            func.lower(Almacen.nombre) == func.lower(nombre_limpio),
            Almacen.estado == True,
        )
    ).scalars().first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un producto activo con el nombre '{nombre_limpio}' ({existente.codigo}).",
        )

    # 2. Validar equivalencias y cantidades
    if datos.cantidad_comprada <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La cantidad comprada debe ser mayor a cero.")
    equiv = datos.equivalencia_unidad if datos.equivalencia_unidad and datos.equivalencia_unidad > 0 else Decimal("1.00")
    if datos.precio_total < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El precio total no puede ser negativo.")

    # 3. Cálculos de stock y precio unitario exactos
    u_control = datos.unidad_control.strip() if datos.unidad_control and datos.unidad_control.strip() else "Unidades"
    cantidad_en_unidad_control = round(datos.cantidad_comprada * equiv, 2)
    precio_unitario = (
        round(datos.precio_total / cantidad_en_unidad_control, 2)
        if cantidad_en_unidad_control > 0
        else Decimal("0.00")
    )
    unidad_compra = datos.unidad_compra.strip() if datos.unidad_compra and datos.unidad_compra.strip() else u_control

    codigo_prod = generar_codigo_producto(db)

    # 4. Crear entidad Almacen
    nuevo_producto = Almacen(
        codigo=codigo_prod,
        nombre=nombre_limpio,
        foto=datos.foto,
        descripcion=datos.descripcion.strip() if datos.descripcion else None,
        unidad_control=u_control,
        stock_actual=cantidad_en_unidad_control,
        stock_minimo=datos.stock_minimo,
        precio_ultima_compra=precio_unitario,
        fecha_ultima_compra=datos.fecha_compra,
        usuario_registro_ci=usuario_ci,
        estado=True,
    )
    db.add(nuevo_producto)
    db.flush()  # Para obtener nuevo_producto.id dentro de la transacción

    # 5. Crear CompraAlmacen
    nro_compra = generar_comprobante(db, "CMP")
    nueva_compra = CompraAlmacen(
        numero_comprobante=nro_compra,
        almacen_id=nuevo_producto.id,
        cantidad_comprada=datos.cantidad_comprada,
        unidad_compra=unidad_compra,
        equivalencia_unidad=equiv,
        cantidad_en_unidad_control=cantidad_en_unidad_control,
        precio_total=datos.precio_total,
        precio_unitario=precio_unitario,
        precio_unitario_anterior=None,
        variacion_porcentual=None,
        fecha_compra=datos.fecha_compra,
        proveedor=datos.proveedor.strip() if datos.proveedor else None,
        numero_factura=datos.numero_factura.strip() if datos.numero_factura else None,
        observaciones=datos.observaciones.strip() if datos.observaciones else None,
        usuario_registro_ci=usuario_ci,
        estado="COMPLETADO",
    )
    db.add(nueva_compra)
    db.flush()

    # 6. Crear MovimientoAlmacen (Entrada inicial)
    nro_mov = generar_comprobante(db, "MOV")
    nuevo_movimiento = MovimientoAlmacen(
        numero_comprobante=nro_mov,
        almacen_id=nuevo_producto.id,
        compra_id=nueva_compra.id,
        tipo_movimiento="ENTRADA_COMPRA",
        cantidad=cantidad_en_unidad_control,
        cantidad_entrada=cantidad_en_unidad_control,
        cantidad_salida=Decimal("0.00"),
        stock_anterior=Decimal("0.00"),
        stock_resultante=cantidad_en_unidad_control,
        motivo="Primera compra al registrar producto",
        observaciones=f"Compra inicial {nro_compra}. Ingresaron {cantidad_en_unidad_control} {nuevo_producto.unidad_control}.",
        fecha_movimiento=datos.fecha_compra,
        usuario_registro_ci=usuario_ci,
        estado="CONFIRMADO",
    )
    db.add(nuevo_movimiento)

    # 7. Registrar en bitácora
    registrar_bitacora(
        db=db,
        modulo="INVENTARIO_ALMACEN",
        accion="CREAR_PRODUCTO",
        descripcion=(
            f"Se registró producto '{nuevo_producto.nombre}' ({nuevo_producto.codigo}) "
            f"con compra inicial {nro_compra} de {cantidad_en_unidad_control} {nuevo_producto.unidad_control} "
            f"a Bs {datos.precio_total} (Bs {precio_unitario}/{nuevo_producto.unidad_control})."
        ),
        usuario_ci=usuario_ci,
    )

    db.commit()
    db.refresh(nuevo_producto)
    return nuevo_producto


# =========================================================================
# REGISTRO DE COMPRAS POSTERIORES
# =========================================================================

def registrar_compra_posterior(
    db: Session,
    datos: CompraPosteriorCreate,
    usuario_ci: Optional[str] = None,
) -> CompraAlmacen:
    # 1. Bloqueo pesimista para concurrencia segura
    producto = db.execute(
        select(Almacen).where(Almacen.id == datos.almacen_id).with_for_update(of=Almacen)
    ).scalars().first()
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
    if not producto.estado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El producto se encuentra inactivo.")

    if datos.cantidad_comprada <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La cantidad comprada debe ser mayor a cero.")
    equiv = datos.equivalencia_unidad if datos.equivalencia_unidad and datos.equivalencia_unidad > 0 else Decimal("1.00")
    if datos.precio_total < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El precio total no puede ser negativo.")

    # 2. Cálculos y comparación de precios
    cantidad_en_unidad_control = round(datos.cantidad_comprada * equiv, 2)
    precio_unitario = (
        round(datos.precio_total / cantidad_en_unidad_control, 2)
        if cantidad_en_unidad_control > 0
        else Decimal("0.00")
    )
    unidad_compra = datos.unidad_compra.strip() if datos.unidad_compra else producto.unidad_control

    precio_anterior = producto.precio_ultima_compra
    variacion_porcentual = None
    if precio_anterior and precio_anterior > 0:
        var = ((precio_unitario - precio_anterior) / precio_anterior) * Decimal("100.00")
        variacion_porcentual = round(var, 2)

    # 3. Crear Compra
    nro_compra = generar_comprobante(db, "CMP")
    nueva_compra = CompraAlmacen(
        numero_comprobante=nro_compra,
        almacen_id=producto.id,
        cantidad_comprada=datos.cantidad_comprada,
        unidad_compra=unidad_compra,
        equivalencia_unidad=equiv,
        cantidad_en_unidad_control=cantidad_en_unidad_control,
        precio_total=datos.precio_total,
        precio_unitario=precio_unitario,
        precio_unitario_anterior=precio_anterior,
        variacion_porcentual=variacion_porcentual,
        fecha_compra=datos.fecha_compra,
        proveedor=datos.proveedor.strip() if datos.proveedor else None,
        numero_factura=datos.numero_factura.strip() if datos.numero_factura else None,
        observaciones=datos.observaciones.strip() if datos.observaciones else None,
        usuario_registro_ci=usuario_ci,
        estado="COMPLETADO",
    )
    db.add(nueva_compra)
    db.flush()

    # 4. Actualizar Stock y registrar Movimiento
    stock_ant = producto.stock_actual
    stock_res = stock_ant + cantidad_en_unidad_control

    nro_mov = generar_comprobante(db, "MOV")
    nuevo_movimiento = MovimientoAlmacen(
        numero_comprobante=nro_mov,
        almacen_id=producto.id,
        compra_id=nueva_compra.id,
        tipo_movimiento="ENTRADA_COMPRA",
        cantidad=cantidad_en_unidad_control,
        cantidad_entrada=cantidad_en_unidad_control,
        cantidad_salida=Decimal("0.00"),
        stock_anterior=stock_ant,
        stock_resultante=stock_res,
        motivo=f"Compra de reposición {nro_compra}",
        observaciones=datos.observaciones,
        fecha_movimiento=datos.fecha_compra,
        usuario_registro_ci=usuario_ci,
        estado="CONFIRMADO",
    )
    db.add(nuevo_movimiento)

    # 5. Actualizar producto
    producto.stock_actual = stock_res
    producto.precio_anterior_compra = precio_anterior
    producto.precio_ultima_compra = precio_unitario
    producto.fecha_ultima_compra = datos.fecha_compra

    # 6. Auditoría
    registrar_bitacora(
        db=db,
        modulo="INVENTARIO_ALMACEN",
        accion="COMPRA",
        descripcion=(
            f"Compra {nro_compra} para '{producto.nombre}': +{cantidad_en_unidad_control} {producto.unidad_control}. "
            f"Precio anterior: Bs {precio_anterior}, Nuevo: Bs {precio_unitario} "
            f"({f'{variacion_porcentual:+.2f}%' if variacion_porcentual is not None else 'N/A'}). Stock actual: {stock_res}."
        ),
        usuario_ci=usuario_ci,
    )

    db.commit()
    db.refresh(nueva_compra)
    return nueva_compra


# =========================================================================
# REGISTRO DE SALIDAS Y ENTREGAS DEL ALMACÉN
# =========================================================================

def registrar_salida_almacen(
    db: Session,
    datos: SalidaAlmacenCreate,
    usuario_ci: Optional[str] = None,
) -> MovimientoAlmacen:
    # 1. Bloqueo pesimista
    producto = db.execute(
        select(Almacen).where(Almacen.id == datos.almacen_id).with_for_update(of=Almacen)
    ).scalars().first()
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
    if not producto.estado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El producto se encuentra inactivo.")

    if datos.cantidad <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La cantidad a retirar debe ser mayor a cero.")

    # 2. Validar existencias disponibles
    if producto.stock_actual < datos.cantidad:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Stock insuficiente. Existencias disponibles: {producto.stock_actual} {producto.unidad_control}. "
                f"Cantidad solicitada: {datos.cantidad} {producto.unidad_control}."
            ),
        )

    # 3. Validar trabajador receptor y área
    trabajador = db.execute(select(Trabajador).where(Trabajador.id == datos.trabajador_id)).scalars().first()
    if not trabajador:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trabajador receptor no encontrado.")

    area = db.execute(select(Area).where(Area.id == datos.area_id)).scalars().first()
    if not area:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Área de destino no encontrada.")

    # 4. Descontar existencias y registrar movimiento
    stock_ant = producto.stock_actual
    stock_res = stock_ant - datos.cantidad

    nro_mov = generar_comprobante(db, "MOV")
    nuevo_movimiento = MovimientoAlmacen(
        numero_comprobante=nro_mov,
        almacen_id=producto.id,
        trabajador_id=trabajador.id,
        area_id=area.id,
        vehiculo_maquinaria=datos.vehiculo_maquinaria.strip() if datos.vehiculo_maquinaria else None,
        tipo_movimiento="SALIDA_ENTREGA",
        cantidad=datos.cantidad,
        cantidad_entrada=Decimal("0.00"),
        cantidad_salida=datos.cantidad,
        stock_anterior=stock_ant,
        stock_resultante=stock_res,
        motivo=datos.motivo.strip(),
        observaciones=datos.observaciones.strip() if datos.observaciones else None,
        fecha_movimiento=datos.fecha_movimiento,
        usuario_registro_ci=usuario_ci,
        estado="CONFIRMADO",
    )
    db.add(nuevo_movimiento)

    producto.stock_actual = stock_res

    # 5. Auditoría
    registrar_bitacora(
        db=db,
        modulo="INVENTARIO_ALMACEN",
        accion="SALIDA",
        descripcion=(
            f"Salida {nro_mov} de '{producto.nombre}': -{datos.cantidad} {producto.unidad_control} "
            f"entregados a {trabajador.nombres} {trabajador.apellidos} para área {area.nombre}. "
            f"Motivo: {datos.motivo}. Stock resultante: {stock_res}."
        ),
        usuario_ci=usuario_ci,
    )

    db.commit()
    db.refresh(nuevo_movimiento)
    return nuevo_movimiento


# =========================================================================
# AJUSTES DE STOCK AUDITADOS
# =========================================================================

def registrar_ajuste_stock(
    db: Session,
    datos: AjusteStockCreate,
    usuario_ci: Optional[str] = None,
) -> MovimientoAlmacen:
    producto = db.execute(
        select(Almacen).where(Almacen.id == datos.almacen_id).with_for_update(of=Almacen)
    ).scalars().first()
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")

    if datos.cantidad <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La cantidad de ajuste debe ser mayor a cero.")

    stock_ant = producto.stock_actual

    if datos.tipo_ajuste == "NEGATIVO":
        if stock_ant < datos.cantidad:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede realizar un ajuste negativo de {datos.cantidad} {producto.unidad_control} porque el stock actual es de {stock_ant} {producto.unidad_control}.",
            )
        stock_res = stock_ant - datos.cantidad
        cant_ent = Decimal("0.00")
        cant_sal = datos.cantidad
        tipo_mov = "AJUSTE_NEGATIVO"
    else:
        stock_res = stock_ant + datos.cantidad
        cant_ent = datos.cantidad
        cant_sal = Decimal("0.00")
        tipo_mov = "AJUSTE_POSITIVO"

    nro_mov = generar_comprobante(db, "MOV")
    nuevo_mov = MovimientoAlmacen(
        numero_comprobante=nro_mov,
        almacen_id=producto.id,
        tipo_movimiento=tipo_mov,
        cantidad=datos.cantidad,
        cantidad_entrada=cant_ent,
        cantidad_salida=cant_sal,
        stock_anterior=stock_ant,
        stock_resultante=stock_res,
        motivo=f"Ajuste {datos.tipo_ajuste}: {datos.motivo.strip()}",
        observaciones=datos.observaciones.strip() if datos.observaciones else None,
        fecha_movimiento=date.today(),
        usuario_registro_ci=usuario_ci,
        estado="CONFIRMADO",
    )
    db.add(nuevo_mov)

    producto.stock_actual = stock_res

    registrar_bitacora(
        db=db,
        modulo="INVENTARIO_ALMACEN",
        accion="AJUSTE_STOCK",
        descripcion=(
            f"Ajuste de inventario {nro_mov} en '{producto.nombre}': "
            f"{tipo_mov} de {datos.cantidad} {producto.unidad_control}. "
            f"Stock anterior: {stock_ant}, Nuevo stock: {stock_res}. Motivo: {datos.motivo}"
        ),
        usuario_ci=usuario_ci,
    )

    db.commit()
    db.refresh(nuevo_mov)
    return nuevo_mov


# =========================================================================
# ANULACIONES Y REVERSIONES DE MOVIMIENTOS
# =========================================================================

def anular_movimiento(
    db: Session,
    movimiento_id: int,
    motivo: str,
    usuario_ci: Optional[str] = None,
) -> dict:
    mov = db.execute(
        select(MovimientoAlmacen).where(MovimientoAlmacen.id == movimiento_id).with_for_update(of=MovimientoAlmacen)
    ).scalars().first()
    if not mov:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimiento no encontrado.")
    if mov.estado == "ANULADO":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El movimiento ya se encuentra anulado.")

    producto = db.execute(
        select(Almacen).where(Almacen.id == mov.almacen_id).with_for_update(of=Almacen)
    ).scalars().first()

    motivo_limpio = motivo.strip()
    stock_ant = producto.stock_actual

    # 1. Si era una SALIDA_ENTREGA -> Restituir stock al almacén
    if mov.tipo_movimiento == "SALIDA_ENTREGA":
        stock_res = stock_ant + mov.cantidad_salida
        producto.stock_actual = stock_res
        mov.estado = "ANULADO"
        mov.motivo_anulacion = motivo_limpio

        # Registrar movimiento compensatorio
        nro_comp = generar_comprobante(db, "MOV")
        db.add(
            MovimientoAlmacen(
                numero_comprobante=nro_comp,
                almacen_id=producto.id,
                movimiento_original_id=mov.id,
                tipo_movimiento="REVERSION_ANULACION",
                cantidad=mov.cantidad_salida,
                cantidad_entrada=mov.cantidad_salida,
                cantidad_salida=Decimal("0.00"),
                stock_anterior=stock_ant,
                stock_resultante=stock_res,
                motivo=f"Restitución por anulación de salida {mov.numero_comprobante}: {motivo_limpio}",
                fecha_movimiento=date.today(),
                usuario_registro_ci=usuario_ci,
                estado="CONFIRMADO",
            )
        )

    # 2. Si era una ENTRADA_COMPRA -> Reducir el stock si hay suficiente
    elif mov.tipo_movimiento == "ENTRADA_COMPRA":
        if stock_ant < mov.cantidad_entrada:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"No es posible anular la compra {mov.numero_comprobante}. "
                    f"Las existencias actuales ({stock_ant} {producto.unidad_control}) son menores "
                    f"a la cantidad ingresada por esta compra ({mov.cantidad_entrada} {producto.unidad_control}) "
                    f"debido a consumos posteriores."
                ),
            )
        stock_res = stock_ant - mov.cantidad_entrada
        producto.stock_actual = stock_res
        mov.estado = "ANULADO"
        mov.motivo_anulacion = motivo_limpio

        if mov.compra_id:
            compra = db.execute(select(CompraAlmacen).where(CompraAlmacen.id == mov.compra_id)).scalars().first()
            if compra:
                compra.estado = "ANULADO"
                compra.motivo_anulacion = motivo_limpio

        nro_comp = generar_comprobante(db, "MOV")
        db.add(
            MovimientoAlmacen(
                numero_comprobante=nro_comp,
                almacen_id=producto.id,
                movimiento_original_id=mov.id,
                tipo_movimiento="REVERSION_ANULACION",
                cantidad=mov.cantidad_entrada,
                cantidad_entrada=Decimal("0.00"),
                cantidad_salida=mov.cantidad_entrada,
                stock_anterior=stock_ant,
                stock_resultante=stock_res,
                motivo=f"Descuento por anulación de compra {mov.numero_comprobante}: {motivo_limpio}",
                fecha_movimiento=date.today(),
                usuario_registro_ci=usuario_ci,
                estado="CONFIRMADO",
            )
        )
    else:
        # Revertir ajuste
        if mov.cantidad_entrada > 0:
            if stock_ant < mov.cantidad_entrada:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stock insuficiente para revertir el ajuste.")
            stock_res = stock_ant - mov.cantidad_entrada
        else:
            stock_res = stock_ant + mov.cantidad_salida

        producto.stock_actual = stock_res
        mov.estado = "ANULADO"
        mov.motivo_anulacion = motivo_limpio

    registrar_bitacora(
        db=db,
        modulo="INVENTARIO_ALMACEN",
        accion="ANULACION",
        descripcion=f"Se anuló el movimiento {mov.numero_comprobante} de '{producto.nombre}'. Motivo: {motivo_limpio}",
        usuario_ci=usuario_ci,
    )

    db.commit()
    return {"mensaje": f"Movimiento {mov.numero_comprobante} anulado exitosamente. Stock actualizado a {producto.stock_actual}."}


# =========================================================================
# CONSULTAS Y LISTADOS DE ALMACÉN
# =========================================================================

def listar_productos(
    db: Session,
    busqueda: Optional[str] = None,
    estado_stock: Optional[str] = None,
    unidad_control: Optional[str] = None,
) -> List[Almacen]:
    stmt = select(Almacen).where(Almacen.estado == True).order_by(Almacen.nombre)

    if busqueda and busqueda.strip():
        term = f"%{busqueda.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Almacen.nombre).like(term),
                func.lower(Almacen.codigo).like(term),
                func.lower(Almacen.descripcion).like(term),
            )
        )

    if unidad_control and unidad_control.strip():
        stmt = stmt.where(func.lower(Almacen.unidad_control) == unidad_control.strip().lower())

    # Filtro a nivel SQL para estado_stock (evita cargar filas innecesarias a memoria)
    if estado_stock and estado_stock.upper() != "TODOS":
        st = estado_stock.strip().upper()
        if st in ("AGOTADO", "AGOTADOS"):
            stmt = stmt.where(Almacen.stock_actual <= 0)
        elif st in ("BAJO", "STOCK BAJO", "STOCK_BAJO"):
            stmt = stmt.where(Almacen.stock_actual > 0, Almacen.stock_actual <= Almacen.stock_minimo)
        elif st in ("NORMAL", "NORMALES"):
            stmt = stmt.where(Almacen.stock_actual > Almacen.stock_minimo)

    return list(db.execute(stmt).scalars().unique().all())


def buscar_productos_autocomplete(db: Session, q: str) -> List[dict]:
    term = f"%{q.strip().lower()}%"
    stmt = (
        select(Almacen)
        .where(
            Almacen.estado == True,
            or_(
                func.lower(Almacen.nombre).like(term),
                func.lower(Almacen.codigo).like(term),
            ),
        )
        .order_by(Almacen.nombre)
        .limit(15)
    )
    prods = db.execute(stmt).scalars().unique().all()
    return [
        {
            "id": p.id,
            "codigo": p.codigo,
            "nombre": p.nombre,
            "unidad_control": p.unidad_control,
            "stock_actual": p.stock_actual,
            "stock_minimo": p.stock_minimo,
            "estado_stock": p.estado_stock,
            "precio_ultima_compra": p.precio_ultima_compra,
            "fecha_ultima_compra": p.fecha_ultima_compra,
        }
        for p in prods
    ]


def obtener_producto_por_id(db: Session, producto_id: int) -> Almacen:
    p = db.execute(select(Almacen).where(Almacen.id == producto_id)).scalars().first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
    return p


def listar_movimientos(
    db: Session,
    almacen_id: Optional[int] = None,
    tipo_movimiento: Optional[str] = None,
    trabajador_id: Optional[int] = None,
    area_id: Optional[int] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
) -> List[MovimientoAlmacen]:
    stmt = select(MovimientoAlmacen).order_by(
        desc(MovimientoAlmacen.fecha_movimiento),
        desc(MovimientoAlmacen.id),
    )

    if almacen_id:
        stmt = stmt.where(MovimientoAlmacen.almacen_id == almacen_id)
    if tipo_movimiento:
        stmt = stmt.where(MovimientoAlmacen.tipo_movimiento == tipo_movimiento.upper())
    if trabajador_id:
        stmt = stmt.where(MovimientoAlmacen.trabajador_id == trabajador_id)
    if area_id:
        stmt = stmt.where(MovimientoAlmacen.area_id == area_id)
    if fecha_inicio:
        stmt = stmt.where(MovimientoAlmacen.fecha_movimiento >= fecha_inicio)
    if fecha_fin:
        stmt = stmt.where(MovimientoAlmacen.fecha_movimiento <= fecha_fin)

    return list(db.execute(stmt).scalars().unique().all())


# =========================================================================
# SERVICIOS DE GASTOS MENORES
# =========================================================================

def crear_gasto_menor(
    db: Session,
    datos: GastoMenorCreate,
    usuario_ci: Optional[str] = None,
) -> GastoMenor:
    nombre_limpio = datos.nombre.strip()
    if not nombre_limpio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre del gasto no puede estar vacío.")

    if datos.importe_total <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El importe total debe ser mayor a cero.")

    if datos.area_id:
        area = db.execute(select(Area).where(Area.id == datos.area_id)).scalars().first()
        if not area:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Área no encontrada.")

    if datos.trabajador_responsable_id:
        trab = db.execute(select(Trabajador).where(Trabajador.id == datos.trabajador_responsable_id)).scalars().first()
        if not trab:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trabajador no encontrado.")

    nro_comp = generar_comprobante(db, "GAS")
    nuevo_gasto = GastoMenor(
        numero_comprobante=nro_comp,
        nombre=nombre_limpio,
        descripcion=datos.descripcion.strip() if datos.descripcion else None,
        foto_comprobante=datos.foto_comprobante,
        importe_total=datos.importe_total,
        fecha_gasto=datos.fecha_gasto,
        area_id=datos.area_id,
        trabajador_responsable_id=datos.trabajador_responsable_id,
        metodo_pago=datos.metodo_pago.upper() if datos.metodo_pago else "EFECTIVO",
        proveedor=datos.proveedor.strip() if datos.proveedor else None,
        numero_comprobante_fiscal=datos.numero_comprobante_fiscal.strip() if datos.numero_comprobante_fiscal else None,
        usuario_registro_ci=usuario_ci,
        estado="REGISTRADO",
    )
    db.add(nuevo_gasto)

    registrar_bitacora(
        db=db,
        modulo="INVENTARIO_GASTOS",
        accion="REGISTRAR_GASTO",
        descripcion=(
            f"Se registró gasto menor {nro_comp}: '{nuevo_gasto.nombre}' por Bs {nuevo_gasto.importe_total}. "
            f"Fecha: {nuevo_gasto.fecha_gasto}. Método: {nuevo_gasto.metodo_pago}."
        ),
        usuario_ci=usuario_ci,
    )

    db.commit()
    db.refresh(nuevo_gasto)
    return nuevo_gasto


def actualizar_gasto_menor(
    db: Session,
    gasto_id: int,
    datos: GastoMenorUpdate,
    usuario_ci: Optional[str] = None,
) -> GastoMenor:
    gasto = db.execute(select(GastoMenor).where(GastoMenor.id == gasto_id)).scalars().first()
    if not gasto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gasto menor no encontrado.")
    if gasto.estado == "ANULADO":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede modificar un gasto anulado.")

    antiguo_resumen = f"Nombre: '{gasto.nombre}', Importe: Bs {gasto.importe_total}, Fecha: {gasto.fecha_gasto}"

    if datos.nombre is not None:
        gasto.nombre = datos.nombre.strip()
    if datos.descripcion is not None:
        gasto.descripcion = datos.descripcion.strip() if datos.descripcion else None
    if datos.foto_comprobante is not None:
        gasto.foto_comprobante = datos.foto_comprobante
    if datos.importe_total is not None:
        if datos.importe_total <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El importe debe ser mayor a cero.")
        gasto.importe_total = datos.importe_total
    if datos.fecha_gasto is not None:
        gasto.fecha_gasto = datos.fecha_gasto
    if datos.area_id is not None:
        gasto.area_id = datos.area_id
    if datos.trabajador_responsable_id is not None:
        gasto.trabajador_responsable_id = datos.trabajador_responsable_id
    if datos.metodo_pago is not None:
        gasto.metodo_pago = datos.metodo_pago.upper()
    if datos.proveedor is not None:
        gasto.proveedor = datos.proveedor.strip() if datos.proveedor else None
    if datos.numero_comprobante_fiscal is not None:
        gasto.numero_comprobante_fiscal = datos.numero_comprobante_fiscal.strip() if datos.numero_comprobante_fiscal else None

    gasto.estado = "CORREGIDO"
    nuevo_resumen = f"Nombre: '{gasto.nombre}', Importe: Bs {gasto.importe_total}, Fecha: {gasto.fecha_gasto}"

    registrar_bitacora(
        db=db,
        modulo="INVENTARIO_GASTOS",
        accion="EDITAR_GASTO",
        descripcion=(
            f"Se corrigió gasto menor {gasto.numero_comprobante}. "
            f"Antes: [{antiguo_resumen}]. Ahora: [{nuevo_resumen}]. Motivo: {datos.motivo_edicion.strip()}"
        ),
        usuario_ci=usuario_ci,
    )

    db.commit()
    db.refresh(gasto)
    return gasto


def anular_gasto_menor(
    db: Session,
    gasto_id: int,
    motivo: str,
    usuario_ci: Optional[str] = None,
) -> dict:
    gasto = db.execute(select(GastoMenor).where(GastoMenor.id == gasto_id)).scalars().first()
    if not gasto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gasto menor no encontrado.")
    if gasto.estado == "ANULADO":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El gasto ya se encuentra anulado.")

    motivo_limpio = motivo.strip()
    gasto.estado = "ANULADO"
    gasto.motivo_anulacion = motivo_limpio

    registrar_bitacora(
        db=db,
        modulo="INVENTARIO_GASTOS",
        accion="ANULAR_GASTO",
        descripcion=f"Se anuló el gasto menor {gasto.numero_comprobante} ('{gasto.nombre}', Bs {gasto.importe_total}). Motivo: {motivo_limpio}",
        usuario_ci=usuario_ci,
    )

    db.commit()
    return {"mensaje": f"Gasto menor {gasto.numero_comprobante} anulado exitosamente."}


def listar_gastos_menores(
    db: Session,
    busqueda: Optional[str] = None,
    area_id: Optional[int] = None,
    trabajador_id: Optional[int] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    estado: Optional[str] = None,
) -> List[GastoMenor]:
    stmt = select(GastoMenor).order_by(desc(GastoMenor.fecha_gasto), desc(GastoMenor.id))

    if busqueda and busqueda.strip():
        term = f"%{busqueda.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(GastoMenor.nombre).like(term),
                func.lower(GastoMenor.numero_comprobante).like(term),
                func.lower(GastoMenor.descripcion).like(term),
                func.lower(GastoMenor.proveedor).like(term),
            )
        )
    if area_id:
        stmt = stmt.where(GastoMenor.area_id == area_id)
    if trabajador_id:
        stmt = stmt.where(GastoMenor.trabajador_responsable_id == trabajador_id)
    if fecha_inicio:
        stmt = stmt.where(GastoMenor.fecha_gasto >= fecha_inicio)
    if fecha_fin:
        stmt = stmt.where(GastoMenor.fecha_gasto <= fecha_fin)
    if estado:
        stmt = stmt.where(GastoMenor.estado == estado.upper())

    return list(db.execute(stmt).scalars().unique().all())


# =========================================================================
# REPORTES Y RESÚMENES EJECUTIVOS
# =========================================================================

def obtener_reporte_almacen(db: Session) -> ReporteAlmacenResumen:
    # Agregaciones SQL directas (cero transferencia de imágenes Base64)
    total_prods = db.scalar(select(func.count(Almacen.id)).where(Almacen.estado == True)) or 0
    agotados = db.scalar(select(func.count(Almacen.id)).where(Almacen.estado == True, Almacen.stock_actual <= 0)) or 0
    bajos = db.scalar(
        select(func.count(Almacen.id)).where(
            Almacen.estado == True,
            Almacen.stock_actual > 0,
            Almacen.stock_actual <= Almacen.stock_minimo,
        )
    ) or 0
    normales = db.scalar(
        select(func.count(Almacen.id)).where(
            Almacen.estado == True,
            Almacen.stock_actual > Almacen.stock_minimo,
        )
    ) or 0

    valor_est = db.scalar(
        select(func.sum(Almacen.stock_actual * Almacen.precio_ultima_compra)).where(Almacen.estado == True)
    ) or Decimal("0.00")

    # Entradas y salidas del mes actual
    hoy = date.today()
    inicio_mes = date(hoy.year, hoy.month, 1)

    entradas_mes = db.scalar(
        select(func.sum(MovimientoAlmacen.cantidad_entrada)).where(
            MovimientoAlmacen.fecha_movimiento >= inicio_mes,
            MovimientoAlmacen.estado != "ANULADO",
        )
    ) or Decimal("0.00")

    salidas_mes = db.scalar(
        select(func.sum(MovimientoAlmacen.cantidad_salida)).where(
            MovimientoAlmacen.fecha_movimiento >= inicio_mes,
            MovimientoAlmacen.estado != "ANULADO",
        )
    ) or Decimal("0.00")

    return ReporteAlmacenResumen(
        total_productos=total_prods,
        productos_normal=normales,
        productos_stock_bajo=bajos,
        productos_agotados=agotados,
        total_entradas_mes=entradas_mes,
        total_salidas_mes=salidas_mes,
        valor_estimado_inventario=round(valor_est, 2),
    )


def obtener_reporte_gastos(
    db: Session,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
) -> ReporteGastosResumen:
    stmt = select(GastoMenor).where(GastoMenor.estado != "ANULADO")

    if fecha_inicio:
        stmt = stmt.where(GastoMenor.fecha_gasto >= fecha_inicio)
    if fecha_fin:
        stmt = stmt.where(GastoMenor.fecha_gasto <= fecha_fin)

    gastos = list(db.execute(stmt).scalars().unique().all())

    total_gastos = sum((g.importe_total for g in gastos), Decimal("0.00"))
    cant_gastos = len(gastos)

    # Agrupado por área
    areas_dict = {}
    for g in gastos:
        a_nom = g.area.nombre if g.area else "Sin Área"
        areas_dict[a_nom] = areas_dict.get(a_nom, Decimal("0.00")) + g.importe_total

    total_por_area = [{"area": k, "total": float(v)} for k, v in areas_dict.items()]

    # Agrupado por método
    metodos_dict = {}
    for g in gastos:
        m = g.metodo_pago
        metodos_dict[m] = metodos_dict.get(m, Decimal("0.00")) + g.importe_total

    total_por_metodo = [{"metodo": k, "total": float(v)} for k, v in metodos_dict.items()]

    return ReporteGastosResumen(
        total_gastos_mes=total_gastos,
        cantidad_gastos_mes=cant_gastos,
        total_por_area=total_por_area,
        total_por_metodo=total_por_metodo,
    )
