import requests
import json
from decimal import Decimal

BASE_URL = "http://127.0.0.1:8000/api"

def main():
    print("=== INICIANDO PRUEBAS DE INTEGRIDAD DEL MÓDULO DE INVENTARIO ===")

    # 1. Login Super Admin
    login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "juanpablovacacarvalho@gmail.com", "contraseña": "123456"}
    )
    assert login_resp.status_code == 200, f"Login falló: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] Autenticación exitosa como Super Administrador")

    # 2. Obtener áreas y trabajadores para salidas
    areas = requests.get(f"{BASE_URL}/trabajadores/areas/all", headers=headers).json()
    area_ganaderia = next((a for a in areas if "Ganadería" in a["nombre"]), areas[0])
    area_agricultura = next((a for a in areas if "Agricultura" in a["nombre"]), areas[0])

    trabajadores = requests.get(f"{BASE_URL}/trabajadores/", headers=headers).json()
    trabajador = trabajadores[0]
    print(f"[OK] Trabajador de prueba: {trabajador['nombres']} {trabajador['apellidos']} (ID: {trabajador['id']})")
    print(f"[OK] Áreas de prueba: {area_ganaderia['nombre']}, {area_agricultura['nombre']}")

    # 3. CASO: CREAR PRODUCTO CON PRIMERA COMPRA DIRECTA
    import time
    ts = int(time.time()) % 100000
    prod_directo = {
        "nombre": f"Diésel Premium #{ts}",
        "descripcion": "Combustible diésel para maquinaria pesada",
        "unidad_control": "Litros",
        "stock_minimo": 150.0,
        "cantidad_comprada": 500.0,
        "unidad_compra": "Litros",
        "equivalencia_unidad": 1.0,
        "precio_total": 1850.0,
        "fecha_compra": "2026-10-28",
        "proveedor": "YPFB",
        "numero_factura": f"FCT-{ts}",
        "observaciones": "Lote inicial de combustible"
    }
    resp1 = requests.post(f"{BASE_URL}/inventario/almacen/productos", json=prod_directo, headers=headers)
    assert resp1.status_code == 201, f"Error creando producto directo: {resp1.text}"
    p1 = resp1.json()
    print(f"[OK] Producto directo creado: {p1['codigo']} - {p1['nombre']}")
    assert float(p1["stock_actual"]) == 500.0, f"Stock incorrecto: {p1['stock_actual']}"
    assert float(p1["precio_ultima_compra"]) == 3.70, f"Precio unitario incorrecto: {p1['precio_ultima_compra']}"
    assert p1["estado_stock"] == "Normal", f"Estado de stock incorrecto: {p1['estado_stock']}"
    print(f"  Validado: Stock={p1['stock_actual']} {p1['unidad_control']}, Precio Unitario=Bs {p1['precio_ultima_compra']}, Estado={p1['estado_stock']}")

    # 4. CASO: CREAR PRODUCTO CON PRESENTACIÓN Y EQUIVALENCIA
    prod_sacos = {
        "nombre": f"Alimento Balanceado Bovino #{ts}",
        "descripcion": "Concentrado para engorde de ganado",
        "unidad_control": "Kilogramos",
        "stock_minimo": 100.0,
        "cantidad_comprada": 10.0,
        "unidad_compra": "Sacos de 40 kg",
        "equivalencia_unidad": 40.0,  # 10 sacos * 40 kg = 400 kg
        "precio_total": 2000.0,      # Bs 2000 / 400 kg = Bs 5.00 por kg
        "fecha_compra": "2026-10-20",
        "proveedor": "Molinos del Oriente",
        "numero_factura": f"FAC-{ts}-A",
        "observaciones": "Primera compra de alimento balanceado"
    }
    resp2 = requests.post(f"{BASE_URL}/inventario/almacen/productos", json=prod_sacos, headers=headers)
    assert resp2.status_code == 201, f"Error creando producto con equivalencias: {resp2.text}"
    p2 = resp2.json()
    p2_id = p2["id"]
    print(f"[OK] Producto con equivalencia creado: {p2['codigo']} - {p2['nombre']}")
    assert float(p2["stock_actual"]) == 400.0, f"Stock esperado 400.0, recibido {p2['stock_actual']}"
    assert float(p2["precio_ultima_compra"]) == 5.00, f"Precio unitario esperado 5.00, recibido {p2['precio_ultima_compra']}"
    print(f"  Validado: 10 sacos x 40 kg = {p2['stock_actual']} kg a Bs {p2['precio_ultima_compra']}/kg")

    # 5. CASO: COMPRA POSTERIOR CON DETECCIÓN DE VARIACIÓN DE PRECIO
    # Comprar 5 sacos a Bs 1200 -> 200 kg total -> Bs 6.00 por kg (aumento de 20%)
    compra_posterior = {
        "almacen_id": p2_id,
        "cantidad_comprada": 5.0,
        "unidad_compra": "Sacos de 40 kg",
        "equivalencia_unidad": 40.0,
        "precio_total": 1200.0,  # 200 kg a Bs 1200 = Bs 6.00/kg
        "fecha_compra": "2026-10-28",
        "proveedor": "Molinos del Oriente",
        "numero_factura": f"FAC-{ts}-B",
        "observaciones": "Reposición con nuevo precio"
    }
    resp_compra2 = requests.post(f"{BASE_URL}/inventario/almacen/compras", json=compra_posterior, headers=headers)
    assert resp_compra2.status_code == 201, f"Error en compra posterior: {resp_compra2.text}"
    c2 = resp_compra2.json()
    print(f"[OK] Compra posterior registrada: {c2['numero_comprobante']}")
    assert float(c2["precio_unitario"]) == 6.00, f"Precio unitario esperado 6.00, recibido {c2['precio_unitario']}"
    assert float(c2["precio_unitario_anterior"]) == 5.00, f"Precio anterior esperado 5.00, recibido {c2['precio_unitario_anterior']}"
    assert float(c2["variacion_porcentual"]) == 20.00, f"Variación porcentual esperada +20.00%, recibido {c2['variacion_porcentual']}%"
    print(f"  Validado: Precio anterior: Bs {c2['precio_unitario_anterior']}, Nuevo: Bs {c2['precio_unitario']}, Variación: +{c2['variacion_porcentual']}%")

    # Verificar stock acumulado del producto (400 + 200 = 600 kg)
    detalle = requests.get(f"{BASE_URL}/inventario/almacen/productos/{p2_id}", headers=headers).json()
    assert float(detalle["stock_actual"]) == 600.0, f"Stock total esperado 600.0, recibido {detalle['stock_actual']}"
    assert len(detalle["compras"]) == 2, f"Deben haber 2 compras, hay {len(detalle['compras'])}"
    assert len(detalle["movimientos"]) == 2, f"Deben haber 2 movimientos de entrada, hay {len(detalle['movimientos'])}"
    print(f"[OK] Stock actual consolidado: {detalle['stock_actual']} kg en 2 compras")

    # 6. CASO: RECHAZO DE SALIDA QUE SUPERA EL STOCK DISPONIBLE
    salida_excesiva = {
        "almacen_id": p2_id,
        "cantidad": 700.0,  # Stock disponible es 600
        "trabajador_id": trabajador["id"],
        "area_id": area_ganaderia["id"],
        "motivo": "Intento de salida excesiva"
    }
    resp_sal_exc = requests.post(f"{BASE_URL}/inventario/almacen/salidas", json=salida_excesiva, headers=headers)
    assert resp_sal_exc.status_code == 400, f"Debería haber sido rechazado: {resp_sal_exc.text}"
    print(f"[OK] Salida excesiva rechazada correctamente: '{resp_sal_exc.json()['detail']}'")

    # 7. CASO: SALIDA VÁLIDA QUE DEJA STOCK BAJO
    # Retirar 550 kg -> Stock restante: 50 kg (stock_minimo es 100) -> Estado: "Stock bajo"
    salida_valida = {
        "almacen_id": p2_id,
        "cantidad": 550.0,
        "trabajador_id": trabajador["id"],
        "area_id": area_ganaderia["id"],
        "motivo": "Alimentación diaria lote lechero corral 4",
        "vehiculo_maquinaria": "Carro mezclador #2"
    }
    resp_sal1 = requests.post(f"{BASE_URL}/inventario/almacen/salidas", json=salida_valida, headers=headers)
    assert resp_sal1.status_code == 201, f"Error en salida válida: {resp_sal1.text}"
    sal1 = resp_sal1.json()
    print(f"[OK] Salida registrada: {sal1['numero_comprobante']}, Cantidad: {sal1['cantidad_salida']} kg")
    assert float(sal1["stock_resultante"]) == 50.0, f"Stock resultante esperado 50.0, recibido {sal1['stock_resultante']}"

    detalle_post_sal = requests.get(f"{BASE_URL}/inventario/almacen/productos/{p2_id}", headers=headers).json()
    assert detalle_post_sal["estado_stock"] == "Stock bajo", f"Estado esperado 'Stock bajo', recibido {detalle_post_sal['estado_stock']}"
    print(f"  Validado: Stock={detalle_post_sal['stock_actual']} kg <= Stock Minimo={detalle_post_sal['stock_minimo']} -> Alerta: {detalle_post_sal['estado_stock']}")

    # 8. CASO: SALIDA QUE AGOTA EL STOCK
    # Retirar los 50 kg restantes -> Stock resultante: 0 -> Estado: "Agotado"
    salida_agotar = {
        "almacen_id": p2_id,
        "cantidad": 50.0,
        "trabajador_id": trabajador["id"],
        "area_id": area_ganaderia["id"],
        "motivo": "Consumo de reserva final de alimento"
    }
    resp_sal2 = requests.post(f"{BASE_URL}/inventario/almacen/salidas", json=salida_agotar, headers=headers)
    assert resp_sal2.status_code == 201
    sal2 = resp_sal2.json()
    mov_sal2_id = sal2["id"]
    detalle_agotado = requests.get(f"{BASE_URL}/inventario/almacen/productos/{p2_id}", headers=headers).json()
    assert float(detalle_agotado["stock_actual"]) == 0.0
    assert detalle_agotado["estado_stock"] == "Agotado"
    print(f"[OK] Stock agotado correctamente: Stock=0, Alerta: {detalle_agotado['estado_stock']}")

    # 9. CASO: ANULACIÓN DE SALIDA CON RESTITUCIÓN DE EXISTENCIAS
    anulacion_salida = {
        "motivo": "Salida registrada por error en corral equivocado"
    }
    resp_anular = requests.patch(f"{BASE_URL}/inventario/almacen/movimientos/{mov_sal2_id}/anular", json=anulacion_salida, headers=headers)
    assert resp_anular.status_code == 200, f"Error al anular: {resp_anular.text}"
    print(f"[OK] Salida anulada: {resp_anular.json()['mensaje']}")

    detalle_restituido = requests.get(f"{BASE_URL}/inventario/almacen/productos/{p2_id}", headers=headers).json()
    assert float(detalle_restituido["stock_actual"]) == 50.0
    assert detalle_restituido["estado_stock"] == "Stock bajo"
    print(f"  Validado: Stock restituido automáticamente a {detalle_restituido['stock_actual']} kg")

    # 10. CASO: GASTOS MENORES (NO AFECTA EL STOCK DEL ALMACÉN)
    gasto_data = {
        "nombre": "Cambio de aceite y filtros tractor John Deere",
        "descripcion": "Mantenimiento realizado en taller externo de Montero",
        "importe_total": 450.0,
        "fecha_gasto": "2026-10-28",
        "area_id": area_agricultura["id"],
        "trabajador_responsable_id": trabajador["id"],
        "metodo_pago": "EFECTIVO",
        "proveedor": "Taller Mecánico Central",
        "numero_comprobante_fiscal": "FAC-88992"
    }
    resp_gasto = requests.post(f"{BASE_URL}/inventario/gastos", json=gasto_data, headers=headers)
    assert resp_gasto.status_code == 201, f"Error al registrar gasto: {resp_gasto.text}"
    gasto = resp_gasto.json()
    gasto_id = gasto["id"]
    print(f"[OK] Gasto menor registrado: {gasto['numero_comprobante']} - '{gasto['nombre']}' por Bs {gasto['importe_total']}")

    # Verificar que el stock de Almacén no cambió
    detalle_check = requests.get(f"{BASE_URL}/inventario/almacen/productos/{p2_id}", headers=headers).json()
    assert float(detalle_check["stock_actual"]) == 50.0, "¡EL GASTO MENOR NO DEBE AFECTAR EL STOCK DEL ALMACÉN!"
    print(f"[OK] Verificación estricta: El gasto menor NO alteró el stock del almacén (Sigue en {detalle_check['stock_actual']} kg)")

    # 11. CASO: ANULACIÓN DE GASTO MENOR
    resp_anular_gasto = requests.patch(
        f"{BASE_URL}/inventario/gastos/{gasto_id}/anular",
        json={"motivo": "Comprobante duplicado por error administrativo"},
        headers=headers
    )
    assert resp_anular_gasto.status_code == 200
    print(f"[OK] Gasto menor anulado correctamente: {resp_anular_gasto.json()['mensaje']}")

    # 12. CASO: REPORTES DE ALMACÉN Y GASTOS
    rep_alm = requests.get(f"{BASE_URL}/inventario/almacen/reportes/resumen", headers=headers).json()
    print(f"[OK] Reporte Almacén: {rep_alm['total_productos']} productos ({rep_alm['productos_normal']} Normal, {rep_alm['productos_stock_bajo']} Bajo, {rep_alm['productos_agotados']} Agotados), Valor estimado: Bs {rep_alm['valor_estimado_inventario']}")

    rep_gas = requests.get(f"{BASE_URL}/inventario/gastos/reportes/resumen", headers=headers).json()
    print(f"[OK] Reporte Gastos: Total Bs {rep_gas['total_gastos_mes']} ({rep_gas['cantidad_gastos_mes']} gastos registrados)")

    print("\n=======================================================")
    print("¡TODAS LAS PRUEBAS DEL BACKEND DE INVENTARIO SUPERADAS CON ÉXITO!")
    print("=======================================================")

if __name__ == "__main__":
    main()

