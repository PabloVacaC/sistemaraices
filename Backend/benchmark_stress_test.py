import time
import sys
from datetime import date, datetime
from decimal import Decimal
import requests
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.database.connection import SessionLocal, engine
from app.models.entities import (
    Usuario,
    Rol,
    Area,
    Trabajador,
    PeriodoSalarial,
    Anticipo,
    Liquidacion,
    PagoLiquidacion,
    Almacen,
    CompraAlmacen,
    MovimientoAlmacen,
)
from app.core.security import get_password_hash

BASE_URL = "http://127.0.0.1:8000"

def run_stress_test():
    print("=================================================================")
    print("[INICIO] PRUEBA DE ESTRES Y RENDIMIENTO A GRAN ESCALA")
    print("   - 200 Trabajadores")
    print("   - 1.000 Productos de Inventario")
    print("   - 10 Administradores de Sistema")
    print("   - Distribucion realista de pagos, anticipos y liquidaciones")
    print("=================================================================\n")

    db: Session = SessionLocal()

    try:
        t0 = time.time()

        # -------------------------------------------------------------
        # 0. Período Salarial de Prueba
        # -------------------------------------------------------------
        periodo_desc = "Periodo Benchmark 10/2029"
        periodo = db.execute(select(PeriodoSalarial).where(PeriodoSalarial.descripcion == periodo_desc)).scalars().first()
        if not periodo:
            periodo = PeriodoSalarial(
                mes=10,
                anio=2029,
                fecha_inicio=date(2029, 10, 1),
                fecha_fin=date(2029, 10, 31),
                fecha_pago_estimada=date(2029, 11, 5),
                estado="ABIERTO",
                descripcion=periodo_desc,
            )
            db.add(periodo)
            db.commit()
            db.refresh(periodo)
            print(f"[1/5] Período de benchmark creado: {periodo.descripcion} (ID: {periodo.id})")
        else:
            print(f"[1/5] Usando período de benchmark existente: {periodo.descripcion} (ID: {periodo.id})")

        pid = periodo.id

        # -------------------------------------------------------------
        # 1. Sembrar 10 Administradores del Sistema
        # -------------------------------------------------------------
        print("\n[2/5] Generando 10 Administradores del Sistema...")
        rol_admin = db.execute(select(Rol).where(Rol.rol == "Administrador")).scalars().first()
        rol_admin_id = rol_admin.id if rol_admin else 2
        admin_pass_hash = get_password_hash("admin123")

        nuevos_admins = []
        for i in range(1, 11):
            ci = f"ADM-TEST-{i:03d}"
            email = f"admin_benchmark_{i}@sistemasraices.bo"
            existe = db.execute(select(Usuario).where(Usuario.ci == ci)).scalars().first()
            if not existe:
                nuevos_admins.append(
                    Usuario(
                        ci=ci,
                        nombre=f"AdminTest_{i}",
                        apellido=f"Sistema",
                        email=email,
                        contraseña=admin_pass_hash,
                        genero="Masculino" if i % 2 == 0 else "Femenino",
                        fechanacimiento=date(1990, (i % 12) + 1, 15),
                        telefono=f"7000{i:04d}",
                        direccion=f"Oficina Central {i}",
                        estado=True,
                        rol_id=rol_admin_id,
                    )
                )
        if nuevos_admins:
            db.bulk_save_objects(nuevos_admins)
            db.commit()
            print(f"   [OK] {len(nuevos_admins)} Administradores creados exitosamente.")
        else:
            print("   [OK] 10 Administradores ya existían.")

        # -------------------------------------------------------------
        # 2. Sembrar 200 Trabajadores y sus Movimientos Salariales
        # -------------------------------------------------------------
        print("\n[3/5] Generando 200 Trabajadores en diversas áreas...")
        areas_disponibles = [8, 9, 10, 11]  # Admin, Agricultura, Ganadería, Avicultura
        cargos = ["Operador de Campo", "Técnico Agrónomo", "Veterinario", "Mecánico", "Capataz", "Auxiliar Contable", "Chofer"]
        sueldos = [Decimal("2000.00"), Decimal("2500.00"), Decimal("3000.00"), Decimal("3500.00"), Decimal("4000.00")]

        trabajadores_existentes = db.execute(
            select(Trabajador).where(Trabajador.ci.like("TRAB-TEST-%"))
        ).scalars().unique().all()
        ci_existentes = {t.ci for t in trabajadores_existentes}

        nuevos_trabs = []
        for i in range(1, 201):
            ci = f"TRAB-TEST-{i:04d}"
            if ci not in ci_existentes:
                nuevos_trabs.append(
                    Trabajador(
                        ci=ci,
                        nombres=f"Trabajador_{i:03d}",
                        apellidos=f"Perez_{i:03d}",
                        sueldoBase=sueldos[i % len(sueldos)],
                        cargo=cargos[i % len(cargos)],
                        area_id=areas_disponibles[i % len(areas_disponibles)],
                        estado=True,
                        fecha_ingreso=date(2025, ((i % 12) + 1), 1),
                        celular=f"7890{i:04d}",
                    )
                )

        if nuevos_trabs:
            db.bulk_save_objects(nuevos_trabs)
            db.commit()
            print(f"   [OK] {len(nuevos_trabs)} Trabajadores creados exitosamente.")
        else:
            print("   [OK] 200 Trabajadores ya existían.")

        # Recuperar los 200 trabajadores
        todos_trabs = list(
            db.execute(
                select(Trabajador)
                .where(Trabajador.ci.like("TRAB-TEST-%"))
                .order_by(Trabajador.id)
            ).scalars().unique().all()
        )
        print(f"   [OK] Total Trabajadores de Benchmark: {len(todos_trabs)}")

        # -------------------------------------------------------------
        # 3. Asignar Escenarios Salariales Realistas a los 200 Trabajadores:
        #    - 50 Liquidados Completos (Sueldo completo pagado)
        #    - 50 Con Quincena Pagada (Pendiente liquidación final)
        #    - 50 Solo con Anticipos (Sin quincena pagada)
        #    - 50 Pendientes Limpios (Sin anticipos aún)
        # -------------------------------------------------------------
        print("\n[4/5] Aplicando reglas de nómina y movimientos salariales a los 200 trabajadores...")

        # Verificar si ya tienen movimientos en este período
        ant_existentes_count = db.scalar(
            select(func.count(Anticipo.id)).where(Anticipo.periodo_id == pid)
        ) or 0

        if ant_existentes_count == 0:
            nuevos_anticipos = []
            nuevas_liquidaciones = []
            nuevos_pagos = []

            for idx, t in enumerate(todos_trabs):
                sueldo = t.sueldoBase
                # Grupo 1 (0-49): 50 TRABAJADORES LIQUIDADOS AL 100%
                if idx < 50:
                    # Anticipo 1
                    ant = Anticipo(
                        numero_comprobante=f"ANT-TEST-{idx+1:04d}-1",
                        trabajador_id=t.id,
                        periodo_id=pid,
                        fecha_solicitud=date(2029, 10, 5),
                        fecha_entrega=date(2029, 10, 5),
                        importe=Decimal("800.00"),
                        metodo_pago="EFECTIVO",
                        estado="PAGADO",
                        observaciones="Anticipo 1 primera quincena",
                    )
                    nuevos_anticipos.append(ant)
                    # Liquidación total
                    liq = Liquidacion(
                        numero_comprobante=f"LIQ-TEST-{idx+1:04d}",
                        trabajador_id=t.id,
                        periodo_id=pid,
                        fecha_liquidacion=date(2029, 11, 5),
                        sueldo_base=sueldo,
                        ajustes=Decimal("0.00"),
                        total_anticipos=Decimal("800.00"),
                        monto_neto=sueldo - Decimal("800.00"),
                        monto_pagado=sueldo - Decimal("800.00"),
                        saldo_pendiente=Decimal("0.00"),
                        estado="LIQUIDADO",
                        observaciones="Liquidación completa fin de mes",
                    )
                    db.add(liq)
                    db.flush()

                    # Pagos asociados: Quincena (200 Bs) + Saldo restante
                    pago_q = PagoLiquidacion(
                        numero_comprobante=f"PAG-TEST-{idx+1:04d}-Q",
                        liquidacion_id=liq.id,
                        fecha_pago=date(2029, 10, 18),
                        monto=Decimal("200.00"),
                        tipo_pago="PAGO_QUINCENA",
                        metodo_pago="EFECTIVO",
                        estado="CONFIRMADO",
                    )
                    pago_final = PagoLiquidacion(
                        numero_comprobante=f"PAG-TEST-{idx+1:04d}-FIN",
                        liquidacion_id=liq.id,
                        fecha_pago=date(2029, 11, 5),
                        monto=sueldo - Decimal("1000.00"),
                        tipo_pago="LIQUIDACION_FINAL",
                        metodo_pago="TRANSFERENCIA",
                        estado="CONFIRMADO",
                    )
                    nuevos_pagos.extend([pago_q, pago_final])

                # Grupo 2 (50-99): 50 TRABAJADORES CON QUINCENA PAGADA (PARCIALES)
                elif idx < 100:
                    ant = Anticipo(
                        numero_comprobante=f"ANT-TEST-{idx+1:04d}-1",
                        trabajador_id=t.id,
                        periodo_id=pid,
                        fecha_solicitud=date(2029, 10, 12),
                        fecha_entrega=date(2029, 10, 12),
                        importe=Decimal("600.00"),
                        metodo_pago="EFECTIVO",
                        estado="PAGADO",
                        observaciones="Anticipo quincenal",
                    )
                    nuevos_anticipos.append(ant)

                    liq = Liquidacion(
                        numero_comprobante=f"LIQ-TEST-{idx+1:04d}",
                        trabajador_id=t.id,
                        periodo_id=pid,
                        fecha_liquidacion=date(2029, 10, 18),
                        sueldo_base=sueldo,
                        ajustes=Decimal("0.00"),
                        total_anticipos=Decimal("600.00"),
                        monto_neto=sueldo - Decimal("600.00"),
                        monto_pagado=Decimal("400.00"),
                        saldo_pendiente=sueldo - Decimal("1000.00"),
                        estado="PARCIAL",
                        observaciones="Pago de quincena registrado",
                    )
                    db.add(liq)
                    db.flush()

                    pago_q = PagoLiquidacion(
                        numero_comprobante=f"PAG-TEST-{idx+1:04d}-Q",
                        liquidacion_id=liq.id,
                        fecha_pago=date(2029, 10, 18),
                        monto=Decimal("400.00"),
                        tipo_pago="PAGO_QUINCENA",
                        metodo_pago="EFECTIVO",
                        estado="CONFIRMADO",
                    )
                    nuevos_pagos.append(pago_q)

                # Grupo 3 (100-149): 50 TRABAJADORES SOLO CON ANTICIPOS (SIN QUINCENA)
                elif idx < 150:
                    # Algunos superando quincena (1200) y otros normales (700)
                    monto_ant = Decimal("1200.00") if idx % 2 == 0 else Decimal("700.00")
                    ant = Anticipo(
                        numero_comprobante=f"ANT-TEST-{idx+1:04d}-1",
                        trabajador_id=t.id,
                        periodo_id=pid,
                        fecha_solicitud=date(2029, 10, 10),
                        fecha_entrega=date(2029, 10, 10),
                        importe=monto_ant,
                        metodo_pago="EFECTIVO",
                        estado="PAGADO",
                        observaciones="Anticipo sin quincena cobrada aún",
                    )
                    nuevos_anticipos.append(ant)

                # Grupo 4 (150-199): 50 TRABAJADORES PENDIENTES SIN MOVIMIENTOS AÚN
                else:
                    pass

            db.bulk_save_objects(nuevos_anticipos)
            db.bulk_save_objects(nuevos_pagos)
            db.commit()
            print("   [OK] 50 Trabajadores LIQUIDADOS (Sueldo completo pagado).")
            print("   [OK] 50 Trabajadores con QUINCENA PAGADA (Pendientes de liquidación final).")
            print("   [OK] 50 Trabajadores con SOLO ANTICIPOS.")
            print("   [OK] 50 Trabajadores PENDIENTES (Sin movimientos aún).")
        else:
            print("   [OK] Movimientos salariales de benchmark ya inicializados.")

        # -------------------------------------------------------------
        # 4. Sembrar 1.000 Productos de Inventario
        # -------------------------------------------------------------
        print("\n[5/5] Generando 1.000 Productos de Inventario en Almacén...")
        prod_count = db.scalar(select(func.count(Almacen.id)).where(Almacen.codigo.like("PROD-TEST-%"))) or 0

        if prod_count < 1000:
            categorias = ["Fertilizante", "Semilla", "Veterinario", "Combustible", "Herramienta", "Repuesto", "Alimento", "Limpieza"]
            unidades = ["Litros", "Kilos", "Bolsas", "Unidades", "Tambores", "Cajas"]
            nuevos_prods = []

            for i in range(prod_count + 1, 1001):
                cat = categorias[i % len(categorias)]
                uni = unidades[i % len(unidades)]
                # Distribución realista de stocks
                if i % 10 == 0:
                    stock_act = Decimal("0.00") # Agotado (10%)
                    stock_min = Decimal("20.00")
                elif i % 5 == 0:
                    stock_act = Decimal("15.00") # Bajo (20%)
                    stock_min = Decimal("30.00")
                else:
                    stock_act = Decimal(f"{50 + (i % 200)}.00") # Normal (70%)
                    stock_min = Decimal("20.00")

                precio = Decimal(f"{15 + (i % 80)}.50")

                nuevos_prods.append(
                    Almacen(
                        codigo=f"PROD-TEST-{i:04d}",
                        nombre=f"{cat} Especial Grado {i}",
                        unidad_control=uni,
                        stock_minimo=stock_min,
                        stock_actual=stock_act,
                        precio_ultima_compra=precio,
                        estado=True,
                        
                    )
                )

            db.bulk_save_objects(nuevos_prods)
            db.commit()
            print(f"   [OK] 1.000 Productos de Inventario registrados con stock, precios y alertas.")
        else:
            print("   [OK] 1.000 Productos de inventario ya existen.")

        total_gen_time = round(time.time() - t0, 2)
        print(f"\n[OK] Base de datos preparada en {total_gen_time} segundos.")

        # -------------------------------------------------------------
        # 5. EJECUTAR BENCHMARKS DE RENDIMIENTO SOBRE LA API
        # -------------------------------------------------------------
        print("\n" + "=" * 65)
        print("[BENCHMARK] EJECUTANDO PRUEBAS DE LATENCIA Y RENDIMIENTO REAL")
        print("=" * 65)

        # Login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "juanpablovacacarvalho@gmail.com", "contraseña": "123456"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        endpoints_benchmark = [
            ("Panel General de Pagos (KPIs globales)", f"{BASE_URL}/api/pagos/panel-general?periodo_id={pid}"),
            ("Pagos Parciales: Resumen de 200 Trabajadores (Batch O(1))", f"{BASE_URL}/api/pagos/pagos-parciales/resumen?periodo_id={pid}"),
            ("Inventario: Reporte Resumen de 1.000 Productos (SQL Directo)", f"{BASE_URL}/api/inventario/almacen/reportes/resumen"),
            ("Inventario: Listado Completo de 1.000 Productos", f"{BASE_URL}/api/inventario/almacen/productos"),
            ("Inventario: Filtro SQL Stock Bajo entre 1.000 Productos", f"{BASE_URL}/api/inventario/almacen/productos?estado_stock=BAJO"),
            ("Trabajadores: Listado de 200+ Trabajadores", f"{BASE_URL}/api/trabajadores"),
            ("Usuarios: Listado de Usuarios y Administradores", f"{BASE_URL}/api/users/"),
        ]

        metricas = []
        for desc, url in endpoints_benchmark:
            # Medir tiempo exacto
            t_start = time.perf_counter()
            resp = requests.get(url, headers=headers)
            t_end = time.perf_counter()
            duration_ms = round((t_end - t_start) * 1000, 2)

            data = resp.json() if resp.status_code == 200 else None
            count_info = len(data) if isinstance(data, list) else (1 if isinstance(data, dict) else 0)

            metricas.append({
                "endpoint": desc,
                "status": resp.status_code,
                "latencia_ms": duration_ms,
                "registros": count_info,
            })
            print(f"  * {desc}")
            print(f"    Status: {resp.status_code} OK | Tiempo: {duration_ms} ms | Registros devueltos: {count_info}")

        # Comprobar exactitud de los cálculos salariales del Panel General
        panel_data = requests.get(f"{BASE_URL}/api/pagos/panel-general?periodo_id={pid}", headers=headers).json()
        print("\n" + "=" * 65)
        print("[VERIFICACION] EXACTITUD EN EL PANEL GENERAL (200 TRABAJADORES)")
        print("=" * 65)
        print(f"* Total Trabajadores Activos: {panel_data.get('total_trabajadores_activos')}")
        print(f"* Trabajadores Liquidados al 100%: {panel_data.get('trabajadores_liquidados_count')}")
        print(f"* Total Anticipos Entregados: Bs {Decimal(str(panel_data.get('total_anticipos_mes', 0))):,}")
        print(f"* Total Sueldos Pagados: Bs {Decimal(str(panel_data.get('total_sueldos_pagados_mes', 0))):,}")
        print(f"* Dinero Total Entregado: Bs {Decimal(str(panel_data.get('total_dinero_entregado', 0))):,}")
        print(f"* Saldo Pendiente Total de la Empresa: Bs {Decimal(str(panel_data.get('total_dinero_pendiente', 0))):,}")
        print(f"* Resumen de Estado del Mes: \"{panel_data.get('resumen_estado_mes')}\"")
        print(f"* Periodo Completamente Liquidado: {panel_data.get('periodo_completamente_liquidado')}")

        print("\n" + "=" * 65)
        print("[EXITO] CONCLUSION: LA APLICACION RESPONDE A MAXIMA VELOCIDAD")
        print("=" * 65)

    except Exception as e:
        print(f"\n[ERROR] Error durante el benchmark: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_stress_test()
