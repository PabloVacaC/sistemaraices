import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DataService } from '../../core/services/data.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import {
  Trabajador,
  Area,
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
  MovimientoHistorial
} from '../../core/models/types';

@Component({
  selector: 'app-pagos',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './pagos.component.html',
  styleUrls: ['./pagos.component.css']
})
export class PagosComponent implements OnInit {
  private dataService = inject(DataService);
  public auth = inject(AuthService);
  private toast = inject(ToastService);

  // Estados principales
  loading = signal<boolean>(false);
  activeTab = signal<'panel' | 'anticipos' | 'pagos_parciales' | 'historial'>('panel');

  // Datos del backend
  periodos = signal<PeriodoSalarial[]>([]);
  selectedPeriodoId = signal<number | null>(null);
  trabajadores = signal<Trabajador[]>([]);
  areas = signal<Area[]>([]);
  panelIndicadores = signal<PanelResumenPagos | null>(null);

  // Listados
  anticiposList = signal<Anticipo[]>([]);
  liquidacionesList = signal<Liquidacion[]>([]);

  // Búsqueda y Filtros de Trabajador
  searchTerm = signal<string>('');
  selectedAreaFilter = signal<number | null>(null);
  selectedTrabajador = signal<Trabajador | null>(null);
  resumenSalarial = signal<ResumenSalarialTrabajador | null>(null);

  // Formulario de Anticipo
  anticipoImporte = signal<number | null>(null);
  anticipoFechaEntrega = signal<string>(new Date().toISOString().substring(0, 10));
  anticipoForm = {
    importe: null as number | null,
    metodo_pago: 'EFECTIVO',
    fecha_entrega: new Date().toISOString().substring(0, 10),
    observaciones: ''
  };

  // Formulario de Pago Parcial
  selectedLiquidacionForPago = signal<Liquidacion | null>(null);
  pagoParcialForm = {
    monto: null as number | null,
    metodo_pago: 'EFECTIVO',
    fecha_pago: new Date().toISOString().substring(0, 10),
    observaciones: ''
  };

  // Historial del trabajador
  historialData = signal<HistorialTrabajadorResponse | null>(null);

  // Pagos Parciales
  resumenPagosParciales = signal<ResumenTrabajadorPagosParciales[]>([]);
  searchTermPagosParciales = signal<string>('');
  selectedTrabajadorQuincena = signal<ResumenTrabajadorPagosParciales | null>(null);
  showModalPagoQuincena = signal<boolean>(false);
  pagoQuincenaForm = {
    monto: null as number | null,
    tipo_pago: 'PAGO_QUINCENA',
    metodo_pago: 'EFECTIVO',
    fecha_pago: new Date().toISOString().substring(0, 10),
    observaciones: ''
  };

  // Modal Liquidación Directa desde Pagos Parciales
  showModalLiquidarTrabajador = signal<boolean>(false);
  selectedTrabajadorForLiquidacion = signal<ResumenTrabajadorPagosParciales | null>(null);
  liquidacionDirectaForm = {
    fecha_liquidacion: new Date().toISOString().substring(0, 10),
    ajustes: 0,
    observaciones: 'Liquidación de sueldo restante (Día 5)',
    pago_inmediato: true,
    monto_pago_inmediato: null as number | null,
    metodo_pago_inmediato: 'EFECTIVO'
  };

  // Comprobante detallado histórico de anticipo
  currentDetailedReceipt = signal<ComprobanteAnticipoDetallado | null>(null);

  // Modales
  showConfirmAnticipoModal = signal<boolean>(false);
  showPagoParcialModal = signal<boolean>(false);
  showReceiptModal = signal<boolean>(false);
  showAnulacionModal = signal<boolean>(false);

  // Datos del comprobante a mostrar
  currentReceipt = signal<{
    tipo: 'ANTICIPO' | 'LIQUIDACION' | 'PAGO_LIQUIDACION';
    numero_comprobante: string;
    trabajador_nombre: string;
    trabajador_ci?: string;
    trabajador_cargo?: string;
    trabajador_area?: string;
    periodo_descripcion: string;
    fecha: string;
    importe: number;
    metodo_pago: string;
    sueldo_base?: number;
    anticipos_descontados?: number;
    ajustes?: number;
    saldo_restante?: number;
    observaciones?: string;
    telefono_contacto?: string;
    usuario_nombre?: string;
    usuario_id?: string;
  } | null>(null);

  // Datos para anulación
  anulacionTarget = signal<{ tipo: 'ANTICIPO' | 'LIQUIDACION'; id: number; comprobante: string; motivo: string } | null>(null);

  // Trabajadores filtrados
  filteredTrabajadores = computed(() => {
    const term = this.searchTerm().toLowerCase().trim();
    const areaId = this.selectedAreaFilter();
    return this.trabajadores().filter(t => {
      const matchArea = areaId ? t.area_id === areaId : true;
      const matchSearch = term === '' ||
        (t.nombres + ' ' + t.apellidos).toLowerCase().includes(term) ||
        (t.ci && t.ci.toLowerCase().includes(term)) ||
        (t.cargo && t.cargo.toLowerCase().includes(term));
      return matchArea && matchSearch;
    });
  });

  filteredPagosParciales = computed(() => {
    const term = this.searchTermPagosParciales().toLowerCase().trim();
    return this.resumenPagosParciales().filter(t => {
      return term === '' ||
        t.nombre_completo.toLowerCase().includes(term) ||
        (t.ci && t.ci.toLowerCase().includes(term)) ||
        t.cargo.toLowerCase().includes(term) ||
        t.area.toLowerCase().includes(term);
    });
  });

  simulacionAnticipo = computed(() => {
    const resumen = this.resumenSalarial();
    const trab = this.selectedTrabajador();
    const monto = Number(this.anticipoImporte() || 0);
    if (!resumen || !trab) return null;

    const totalPrevio = Number(resumen.total_anticipos || 0);
    const antes18Previo = Number(resumen.anticipos_antes_dia_18 || 0);
    const quincenaRef = Number(resumen.quincena_referencia || 1000);
    const sueldoBase = Number(trab.sueldoBase || 0);
    const totalPagos = Number(resumen.total_pagos_parciales || 0);

    const f = this.anticipoFechaEntrega();
    let diaEntrega = 1;
    if (f) {
      const parts = f.split('-');
      if (parts.length === 3) {
        diaEntrega = parseInt(parts[2], 10) || 1;
      }
    }
    const esAntes18 = diaEntrega <= 18;

    const nuevoTotalAntes18 = esAntes18 ? (antes18Previo + monto) : antes18Previo;
    const nuevoTotalAnticipos = totalPrevio + monto;
    const nuevaDiferenciaQuincena = Math.max(0, quincenaRef - nuevoTotalAntes18);
    const nuevoSaldoRestante = sueldoBase - nuevoTotalAnticipos - totalPagos;
    const superaQuincena = nuevoTotalAntes18 > quincenaRef;
    const excedenteQuincena = superaQuincena ? (nuevoTotalAntes18 - quincenaRef) : 0;
    const superaSueldoBase = nuevoTotalAnticipos > sueldoBase;

    return {
      monto,
      esAntes18,
      nuevoTotalAntes18,
      nuevoTotalAnticipos,
      nuevaDiferenciaQuincena,
      nuevoSaldoRestante,
      superaQuincena,
      excedenteQuincena,
      superaSueldoBase,
    };
  });

  ngOnInit() {
    this.cargarDatosIniciales();
  }

  cargarDatosIniciales() {
    this.loading.set(true);
    // Cargar períodos
    this.dataService.getPeriodos().subscribe({
      next: (pers) => {
        this.periodos.set(pers);
        if (pers.length > 0 && !this.selectedPeriodoId()) {
          // Seleccionar período actual o más reciente
          const actual = pers.find(p => p.mes === (new Date().getMonth() + 1) && p.anio === new Date().getFullYear()) || pers[0];
          this.selectedPeriodoId.set(actual.id);
        }
        this.cargarIndicadores();
        this.cargarLiquidaciones();
        this.cargarAnticipos();
        this.cargarPagosParciales();
      },
      error: () => this.toast.error('Error al cargar períodos salariales')
    });

    // Cargar áreas
    this.dataService.getAreas().subscribe({
      next: (a) => this.areas.set(a),
      error: () => {}
    });

    // Cargar trabajadores
    this.dataService.getTrabajadores(undefined, undefined, true).subscribe({
      next: (trabs) => {
        this.trabajadores.set(trabs);
        this.loading.set(false);
      },
      error: () => {
        this.toast.error('Error al cargar lista de trabajadores');
        this.loading.set(false);
      }
    });
  }

  cargarIndicadores() {
    const pid = this.selectedPeriodoId();
    this.dataService.getPanelGeneralPagos(pid || undefined).subscribe({
      next: (panel) => this.panelIndicadores.set(panel),
      error: () => {}
    });
  }

  cargarAnticipos() {
    const pid = this.selectedPeriodoId();
    this.dataService.getAnticipos(pid || undefined).subscribe({
      next: (ants) => this.anticiposList.set(ants),
      error: () => {}
    });
  }

  cargarLiquidaciones() {
    const pid = this.selectedPeriodoId();
    this.dataService.getLiquidaciones(pid || undefined).subscribe({
      next: (liqs) => this.liquidacionesList.set(liqs),
      error: () => {}
    });
  }

  onPeriodoChange(periodoId: any) {
    const pid = Number(periodoId);
    this.selectedPeriodoId.set(pid);
    this.cargarIndicadores();
    this.cargarLiquidaciones();
    this.cargarAnticipos();
    this.cargarPagosParciales();
    if (this.selectedTrabajador()) {
      this.cargarResumenSalarial(this.selectedTrabajador()!.id);
    }
  }

  setTab(tab: 'panel' | 'anticipos' | 'pagos_parciales' | 'historial') {
    this.activeTab.set(tab);
    if (tab === 'pagos_parciales') {
      this.cargarPagosParciales();
    } else if (tab === 'panel') {
      this.cargarIndicadores();
      this.cargarLiquidaciones();
      this.cargarAnticipos();
    } else if (tab === 'anticipos') {
      this.cargarAnticipos();
      if (this.selectedTrabajador()) {
        this.cargarResumenSalarial(this.selectedTrabajador()!.id);
      }
    }
  }

  cargarPagosParciales() {
    const pid = this.selectedPeriodoId();
    if (!pid) return;
    this.dataService.getResumenPagosParciales(pid).subscribe({
      next: (res) => this.resumenPagosParciales.set(res),
      error: (err) => {
        console.error('Error al cargar pagos parciales:', err);
        this.toast.error(err?.error?.detail || 'Error al cargar lista de pagos parciales');
      }
    });
  }

  abrirModalPagoQuincena(trab: ResumenTrabajadorPagosParciales) {
    this.selectedTrabajadorQuincena.set(trab);
    this.pagoQuincenaForm.monto = trab.monto_sugerido_quincena;
    this.pagoQuincenaForm.tipo_pago = trab.supera_quincena ? 'REVISION_QUINCENA' : 'PAGO_QUINCENA';
    this.pagoQuincenaForm.fecha_pago = new Date().toISOString().substring(0, 10);
    this.pagoQuincenaForm.metodo_pago = 'EFECTIVO';
    this.pagoQuincenaForm.observaciones = trab.supera_quincena
      ? 'Quincena cubierta en su totalidad por anticipos acumulados'
      : 'Pago de primera quincena (Día 18)';
    this.showModalPagoQuincena.set(true);
  }

  confirmarPagoQuincenaDirecto() {
    const trab = this.selectedTrabajadorQuincena();
    const pid = this.selectedPeriodoId();
    if (!trab || !pid) return;

    const monto = Number(this.pagoQuincenaForm.monto ?? 0);
    if (monto < 0) {
      this.toast.warning('El monto a pagar no puede ser negativo.');
      return;
    }
    if (monto > trab.saldo_salarial_pendiente && trab.saldo_salarial_pendiente > 0) {
      this.toast.warning(`El monto supera el saldo pendiente de Bs ${trab.saldo_salarial_pendiente}.`);
      return;
    }

    this.loading.set(true);
    this.showModalPagoQuincena.set(false);

    const payload: PagoParcialDirectoPayload = {
      trabajador_id: trab.trabajador_id,
      periodo_id: pid,
      monto: monto,
      tipo_pago: this.pagoQuincenaForm.tipo_pago,
      metodo_pago: this.pagoQuincenaForm.metodo_pago,
      fecha_pago: this.pagoQuincenaForm.fecha_pago,
      observaciones: this.pagoQuincenaForm.observaciones,
    };

    this.dataService.registrarPagoParcialDirecto(payload).subscribe({
      next: (pago) => {
        this.toast.success(`Pago de quincena registrado: ${pago.numero_comprobante}`);
        this.loading.set(false);
        this.cargarIndicadores();
        this.cargarPagosParciales();
        this.cargarLiquidaciones();
        if (this.selectedTrabajador()?.id === trab.trabajador_id) {
          this.cargarResumenSalarial(trab.trabajador_id);
        }

        const periodoDesc = this.periodos().find(p => p.id === pid)?.descripcion || '';
        this.currentDetailedReceipt.set(null);
        this.abrirComprobante({
          tipo: 'PAGO_LIQUIDACION',
          numero_comprobante: pago.numero_comprobante,
          trabajador_nombre: trab.nombre_completo,
          trabajador_ci: trab.ci,
          trabajador_cargo: trab.cargo,
          trabajador_area: trab.area,
          periodo_descripcion: periodoDesc,
          fecha: pago.fecha_pago,
          importe: pago.monto,
          metodo_pago: pago.metodo_pago,
          sueldo_base: trab.sueldo_base,
          saldo_restante: trab.saldo_salarial_pendiente - pago.monto,
          observaciones: `${pago.tipo_pago}: ${pago.observaciones || ''}`,
          usuario_nombre: pago.usuario_nombre,
          usuario_id: pago.usuario_id,
        });
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al registrar pago de quincena');
        this.loading.set(false);
      }
    });
  }

  calcularSaldoLiquidacionDirecta(): number {
    const trab = this.selectedTrabajadorForLiquidacion();
    if (!trab) return 0;
    const base = Number(trab.sueldo_base || 0);
    const ajustes = Number(this.liquidacionDirectaForm.ajustes || 0);
    const anticipos = Number(trab.total_anticipos_periodo || 0);
    const pagos = Number(trab.total_pagos_parciales || 0);
    return Math.max(0, base + ajustes - anticipos - pagos);
  }

  abrirModalLiquidarTrabajador(trab: ResumenTrabajadorPagosParciales) {
    this.selectedTrabajadorForLiquidacion.set(trab);
    const base = Number(trab.sueldo_base || 0);
    const anticipos = Number(trab.total_anticipos_periodo || 0);
    const pagos = Number(trab.total_pagos_parciales || 0);
    const saldoRestante = Math.max(0, base - anticipos - pagos);

    this.liquidacionDirectaForm = {
      fecha_liquidacion: new Date().toISOString().substring(0, 10),
      ajustes: 0,
      observaciones: 'Liquidación de sueldo restante (Día 5)',
      pago_inmediato: true,
      monto_pago_inmediato: saldoRestante,
      metodo_pago_inmediato: 'EFECTIVO'
    };
    this.showModalLiquidarTrabajador.set(true);
  }

  confirmarLiquidacionDirecta() {
    const trab = this.selectedTrabajadorForLiquidacion();
    const pid = this.selectedPeriodoId();
    if (!trab || !pid) return;

    const saldoCalculado = this.calcularSaldoLiquidacionDirecta();
    if (this.liquidacionDirectaForm.pago_inmediato) {
      const monto = Number(this.liquidacionDirectaForm.monto_pago_inmediato ?? 0);
      if (monto < 0) {
        this.toast.warning('El monto a pagar no puede ser negativo.');
        return;
      }
      if (monto > saldoCalculado && saldoCalculado > 0) {
        this.toast.warning(`El monto a pagar supera el saldo de Bs ${saldoCalculado}.`);
        return;
      }
    }

    this.loading.set(true);
    this.showModalLiquidarTrabajador.set(false);

    const payload = {
      trabajador_id: trab.trabajador_id,
      periodo_id: pid,
      fecha_liquidacion: this.liquidacionDirectaForm.fecha_liquidacion,
      ajustes: Number(this.liquidacionDirectaForm.ajustes || 0),
      observaciones: this.liquidacionDirectaForm.observaciones,
      pago_inmediato: this.liquidacionDirectaForm.pago_inmediato,
      monto_pago_inmediato: this.liquidacionDirectaForm.pago_inmediato ? this.liquidacionDirectaForm.monto_pago_inmediato : null,
      metodo_pago_inmediato: this.liquidacionDirectaForm.metodo_pago_inmediato
    };

    this.dataService.createLiquidacion(payload).subscribe({
      next: (liq) => {
        this.toast.success(`Liquidación registrada: ${liq.numero_comprobante}`);
        this.loading.set(false);
        this.cargarIndicadores();
        this.cargarPagosParciales();
        this.cargarLiquidaciones();

        const periodoDesc = this.periodos().find(p => p.id === pid)?.descripcion || '';
        this.currentDetailedReceipt.set(null);
        this.abrirComprobante({
          tipo: 'LIQUIDACION',
          numero_comprobante: liq.numero_comprobante,
          trabajador_nombre: trab.nombre_completo,
          trabajador_ci: trab.ci,
          trabajador_cargo: trab.cargo,
          trabajador_area: trab.area,
          periodo_descripcion: periodoDesc,
          fecha: liq.fecha_liquidacion,
          importe: liq.monto_pagado,
          metodo_pago: this.liquidacionDirectaForm.pago_inmediato ? this.liquidacionDirectaForm.metodo_pago_inmediato : 'POR PAGAR',
          sueldo_base: liq.sueldo_base,
          saldo_restante: liq.saldo_pendiente,
          observaciones: liq.observaciones || 'Liquidación Salarial Final (Día 5)',
          usuario_nombre: liq.usuario_nombre,
          usuario_id: liq.usuario_id,
        });
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al registrar liquidación');
        this.loading.set(false);
      }
    });
  }

  abrirComprobanteAnticipoDetallado(anticipoId: number) {
    this.loading.set(true);
    this.dataService.getComprobanteAnticipoDetallado(anticipoId).subscribe({
      next: (comp) => {
        this.currentDetailedReceipt.set(comp);
        this.currentReceipt.set({
          tipo: 'ANTICIPO',
          numero_comprobante: comp.numero_comprobante,
          trabajador_nombre: comp.trabajador_nombre,
          trabajador_ci: comp.trabajador_ci,
          trabajador_cargo: comp.trabajador_cargo,
          trabajador_area: comp.trabajador_area,
          periodo_descripcion: comp.periodo_descripcion,
          fecha: comp.fecha_anticipo,
          importe: comp.importe_actual,
          metodo_pago: comp.metodo_entrega,
          sueldo_base: comp.sueldo_base,
          observaciones: comp.motivo,
          usuario_nombre: comp.usuario_nombre,
          usuario_id: comp.usuario_ci,
        });
        this.showReceiptModal.set(true);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.toast.error('Error al cargar comprobante detallado');
      }
    });
  }

  selectTrabajador(t: Trabajador) {
    this.selectedTrabajador.set(t);
    this.anticipoImporte.set(null);
    this.anticipoForm.importe = null;
    this.cargarResumenSalarial(t.id);
  }

  onAnticipoImporteChange(val: any) {
    const num = (val !== null && val !== '' && !isNaN(Number(val))) ? Number(val) : null;
    this.anticipoImporte.set(num);
    this.anticipoForm.importe = num;
  }

  onAnticipoFechaEntregaChange(val: string) {
    this.anticipoFechaEntrega.set(val);
    this.anticipoForm.fecha_entrega = val;
  }

  cargarResumenSalarial(trabajadorId: number) {
    const pid = this.selectedPeriodoId();
    if (!pid) return;

    this.loading.set(true);
    this.dataService.getResumenSalarial(trabajadorId, pid).subscribe({
      next: (res) => {
        this.resumenSalarial.set(res);
        this.loading.set(false);
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al obtener resumen salarial');
        this.loading.set(false);
      }
    });
  }

  // ==========================================
  // FLUJO DE REGISTRO DE ANTICIPO
  // ==========================================
  prepararAnticipo() {
    const trab = this.selectedTrabajador();
    const pid = this.selectedPeriodoId();
    if (!trab || !pid) {
      this.toast.warning('Por favor selecciona un trabajador y un período.');
      return;
    }
    const monto = this.anticipoImporte();
    if (!monto || monto <= 0) {
      this.toast.warning('El importe del anticipo debe ser mayor a Bs 0.');
      return;
    }
    const resumen = this.resumenSalarial();
    if (resumen && trab.sueldoBase > 0) {
      const nuevoTotal = Number(resumen.total_anticipos) + Number(monto);
      if (nuevoTotal > trab.sueldoBase) {
        this.toast.warning(`El importe solicitado superaría el sueldo base del trabajador (Bs ${trab.sueldoBase}).`);
        return;
      }
    }
    this.showConfirmAnticipoModal.set(true);
  }

  confirmarRegistroAnticipo() {
    const trab = this.selectedTrabajador();
    const pid = this.selectedPeriodoId();
    const monto = this.anticipoImporte();
    if (!trab || !pid || !monto) return;

    this.loading.set(true);
    this.showConfirmAnticipoModal.set(false);

    const payload = {
      trabajador_id: trab.id,
      periodo_id: pid,
      importe: monto,
      metodo_pago: this.anticipoForm.metodo_pago,
      fecha_entrega: this.anticipoFechaEntrega(),
      observaciones: this.anticipoForm.observaciones
    };

    this.dataService.createAnticipo(payload).subscribe({
      next: (nuevoAnt) => {
        this.toast.success(`Anticipo registrado exitosamente: ${nuevoAnt.numero_comprobante}`);
        this.loading.set(false);
        this.anticipoImporte.set(null);
        this.anticipoForm.importe = null;
        this.anticipoForm.observaciones = '';

        // Actualizar datos
        this.cargarIndicadores();
        this.cargarAnticipos();
        this.cargarPagosParciales();
        this.cargarResumenSalarial(trab.id);

        // Abrir comprobante histórico detallado
        this.abrirComprobanteAnticipoDetallado(nuevoAnt.id);
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al registrar anticipo');
        this.loading.set(false);
      }
    });
  }

  // ==========================================
  // FLUJO DE PAGO PARCIAL A LIQUIDACIÓN
  // ==========================================
  abrirModalPagoParcial(liq: Liquidacion) {
    this.selectedLiquidacionForPago.set(liq);
    this.pagoParcialForm.monto = liq.saldo_pendiente;
    this.pagoParcialForm.fecha_pago = new Date().toISOString().substring(0, 10);
    this.pagoParcialForm.metodo_pago = 'EFECTIVO';
    this.pagoParcialForm.observaciones = '';
    this.showPagoParcialModal.set(true);
  }

  confirmarPagoParcial() {
    const liq = this.selectedLiquidacionForPago();
    if (!liq || !this.pagoParcialForm.monto || this.pagoParcialForm.monto <= 0) {
      this.toast.warning('Ingresa un monto de pago válido.');
      return;
    }
    if (this.pagoParcialForm.monto > liq.saldo_pendiente) {
      this.toast.warning(`El monto no puede superar el saldo pendiente de Bs ${liq.saldo_pendiente}.`);
      return;
    }

    this.loading.set(true);
    this.showPagoParcialModal.set(false);

    const payload = {
      liquidacion_id: liq.id,
      monto: this.pagoParcialForm.monto,
      metodo_pago: this.pagoParcialForm.metodo_pago,
      fecha_pago: this.pagoParcialForm.fecha_pago,
      observaciones: this.pagoParcialForm.observaciones
    };

    this.dataService.createPagoLiquidacion(payload).subscribe({
      next: (pago) => {
        this.toast.success(`Pago registrado: ${pago.numero_comprobante}`);
        this.loading.set(false);
        this.cargarIndicadores();
        this.cargarLiquidaciones();
        if (this.selectedTrabajador()) {
          this.cargarResumenSalarial(this.selectedTrabajador()!.id);
        }

        const trab = this.trabajadores().find(t => t.id === liq.trabajador_id);
        const periodoDesc = this.periodos().find(p => p.id === liq.periodo_id)?.descripcion || '';
        const nuevoSaldo = Number(liq.saldo_pendiente) - Number(pago.monto);

        this.abrirComprobante({
          tipo: 'PAGO_LIQUIDACION',
          numero_comprobante: pago.numero_comprobante,
          trabajador_nombre: trab ? `${trab.nombres} ${trab.apellidos}` : 'Trabajador',
          trabajador_ci: trab?.ci,
          trabajador_cargo: trab?.cargo,
          trabajador_area: trab?.area?.nombre,
          periodo_descripcion: periodoDesc,
          fecha: pago.fecha_pago,
          importe: pago.monto,
          metodo_pago: pago.metodo_pago,
          saldo_restante: nuevoSaldo,
          observaciones: pago.observaciones,
          telefono_contacto: trab?.celular,
          usuario_nombre: pago.usuario_nombre,
          usuario_id: pago.usuario_id
        });
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al registrar pago parcial');
        this.loading.set(false);
      }
    });
  }

  // ==========================================
  // CONSULTA DE HISTORIAL DEL TRABAJADOR
  // ==========================================
  verHistorialTrabajador(trabajadorId: number) {
    this.activeTab.set('historial');
    this.loading.set(true);
    this.dataService.getHistorialTrabajador(trabajadorId).subscribe({
      next: (res) => {
        this.historialData.set(res);
        this.loading.set(false);
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al obtener historial');
        this.loading.set(false);
      }
    });
  }

  // ==========================================
  // COMPROBANTES Y WHATSAPP
  // ==========================================
  abrirComprobante(data: any) {
    if (data.tipo !== 'ANTICIPO') {
      this.currentDetailedReceipt.set(null);
    }
    this.currentReceipt.set(data);
    this.showReceiptModal.set(true);
  }

  imprimirComprobante() {
    window.print();
  }

  compartirWhatsApp() {
    const rc = this.currentReceipt();
    if (!rc) return;

    let concepto = '';
    if (rc.tipo === 'ANTICIPO') concepto = 'Anticipo de Sueldo';
    else if (rc.tipo === 'LIQUIDACION') concepto = 'Liquidación Mensual de Sueldo';
    else concepto = 'Pago de Liquidación de Sueldo';

    const texto = `*SISTEMAS RAÍCES - COMPROBANTE DE PAGO*\n\n` +
      `Estimado(a) *${rc.trabajador_nombre}*,\n` +
      `Se ha registrado su comprobante de pago:\n\n` +
      `• *Nro. Comprobante:* ${rc.numero_comprobante}\n` +
      `• *Concepto:* ${concepto}\n` +
      `• *Período:* ${rc.periodo_descripcion}\n` +
      `• *Importe:* Bs ${Number(rc.importe).toLocaleString('es-BO', { minimumFractionDigits: 2 })}\n` +
      `• *Fecha:* ${rc.fecha}\n` +
      `• *Método de Pago:* ${rc.metodo_pago}\n` +
      (rc.saldo_restante !== undefined ? `• *Saldo Pendiente:* Bs ${Number(rc.saldo_restante).toLocaleString('es-BO', { minimumFractionDigits: 2 })}\n` : '') +
      `\nConserve este mensaje como comprobante oficial de Sistemas Raíces.`;

    const encodedText = encodeURIComponent(texto);
    let url = '';
    if (rc.telefono_contacto && rc.telefono_contacto.trim().length >= 7) {
      const cleanPhone = rc.telefono_contacto.replace(/[^0-9]/g, '');
      const fullPhone = cleanPhone.startsWith('591') ? cleanPhone : `591${cleanPhone}`;
      url = `https://api.whatsapp.com/send?phone=${fullPhone}&text=${encodedText}`;
    } else {
      url = `https://api.whatsapp.com/send?text=${encodedText}`;
    }

    window.open(url, '_blank');
    this.toast.info('Se abrió WhatsApp con el comprobante preparado para compartir.');
  }

  // ==========================================
  // ANULACIONES
  // ==========================================
  abrirModalAnulacion(tipo: 'ANTICIPO' | 'LIQUIDACION', id: number, comprobante: string) {
    this.anulacionTarget.set({ tipo, id, comprobante, motivo: '' });
    this.showAnulacionModal.set(true);
  }

  confirmarAnulacion() {
    const target = this.anulacionTarget();
    if (!target || !target.motivo || target.motivo.trim().length < 3) {
      this.toast.warning('Debes ingresar un motivo de anulación claro (mínimo 3 caracteres).');
      return;
    }

    this.loading.set(true);
    this.showAnulacionModal.set(false);

    if (target.tipo === 'ANTICIPO') {
      this.dataService.anularAnticipo(target.id, target.motivo).subscribe({
        next: (res) => {
          this.toast.success(res.mensaje || 'Anticipo anulado correctamente');
          this.loading.set(false);
          this.cargarIndicadores();
          this.cargarAnticipos();
          if (this.selectedTrabajador()) {
            this.cargarResumenSalarial(this.selectedTrabajador()!.id);
          }
        },
        error: (err) => {
          this.toast.error(err?.error?.detail || 'Error al anular anticipo');
          this.loading.set(false);
        }
      });
    } else {
      this.dataService.anularLiquidacion(target.id, target.motivo).subscribe({
        next: (res) => {
          this.toast.success(res.mensaje || 'Liquidación anulada correctamente');
          this.loading.set(false);
          this.cargarIndicadores();
          this.cargarLiquidaciones();
          if (this.selectedTrabajador()) {
            this.cargarResumenSalarial(this.selectedTrabajador()!.id);
          }
        },
        error: (err) => {
          this.toast.error(err?.error?.detail || 'Error al anular liquidación');
          this.loading.set(false);
        }
      });
    }
  }

  getPeriodoDescripcion(pid?: number | null): string {
    if (!pid) return '';
    return this.periodos().find(p => p.id === pid)?.descripcion || '';
  }

  getNombreTrabajador(tid: number): string {
    const t = this.trabajadores().find(x => x.id === tid);
    return t ? `${t.nombres} ${t.apellidos}` : `Trabajador #${tid}`;
  }

  getAreaTrabajador(tid: number): string {
    const t = this.trabajadores().find(x => x.id === tid);
    return t?.area?.nombre || 'Sin Área';
  }

  getInitials(name?: string): string {
    if (!name || !name.trim()) return 'U';
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return parts[0].substring(0, 2).toUpperCase();
  }

  getUsuarioDisplay(nombre?: string, ci?: string): string {
    if (nombre && nombre.trim()) return nombre.trim();
    if (ci && ci.trim()) return `CI: ${ci.trim()}`;
    return 'Sistema';
  }

  isFechaPostDia18(): boolean {
    const f = this.anticipoFechaEntrega();
    if (f) {
      const parts = f.split('-');
      if (parts.length === 3) {
        const day = parseInt(parts[2], 10);
        if (!isNaN(day)) return day >= 19;
      }
    }
    return new Date().getDate() >= 19;
  }

  getOrdinalAnticipo(index: number): string {
    const ordinals = [
      'Primer',
      'Segundo',
      'Tercer',
      'Cuarto',
      'Quinto',
      'Sexto',
      'Séptimo',
      'Octavo',
      'Noveno',
      'Décimo',
      'Undécimo',
      'Duodécimo'
    ];
    if (index >= 0 && index < ordinals.length) {
      return `${ordinals[index]} Anticipo`;
    }
    return `${index + 1}° Anticipo`;
  }

  getAnticiposDelComprobante(): Anticipo[] {
    const comp = this.currentDetailedReceipt();
    if (!comp) return [];
    if (comp.anticipos_periodo && comp.anticipos_periodo.length > 0) {
      return comp.anticipos_periodo;
    }
    // Fallback si por alguna razón viniera solo con anticipos_historicos
    const lista: Anticipo[] = [...(comp.anticipos_historicos || [])];
    const yaEsta = lista.some(
      a => a.numero_comprobante === comp.numero_comprobante
    );
    if (!yaEsta) {
      lista.push({
        id: 0,
        numero_comprobante: comp.numero_comprobante,
        trabajador_id: comp.trabajador_id,
        periodo_id: comp.periodo_id,
        fecha_solicitud: comp.fecha_anticipo,
        fecha_entrega: comp.fecha_anticipo,
        importe: comp.importe_actual,
        metodo_pago: comp.metodo_entrega,
        estado: 'PAGADO',
        observaciones: comp.motivo
      });
    }
    return lista;
  }
}
