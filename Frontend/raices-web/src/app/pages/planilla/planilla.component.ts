import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DataService } from '../../core/services/data.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import {
  PeriodoSalarial,
  Area,
  PlanillaMensual,
  PlanillaFila,
  PlanillaCierre,
  CerrarPlanillaPayload,
  ActualizarDiasTrabajadosPayload,
  Descuento,
  DescuentoCreatePayload,
  Anticipo,
  AnticipoRider,
  AnticipoRiderCreatePayload,
} from '../../core/models/types';

@Component({
  selector: 'app-planilla',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './planilla.component.html',
  styleUrls: ['./planilla.component.css']
})
export class PlanillaComponent implements OnInit {
  private dataService = inject(DataService);
  public auth = inject(AuthService);
  private toast = inject(ToastService);

  // Estados principales
  loading = signal<boolean>(false);
  periodos = signal<PeriodoSalarial[]>([]);
  selectedPeriodoId = signal<number | null>(null);
  planilla = signal<PlanillaMensual | null>(null);
  areas = signal<Area[]>([]);

  periodoActual = computed(() => {
    const id = this.selectedPeriodoId();
    return this.periodos().find(p => p.id === id) || null;
  });

  getFechaValidaEnPeriodo(diaPreferido?: number): string {
    const per = this.periodoActual();
    if (!per) return new Date().toISOString().substring(0, 10);

    const hoy = new Date().toISOString().substring(0, 10);
    if (hoy >= per.fecha_inicio && hoy <= per.fecha_fin) {
      return hoy;
    }

    if (diaPreferido) {
      const year = per.anio;
      const month = String(per.mes).padStart(2, '0');
      const maxDia = new Date(year, per.mes, 0).getDate();
      const diaClamped = Math.min(diaPreferido, maxDia);
      const diaStr = String(diaClamped).padStart(2, '0');
      const candidate = `${year}-${month}-${diaStr}`;
      if (candidate >= per.fecha_inicio && candidate <= per.fecha_fin) {
        return candidate;
      }
    }

    return per.fecha_inicio;
  }

  getFechaValidaParaLiquidacion(): string {
    const per = this.periodoActual();
    if (!per) return new Date().toISOString().substring(0, 10);

    const maxFecha = per.fecha_limite_pago || per.fecha_fin;
    const hoy = new Date().toISOString().substring(0, 10);
    if (hoy >= per.fecha_inicio && hoy <= maxFecha) {
      return hoy;
    }

    if (per.fecha_pago_estimada && per.fecha_pago_estimada >= per.fecha_inicio && per.fecha_pago_estimada <= maxFecha) {
      return per.fecha_pago_estimada;
    }

    return per.fecha_fin;
  }

  // Filtros
  searchTerm = signal<string>('');
  selectedAreaFilter = signal<number | null>(null);

  // Modales interactivos
  showModalDias = signal<boolean>(false);
  selectedFilaDias = signal<PlanillaFila | null>(null);
  diasForm = {
    dias_trabajados: 30,
    observaciones: ''
  };

  showModalDescuentos = signal<boolean>(false);
  selectedFilaDescuentos = signal<PlanillaFila | null>(null);
  descuentosList = signal<Descuento[]>([]);
  showFormNuevoDescuento = signal<boolean>(false);
  descuentoForm = {
    fecha: new Date().toISOString().substring(0, 10),
    importe: null as number | null,
    concepto: '',
    observaciones: ''
  };

  // Anticipos Rider y Otros Anticipos (spec.md)
  showModalAnticiposRiderFila = signal<boolean>(false);
  selectedFilaAnticiposRider = signal<PlanillaFila | null>(null);
  anticiposRiderFilaList = signal<AnticipoRider[]>([]);
  showFormNuevoAnticipoRiderFila = signal<boolean>(false);
  anticipoRiderFilaForm = {
    importe: null as number | null,
    metodo_pago: 'EFECTIVO',
    fecha_entrega: new Date().toISOString().substring(0, 10),
    observaciones: ''
  };

  showModalAnticiposFila = signal<boolean>(false);
  selectedFilaAnticipos = signal<PlanillaFila | null>(null);
  anticiposFilaList = signal<Anticipo[]>([]);
  showFormNuevoAnticipoFila = signal<boolean>(false);
  anticipoFilaForm = {
    importe: null as number | null,
    metodo_pago: 'EFECTIVO',
    fecha_entrega: new Date().toISOString().substring(0, 10),
    observaciones: '',
    confirmar_excedente: false
  };

  showModalCerrarPlanilla = signal<boolean>(false);
  modoVerCierre = signal<boolean>(false);
  cierreExistente = signal<PlanillaCierre | null>(null);

  cerrarPlanillaForm = {
    observaciones: '',
    confirmar_pendientes: false,
    entregado_quincena: null as number | null,
    solicitud_quincena: 0,
    entregado_sueldo: null as number | null,
    solicitud_sueldo: 0,
    otros_gastos: null as number | null,
    otros_gastos_detalle: ''
  };
  advertenciaCierre = signal<string | null>(null);

  get diferenciaQuincena(): number {
    const ent = Number(this.cerrarPlanillaForm.entregado_quincena) || 0;
    const sol = Number(this.cerrarPlanillaForm.solicitud_quincena) || 0;
    return ent - sol;
  }

  get diferenciaSueldo(): number {
    const ent = Number(this.cerrarPlanillaForm.entregado_sueldo) || 0;
    const sol = Number(this.cerrarPlanillaForm.solicitud_sueldo) || 0;
    return ent - sol;
  }

  get totalDiferencia(): number {
    const otros = Number(this.cerrarPlanillaForm.otros_gastos) || 0;
    return this.diferenciaQuincena + this.diferenciaSueldo + otros;
  }

  // Modal Pago de Quincena (Día 18)
  showModalPagoQuincena = signal<boolean>(false);
  selectedFilaQuincena = signal<PlanillaFila | null>(null);
  pagoQuincenaForm = {
    monto: null as number | null,
    tipo_pago: 'PAGO_QUINCENA',
    metodo_pago: 'EFECTIVO',
    fecha_pago: new Date().toISOString().substring(0, 10),
    observaciones: ''
  };

  // Modal Comprobante Oficial
  showReceiptModal = signal<boolean>(false);
  currentReceipt = signal<any | null>(null);

  // Modal Liquidación de Sueldo Restante (Día 5)
  showModalLiquidarFila = signal<boolean>(false);
  selectedFilaLiquidacion = signal<PlanillaFila | null>(null);
  liquidacionFilaForm = {
    fecha_liquidacion: new Date().toISOString().substring(0, 10),
    ajustes: 0,
    observaciones: 'Liquidación de sueldo restante (Día 5)',
    pago_inmediato: true,
    monto_pago_inmediato: null as number | null,
    metodo_pago_inmediato: 'EFECTIVO'
  };

  // Filas filtradas de la tabla
  filasFiltradas = computed(() => {
    const pl = this.planilla();
    if (!pl) return [];
    const term = this.searchTerm().toLowerCase().trim();
    const areaId = this.selectedAreaFilter();

    return pl.filas.filter(f => {
      const matchSearch =
        term === '' ||
        f.nombre_completo.toLowerCase().includes(term) ||
        (f.ci && f.ci.toLowerCase().includes(term)) ||
        f.cargo.toLowerCase().includes(term);

      const matchArea =
        areaId === null ||
        (f.area && f.area.toLowerCase() === this.areas().find(a => a.id === areaId)?.nombre.toLowerCase());

      return matchSearch && matchArea;
    });
  });

  ngOnInit() {
    this.cargarDatosIniciales();
  }

  cargarDatosIniciales() {
    this.loading.set(true);
    // 1. Cargar períodos
    this.dataService.getPeriodos().subscribe({
      next: (pers) => {
        this.periodos.set(pers);
        if (pers.length > 0 && !this.selectedPeriodoId()) {
          // Seleccionar período actual o el más reciente
          const hoy = new Date();
          const mesActual = hoy.getMonth() + 1;
          const anioActual = hoy.getFullYear();
          const actual = pers.find(p => p.mes === mesActual && p.anio === anioActual) || pers[0];
          this.selectedPeriodoId.set(actual.id);
        }
        this.cargarPlanilla();
      },
      error: () => {
        this.toast.error('Error al cargar períodos salariales');
        this.loading.set(false);
      }
    });

    // 2. Cargar áreas para filtros
    this.dataService.getAreas().subscribe({
      next: (a) => this.areas.set(a),
      error: () => {}
    });
  }

  cargarPlanilla() {
    const pid = this.selectedPeriodoId();
    if (!pid) return;

    this.loading.set(true);
    this.dataService.getPlanillaPeriodo(pid).subscribe({
      next: (pl) => {
        this.planilla.set(pl);
        this.loading.set(false);
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al cargar la planilla salarial');
        this.loading.set(false);
      }
    });
  }

  onPeriodoChange(pid: any) {
    this.selectedPeriodoId.set(Number(pid));
    this.cargarPlanilla();
  }

  // ==========================================
  // MODIFICAR DÍAS TRABAJADOS (RF-16)
  // ==========================================
  abrirModalDias(fila: PlanillaFila) {
    if (this.planilla()?.estado_periodo === 'CERRADO') {
      this.toast.warning('Esta planilla está CERRADA. No se admiten modificaciones de días.');
      return;
    }
    this.selectedFilaDias.set(fila);
    this.diasForm.dias_trabajados = fila.dias_trabajados;
    this.diasForm.observaciones = '';
    this.showModalDias.set(true);
  }

  calcularSimulacionGanado(): number {
    const fila = this.selectedFilaDias();
    if (!fila) return 0;
    const dias = Number(this.diasForm.dias_trabajados || 0);
    if (dias >= 30) return fila.haber_basico;
    if (dias <= 0) return 0;
    return Math.round(((fila.haber_basico / 30) * dias) * 100) / 100;
  }

  guardarDiasTrabajados() {
    const fila = this.selectedFilaDias();
    const pid = this.selectedPeriodoId();
    if (!fila || !pid) return;

    const dias = Number(this.diasForm.dias_trabajados);
    if (dias < 0 || dias > 30) {
      this.toast.warning('Los días trabajados deben estar entre 0 y 30.');
      return;
    }

    this.loading.set(true);
    this.dataService.actualizarDiasTrabajados({
      trabajador_id: fila.trabajador_id,
      periodo_id: pid,
      dias_trabajados: dias,
      observaciones: this.diasForm.observaciones
    }).subscribe({
      next: (filaActualizada) => {
        this.toast.success(`Días trabajados actualizados para ${fila.nombre_completo}`);
        this.showModalDias.set(false);
        this.cargarPlanilla();
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al actualizar días trabajados');
        this.loading.set(false);
      }
    });
  }

  // ==========================================
  // GESTIÓN DE DESCUENTOS (RF-29 A RF-32)
  // ==========================================
  abrirModalDescuentos(fila: PlanillaFila) {
    this.selectedFilaDescuentos.set(fila);
    this.showFormNuevoDescuento.set(false);
    this.descuentoForm = {
      fecha: this.getFechaValidaEnPeriodo(),
      importe: null,
      concepto: '',
      observaciones: ''
    };
    this.cargarDescuentosDeFila(fila.trabajador_id);
    this.showModalDescuentos.set(true);
  }

  cargarDescuentosDeFila(trabajadorId: number) {
    const pid = this.selectedPeriodoId();
    if (!pid) return;

    this.dataService.getDescuentos(pid, trabajadorId).subscribe({
      next: (list) => this.descuentosList.set(list),
      error: () => this.toast.error('Error al cargar descuentos')
    });
  }

  guardarNuevoDescuento() {
    const fila = this.selectedFilaDescuentos();
    const pid = this.selectedPeriodoId();
    if (!fila || !pid) return;

    const monto = Number(this.descuentoForm.importe || 0);
    if (monto <= 0) {
      this.toast.warning('El importe del descuento debe ser mayor a Bs 0.');
      return;
    }
    if (!this.descuentoForm.concepto.trim()) {
      this.toast.warning('Debes ingresar el concepto o motivo del descuento.');
      return;
    }

    this.loading.set(true);
    const payload: DescuentoCreatePayload = {
      trabajador_id: fila.trabajador_id,
      periodo_id: pid,
      fecha: this.descuentoForm.fecha,
      importe: monto,
      concepto: this.descuentoForm.concepto.trim(),
      observaciones: this.descuentoForm.observaciones
    };

    this.dataService.crearDescuento(payload).subscribe({
      next: (desc) => {
        this.toast.success(`Descuento registrado: ${desc.numero_comprobante}`);
        this.showFormNuevoDescuento.set(false);
        this.cargarDescuentosDeFila(fila.trabajador_id);
        this.cargarPlanilla();
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al registrar descuento');
        this.loading.set(false);
      }
    });
  }

  anularDescuento(desc: Descuento) {
    const motivo = prompt(`¿Motivo de anulación para el descuento ${desc.numero_comprobante}?`);
    if (!motivo || !motivo.trim()) return;

    this.loading.set(true);
    this.dataService.anularDescuento(desc.id, motivo.trim()).subscribe({
      next: () => {
        this.toast.success(`Descuento ${desc.numero_comprobante} anulado.`);
        const fila = this.selectedFilaDescuentos();
        if (fila) this.cargarDescuentosDeFila(fila.trabajador_id);
        this.cargarPlanilla();
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al anular descuento');
        this.loading.set(false);
      }
    });
  }

  // ==========================================
  // GESTIÓN DE ANTICIPOS RIDER Y OTROS (spec.md)
  // ==========================================
  abrirModalAnticiposRiderFila(fila: PlanillaFila) {
    this.selectedFilaAnticiposRider.set(fila);
    this.showFormNuevoAnticipoRiderFila.set(false);
    this.anticipoRiderFilaForm = {
      importe: null,
      metodo_pago: 'EFECTIVO',
      fecha_entrega: this.getFechaValidaEnPeriodo(),
      observaciones: ''
    };
    this.cargarAnticiposRiderDeFila(fila.trabajador_id);
    this.showModalAnticiposRiderFila.set(true);
  }

  cargarAnticiposRiderDeFila(trabajadorId: number) {
    const pid = this.selectedPeriodoId();
    if (!pid) return;

    this.dataService.getAnticiposRider(pid, trabajadorId).subscribe({
      next: (list) => {
        this.anticiposRiderFilaList.set(list);
      },
      error: () => this.toast.error('Error al cargar lista de anticipos rider')
    });
  }

  guardarNuevoAnticipoRiderFila() {
    const fila = this.selectedFilaAnticiposRider();
    const pid = this.selectedPeriodoId();
    if (!fila || !pid) return;

    if (fila.estado_liquidacion === 'LIQUIDADO') {
      this.toast.warning('El sueldo de este trabajador ya fue LIQUIDADO. No se pueden registrar más anticipos rider.');
      return;
    }

    const monto = Number(this.anticipoRiderFilaForm.importe || 0);
    if (monto <= 0) {
      this.toast.warning('El importe del anticipo rider debe ser mayor a Bs 0.');
      return;
    }

    this.loading.set(true);
    const payload: AnticipoRiderCreatePayload = {
      trabajador_id: fila.trabajador_id,
      periodo_id: pid,
      importe: monto,
      metodo_pago: this.anticipoRiderFilaForm.metodo_pago,
      fecha_entrega: this.anticipoRiderFilaForm.fecha_entrega,
      observaciones: this.anticipoRiderFilaForm.observaciones
    };

    this.dataService.crearAnticipoRider(payload).subscribe({
      next: (ar: AnticipoRider) => {
        this.toast.success(`Anticipo Rider registrado: ${ar.numero_comprobante}`);
        this.showFormNuevoAnticipoRiderFila.set(false);
        this.cargarAnticiposRiderDeFila(fila.trabajador_id);
        this.cargarPlanilla();
        this.loading.set(false);
      },
      error: (err: any) => {
        const msg = err?.error?.detail || 'Error al registrar anticipo rider';
        this.toast.error(msg);
        this.loading.set(false);
      }
    });
  }

  anularAnticipoRider(ar: AnticipoRider) {
    const motivo = prompt(`¿Estás seguro de anular el anticipo rider ${ar.numero_comprobante} por Bs ${ar.importe}?\nIngresa el motivo de anulación:`);
    if (!motivo || !motivo.trim()) return;

    this.loading.set(true);
    this.dataService.anularAnticipoRider(ar.id, motivo.trim()).subscribe({
      next: () => {
        this.toast.success(`Anticipo rider ${ar.numero_comprobante} anulado.`);
        const fila = this.selectedFilaAnticiposRider();
        if (fila) {
          this.cargarAnticiposRiderDeFila(fila.trabajador_id);
        }
        this.cargarPlanilla();
        this.loading.set(false);
      },
      error: (err: any) => {
        const msg = err?.error?.detail || 'Error al anular anticipo rider';
        this.toast.error(msg);
        this.loading.set(false);
      }
    });
  }

  // ==========================================
  // GESTIÓN DE ANTICIPOS DE LA FILA (RF-22 A RF-28)
  // ==========================================
  abrirModalAnticiposFila(fila: PlanillaFila) {
    this.selectedFilaAnticipos.set(fila);
    this.showFormNuevoAnticipoFila.set(false);
    this.anticipoFilaForm = {
      importe: null,
      metodo_pago: 'EFECTIVO',
      fecha_entrega: this.getFechaValidaEnPeriodo(),
      observaciones: '',
      confirmar_excedente: false
    };
    this.cargarAnticiposDeFila(fila.trabajador_id);
    this.showModalAnticiposFila.set(true);
  }

  cargarAnticiposDeFila(trabajadorId: number) {
    const pid = this.selectedPeriodoId();
    if (!pid) return;

    this.dataService.getAnticipos(pid).subscribe({
      next: (list) => {
        const filtrados = list.filter(a => a.trabajador_id === trabajadorId);
        this.anticiposFilaList.set(filtrados);
      },
      error: () => this.toast.error('Error al cargar lista de anticipos')
    });
  }

  guardarNuevoAnticipoFila() {
    const fila = this.selectedFilaAnticipos();
    const pid = this.selectedPeriodoId();
    if (!fila || !pid) return;

    if (fila.estado_liquidacion === 'LIQUIDADO') {
      this.toast.warning('El sueldo de este trabajador ya fue LIQUIDADO. No se pueden registrar más anticipos.');
      return;
    }

    const monto = Number(this.anticipoFilaForm.importe || 0);
    if (monto <= 0) {
      this.toast.warning('El importe del anticipo debe ser mayor a Bs 0.');
      return;
    }

    this.loading.set(true);
    const payload = {
      trabajador_id: fila.trabajador_id,
      periodo_id: pid,
      importe: monto,
      metodo_pago: this.anticipoFilaForm.metodo_pago,
      fecha_entrega: this.anticipoFilaForm.fecha_entrega,
      observaciones: this.anticipoFilaForm.observaciones,
      es_periodo_siguiente: false,
      confirmar_excedente: this.anticipoFilaForm.confirmar_excedente
    };

    this.dataService.createAnticipo(payload).subscribe({
      next: (ant: Anticipo) => {
        this.toast.success(`Vale de anticipo registrado: ${ant.numero_comprobante}`);
        this.showFormNuevoAnticipoFila.set(false);
        this.cargarAnticiposDeFila(fila.trabajador_id);
        this.cargarPlanilla();
      },
      error: (err: any) => {
        const msg = err?.error?.detail || '';
        if (msg.includes('ADVERTENCIA_EXCEDENTE')) {
          const resp = confirm(`${msg}\n\n¿Deseas confirmar la entrega del anticipo a pesar de superar el saldo disponible?`);
          if (resp) {
            this.anticipoFilaForm.confirmar_excedente = true;
            this.guardarNuevoAnticipoFila();
            return;
          }
        } else {
          this.toast.error(msg || 'Error al registrar anticipo');
        }
        this.loading.set(false);
      }
    });
  }

  // ==========================================
  // CIERRE FORMAL DE PLANILLA (spec.md)
  // ==========================================
  abrirModalCierre(verModo: boolean = false) {
    const pl = this.planilla();
    if (!pl) return;

    if (pl.estado_periodo === 'CERRADO' || verModo) {
      this.modoVerCierre.set(true);
      this.advertenciaCierre.set(null);
      if (pl.cierre) {
        this.cierreExistente.set(pl.cierre);
        this.cerrarPlanillaForm = {
          observaciones: pl.cierre.observaciones || '',
          confirmar_pendientes: false,
          entregado_quincena: Number(pl.cierre.entregado_quincena || 0),
          solicitud_quincena: Number(pl.cierre.solicitud_quincena || 0),
          entregado_sueldo: Number(pl.cierre.entregado_sueldo || 0),
          solicitud_sueldo: Number(pl.cierre.solicitud_sueldo || 0),
          otros_gastos: Number(pl.cierre.otros_gastos || 0),
          otros_gastos_detalle: pl.cierre.otros_gastos_detalle || ''
        };
        this.showModalCerrarPlanilla.set(true);
      } else {
        this.loading.set(true);
        this.dataService.getCierrePlanilla(pl.periodo_id).subscribe({
          next: (cierre) => {
            this.loading.set(false);
            if (cierre) {
              this.cierreExistente.set(cierre);
              this.cerrarPlanillaForm = {
                observaciones: cierre.observaciones || '',
                confirmar_pendientes: false,
                entregado_quincena: Number(cierre.entregado_quincena || 0),
                solicitud_quincena: Number(cierre.solicitud_quincena || 0),
                entregado_sueldo: Number(cierre.entregado_sueldo || 0),
                solicitud_sueldo: Number(cierre.solicitud_sueldo || 0),
                otros_gastos: Number(cierre.otros_gastos || 0),
                otros_gastos_detalle: cierre.otros_gastos_detalle || ''
              };
            }
            this.showModalCerrarPlanilla.set(true);
          },
          error: () => {
            this.loading.set(false);
            this.showModalCerrarPlanilla.set(true);
          }
        });
      }
      return;
    }

    // Período ABIERTO: Formulario activo de cierre
    this.modoVerCierre.set(false);
    this.cierreExistente.set(null);
    this.advertenciaCierre.set(null);

    const solQuincena = Number(pl.totales?.solicitud_quincena || 0);
    const solSueldo = Number(pl.totales?.solicitud_sueldo || 0);
    const anticiposSig = Number(pl.totales?.total_anticipos_periodo_siguiente || 0);

    this.cerrarPlanillaForm = {
      observaciones: 'Cierre mensual consolidado de haberes y liquidaciones',
      confirmar_pendientes: false,
      entregado_quincena: null,
      solicitud_quincena: solQuincena,
      entregado_sueldo: null,
      solicitud_sueldo: solSueldo,
      otros_gastos: anticiposSig > 0 ? -Math.abs(anticiposSig) : null,
      otros_gastos_detalle: anticiposSig > 0 ? 'Anticipos para el siguiente mes (Excedentes de sueldo)' : ''
    };
    this.showModalCerrarPlanilla.set(true);
  }

  confirmarCierrePlanilla() {
    const pid = this.selectedPeriodoId();
    if (!pid) return;

    if (this.cerrarPlanillaForm.entregado_quincena === null || this.cerrarPlanillaForm.entregado_quincena === undefined) {
      this.toast.warning('Por favor ingresa el monto entregado para la Quincena.');
      return;
    }
    if (this.cerrarPlanillaForm.entregado_sueldo === null || this.cerrarPlanillaForm.entregado_sueldo === undefined) {
      this.toast.warning('Por favor ingresa el monto entregado para el Sueldo.');
      return;
    }

    const payload: CerrarPlanillaPayload = {
      observaciones: this.cerrarPlanillaForm.observaciones,
      confirmar_pendientes: this.cerrarPlanillaForm.confirmar_pendientes,
      entregado_quincena: Number(this.cerrarPlanillaForm.entregado_quincena) || 0,
      solicitud_quincena: Number(this.cerrarPlanillaForm.solicitud_quincena) || 0,
      entregado_sueldo: Number(this.cerrarPlanillaForm.entregado_sueldo) || 0,
      solicitud_sueldo: Number(this.cerrarPlanillaForm.solicitud_sueldo) || 0,
      otros_gastos: Number(this.cerrarPlanillaForm.otros_gastos) || 0,
      otros_gastos_detalle: this.cerrarPlanillaForm.otros_gastos_detalle || ''
    };

    this.loading.set(true);
    this.dataService.cerrarPlanilla(pid, payload).subscribe({
      next: (res) => {
        if (res.requiere_confirmacion) {
          this.advertenciaCierre.set(res.mensaje);
          this.cerrarPlanillaForm.confirmar_pendientes = true;
          this.loading.set(false);
          return;
        }

        this.toast.success(res.mensaje || 'Planilla cerrada exitosamente.');
        this.showModalCerrarPlanilla.set(false);
        this.cargarPlanilla();
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al cerrar planilla');
        this.loading.set(false);
      }
    });
  }

  // ==========================================
  // GESTIÓN DE PAGO DE QUINCENA (DÍA 18)
  // ==========================================
  abrirModalPagoQuincenaFila(fila: PlanillaFila) {
    this.selectedFilaQuincena.set(fila);
    this.pagoQuincenaForm.monto = Number(fila.quincena_sugerida || 0);
    this.pagoQuincenaForm.tipo_pago = fila.supera_quincena ? 'REVISION_QUINCENA' : 'PAGO_QUINCENA';
    this.pagoQuincenaForm.fecha_pago = this.getFechaValidaEnPeriodo(18);
    this.pagoQuincenaForm.metodo_pago = 'EFECTIVO';
    this.pagoQuincenaForm.observaciones = fila.supera_quincena
      ? 'Quincena cubierta en su totalidad por anticipos acumulados'
      : 'Pago de primera quincena (Día 18)';
    this.showModalPagoQuincena.set(true);
  }

  confirmarPagoQuincenaFila() {
    const fila = this.selectedFilaQuincena();
    const pid = this.selectedPeriodoId();
    if (!fila || !pid) return;

    const monto = Number(this.pagoQuincenaForm.monto ?? 0);
    if (monto < 0) {
      this.toast.warning('El monto a pagar no puede ser negativo.');
      return;
    }

    this.loading.set(true);
    this.showModalPagoQuincena.set(false);

    const payload = {
      trabajador_id: fila.trabajador_id,
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
        this.cargarPlanilla();

        const periodoDesc = this.periodos().find(p => p.id === pid)?.descripcion || '';
        this.abrirComprobantePago({
          tipo: 'PAGO_LIQUIDACION',
          numero_comprobante: pago.numero_comprobante,
          trabajador_nombre: fila.nombre_completo,
          trabajador_ci: fila.ci || '',
          trabajador_cargo: fila.cargo,
          trabajador_area: fila.area,
          periodo_descripcion: periodoDesc,
          fecha: pago.fecha_pago,
          importe: pago.monto,
          metodo_pago: pago.metodo_pago,
          sueldo_base: fila.haber_basico,
          anticipos_descontados: fila.pago_anticipos,
          saldo_restante: Math.max(0, (fila.saldo_pendiente_real || fila.liquido_pagable) - pago.monto),
          observaciones: `${pago.tipo_pago}: ${pago.observaciones || ''}`,
          usuario_nombre: pago.usuario_nombre || this.auth.currentUser()?.nombre || 'Administrador',
          usuario_id: pago.usuario_id || this.auth.currentUser()?.ci || '',
        });
      },
      error: (err: any) => {
        this.toast.error(err?.error?.detail || 'Error al registrar el pago de quincena');
        this.loading.set(false);
      }
    });
  }

  // ==========================================
  // GESTIÓN DE LIQUIDACIÓN DE SUELDO (DÍA 5)
  // ==========================================
  calcularSaldoLiquidacionFila(): number {
    const fila = this.selectedFilaLiquidacion();
    if (!fila) return 0;
    const saldoBase = fila.saldo_pendiente_real > 0 ? fila.saldo_pendiente_real : Math.max(0, fila.liquido_pagable);
    const ajustes = Number(this.liquidacionFilaForm.ajustes || 0);
    return Math.max(0, saldoBase + ajustes);
  }

  abrirModalLiquidarFila(fila: PlanillaFila) {
    if (fila.estado_liquidacion === 'LIQUIDADO') {
      this.toast.info(`El trabajador ${fila.nombre_completo} ya tiene su sueldo liquidado en este período.`);
      if (fila.liquidacion_comprobante) {
        const pid = this.selectedPeriodoId();
        const periodoDesc = this.periodos().find(p => p.id === pid)?.descripcion || '';

        // El importe de la liquidación final debe reflejar el monto de la liquidación (sin mezclar la quincena)
        const montoLiquidado = (fila.pago_liquidacion !== undefined && fila.pago_liquidacion !== null && Number(fila.pago_liquidacion) > 0)
          ? Number(fila.pago_liquidacion)
          : (Number(fila.monto_pagado_total || 0) > Number(fila.pago_quincena || 0)
              ? Number(fila.monto_pagado_total) - Number(fila.pago_quincena || 0)
              : Math.max(0, Number(fila.liquido_pagable || 0)));

        const excedente = Number(fila.anticipos_periodo_siguiente || 0);
        const sueldoLiquidoPeriodo = Math.max(0, montoLiquidado - excedente);

        this.abrirComprobantePago({
          tipo: 'LIQUIDACION',
          numero_comprobante: fila.liquidacion_comprobante,
          trabajador_nombre: fila.nombre_completo,
          trabajador_ci: fila.ci || '',
          trabajador_cargo: fila.cargo,
          trabajador_area: fila.area,
          periodo_descripcion: periodoDesc,
          fecha: fila.fecha_liquidacion || new Date().toISOString().substring(0, 10),
          importe: montoLiquidado > 0 ? montoLiquidado : (Number(fila.liquido_pagable) || Number(fila.total_ganado)),
          sueldo_liquido_periodo: sueldoLiquidoPeriodo,
          excedente_siguiente_mes: excedente,
          metodo_pago: fila.liquidacion_metodo_pago || 'EFECTIVO',
          sueldo_base: fila.total_ganado || fila.haber_basico,
          anticipos_descontados: fila.pago_anticipos,
          anticipos_rider_descontados: fila.pago_anticipos_rider || 0,
          descuentos_salariales: fila.total_descuentos,
          quincena_descontada: fila.pago_quincena,
          ajustes: fila.liquidacion_ajustes || 0,
          saldo_restante: 0,
          observaciones: fila.liquidacion_observaciones || 'Liquidación salarial completada',
          usuario_nombre: this.auth.currentUser()?.nombre || 'Administrador',
          usuario_id: fila.liquidacion_usuario_id || this.auth.currentUser()?.ci || '',
        });
      }
      return;
    }

    this.selectedFilaLiquidacion.set(fila);
    const saldoCalculado = fila.saldo_pendiente_real > 0 ? fila.saldo_pendiente_real : Math.max(0, fila.liquido_pagable);
    this.liquidacionFilaForm = {
      fecha_liquidacion: this.getFechaValidaParaLiquidacion(),
      ajustes: 0,
      observaciones: 'Liquidación de sueldo restante (Día 5)',
      pago_inmediato: true,
      monto_pago_inmediato: saldoCalculado,
      metodo_pago_inmediato: 'EFECTIVO'
    };
    this.showModalLiquidarFila.set(true);
  }

  confirmarLiquidacionFila() {
    const fila = this.selectedFilaLiquidacion();
    const pid = this.selectedPeriodoId();
    if (!fila || !pid) return;

    const saldoCalculado = this.calcularSaldoLiquidacionFila();
    if (this.liquidacionFilaForm.pago_inmediato) {
      const monto = Number(this.liquidacionFilaForm.monto_pago_inmediato ?? 0);
      if (monto < 0) {
        this.toast.warning('El monto a pagar no puede ser negativo.');
        return;
      }
    }

    this.loading.set(true);
    this.showModalLiquidarFila.set(false);

    const payload = {
      trabajador_id: fila.trabajador_id,
      periodo_id: pid,
      fecha_liquidacion: this.liquidacionFilaForm.fecha_liquidacion,
      ajustes: Number(this.liquidacionFilaForm.ajustes || 0),
      observaciones: this.liquidacionFilaForm.observaciones,
      pago_inmediato: this.liquidacionFilaForm.pago_inmediato,
      monto_pago_inmediato: this.liquidacionFilaForm.pago_inmediato ? this.liquidacionFilaForm.monto_pago_inmediato : null,
      metodo_pago_inmediato: this.liquidacionFilaForm.metodo_pago_inmediato
    };

    this.dataService.createLiquidacion(payload).subscribe({
      next: (liq) => {
        this.toast.success(`Liquidación registrada: ${liq.numero_comprobante}`);
        this.loading.set(false);
        this.cargarPlanilla();

        const periodoDesc = this.periodos().find(p => p.id === pid)?.descripcion || '';
        const montoEntregado = (liq.pago_inmediato_monto !== undefined && liq.pago_inmediato_monto !== null)
          ? Number(liq.pago_inmediato_monto)
          : (this.liquidacionFilaForm.pago_inmediato ? Number(this.liquidacionFilaForm.monto_pago_inmediato || 0) : 0);

        const excedente = (liq.excedente_siguiente_mes !== undefined && liq.excedente_siguiente_mes !== null)
          ? Number(liq.excedente_siguiente_mes)
          : Math.max(0, montoEntregado - saldoCalculado);

        this.abrirComprobantePago({
          tipo: 'LIQUIDACION',
          numero_comprobante: liq.numero_comprobante,
          trabajador_nombre: fila.nombre_completo,
          trabajador_ci: fila.ci || '',
          trabajador_cargo: fila.cargo,
          trabajador_area: fila.area,
          periodo_descripcion: periodoDesc,
          fecha: liq.fecha_liquidacion,
          importe: montoEntregado,
          sueldo_liquido_periodo: saldoCalculado,
          excedente_siguiente_mes: excedente,
          metodo_pago: this.liquidacionFilaForm.pago_inmediato ? this.liquidacionFilaForm.metodo_pago_inmediato : 'POR PAGAR',
          sueldo_base: liq.sueldo_base || fila.haber_basico,
          anticipos_descontados: fila.pago_anticipos,
          anticipos_rider_descontados: fila.pago_anticipos_rider || 0,
          descuentos_salariales: fila.total_descuentos,
          quincena_descontada: liq.pago_quincena_previo ?? fila.pago_quincena,
          ajustes: liq.ajustes,
          saldo_restante: liq.saldo_pendiente,
          observaciones: liq.observaciones || 'Liquidación Salarial Final (Día 5)',
          usuario_nombre: liq.usuario_nombre || this.auth.currentUser()?.nombre || 'Administrador',
          usuario_id: liq.usuario_id || this.auth.currentUser()?.ci || '',
        });
      },
      error: (err: any) => {
        this.toast.error(err?.error?.detail || 'Error al registrar liquidación');
        this.loading.set(false);
      }
    });
  }

  // ==========================================
  // COMPROBANTE OFICIAL Y WHATSAPP
  // ==========================================
  abrirComprobantePago(data: any) {
    this.currentReceipt.set(data);
    this.showReceiptModal.set(true);
  }

  imprimirComprobante() {
    window.print();
  }

  compartirWhatsApp() {
    const rc = this.currentReceipt();
    if (!rc) return;

    let mensaje = `*COMPROBANTE OFICIAL - SISTEMAS RAÍCES*\n`;
    mensaje += `*${rc.tipo}*: ${rc.numero_comprobante}\n`;
    mensaje += `*Fecha*: ${rc.fecha}\n`;
    mensaje += `*Trabajador*: ${rc.trabajador_nombre}\n`;
    if (rc.trabajador_ci) mensaje += `*CI*: ${rc.trabajador_ci}\n`;
    mensaje += `*Cargo*: ${rc.trabajador_cargo} (${rc.trabajador_area})\n`;
    mensaje += `*Período Salarial*: ${rc.periodo_descripcion}\n`;
    mensaje += `*Importe*: Bs ${Number(rc.importe).toFixed(2)}\n`;
    if (rc.excedente_siguiente_mes && Number(rc.excedente_siguiente_mes) > 0) {
      mensaje += `  - Sueldo Líquido del Período: Bs ${Number(rc.sueldo_liquido_periodo || 0).toFixed(2)}\n`;
      mensaje += `  - Anticipo para Siguiente Mes: +Bs ${Number(rc.excedente_siguiente_mes).toFixed(2)}\n`;
    }
    mensaje += `*Método*: ${rc.metodo_pago}\n`;
    if (rc.observaciones) mensaje += `*Observaciones*: ${rc.observaciones}\n`;
    mensaje += `\n_Emitido oficialmente a través del Sistema Empresarial Raíces._`;

    const encoded = encodeURIComponent(mensaje);
    window.open(`https://wa.me/?text=${encoded}`, '_blank');
  }

  getUsuarioDisplay(nombre?: string, id?: string): string {
    if (nombre && nombre.trim()) return nombre.trim();
    if (id && id.trim()) return `CI: ${id}`;
    return 'Administrador';
  }

  // ==========================================
  // IMPRESIÓN Y PDF INSTITUCIONAL (RF-71)
  // ==========================================
  imprimirPlanilla() {
    window.print();
  }
}
