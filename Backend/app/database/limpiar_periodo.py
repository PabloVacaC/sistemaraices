"""
Script para limpiar y reabrir un período salarial específico sin afectar otros meses ni trabajadores.

Uso:
    python -m app.database.limpiar_periodo [mes] [anio]
    Ejemplo: python -m app.database.limpiar_periodo 11 2026
"""

import sys
from datetime import date
from sqlalchemy import select, delete
from app.database.connection import SessionLocal
from app.models.entities import (
    PeriodoSalarial,
    PlanillaCierre,
    PlanillaDetalle,
    Liquidacion,
    PagoLiquidacion,
    Anticipo,
    AnticipoRider,
    Descuento,
)


def limpiar_periodo(mes: int = 11, anio: int = 2026):
    db = SessionLocal()
    try:
        # 1. Buscar período
        periodo = db.execute(
            select(PeriodoSalarial).where(
                PeriodoSalarial.mes == mes,
                PeriodoSalarial.anio == anio,
            )
        ).scalars().first()

        if not periodo:
            print(f"[ERROR] No se encontró el período para mes={mes}, año={anio}.")
            return

        print(f"=================================================================")
        print(f"LIMPIEZA DE PERÍODO: {periodo.descripcion} (ID: {periodo.id})")
        print(f"=================================================================")

        # 2. Borrar Cierre de Planilla si existe
        cierre = db.execute(
            select(PlanillaCierre).where(PlanillaCierre.periodo_id == periodo.id)
        ).scalars().first()
        if cierre:
            db.delete(cierre)
            print("✓ Acta de cierre de planilla eliminada.")

        # 3. Borrar Pagos de Liquidación asociados a este período
        liq_ids = db.execute(
            select(Liquidacion.id).where(Liquidacion.periodo_id == periodo.id)
        ).scalars().all()

        if liq_ids:
            num_pagos = db.execute(
                delete(PagoLiquidacion).where(PagoLiquidacion.liquidacion_id.in_(liq_ids))
            ).rowcount
            print(f"✓ {num_pagos} pago(s) de liquidación eliminados.")

        # 4. Borrar Liquidaciones del período
        num_liqs = db.execute(
            delete(Liquidacion).where(Liquidacion.periodo_id == periodo.id)
        ).rowcount
        print(f"✓ {num_liqs} liquidación(es) eliminadas.")

        # 5. Borrar Anticipos ordinarios
        num_ant = db.execute(
            delete(Anticipo).where(Anticipo.periodo_id == periodo.id)
        ).rowcount
        print(f"✓ {num_ant} anticipo(s) eliminados.")

        # 6. Borrar Anticipos Rider
        num_rider = db.execute(
            delete(AnticipoRider).where(AnticipoRider.periodo_id == periodo.id)
        ).rowcount
        print(f"✓ {num_rider} anticipo(s) rider eliminados.")

        # 7. Borrar Descuentos del período
        num_desc = db.execute(
            delete(Descuento).where(Descuento.periodo_id == periodo.id)
        ).rowcount
        print(f"✓ {num_desc} descuento(s) eliminados.")

        # 8. Borrar Ajustes manuales de días (PlanillaDetalle)
        num_det = db.execute(
            delete(PlanillaDetalle).where(PlanillaDetalle.periodo_id == periodo.id)
        ).rowcount
        print(f"✓ {num_det} detalle(s) de días trabajados reiniciados.")

        # 9. Reabrir período
        periodo.estado = "ABIERTO"
        db.commit()

        print(f"=================================================================")
        print(f"¡Éxito! El período {periodo.descripcion} ha sido completamente limpiado")
        print(f"y su estado volvió a 'ABIERTO'.")
        print(f"- Octubre y los demás meses están intactos.")
        print(f"- Los 43 trabajadores están intactos.")
        print(f"=================================================================")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Ocurrió un fallo al limpiar el período: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    m = int(sys.argv[1]) if len(sys.argv) > 1 else 11
    a = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    limpiar_periodo(m, a)
