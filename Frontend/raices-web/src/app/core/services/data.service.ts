import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';
import {
  Usuario,
  Rol,
  Permiso,
  Trabajador,
  Area,
  Bitacora,
  PeriodoSalarial,
  Anticipo,
  Liquidacion,
  PagoLiquidacion,
  ResumenSalarialTrabajador,
  ResumenTrabajadorPagosParciales,
  ComprobanteAnticipoDetallado,
  PagoParcialDirectoPayload,
  PanelResumenPagos,
  HistorialTrabajadorResponse,
  ProductoAlmacen,
  ProductoAlmacenDetalle,
  CompraAlmacen,
  MovimientoAlmacen,
  GastoMenor,
  ReporteAlmacenResumen,
  ReporteGastosResumen,
  ContabilidadReporteMensual,
  ContabilidadReporteAnual,
} from '../models/types';

@Injectable({
  providedIn: 'root'
})
export class DataService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private readonly API_URL = (typeof window !== 'undefined' && window.location.port === '4200')
    ? 'http://localhost:8000/api'
    : '/api';

  // --- Usuarios & Roles ---
  getUsers(): Observable<Usuario[]> {
    return this.http.get<Usuario[]>(`${this.API_URL}/users/`, {
      headers: this.auth.getHeaders()
    });
  }

  getUserByCi(ci: string): Observable<Usuario> {
    return this.http.get<Usuario>(`${this.API_URL}/users/${ci}`, {
      headers: this.auth.getHeaders()
    });
  }

  createUser(payload: any): Observable<Usuario> {
    return this.http.post<Usuario>(`${this.API_URL}/users/`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  updateUser(ci: string, payload: any): Observable<Usuario> {
    return this.http.put<Usuario>(`${this.API_URL}/users/${ci}`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  toggleUserStatus(ci: string): Observable<Usuario> {
    return this.http.patch<Usuario>(`${this.API_URL}/users/${ci}/toggle-estado`, {}, {
      headers: this.auth.getHeaders()
    });
  }

  getRoles(): Observable<Rol[]> {
    return this.http.get<Rol[]>(`${this.API_URL}/users/roles/all`, {
      headers: this.auth.getHeaders()
    });
  }

  createRole(payload: any): Observable<Rol> {
    return this.http.post<Rol>(`${this.API_URL}/users/roles`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  getPermisos(): Observable<Permiso[]> {
    return this.http.get<Permiso[]>(`${this.API_URL}/users/permisos/all`, {
      headers: this.auth.getHeaders()
    });
  }

  // --- Trabajadores & Áreas ---
  getTrabajadores(busqueda?: string, areaId?: number, soloActivos?: boolean): Observable<Trabajador[]> {
    let params: any = {};
    if (busqueda) params.busqueda = busqueda;
    if (areaId !== undefined && areaId !== null) params.area_id = areaId;
    if (soloActivos !== undefined && soloActivos !== null) params.solo_activos = soloActivos;

    return this.http.get<Trabajador[]>(`${this.API_URL}/trabajadores/`, {
      headers: this.auth.getHeaders(),
      params
    });
  }

  getTrabajadorById(id: number): Observable<Trabajador> {
    return this.http.get<Trabajador>(`${this.API_URL}/trabajadores/${id}`, {
      headers: this.auth.getHeaders()
    });
  }

  createTrabajador(payload: any): Observable<Trabajador> {
    return this.http.post<Trabajador>(`${this.API_URL}/trabajadores/`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  updateTrabajador(id: number, payload: any): Observable<Trabajador> {
    return this.http.put<Trabajador>(`${this.API_URL}/trabajadores/${id}`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  toggleTrabajadorStatus(id: number): Observable<Trabajador> {
    return this.http.patch<Trabajador>(`${this.API_URL}/trabajadores/${id}/toggle-estado`, {}, {
      headers: this.auth.getHeaders()
    });
  }

  getAreas(): Observable<Area[]> {
    return this.http.get<Area[]>(`${this.API_URL}/trabajadores/areas/all`, {
      headers: this.auth.getHeaders()
    });
  }

  createArea(payload: any): Observable<Area> {
    return this.http.post<Area>(`${this.API_URL}/trabajadores/areas`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  // --- Bitácora ---
  getBitacora(limit: number = 50, modulo?: string): Observable<Bitacora[]> {
    let params: any = { limit };
    if (modulo) params.modulo = modulo;
    return this.http.get<Bitacora[]>(`${this.API_URL}/bitacora/`, {
      headers: this.auth.getHeaders(),
      params
    });
  }

  // --- Pagos y Anticipos ---
  getPeriodos(): Observable<PeriodoSalarial[]> {
    return this.http.get<PeriodoSalarial[]>(`${this.API_URL}/pagos/periodos`, {
      headers: this.auth.getHeaders()
    });
  }

  createPeriodo(payload: any): Observable<PeriodoSalarial> {
    return this.http.post<PeriodoSalarial>(`${this.API_URL}/pagos/periodos`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  getPanelGeneralPagos(periodoId?: number): Observable<PanelResumenPagos> {
    let params: any = {};
    if (periodoId) params.periodo_id = periodoId;
    return this.http.get<PanelResumenPagos>(`${this.API_URL}/pagos/panel-general`, {
      headers: this.auth.getHeaders(),
      params
    });
  }

  getResumenSalarial(trabajadorId: number, periodoId: number): Observable<ResumenSalarialTrabajador> {
    return this.http.get<ResumenSalarialTrabajador>(
      `${this.API_URL}/pagos/trabajador/${trabajadorId}/resumen-salarial`,
      {
        headers: this.auth.getHeaders(),
        params: { periodo_id: periodoId }
      }
    );
  }

  getAnticipos(periodoId?: number, trabajadorId?: number, areaId?: number): Observable<Anticipo[]> {
    let params: any = {};
    if (periodoId) params.periodo_id = periodoId;
    if (trabajadorId) params.trabajador_id = trabajadorId;
    if (areaId) params.area_id = areaId;
    return this.http.get<Anticipo[]>(`${this.API_URL}/pagos/anticipos`, {
      headers: this.auth.getHeaders(),
      params
    });
  }

  createAnticipo(payload: any): Observable<Anticipo> {
    return this.http.post<Anticipo>(`${this.API_URL}/pagos/anticipos`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  anularAnticipo(id: number, motivo: string): Observable<any> {
    return this.http.patch(`${this.API_URL}/pagos/anticipos/${id}/anular`, { motivo }, {
      headers: this.auth.getHeaders()
    });
  }

  getComprobanteAnticipoDetallado(anticipoId: number): Observable<ComprobanteAnticipoDetallado> {
    return this.http.get<ComprobanteAnticipoDetallado>(`${this.API_URL}/pagos/anticipos/${anticipoId}/comprobante`, {
      headers: this.auth.getHeaders()
    });
  }

  getResumenPagosParciales(periodoId: number): Observable<ResumenTrabajadorPagosParciales[]> {
    return this.http.get<ResumenTrabajadorPagosParciales[]>(`${this.API_URL}/pagos/pagos-parciales/resumen`, {
      headers: this.auth.getHeaders(),
      params: { periodo_id: periodoId }
    });
  }

  registrarPagoParcialDirecto(payload: PagoParcialDirectoPayload): Observable<PagoLiquidacion> {
    return this.http.post<PagoLiquidacion>(`${this.API_URL}/pagos/pagos-parciales/directo`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  getLiquidaciones(periodoId?: number, trabajadorId?: number, estado?: string, areaId?: number): Observable<Liquidacion[]> {
    let params: any = {};
    if (periodoId) params.periodo_id = periodoId;
    if (trabajadorId) params.trabajador_id = trabajadorId;
    if (estado) params.estado = estado;
    if (areaId) params.area_id = areaId;
    return this.http.get<Liquidacion[]>(`${this.API_URL}/pagos/liquidaciones`, {
      headers: this.auth.getHeaders(),
      params
    });
  }

  createLiquidacion(payload: any): Observable<Liquidacion> {
    return this.http.post<Liquidacion>(`${this.API_URL}/pagos/liquidaciones`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  createPagoLiquidacion(payload: any): Observable<PagoLiquidacion> {
    return this.http.post<PagoLiquidacion>(`${this.API_URL}/pagos/liquidaciones/pagos`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  anularLiquidacion(id: number, motivo: string): Observable<any> {
    return this.http.patch(`${this.API_URL}/pagos/liquidaciones/${id}/anular`, { motivo }, {
      headers: this.auth.getHeaders()
    });
  }

  getHistorialTrabajador(trabajadorId: number): Observable<HistorialTrabajadorResponse> {
    return this.http.get<HistorialTrabajadorResponse>(`${this.API_URL}/pagos/historial/${trabajadorId}`, {
      headers: this.auth.getHeaders()
    });
  }

  // ==========================================
  // INVENTARIO: ALMACÉN
  // ==========================================

  getProductosAlmacen(busqueda?: string, estado_stock?: string, unidad_control?: string): Observable<ProductoAlmacen[]> {
    let params: any = {};
    if (busqueda) params.busqueda = busqueda;
    if (estado_stock && estado_stock !== 'TODOS') params.estado_stock = estado_stock;
    if (unidad_control) params.unidad_control = unidad_control;
    return this.http.get<ProductoAlmacen[]>(`${this.API_URL}/inventario/almacen/productos`, {
      headers: this.auth.getHeaders(),
      params
    });
  }

  buscarProductosAlmacen(q: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.API_URL}/inventario/almacen/productos/buscar`, {
      headers: this.auth.getHeaders(),
      params: { q }
    });
  }

  getProductoDetalle(id: number): Observable<ProductoAlmacenDetalle> {
    return this.http.get<ProductoAlmacenDetalle>(`${this.API_URL}/inventario/almacen/productos/${id}`, {
      headers: this.auth.getHeaders()
    });
  }

  crearProductoConPrimeraCompra(payload: any): Observable<ProductoAlmacen> {
    return this.http.post<ProductoAlmacen>(`${this.API_URL}/inventario/almacen/productos`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  registrarCompraPosterior(payload: any): Observable<CompraAlmacen> {
    return this.http.post<CompraAlmacen>(`${this.API_URL}/inventario/almacen/compras`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  registrarSalidaAlmacen(payload: any): Observable<MovimientoAlmacen> {
    return this.http.post<MovimientoAlmacen>(`${this.API_URL}/inventario/almacen/salidas`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  registrarAjusteStock(payload: any): Observable<MovimientoAlmacen> {
    return this.http.post<MovimientoAlmacen>(`${this.API_URL}/inventario/almacen/ajustes`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  anularMovimientoAlmacen(id: number, motivo: string): Observable<any> {
    return this.http.patch(`${this.API_URL}/inventario/almacen/movimientos/${id}/anular`, { motivo }, {
      headers: this.auth.getHeaders()
    });
  }

  getMovimientosAlmacen(paramsObj?: any): Observable<MovimientoAlmacen[]> {
    let params: any = {};
    if (paramsObj) {
      if (paramsObj.almacen_id) params.almacen_id = paramsObj.almacen_id;
      if (paramsObj.tipo_movimiento) params.tipo_movimiento = paramsObj.tipo_movimiento;
      if (paramsObj.trabajador_id) params.trabajador_id = paramsObj.trabajador_id;
      if (paramsObj.area_id) params.area_id = paramsObj.area_id;
      if (paramsObj.fecha_inicio) params.fecha_inicio = paramsObj.fecha_inicio;
      if (paramsObj.fecha_fin) params.fecha_fin = paramsObj.fecha_fin;
    }
    return this.http.get<MovimientoAlmacen[]>(`${this.API_URL}/inventario/almacen/movimientos`, {
      headers: this.auth.getHeaders(),
      params
    });
  }

  getReporteAlmacen(): Observable<ReporteAlmacenResumen> {
    return this.http.get<ReporteAlmacenResumen>(`${this.API_URL}/inventario/almacen/reportes/resumen`, {
      headers: this.auth.getHeaders()
    });
  }

  // ==========================================
  // INVENTARIO: GASTOS MENORES
  // ==========================================

  getGastosMenores(paramsObj?: any): Observable<GastoMenor[]> {
    let params: any = {};
    if (paramsObj) {
      if (paramsObj.busqueda) params.busqueda = paramsObj.busqueda;
      if (paramsObj.area_id) params.area_id = paramsObj.area_id;
      if (paramsObj.trabajador_id) params.trabajador_id = paramsObj.trabajador_id;
      if (paramsObj.fecha_inicio) params.fecha_inicio = paramsObj.fecha_inicio;
      if (paramsObj.fecha_fin) params.fecha_fin = paramsObj.fecha_fin;
      if (paramsObj.estado) params.estado = paramsObj.estado;
    }
    return this.http.get<GastoMenor[]>(`${this.API_URL}/inventario/gastos`, {
      headers: this.auth.getHeaders(),
      params
    });
  }

  crearGastoMenor(payload: any): Observable<GastoMenor> {
    return this.http.post<GastoMenor>(`${this.API_URL}/inventario/gastos`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  actualizarGastoMenor(id: number, payload: any): Observable<GastoMenor> {
    return this.http.put<GastoMenor>(`${this.API_URL}/inventario/gastos/${id}`, payload, {
      headers: this.auth.getHeaders()
    });
  }

  anularGastoMenor(id: number, motivo: string): Observable<any> {
    return this.http.patch(`${this.API_URL}/inventario/gastos/${id}/anular`, { motivo }, {
      headers: this.auth.getHeaders()
    });
  }

  getReporteGastos(fecha_inicio?: string, fecha_fin?: string): Observable<ReporteGastosResumen> {
    let params: any = {};
    if (fecha_inicio) params.fecha_inicio = fecha_inicio;
    if (fecha_fin) params.fecha_fin = fecha_fin;
    return this.http.get<ReporteGastosResumen>(`${this.API_URL}/inventario/gastos/reportes/resumen`, {
      headers: this.auth.getHeaders(),
      params
    });
  }

  // --- Contabilidad y Finanzas ---
  getContabilidadAnios(): Observable<number[]> {
    return this.http.get<number[]>(`${this.API_URL}/contabilidad/anios-disponibles`, {
      headers: this.auth.getHeaders()
    });
  }

  getContabilidadMensual(mes: number, anio: number, areaId?: number): Observable<ContabilidadReporteMensual> {
    let params: any = { mes, anio };
    if (areaId) {
      params.area_id = areaId;
    }
    return this.http.get<ContabilidadReporteMensual>(`${this.API_URL}/contabilidad/mensual`, {
      headers: this.auth.getHeaders(),
      params
    });
  }

  getContabilidadAnual(anio: number, areaId?: number): Observable<ContabilidadReporteAnual> {
    let params: any = { anio };
    if (areaId) {
      params.area_id = areaId;
    }
    return this.http.get<ContabilidadReporteAnual>(`${this.API_URL}/contabilidad/anual`, {
      headers: this.auth.getHeaders(),
      params
    });
  }
}
