export interface Permiso {
  id: number;
  permisos: string;
}

export interface Rol {
  id: number;
  rol: string;
  niveljerarquico: number;
  descripcion?: string;
  permisos: Permiso[];
}

export interface Usuario {
  ci: string;
  nombre: string;
  apellido: string;
  email: string;
  genero?: string;
  fechanacimiento?: string;
  telefono?: string;
  direccion?: string;
  foto?: string;
  estado: boolean;
  rol_id: number;
  rol?: Rol;
}

export interface Area {
  id: number;
  nombre: string;
  estado: boolean;
  descripcion?: string;
}

export interface ContactoEmergencia {
  id?: number;
  nombrecompleto: string;
  parentesco: string;
  celular: string;
}

export interface Trabajador {
  id: number;
  ci?: string;
  nombres: string;
  apellidos: string;
  fotografia?: string;
  celular?: string;
  fecha_ingreso: string;
  cargo: string;
  sueldoBase: number;
  estado: boolean;
  area_id?: number;
  area?: Area;
  contactos_emergencia: ContactoEmergencia[];
}

export interface Bitacora {
  id: number;
  fecha: string;
  hora: string;
  modulo: string;
  accion: string;
  descripcion: string;
  usuario_ci?: string;
}

export interface UserSummary {
  ci: string;
  nombre: string;
  apellido: string;
  email: string;
  rol?: string;
  niveljerarquico?: number;
  permisos: string[];
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserSummary;
}

export interface PeriodoSalarial {
  id: number;
  mes: number;
  anio: number;
  fecha_inicio: string;
  fecha_fin: string;
  fecha_pago_estimada: string;
  fecha_limite_pago?: string;
  estado: string;
  descripcion: string;
}

export interface Anticipo {
  id: number;
  numero_comprobante: string;
  trabajador_id: number;
  periodo_id: number;
  fecha_solicitud: string;
  fecha_entrega: string;
  importe: number;
  metodo_pago: string;
  estado: string;
  observaciones?: string;
  motivo_anulacion?: string;
  usuario_id?: string;
  usuario_nombre?: string;
  es_periodo_siguiente?: boolean;
}

export interface PagoLiquidacion {
  id: number;
  numero_comprobante: string;
  liquidacion_id: number;
  fecha_pago: string;
  monto: number;
  tipo_pago?: string;
  metodo_pago: string;
  observaciones?: string;
  estado: string;
  motivo_anulacion?: string;
  usuario_id?: string;
  usuario_nombre?: string;
  es_periodo_siguiente?: boolean;
}

export interface Liquidacion {
  id: number;
  numero_comprobante: string;
  trabajador_id: number;
  periodo_id: number;
  fecha_liquidacion: string;
  sueldo_base: number;
  ajustes: number;
  total_anticipos: number;
  monto_neto: number;
  monto_pagado: number;
  saldo_pendiente: number;
  estado: string;
  observaciones?: string;
  motivo_anulacion?: string;
  usuario_id?: string;
  usuario_nombre?: string;
  pago_inmediato_monto?: number;
  pago_inmediato_comprobante?: string;
  total_pagos_previos?: number;
  pago_quincena_previo?: number;
  pagos: PagoLiquidacion[];
}

export interface ResumenSalarialTrabajador {
  trabajador_id: number;
  nombre_completo: string;
  ci?: string;
  cargo: string;
  area: string;
  sueldo_base: number;
  periodo_id: number;
  periodo_descripcion: string;
  quincena_referencia?: number;
  anticipos: Anticipo[];
  total_anticipos: number;
  anticipos_antes_dia_18?: number;
  diferencia_quincena?: number;
  monto_sugerido_quincena?: number;
  pago_quincena_realizado?: number;
  quincena_pagada?: boolean;
  anticipos_posteriores_dia_18?: number;
  total_pagos_parciales?: number;
  saldo_salarial_pendiente?: number;
  supera_quincena?: boolean;
  excedente_quincena?: number;
  fecha_ultimo_anticipo?: string | null;
  liquidacion?: Liquidacion;
  total_pagos_anteriores: number;
  saldo_pendiente_liquidacion: number;
  estado_liquidacion: string;
}

export interface ResumenTrabajadorPagosParciales {
  trabajador_id: number;
  nombre_completo: string;
  ci?: string;
  cargo: string;
  area: string;
  sueldo_base: number;
  quincena_referencia: number;
  anticipos_antes_dia_18: number;
  diferencia_quincena: number;
  pago_quincena_realizado: number;
  anticipos_posteriores_dia_18: number;
  total_anticipos_periodo: number;
  total_descuentos?: number;
  total_pagos_parciales: number;
  saldo_salarial_pendiente: number;
  estado_periodo: string;
  supera_quincena: boolean;
  excedente_quincena: number;
  monto_sugerido_quincena: number;
  quincena_pagada?: boolean;
  fecha_ultimo_anticipo?: string | null;
  liquidacion_id?: number | null;
  liquidacion_comprobante?: string | null;
}

export interface ComprobanteAnticipoDetallado {
  empresa_nombre: string;
  numero_comprobante: string;
  trabajador_id: number;
  trabajador_nombre: string;
  trabajador_ci?: string;
  trabajador_cargo?: string;
  trabajador_area?: string;
  periodo_id: number;
  periodo_descripcion: string;
  fecha_anticipo: string;
  importe_actual: number;
  metodo_entrega: string;
  usuario_nombre?: string;
  usuario_ci?: string;
  motivo?: string;
  total_anticipos_anteriores: number;
  anticipos_historicos: Anticipo[];
  anticipos_periodo?: Anticipo[];
  total_acumulado: number;
  sueldo_base: number;
  quincena_referencia: number;
  diferencia_quincena: number;
  saldo_salarial_estimado: number;
  supera_quincena: boolean;
  excedente_quincena: number;
  quincena_pagada?: boolean;
  estado_quincena?: string;
  pago_quincena_realizado?: number;
  total_pagos_realizados?: number;
}

export interface PagoParcialDirectoPayload {
  trabajador_id: number;
  periodo_id: number;
  monto: number;
  tipo_pago: string;
  metodo_pago: string;
  fecha_pago: string;
  observaciones?: string;
}

export interface PanelResumenPagos {
  total_anticipos_mes: number;
  total_sueldos_pagados_mes: number;
  liquidaciones_pendientes_count: number;
  liquidaciones_parciales_count: number;
  liquidaciones_completadas_count: number;
  trabajadores_con_pendientes_count: number;
  total_dinero_entregado: number;
  total_dinero_pendiente: number;
  total_trabajadores_activos?: number;
  trabajadores_liquidados_count?: number;
  periodo_completamente_liquidado?: boolean;
  resumen_estado_mes?: string;
}

export interface MovimientoHistorial {
  id: number;
  tipo: string;
  numero_comprobante: string;
  liquidacion_comprobante?: string;
  fecha: string;
  periodo: string;
  monto: number;
  metodo_pago: string;
  estado: string;
  observaciones?: string;
  usuario_id?: string;
  usuario_nombre?: string;
  sueldo_base?: number;
  total_anticipos?: number;
  quincena_descontada?: number;
  saldo_pendiente?: number;
}

export interface HistorialTrabajadorResponse {
  trabajador: {
    id: number;
    ci: string;
    nombre_completo: string;
    cargo: string;
    sueldo_base: number;
    area: string;
    estado: boolean;
  };
  movimientos: MovimientoHistorial[];
}

// =========================================================================
// MÓDULO DE INVENTARIO: ALMACÉN Y GASTOS MENORES
// =========================================================================

export interface CompraAlmacen {
  id: number;
  numero_comprobante: string;
  almacen_id: number;
  cantidad_comprada: number;
  unidad_compra: string;
  equivalencia_unidad: number;
  cantidad_en_unidad_control: number;
  precio_total: number;
  precio_unitario: number;
  precio_unitario_anterior?: number;
  variacion_porcentual?: number;
  fecha_compra: string;
  proveedor?: string;
  numero_factura?: string;
  observaciones?: string;
  usuario_registro_ci?: string;
  usuario_registro_nombre?: string;
  estado: string;
  motivo_anulacion?: string;
  fecha_creacion: string;
}

export interface MovimientoAlmacen {
  id: number;
  numero_comprobante: string;
  almacen_id: number;
  compra_id?: number;
  movimiento_original_id?: number;
  trabajador_id?: number;
  trabajador_nombre?: string;
  area_id?: number;
  area_nombre?: string;
  vehiculo_maquinaria?: string;
  usuario_registro_ci?: string;
  usuario_registro_nombre?: string;
  tipo_movimiento: string;
  cantidad: number;
  cantidad_entrada: number;
  cantidad_salida: number;
  stock_anterior: number;
  stock_resultante: number;
  motivo: string;
  observaciones?: string;
  fecha_movimiento: string;
  hora_movimiento: string;
  estado: string;
  motivo_anulacion?: string;
  fecha_creacion: string;
}

export interface ProductoAlmacen {
  id: number;
  codigo: string;
  nombre: string;
  foto?: string;
  descripcion?: string;
  unidad_control: string;
  stock_actual: number;
  stock_minimo: number;
  estado_stock: 'Normal' | 'Stock bajo' | 'Agotado' | string;
  precio_ultima_compra: number;
  fecha_ultima_compra?: string;
  precio_anterior?: number;
  variacion_porcentual?: number;
  usuario_registro_ci?: string;
  usuario_registro_nombre?: string;
  estado: boolean;
  fecha_creacion: string;
}

export interface ProductoAlmacenDetalle extends ProductoAlmacen {
  compras: CompraAlmacen[];
  movimientos: MovimientoAlmacen[];
}

export interface GastoMenor {
  id: number;
  numero_comprobante: string;
  nombre: string;
  descripcion?: string;
  foto_comprobante?: string;
  importe_total: number;
  fecha_gasto: string;
  area_id?: number;
  area_nombre?: string;
  trabajador_responsable_id?: number;
  trabajador_nombre?: string;
  metodo_pago: string;
  proveedor?: string;
  numero_comprobante_fiscal?: string;
  usuario_registro_ci?: string;
  usuario_registro_nombre?: string;
  estado: string;
  motivo_anulacion?: string;
  fecha_creacion: string;
}

export interface ReporteAlmacenResumen {
  total_productos: number;
  productos_normal: number;
  productos_stock_bajo: number;
  productos_agotados: number;
  total_entradas_mes: number;
  total_salidas_mes: number;
  valor_estimado_inventario: number;
}

export interface ReporteGastosResumen {
  total_gastos_mes: number;
  cantidad_gastos_mes: number;
  total_por_area: { area: string; total: number }[];
  total_por_metodo: { metodo: string; total: number }[];
}

export interface ResumenContableKPIs {
  total_egresos_global: number;
  total_nomina_pagada: number;
  total_anticipos_pagados: number;
  total_sueldos_pagados: number;
  total_compras_inventario: number;
  total_gastos_menores: number;
  total_compromisos_pendientes: number;
  cantidad_transacciones: number;
  promedio_diario_egresos: number;
}

export interface DesglosePorArea {
  area_id?: number;
  area_nombre: string;
  total_nomina: number;
  total_gastos_menores: number;
  total_compras: number;
  total_egresos: number;
  porcentaje: number;
}

export interface MovimientoContable {
  id: string;
  fecha: string;
  tipo_categoria: 'NOMINA_ANTICIPO' | 'NOMINA_SUELDO' | 'COMPRA_INVENTARIO' | 'GASTO_OPERATIVO';
  tipo_label: string;
  numero_comprobante: string;
  beneficiario_proveedor: string;
  concepto: string;
  area_nombre: string;
  metodo_pago: string;
  monto: number;
  usuario_registro_ci?: string;
}

export interface ContabilidadReporteMensual {
  mes: number;
  anio: number;
  mes_nombre: string;
  rango_fechas: string;
  kpis: ResumenContableKPIs;
  desglose_areas: DesglosePorArea[];
  movimientos: MovimientoContable[];
  metodos_pago_resumen: { [key: string]: number };
}

export interface MesComparativoAnual {
  mes: number;
  mes_nombre: string;
  total_nomina: number;
  total_compras: number;
  total_gastos: number;
  total_global: number;
}

export interface ContabilidadReporteAnual {
  anio: number;
  kpis: ResumenContableKPIs;
  meses: MesComparativoAnual[];
  desglose_areas: DesglosePorArea[];
  metodos_pago_resumen: { [key: string]: number };
}

// ==========================================
// MÓDULO DE PLANILLA Y SALARIOS
// ==========================================
export interface PlanillaFila {
  nro: number;
  trabajador_id: number;
  nombre_completo: string;
  ci?: string;
  cargo: string;
  area: string;
  fecha_ingreso: string;
  haber_basico: number;
  dias_trabajados: number;
  dias_manual: boolean;
  total_ganado: number;
  pago_quincena: number;
  estado_quincena: string;
  quincena_sugerida: number;
  supera_quincena: boolean;
  excedente_quincena: number;
  quincena_referencia?: number;
  anticipos_antes_dia_18?: number;
  diferencia_quincena?: number;
  pago_anticipos_rider?: number;
  anticipos_rider_count?: number;
  pago_anticipos: number;
  anticipos_count: number;
  reposicion_ebert?: number;
  reposicion_antes_sueldo?: number;
  total_descuentos: number;
  descuentos_count: number;
  total_anticipos_descuentos: number;
  anticipos_periodo_siguiente: number;
  liquido_pagable: number;
  monto_pagado_total: number;
  saldo_pendiente_real: number;
  estado_liquidacion: string;
  liquidacion_id?: number | null;
  liquidacion_comprobante?: string | null;
  pago_liquidacion?: number;
  fecha_liquidacion?: string;
  liquidacion_metodo_pago?: string;
  liquidacion_observaciones?: string;
  liquidacion_ajustes?: number;
  liquidacion_usuario_id?: string;
}

export interface PlanillaResumenTotales {
  total_haber_basico: number;
  total_ganado: number;
  total_quincena: number;
  total_anticipos_rider?: number;
  total_anticipos: number;
  total_descuentos: number;
  total_anticipos_descuentos: number;
  total_anticipos_periodo_siguiente: number;
  total_liquido_pagable: number;
  total_trabajadores: number;
  trabajadores_liquidados: number;
  trabajadores_pendientes: number;
  // 8 Indicadores Clave de Ciclo Salarial (spec.md)
  reposicion_ebert?: number;
  solicitud_quincena?: number;
  reposicion_antes_sueldo?: number;
  liquido_sueldo?: number;
  solicitud_sueldo?: number;
  solicitud_total_mes?: number;
  total_saldo_pendiente?: number;
}

export interface PlanillaCierre {
  id: number;
  periodo_id: number;
  entregado_quincena: number;
  solicitud_quincena: number;
  diferencia_quincena: number;
  entregado_sueldo: number;
  solicitud_sueldo: number;
  diferencia_sueldo: number;
  otros_gastos: number;
  otros_gastos_detalle?: string | null;
  total_diferencia: number;
  observaciones?: string | null;
  usuario_ci?: string | null;
  usuario_nombre?: string | null;
  fecha_cierre: string;
}

export interface CerrarPlanillaPayload {
  observaciones?: string;
  confirmar_pendientes?: boolean;
  entregado_quincena: number;
  solicitud_quincena: number;
  entregado_sueldo: number;
  solicitud_sueldo: number;
  otros_gastos: number;
  otros_gastos_detalle?: string;
}

export interface PlanillaMensual {
  periodo_id: number;
  periodo_descripcion: string;
  mes: number;
  anio: number;
  fecha_inicio: string;
  fecha_fin: string;
  fecha_pago_estimada?: string;
  fecha_limite_pago?: string;
  estado_periodo: string;
  filas: PlanillaFila[];
  totales: PlanillaResumenTotales;
  cierre?: PlanillaCierre | null;
}

export interface ActualizarDiasTrabajadosPayload {
  trabajador_id: number;
  periodo_id: number;
  dias_trabajados: number;
  observaciones?: string;
}

export interface Descuento {
  id: number;
  numero_comprobante: string;
  trabajador_id: number;
  trabajador_nombre?: string;
  periodo_id: number;
  fecha: string;
  importe: number;
  concepto: string;
  observaciones?: string;
  estado: string;
  usuario_id?: string;
  usuario_nombre?: string;
  fecha_creacion: string;
}

export interface DescuentoCreatePayload {
  trabajador_id: number;
  periodo_id: number;
  fecha: string;
  importe: number;
  concepto: string;
  observaciones?: string;
}



export interface AnticipoRider {
  id: number;
  numero_comprobante: string;
  trabajador_id: number;
  trabajador_nombre?: string;
  periodo_id: number;
  fecha_solicitud: string;
  fecha_entrega: string;
  importe: number;
  metodo_pago: string;
  estado: string;
  observaciones?: string;
  motivo_anulacion?: string;
  usuario_id?: string;
  usuario_nombre?: string;
}

export interface AnticipoRiderCreatePayload {
  trabajador_id: number;
  periodo_id: number;
  fecha_entrega: string;
  importe: number;
  metodo_pago: string;
  observaciones?: string;
}
