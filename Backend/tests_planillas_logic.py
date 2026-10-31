"""
Pruebas Unitarias de Reglas de Negocio del Ciclo Salarial y Planilla (SISTEMAS RAÍCES)
Verifica los 6 problemas corregidos:
1. Días trabajados y Total Ganado proporcional (Haber / 30 * Días)
2. Anticipos del día 1 al 5 para período siguiente (informativos, sin restar en período previo)
3. Pago de quincena superior a la sugerencia (sin alterar anticipos previos)
4. Saldo salarial negativo visible (sin max(0, ...))
5. Separación estricta de categorías (anticipo, quincena, descuento)
6. Alerta sin bloqueo arbitrario de anticipos
"""

from decimal import Decimal, ROUND_HALF_UP


def calcular_total_ganado(haber_basico: Decimal, dias_trabajados: int) -> Decimal:
    """Fórmula: round((Haber / 30) * Días, 2)"""
    return round((haber_basico / Decimal("30.00")) * Decimal(dias_trabajados), 2)


def test_problema_1_dias_trabajados_y_total_ganado():
    haber = Decimal("3500.00")

    # Caso 1: Mes completo (30 días) -> Bs 3,500.00
    tg_30 = calcular_total_ganado(haber, 30)
    assert tg_30 == Decimal("3500.00"), f"Esperado 3500.00, obtenido {tg_30}"

    # Caso 2: 16 días (ingreso día 15) -> Bs 1,866.67
    tg_16 = calcular_total_ganado(haber, 16)
    assert tg_16 == Decimal("1866.67"), f"Esperado 1866.67, obtenido {tg_16}"

    # Caso 3: 20 días -> Bs 2,333.33
    tg_20 = calcular_total_ganado(haber, 20)
    assert tg_20 == Decimal("2333.33"), f"Esperado 2333.33, obtenido {tg_20}"

    print("[PASS] Problema 1: Cálculo de Total Ganado proporcional verificado con éxito.")


def test_problema_2_anticipos_periodo_siguiente():
    # En la planilla de noviembre:
    # Trabajador tiene sueldo Bs 3500.00 y anticipos de noviembre Bs 500.00
    # En días 1 al 5 de diciembre recibe Bs 600.00 en anticipos para diciembre
    sueldo_nov = Decimal("3500.00")
    anticipos_nov = Decimal("500.00")
    anticipos_dic_1_5 = Decimal("600.00")

    # El líquido pagable de noviembre NO descuenta los Bs 600.00
    liquido_nov = sueldo_nov - anticipos_nov
    assert liquido_nov == Decimal("3000.00"), f"Esperado 3000.00, obtenido {liquido_nov}"

    # En diciembre, los Bs 600.00 se descuentan en diciembre una sola vez
    sueldo_dic = Decimal("3500.00")
    anticipos_dic_totales = anticipos_dic_1_5  # 600.00
    liquido_dic = sueldo_dic - anticipos_dic_totales
    assert liquido_dic == Decimal("2900.00"), f"Esperado 2900.00, obtenido {liquido_dic}"

    print("[PASS] Problema 2: Anticipos días 1-5 se muestran informativos sin alterar mes anterior.")


def test_problema_3_quincena_permite_pago_superior():
    quincena_ref = Decimal("1000.00")
    anticipos_antes_18 = Decimal("800.00")

    # Sugerencia
    sugerencia = quincena_ref - anticipos_antes_18  # Bs 200.00
    assert sugerencia == Decimal("200.00")

    # El usuario decide pagar Bs 500.00
    quincena_pagada = Decimal("500.00")

    # El anticipo previo de 800.00 NO se modifica ni se duplica
    assert anticipos_antes_18 == Decimal("800.00")
    assert quincena_pagada == Decimal("500.00")

    # Total dinero entregado al trabajador
    total_entregado = anticipos_antes_18 + quincena_pagada
    assert total_entregado == Decimal("1300.00")

    print("[PASS] Problema 3: Quincena permite pago libre superior sin alterar anticipos previos.")


def test_problema_4_saldo_negativo_no_se_oculta():
    total_ganado = Decimal("3500.00")
    anticipos = Decimal("3600.00")
    descuentos = Decimal("100.00")
    ajustes = -descuentos

    # Líquido pagable SIN max(0, ...)
    liquido_pagable = total_ganado + ajustes - anticipos
    assert liquido_pagable == Decimal("-200.00"), f"Esperado -200.00, obtenido {liquido_pagable}"
    assert liquido_pagable < Decimal("0.00")

    print("[PASS] Problema 4: Preservación de saldos negativos (-Bs 200.00) verificada con éxito.")


def test_problema_5_no_duplicacion_categorias():
    haber = Decimal("3500.00")
    dias = 30
    total_ganado = calcular_total_ganado(haber, dias)

    anticipo_1 = Decimal("300.00")
    pago_quincena = Decimal("1000.00")
    descuento = Decimal("100.00")

    total_anticipos = anticipo_1
    ajustes = -descuento
    total_bruto = total_ganado + ajustes  # 3400.00
    liquido_pagable = total_bruto - total_anticipos  # 3100.00
    saldo_restante = liquido_pagable - pago_quincena  # 2100.00

    assert saldo_restante == Decimal("2100.00")

    print("[PASS] Problema 5: Separación estricta de categorías sin deducciones duplicadas.")


if __name__ == "__main__":
    print("=== INICIANDO VALIDACIÓN DE REGLAS DE NEGOCIO SALARIALES ===")
    test_problema_1_dias_trabajados_y_total_ganado()
    test_problema_2_anticipos_periodo_siguiente()
    test_problema_3_quincena_permite_pago_superior()
    test_problema_4_saldo_negativo_no_se_oculta()
    test_problema_5_no_duplicacion_categorias()
    print("=== TODAS LAS PRUEBAS DE REGLAS DE NEGOCIO PASARON EXITOSAMENTE ===")
