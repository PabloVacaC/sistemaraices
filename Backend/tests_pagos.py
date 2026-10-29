import requests
import json
from decimal import Decimal

BASE_URL = "http://127.0.0.1:8000/api"

def main():
    print("=== INICIANDO PRUEBAS DE INTEGRIDAD Y CÁLCULOS DEL MÓDULO DE PAGOS ===")
    
    # 1. Login Super Admin
    login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "juanpablovacacarvalho@gmail.com", "contraseña": "123456"}
    )
    assert login_resp.status_code == 200, f"Login falló: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] Autenticación exitosa como Super Administrador")

    # 2. Obtener períodos
    periodos_resp = requests.get(f"{BASE_URL}/pagos/periodos", headers=headers)
    assert periodos_resp.status_code == 200, f"Error al obtener períodos: {periodos_resp.text}"
    periodos = periodos_resp.json()
    assert len(periodos) > 0, "No hay períodos salariales"
    periodo = next((p for p in periodos if p["mes"] == 10 and p["anio"] == 2026), periodos[0])
    periodo_id = periodo["id"]
    print(f"[OK] Período salarial seleccionado: {periodo['descripcion']} (ID: {periodo_id})")

    # 3. Crear o seleccionar trabajador de prueba
    import time
    test_ci = f"99{int(time.time()) % 1000000:06d}"
    areas_resp = requests.get(f"{BASE_URL}/trabajadores/areas/all", headers=headers)
    area_ganaderia = next((a for a in areas_resp.json() if "Ganadería" in a["nombre"]), areas_resp.json()[0])
    
    nuevo_trab = {
        "ci": test_ci,
        "nombres": "Juan",
        "apellidos": f"Perez {test_ci[-4:]}",
        "telefono": "77123456",
        "cargo": "Operario de Campo",
        "area_id": area_ganaderia["id"],
        "sueldoBase": 3000.0,
        "estado": "ACTIVO"
    }
    crear_trab_resp = requests.post(f"{BASE_URL}/trabajadores/", json=nuevo_trab, headers=headers)
    assert crear_trab_resp.status_code == 201, f"Error creando trabajador: {crear_trab_resp.text}"
    trabajador = crear_trab_resp.json()
    print(f"[OK] Creado trabajador de prueba con CI {test_ci}: {trabajador['nombres']} {trabajador['apellidos']} (Sueldo: Bs {trabajador['sueldoBase']})")

    trabajador_id = trabajador["id"]

    # 4. CASO 1 & 2: Registro de anticipos (Bs 500 + Bs 300)
    # Primero consultar resumen antes de anticipos
    res_inicial = requests.get(
        f"{BASE_URL}/pagos/trabajador/{trabajador_id}/resumen-salarial?periodo_id={periodo_id}",
        headers=headers
    ).json()
    print(f"  Estado inicial: Sueldo={res_inicial['sueldo_base']}, Anticipos={res_inicial['total_anticipos']}, Saldo Preliminar={res_inicial['saldo_pendiente_liquidacion']}")

    # Registrar Anticipo 1: Bs 500
    ant1_payload = {
        "trabajador_id": trabajador_id,
        "periodo_id": periodo_id,
        "fecha_entrega": "2026-10-10",
        "importe": 500.0,
        "metodo_pago": "EFECTIVO",
        "observaciones": "Primer anticipo quincenal"
    }
    r_ant1 = requests.post(f"{BASE_URL}/pagos/anticipos", json=ant1_payload, headers=headers)
    assert r_ant1.status_code == 201, f"Error en anticipo 1: {r_ant1.text}"
    ant1 = r_ant1.json()
    print(f"[OK] Anticipo 1 registrado: Comprobante {ant1['numero_comprobante']}, Monto Bs {ant1['importe']}")

    # Verificar resumen salarial tras anticipo 1
    res_ant1 = requests.get(
        f"{BASE_URL}/pagos/trabajador/{trabajador_id}/resumen-salarial?periodo_id={periodo_id}",
        headers=headers
    ).json()
    assert Decimal(str(res_ant1["total_anticipos"])) == Decimal("500.00")
    assert Decimal(str(res_ant1["saldo_pendiente_liquidacion"])) == Decimal("2500.00")
    print("[OK] CASO 1 VALIDADO: Anticipo Bs 500 -> Saldo preliminar = Bs 2,500.00")

    # Registrar Anticipo 2: Bs 300
    ant2_payload = {
        "trabajador_id": trabajador_id,
        "periodo_id": periodo_id,
        "fecha_entrega": "2026-10-20",
        "importe": 300.0,
        "metodo_pago": "TRANSFERENCIA",
        "observaciones": "Segundo anticipo fin de mes"
    }
    r_ant2 = requests.post(f"{BASE_URL}/pagos/anticipos", json=ant2_payload, headers=headers)
    assert r_ant2.status_code == 201, f"Error en anticipo 2: {r_ant2.text}"
    ant2 = r_ant2.json()
    print(f"[OK] Anticipo 2 registrado: Comprobante {ant2['numero_comprobante']}, Monto Bs {ant2['importe']}")

    # Verificar resumen salarial tras anticipo 2
    res_ant2 = requests.get(
        f"{BASE_URL}/pagos/trabajador/{trabajador_id}/resumen-salarial?periodo_id={periodo_id}",
        headers=headers
    ).json()
    assert Decimal(str(res_ant2["total_anticipos"])) == Decimal("800.00")
    assert Decimal(str(res_ant2["saldo_pendiente_liquidacion"])) == Decimal("2200.00")
    print("[OK] CASO 2 VALIDADO: Total anticipos = Bs 800.00, Saldo preliminar = Bs 2,200.00")

    # 5. CASO 3: Registro de Liquidación Mensual
    # Sueldo 3000, Anticipos 800 -> Neto = Bs 2200
    liq_payload = {
        "trabajador_id": trabajador_id,
        "periodo_id": periodo_id,
        "fecha_liquidacion": "2026-10-31",
        "ajustes": 0.0,
        "observaciones": "Liquidación sueldo octubre",
        "pago_inmediato": False
    }
    r_liq = requests.post(f"{BASE_URL}/pagos/liquidaciones", json=liq_payload, headers=headers)
    assert r_liq.status_code == 201, f"Error en liquidación: {r_liq.text}"
    liq = r_liq.json()
    assert Decimal(str(liq["monto_neto"])) == Decimal("2200.00")
    assert Decimal(str(liq["saldo_pendiente"])) == Decimal("2200.00")
    assert liq["estado"] == "PENDIENTE"
    print(f"[OK] Liquidación registrada: Comprobante {liq['numero_comprobante']}, Neto Bs {liq['monto_neto']}, Saldo Bs {liq['saldo_pendiente']}")
    liq_id = liq["id"]

    # 6. CASO 5: Prevención de duplicados (intentar liquidar de nuevo el mismo período)
    r_liq_dup = requests.post(f"{BASE_URL}/pagos/liquidaciones", json=liq_payload, headers=headers)
    assert r_liq_dup.status_code == 400, "Debería rechazar liquidación duplicada"
    print("[OK] CASO 5 VALIDADO: Prevención de liquidaciones duplicadas funciona correctamente (400 Bad Request)")

    # 7. CASO 4: Pagos parciales (1200 + 1000)
    # Pago 1: Bs 1200
    pago1_payload = {
        "liquidacion_id": liq_id,
        "fecha_pago": "2026-11-05",
        "monto": 1200.0,
        "metodo_pago": "TRANSFERENCIA",
        "observaciones": "Primer pago parcial de sueldo"
    }
    r_pago1 = requests.post(f"{BASE_URL}/pagos/liquidaciones/pagos", json=pago1_payload, headers=headers)
    assert r_pago1.status_code == 201, f"Error en pago 1: {r_pago1.text}"
    pago1 = r_pago1.json()
    print(f"[OK] Pago parcial 1 registrado: Comprobante {pago1['numero_comprobante']}, Monto Bs {pago1['monto']}")

    # Consultar liquidación para verificar saldo
    liqs_actuales = requests.get(f"{BASE_URL}/pagos/liquidaciones?periodo_id={periodo_id}&trabajador_id={trabajador_id}", headers=headers).json()
    liq_despues_p1 = next(l for l in liqs_actuales if l["id"] == liq_id)
    assert Decimal(str(liq_despues_p1["monto_pagado"])) == Decimal("1200.00")
    assert Decimal(str(liq_despues_p1["saldo_pendiente"])) == Decimal("1000.00")
    assert liq_despues_p1["estado"] == "PARCIAL"
    print("[OK] CASO 4A VALIDADO: Pago 1 de Bs 1,200 -> Saldo pendiente = Bs 1,000.00, Estado = PARCIAL")

    # Intentar pagar más del saldo pendiente (Bs 1500 > Bs 1000)
    pago_exceso_payload = {
        "liquidacion_id": liq_id,
        "fecha_pago": "2026-11-08",
        "monto": 1500.0,
        "metodo_pago": "EFECTIVO"
    }
    r_exceso = requests.post(f"{BASE_URL}/pagos/liquidaciones/pagos", json=pago_exceso_payload, headers=headers)
    assert r_exceso.status_code == 400, "Debería rechazar pago superior al saldo pendiente"
    print("[OK] CASO VALIDADO: Pago superior al saldo rechazado correctamente")

    # Pago 2: Bs 1000 (saldo final)
    pago2_payload = {
        "liquidacion_id": liq_id,
        "fecha_pago": "2026-11-08",
        "monto": 1000.0,
        "metodo_pago": "EFECTIVO",
        "observaciones": "Cancelación de saldo de sueldo"
    }
    r_pago2 = requests.post(f"{BASE_URL}/pagos/liquidaciones/pagos", json=pago2_payload, headers=headers)
    assert r_pago2.status_code == 201, f"Error en pago 2: {r_pago2.text}"
    pago2 = r_pago2.json()
    print(f"[OK] Pago parcial 2 registrado: Comprobante {pago2['numero_comprobante']}, Monto Bs {pago2['monto']}")

    # Consultar liquidación para verificar saldo cero y estado LIQUIDADO
    liqs_finales = requests.get(f"{BASE_URL}/pagos/liquidaciones?periodo_id={periodo_id}&trabajador_id={trabajador_id}", headers=headers).json()
    liq_final = next(l for l in liqs_finales if l["id"] == liq_id)
    assert Decimal(str(liq_final["monto_pagado"])) == Decimal("2200.00")
    assert Decimal(str(liq_final["saldo_pendiente"])) == Decimal("0.00")
    assert liq_final["estado"] == "LIQUIDADO"
    print("[OK] CASO 4B & 3 VALIDADO: Pago 2 de Bs 1,000 -> Saldo pendiente = Bs 0.00, Estado = LIQUIDADO")

    # 8. Historial de movimientos
    historial_resp = requests.get(f"{BASE_URL}/pagos/historial/{trabajador_id}", headers=headers).json()
    movimientos = historial_resp["movimientos"]
    print(f"[OK] Historial de movimientos del trabajador ({len(movimientos)} transacciones registradas):")
    for m in movimientos:
        print(f"  - [{m['tipo']}] Comprobante: {m['numero_comprobante']} | Fecha: {m['fecha']} | Monto: Bs {m['monto']} | Estado: {m['estado']}")

    # 9. Panel General de Indicadores
    panel = requests.get(f"{BASE_URL}/pagos/panel-general?periodo_id={periodo_id}", headers=headers).json()
    print("\n=== PANEL GENERAL DE PAGOS (INDICADORES) ===")
    print(f"  Total Anticipos Entregados: Bs {panel['total_anticipos_mes']}")
    print(f"  Total Sueldos Pagados:      Bs {panel['total_sueldos_pagados_mes']}")
    print(f"  Total Dinero Entregado:     Bs {panel['total_dinero_entregado']}")
    print(f"  Total Dinero Pendiente:     Bs {panel['total_dinero_pendiente']}")
    print(f"  Liquidaciones Completadas:  {panel['liquidaciones_completadas_count']}")
    print(f"  Liquidaciones Parciales:    {panel['liquidaciones_parciales_count']}")
    print(f"  Liquidaciones Pendientes:   {panel['liquidaciones_pendientes_count']}")

    print("\n=======================================================")
    print("¡TODAS LAS PRUEBAS DE CÁLCULO E INTEGRIDAD SUPERADAS CON ÉXITO!")
    print("=======================================================")

if __name__ == "__main__":
    main()
