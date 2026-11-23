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
  es_periodo_siguiente?: boolean;
  observaciones?: string;
  motivo_anulacion?: string;
  usuario_id?: string;
  usuario_nombre?: string;
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
  es_periodo_siguiente?: boolean;
  observaciones?: string;
  motivo_anulacion?: string;
  usuario_id?: string;
  usuario_nombre?: string;
  pago_inmediato_monto?: number;
  pago_inmediato_comprobante?: string;
  total_pagos_previos?: number;
  pago_quincena_previo?: number;
  excedente_siguiente_mes?: number;
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
  es_periodo_siguiente?: boolean;
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
  pago_quincena_id?: number;
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

export interface ActualizarFilaPlanillaPayload {
  trabajador_id: number;
  periodo_id: number;
  haber_basico?: number;
  dias_trabajados?: number;
  pago_quincena?: number;
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
  es_periodo_siguiente?: boolean;
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

// ==========================================
// GANADERÍA - MÓDULO INTEGRAL (SPEC-001)
// ==========================================

export interface Animal {
  id: number;
  codigo_interno: string;
  numero_arete?: string | null;
  nombre?: string | null;
  tipo_ganado: string;
  raza: string;
  sexo: string;
  fecha_nacimiento?: string | null;
  edad_estimada_meses?: number | null;
  peso_inicial?: number | null;
  peso_actual?: number | null;
  fecha_ultimo_pesaje?: string | null;
  categoria?: string | null;
  estado: string;
  potrero_id?: number | null;
  ubicacion: string;
  foto_url?: string | null;
  observaciones?: string | null;
  procedencia: string;
  madre_id?: number | null;
  madre_codigo?: string | null;
  madre_arete?: string | null;
  padre_id?: number | null;
  padre_codigo?: string | null;
  padre_arete?: string | null;
  fecha_registro: string;
  fecha_actualizacion?: string | null;
}

export interface PesajeGanado {
  id: number;
  animal_id: number;
  fecha_pesaje: string;
  peso: number;
  notas?: string | null;
  usuario_id?: string | null;
  usuario_nombre?: string | null;
  fecha_creacion: string;
}

export interface HistorialArete {
  id: number;
  animal_id: number;
  arete_anterior?: string | null;
  arete_nuevo: string;
  motivo?: string | null;
  fecha_cambio: string;
  usuario_id?: string | null;
  usuario_nombre?: string | null;
}

export interface NacimientoGanado {
  id: number;
  codigo_parto: string;
  madre_id: number;
  madre_codigo?: string | null;
  madre_arete?: string | null;
  padre_id?: number | null;
  padre_codigo?: string | null;
  padre_arete?: string | null;
  fecha_parto: string;
  condicion_cria: string;
  observaciones?: string | null;
  cria_id?: number | null;
  cria_codigo?: string | null;
  cria_arete?: string | null;
  cria_sexo?: string | null;
  cria_peso_nacer?: number | null;
  usuario_id?: string | null;
  usuario_nombre?: string | null;
  fecha_registro: string;
}

export interface CompraGanadoDetalle {
  id: number;
  compra_id: number;
  animal_id: number;
  animal_codigo?: string | null;
  animal_arete?: string | null;
  tipo_ganado: string;
  raza: string;
  sexo: string;
  peso_compra?: number | null;
  precio_unitario: number;
  modalidad_precio: string;
  subtotal: number;
}

export interface CompraGanado {
  id: number;
  numero_comprobante: string;
  proveedor: string;
  fecha_compra: string;
  numero_documento?: string | null;
  cantidad_cabezas: number;
  costos_adicionales: number;
  costo_transporte: number;
  total_compra: number;
  observaciones?: string | null;
  documento_adjunto_url?: string | null;
  usuario_id?: string | null;
  usuario_nombre?: string | null;
  fecha_registro: string;
  detalles: CompraGanadoDetalle[];
}

export interface VentaGanadoDetalle {
  id: number;
  venta_id: number;
  animal_id: number;
  animal_codigo?: string | null;
  animal_arete?: string | null;
  tipo_ganado: string;
  raza: string;
  sexo: string;
  peso_venta?: number | null;
  precio_unitario: number;
  modalidad_precio: string;
  subtotal: number;
}

export interface VentaGanado {
  id: number;
  numero_comprobante: string;
  cliente: string;
  fecha_venta: string;
  cantidad_cabezas: number;
  modalidad_venta: string;
  total_bruto: number;
  descuento: number;
  costo_transporte: number;
  total_neto: number;
  metodo_pago?: string | null;
  numero_documento?: string | null;
  observaciones?: string | null;
  documento_adjunto_url?: string | null;
  estado: string;
  motivo_anulacion?: string | null;
  usuario_id?: string | null;
  usuario_nombre?: string | null;
  fecha_registro: string;
  detalles: VentaGanadoDetalle[];
}

export interface BajaGanado {
  id: number;
  numero_acta: string;
  animal_id: number;
  animal_codigo?: string | null;
  animal_arete?: string | null;
  tipo_baja: string;
  fecha_baja: string;
  causa_diagnostico?: string | null;
  necropsia_realizada: boolean;
  destino_cuerpo?: string | null;
  valor_estimado_perdida: number;
  observaciones?: string | null;
  documento_adjunto_url?: string | null;
  estado: string;
  motivo_anulacion?: string | null;
  usuario_id?: string | null;
  usuario_nombre?: string | null;
  fecha_registro: string;
}

export interface AnimalPerfil {
  animal: Animal;
  pesajes: PesajeGanado[];
  historial_aretes: HistorialArete[];
  madre?: Animal | null;
  padre?: Animal | null;
  partos_madre: NacimientoGanado[];
  hijos: Animal[];
  detalles_compra?: CompraGanadoDetalle | null;
  detalles_venta?: VentaGanadoDetalle | null;
  detalles_baja?: BajaGanado | null;
}

export interface GanaderiaKPIs {
  total_hato: number;
  activos: number;
  machos: number;
  hembras: number;
  vendidos: number;
  fallecidos_bajas: number;
  total_nacimientos: number;
  total_compras: number;
  peso_promedio_activo: number;
}

export interface AnimalCreatePayload {
  numero_arete?: string | null;
  nombre?: string | null;
  tipo_ganado: string;
  raza: string;
  sexo: string;
  fecha_nacimiento?: string | null;
  edad_estimada_meses?: number | null;
  peso_inicial?: number | null;
  categoria?: string | null;
  estado?: string;
  potrero_id?: number | null;
  ubicacion: string;
  observaciones?: string | null;
  procedencia?: string;
  madre_id?: number | null;
  padre_id?: number | null;
}

export interface AnimalUpdatePayload {
  numero_arete?: string | null;
  nombre?: string | null;
  tipo_ganado?: string;
  raza?: string;
  sexo?: string;
  fecha_nacimiento?: string | null;
  edad_estimada_meses?: number | null;
  categoria?: string | null;
  estado?: string;
  potrero_id?: number | null;
  ubicacion?: string;
  observaciones?: string | null;
  motivo_cambio_arete?: string | null;
  madre_id?: number | null;
  padre_id?: number | null;
}

export interface PesajeCreatePayload {
  fecha_pesaje: string;
  peso: number;
  notas?: string | null;
}

export interface NacimientoCreatePayload {
  madre_id: number;
  padre_id?: number | null;
  fecha_parto: string;
  condicion_cria: string;
  observaciones?: string | null;
  cria_tipo_ganado?: string;
  cria_raza?: string;
  cria_sexo?: string;
  cria_peso_nacer?: number | null;
  cria_numero_arete?: string | null;
  cria_potrero_id?: number | null;
  cria_ubicacion?: string;
}

export interface CompraGanadoDetallePayload {
  tipo_ganado: string;
  raza: string;
  sexo: string;
  fecha_nacimiento?: string | null;
  edad_estimada_meses?: number | null;
  numero_arete?: string | null;
  peso?: number | null;
  precio_compra: number;
  modalidad_precio: string;
  potrero_id?: number | null;
  ubicacion: string;
  observaciones?: string | null;
}

export interface CompraGanadoCreatePayload {
  proveedor: string;
  fecha_compra: string;
  numero_documento?: string | null;
  costos_adicionales?: number;
  costo_transporte?: number;
  observaciones?: string | null;
  detalles: CompraGanadoDetallePayload[];
}

export interface VentaGanadoItemPayload {
  animal_id: number;
  precio: number;
  modalidad_precio: string;
}

export interface VentaGanadoCreatePayload {
  cliente: string;
  fecha_venta: string;
  modalidad_venta: string;
  metodo_pago?: string | null;
  costo_transporte?: number;
  descuento?: number;
  numero_documento?: string | null;
  observaciones?: string | null;
  animales: VentaGanadoItemPayload[];
}

export interface BajaGanadoCreatePayload {
  animal_id: number;
  tipo_baja: string;
  fecha_baja: string;
  causa_diagnostico?: string | null;
  necropsia_realizada?: boolean;
  destino_cuerpo?: string | null;
  valor_estimado_perdida?: number;
  observaciones?: string | null;
}

// ==========================================
// GESTIÓN DE POTREROS Y MOVIMIENTOS (SPEC-002)
// ==========================================

export interface Potrero {
  id: number;
  codigo: string;
  nombre: string;
  tipo_area: 'POTRERO' | 'CORRAL' | 'CUARENTENA' | 'MATERNIDAD' | 'OTRO' | string;
  superficie_ha?: number | null;
  capacidad_cabezas: number;
  color_hex: string;
  poligono_geojson: string;
  centroide_lat?: number | null;
  centroide_lng?: number | null;
  estado: string;
  activo?: boolean;
  total_animales: number;
  animales_actuales?: number;
  total_machos: number;
  total_hembras: number;
  observaciones?: string | null;
  fecha_creacion: string;
  fecha_actualizacion: string;
  animales?: Animal[];
}

export interface MovimientoGanadoDetalle {
  id: number;
  movimiento_id: number;
  animal_id: number;
  numero_arete?: string | null;
  codigo_interno: string;
  potrero_origen_id: number;
  potrero_destino_id: number;
  animal_nombre?: string | null;
  animal_raza?: string | null;
  animal_sexo?: string | null;
  animal_peso_actual?: number | null;
}

export interface MovimientoGanado {
  id: number;
  numero_comprobante: string;
  fecha_movimiento: string;
  potrero_origen_id: number;
  potrero_origen_nombre?: string | null;
  potrero_destino_id: number;
  potrero_destino_nombre?: string | null;
  tipo_operacion: string;
  cantidad_animales: number;
  motivo?: string | null;
  responsable?: string | null;
  observaciones?: string | null;
  estado: string;
  motivo_anulacion?: string | null;
  usuario_ci?: string | null;
  fecha_creacion: string;
  detalles: MovimientoGanadoDetalle[];
}

export interface MovimientoGanadoCreatePayload {
  potrero_origen_id: number;
  potrero_destino_id: number;
  animales_ids: number[];
  fecha_movimiento?: string | null;
  tipo_operacion?: string;
  motivo?: string | null;
  responsable?: string | null;
  observaciones?: string | null;
}

export interface AnimalPuntoMapa {
  id: number;
  codigo_interno: string;
  numero_arete?: string | null;
  nombre?: string | null;
  tipo: string;
  raza: string;
  sexo: string;
  peso_actual?: number | null;
  potrero_id: number;
  potrero_nombre: string;
  lat: number;
  lng: number;
}

export interface MapaDistribucion {
  potreros: Potrero[];
  animales: AnimalPuntoMapa[];
  total_cabezas_activas: number;
}

// =========================================================================
// MÓDULO DE GANADERÍA — SANIDAD Y TRATAMIENTOS (SPEC-003)
// =========================================================================

export interface SanidadVacuna {
  id: number;
  codigo: string;
  nombre: string;
  nombre_comercial?: string | null;
  enfermedad_objetivo: string;
  especie: string;
  dosis_defecto_ml?: number | null;
  via_administracion: string;
  dias_retiro_carne: number;
  dias_retiro_leche: number;
  requiere_refuerzo: boolean;
  dias_refuerzo?: number | null;
  estado: string;
  observaciones?: string | null;
  fecha_creacion?: string;
}

export interface SanidadMedicamento {
  id: number;
  codigo: string;
  nombre: string;
  nombre_comercial?: string | null;
  tipo_farmaco: string;
  principio_activo?: string | null;
  concentracion?: string | null;
  unidad_medida: string;
  via_administracion: string;
  dias_retiro_carne: number;
  dias_retiro_leche: number;
  almacen_id?: number | null;
  almacen_nombre?: string | null;
  estado: string;
  observaciones?: string | null;
  fecha_creacion?: string;
}

export interface SanidadSeguimiento {
  id: number;
  detalle_id: number;
  fecha_seguimiento: string;
  estado_salud: string;
  temperatura_c?: number | null;
  peso_actual_kg?: number | null;
  observaciones?: string | null;
  usuario_ci?: string | null;
  usuario_nombre?: string | null;
  fecha_creacion?: string;
}

export interface SanidadOperacionDetalle {
  id: number;
  operacion_id: number;
  animal_id: number;
  numero_arete?: string | null;
  codigo_interno: string;
  animal_nombre?: string | null;
  animal_raza?: string | null;
  animal_sexo?: string | null;
  dosis_aplicada?: number | null;
  unidad_medida: string;
  fecha_fin_retiro_carne?: string | null;
  fecha_fin_retiro_leche?: string | null;
  en_retiro_carne?: boolean;
  en_retiro_leche?: boolean;
  dias_restantes_retiro_carne?: number;
  dias_restantes_retiro_leche?: number;
  estado_aplicacion: string;
  reaccion_adversa?: string | null;
  observaciones?: string | null;
  seguimientos?: SanidadSeguimiento[];
}

export interface SanidadOperacion {
  id: number;
  numero_comprobante: string;
  tipo_operacion: string;
  fecha_aplicacion: string;
  fecha_programada?: string | null;
  potrero_origen_id?: number | null;
  potrero_origen_nombre?: string | null;
  vacuna_id?: number | null;
  vacuna_nombre?: string | null;
  medicamento_id?: number | null;
  medicamento_nombre?: string | null;
  producto_aplicado?: string;
  lote_producto?: string | null;
  fecha_vencimiento_producto?: string | null;
  diagnostico?: string | null;
  sintomas?: string | null;
  cantidad_animales: number;
  trabajador_id?: number | null;
  trabajador_nombre?: string | null;
  veterinario_nombre?: string | null;
  costo_total_estimado?: number | null;
  descontar_inventario: boolean;
  movimiento_almacen_id?: number | null;
  traslado_cuarentena_id?: number | null;
  estado: string;
  motivo_anulacion?: string | null;
  observaciones?: string | null;
  usuario_ci?: string | null;
  usuario_nombre?: string | null;
  fecha_creacion: string;
  detalles?: SanidadOperacionDetalle[];
}

export interface AnimalOperacionItemPayload {
  animal_id: number;
  dosis_aplicada?: number | null;
  unidad_medida?: string;
  estado_aplicacion?: 'APLICADO' | 'PENDIENTE' | 'RECHAZADO';
  reaccion_adversa?: string | null;
  observaciones?: string | null;
}

export interface SanidadOperacionCreatePayload {
  tipo_operacion: string;
  fecha_aplicacion: string;
  fecha_programada?: string | null;
  potrero_origen_id?: number | null;
  vacuna_id?: number | null;
  medicamento_id?: number | null;
  lote_producto?: string | null;
  fecha_vencimiento_producto?: string | null;
  diagnostico?: string | null;
  sintomas?: string | null;
  trabajador_id?: number | null;
  veterinario_nombre?: string | null;
  costo_total_estimado?: number | null;
  descontar_inventario: boolean;
  trasladar_a_cuarentena: boolean;
  potrero_cuarentena_id?: number | null;
  observaciones?: string | null;
  animales: AnimalOperacionItemPayload[];
}

export interface AlertaRetiro {
  animal_id: number;
  codigo_interno: string;
  numero_arete?: string | null;
  potrero_id?: number | null;
  potrero_nombre?: string | null;
  tipo_retiro: 'CARNE' | 'LECHE' | 'AMBOS';
  fecha_fin_retiro_carne?: string | null;
  fecha_fin_retiro_leche?: string | null;
  dias_restantes_carne: number;
  dias_restantes_leche: number;
  producto_origen: string;
  numero_comprobante: string;
  fecha_aplicacion: string;
}

export interface SanidadKPIs {
  total_vacunaciones_mes: number;
  total_tratamientos_activos: number;
  animales_en_retiro_carne: number;
  animales_en_retiro_leche: number;
  vacunas_catalogo_activas: number;
  medicamentos_catalogo_activos: number;
  alertas_retiro_proximas: AlertaRetiro[];
}

export interface HistorialSanitarioAnimal {
  animal_id: number;
  codigo_interno: string;
  numero_arete?: string | null;
  en_retiro_carne: boolean;
  en_retiro_leche: boolean;
  fecha_fin_retiro_carne?: string | null;
  fecha_fin_retiro_leche?: string | null;
  dias_restantes_retiro_carne: number;
  dias_restantes_retiro_leche: number;
  vacunaciones: SanidadOperacionDetalle[];
  tratamientos: SanidadOperacionDetalle[];
}

// =========================================================================
// MÓDULO DE GESTIÓN AGRÍCOLA (SPEC-004)
// =========================================================================

export interface ActividadPreparacion {
  id: number;
  ciclo_agricola_id: number;
  tipo_actividad: string; // ARADO, RASTRA, ROLO, SUBSOLADO, OTRO
  fecha: string;
  completada: boolean;
  observaciones?: string | null;
  fecha_creacion?: string;
}

export interface ActividadManejo {
  id: number;
  ciclo_agricola_id: number;
  fecha: string;
  tipo_actividad: string; // FUMIGACION, HERBICIDA, INSECTICIDA, FUNGICIDA, FERTILIZACION, APLICACION_FOLIAR, OTRO
  producto_utilizado: string;
  cantidad_aplicada: number;
  unidad_medida: string; // LT, KG, DOSIS
  dosis_por_ha?: number | null;
  superficie_aplicada_ha?: number | null;
  observaciones?: string | null;
  fecha_creacion?: string;
}

export interface CosechaRegistro {
  id: number;
  ciclo_agricola_id: number;
  fecha_cosecha: string;
  fecha_fin_cosecha?: string | null;
  cultivo_cosechado: string;
  superficie_cosechada_ha: number;
  cantidad_producida: number;
  unidad_medida: string; // TN, KG, QQ
  rendimiento_calculado_ha: number;
  observaciones?: string | null;
  fecha_creacion?: string;
}

export interface CicloAgricola {
  id: number;
  area_agricola_id: number;
  cultivo: string;
  variedad_hibrido?: string | null;
  campana: string;
  fecha_inicio: string;
  superficie_utilizada_ha: number;
  fase_actual: 'PREPARACION' | 'SIEMBRA' | 'MANEJO' | 'COSECHA' | 'FINALIZADO';
  estado: 'ACTIVO' | 'FINALIZADO' | 'CANCELADO';
  fecha_cierre?: string | null;
  total_cosechado?: number | null;
  unidad_cosecha?: string;
  rendimiento_promedio_ha?: number | null;
  observaciones?: string | null;
  actividades_preparacion: ActividadPreparacion[];
  actividades_manejo: ActividadManejo[];
  cosechas: CosechaRegistro[];
  fecha_creacion?: string;
}

export interface AreaAgricola {
  id: number;
  codigo: string;
  nombre: string;
  superficie_ha: number;
  poligono_geojson?: string | null;
  centroide_lat?: number | null;
  centroide_lng?: number | null;
  color_hex: string;
  estado: string; // ACTIVO, INACTIVO
  observaciones?: string | null;
  ciclo_activo?: CicloAgricola | null;
  total_ciclos_historicos: number;
  fecha_creacion?: string;
  fecha_actualizacion?: string;
}

export interface AreaAgricolaCreatePayload {
  nombre: string;
  superficie_ha: number;
  poligono_geojson?: string | null;
  color_hex?: string;
  observaciones?: string | null;
}

export interface CicloAgricolaCreatePayload {
  cultivo: string;
  variedad_hibrido?: string | null;
  campana: string;
  fecha_inicio: string;
  superficie_utilizada_ha: number;
  observaciones?: string | null;
}

export interface SiembraUpdatePayload {
  cultivo: string;
  variedad_hibrido?: string | null;
  fecha_siembra: string;
  superficie_sembrada_ha: number;
  observaciones?: string | null;
}

export interface ActividadManejoCreatePayload {
  fecha: string;
  tipo_actividad: string;
  producto_utilizado: string;
  cantidad_aplicada: number;
  unidad_medida: string;
  dosis_por_ha?: number | null;
  superficie_aplicada_ha?: number | null;
  observaciones?: string | null;
}

export interface CosechaCreatePayload {
  fecha_cosecha: string;
  fecha_fin_cosecha?: string | null;
  cultivo_cosechado: string;
  superficie_cosechada_ha: number;
  cantidad_producida: number;
  unidad_medida: string;
  observaciones?: string | null;
}

export interface AgriculturaKPIs {
  total_areas: number;
  superficie_total_ha: number;
  ciclos_activos: number;
  hectareas_en_produccion: number;
  distribucion_fases: { [key: string]: number };
  rendimiento_promedio_ultimas_campanas: number;
}



