from decimal import Decimal
from datetime import date
from app.database.connection import SessionLocal
from app.models.entities import PeriodoSalarial, Trabajador, Descuento, Usuario
from app.modules.planilla import service
from app.modules.planilla.schemas import (
    ActualizarDiasTrabajadosIn,
    DescuentoCreate,
)

db = SessionLocal()
print("--- 1. Probando carga de planilla para Octubre 2026 (Periodo 2) ---")
planilla = service.obtener_o_generar_planilla(db, 2)
print(f"Periodo: {planilla.periodo_descripcion} (Estado: {planilla.estado_periodo})")
print(f"Total trabajadores en planilla: {len(planilla.filas)}")
assert len(planilla.filas) > 0, "Debe haber trabajadores en la planilla"

for f in planilla.filas[:3]:
    print(f"\nFila #{f.nro}: {f.nombre_completo} (CI: {f.ci}) - {f.cargo} ({f.area})")
    print(f"  Ingreso: {f.fecha_ingreso} | Haber: Bs {f.haber_basico} | Días: {f.dias_trabajados} (Manual: {f.dias_manual})")
    print(f"  Total Ganado: Bs {f.total_ganado}")
    print(f"  Quincena: Bs {f.pago_quincena} ({f.estado_quincena}) | Sugerida: Bs {f.quincena_sugerida}")
    print(f"  Anticipos: Bs {f.pago_anticipos} (Cant: {f.anticipos_count})")
    print(f"  Descuentos: Bs {f.total_descuentos} (Cant: {f.descuentos_count})")
    print(f"  Total Ant+Desc: Bs {f.total_anticipos_descuentos}")
    print(f"  Líquido Pagable: Bs {f.liquido_pagable}")
    print(f"  Estado Liq: {f.estado_liquidacion} | Saldo Pend: Bs {f.saldo_pendiente_real}")

print("\nTotales de la Planilla:")
print(f"  Haber Base Total: Bs {planilla.totales.total_haber_basico}")
print(f"  Total Ganado: Bs {planilla.totales.total_ganado}")
print(f"  Total Quincenas: Bs {planilla.totales.total_quincena}")
print(f"  Total Anticipos: Bs {planilla.totales.total_anticipos}")
print(f"  Total Descuentos: Bs {planilla.totales.total_descuentos}")
print(f"  Total Líquido Pagable: Bs {planilla.totales.total_liquido_pagable}")

print("\n--- 2. Probando registro de un Descuento en Noviembre 2026 (Periodo 4, ABIERTO) ---")
trab = db.query(Trabajador).first()
user = db.query(Usuario).first()
admin_ci = user.ci if user else None
print(f"Usuario admin CI: {admin_ci}")

desc_in = DescuentoCreate(
    trabajador_id=trab.id,
    periodo_id=4,
    fecha=date(2026, 11, 2),
    importe=Decimal("150.00"),
    concepto="Descuento por daño menor de herramienta",
    observaciones="Prueba automatizada de descuento dinámico",
)
desc_creado = service.registrar_descuento(db, desc_in, usuario_ci=admin_ci)
print(f"Descuento creado: {desc_creado.numero_comprobante} - Bs {desc_creado.importe} ({desc_creado.concepto})")
assert desc_creado.numero_comprobante.startswith("DESC-")

print("\n--- 3. Probando actualización de días trabajados en Noviembre 2026 (Periodo 4) ---")
fila_act = service.actualizar_dias_trabajados(
    db,
    ActualizarDiasTrabajadosIn(
        trabajador_id=trab.id,
        periodo_id=4,
        dias_trabajados=20,
        observaciones="Ajuste a 20 días por permiso no remunerado",
    ),
    usuario_ci=admin_ci,
)
print(f"Trabajador: {fila_act.nombre_completo}")
print(f"Días ajustados: {fila_act.dias_trabajados} | Total ganado recalculado: Bs {fila_act.total_ganado}")
esperado = round((fila_act.haber_basico / Decimal("30")) * Decimal("20"), 2)
assert fila_act.total_ganado == esperado, f"Esperado {esperado}, obtenido {fila_act.total_ganado}"
print(f"Verificación de fórmula exacta exitosa: {fila_act.total_ganado} == {esperado}")

print("\n--- 4. Probando anulación del descuento ---")
desc_anulado = service.anular_descuento(db, desc_creado.id, "Error de digitación", usuario_ci=admin_ci)
print(f"Descuento {desc_anulado.numero_comprobante} estado: {desc_anulado.estado}")
assert desc_anulado.estado == "ANULADO"

print("\n¡TODAS LAS PRUEBAS DE LA ETAPA 2 (BACKEND) PASARON CON ÉXITO!")
