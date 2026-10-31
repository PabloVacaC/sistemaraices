import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { DataService } from '../../core/services/data.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import {
  PlanillaResumen,
  PlanillaItem,
  PeriodoPlanillaListItem,
  Area,
} from '../../core/models/types';

@Component({
  selector: 'app-planilla',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './planilla.component.html',
  styleUrls: ['./planilla.component.css'],
})
export class PlanillaComponent implements OnInit {
  private dataService = inject(DataService);
  public auth = inject(AuthService);
  private toast = inject(ToastService);
  private router = inject(Router);

  // Estados reactivos (Signals)
  loading = signal<boolean>(false);
  resumenPlanilla = signal<PlanillaResumen | null>(null);
  periodos = signal<PeriodoPlanillaListItem[]>([]);
  selectedPeriodoId = signal<number | null>(null);
  areas = signal<Area[]>([]);

  // Filtros de tabla
  searchTerm = signal<string>('');
  selectedAreaFilter = signal<number | null>(null);
  statusFilter = signal<string>('TODOS'); // TODOS, LIQUIDADO, PARCIAL, PENDIENTE

  // Modales
  showModalCierre = signal<boolean>(false);
  showModalReapertura = signal<boolean>(false);
  showModalDetalleTrabajador = signal<boolean>(false);
  selectedItemDetalle = signal<PlanillaItem | null>(null);

  // Formularios de modales
  confirmarPendientes = signal<boolean>(false);
  observacionesCierre = signal<string>('');
  motivoReapertura = signal<string>('');

  // Ítems filtrados
  filteredItems = computed(() => {
    const resumen = this.resumenPlanilla();
    if (!resumen) return [];
    let items = resumen.items;

    // Filtro por término de búsqueda (CI, Nombre, Cargo)
    const term = this.searchTerm().toLowerCase().trim();
    if (term) {
      items = items.filter(
        (it) =>
          it.nombre_completo.toLowerCase().includes(term) ||
          (it.ci && it.ci.toLowerCase().includes(term)) ||
          it.cargo.toLowerCase().includes(term) ||
          it.area.toLowerCase().includes(term)
      );
    }

    // Filtro por Área
    const areaId = this.selectedAreaFilter();
    if (areaId) {
      const areaObj = this.areas().find((a) => a.id === areaId);
      if (areaObj) {
        items = items.filter((it) => it.area.toLowerCase() === areaObj.nombre.toLowerCase());
      }
    }

    // Filtro por Estado
    const st = this.statusFilter();
    if (st !== 'TODOS') {
      if (st === 'LIQUIDADO') {
        items = items.filter((it) => it.estado_pago === 'LIQUIDADO' || it.saldo_pendiente <= 0);
      } else if (st === 'PARCIAL') {
        items = items.filter((it) => it.estado_pago === 'PARCIAL' || (it.total_pagado > 0 && it.saldo_pendiente > 0));
      } else if (st === 'PENDIENTE') {
        items = items.filter((it) => it.estado_pago === 'PENDIENTE' || it.estado_pago === 'ANTICIPOS_PENDIENTES' || it.estado_pago === 'SIN_MOVIMIENTOS');
      }
    }

    return items;
  });

  // Trabajadores con saldo pendiente para advertencia de cierre
  trabajadoresPendientes = computed(() => {
    const resumen = this.resumenPlanilla();
    if (!resumen) return [];
    return resumen.items.filter((it) => it.saldo_pendiente > 0);
  });

  ngOnInit() {
    this.cargarDatosIniciales();
  }

  cargarDatosIniciales() {
    this.loading.set(true);

    // 1. Cargar áreas
    this.dataService.getAreas().subscribe({
      next: (a) => this.areas.set(a),
      error: () => {},
    });

    // 2. Cargar períodos y planilla actual
    this.dataService.getPeriodosPlanilla().subscribe({
      next: (pers) => {
        this.periodos.set(pers);
        // Cargar planilla del período actual
        this.dataService.getPlanillaPeriodoActual().subscribe({
          next: (res) => {
            this.resumenPlanilla.set(res);
            this.selectedPeriodoId.set(res.periodo.id);
            this.loading.set(false);
          },
          error: (err) => {
            this.loading.set(false);
            this.toast.error(err?.error?.detail || 'Error al cargar planilla actual');
          },
        });
      },
      error: () => {
        this.loading.set(false);
        this.toast.error('Error al cargar lista de períodos');
      },
    });
  }

  onPeriodoChange(event: any) {
    const pid = Number(event);
    if (!pid) return;
    this.selectedPeriodoId.set(pid);
    this.cargarPlanilla(pid);
  }

  cargarPlanilla(periodoId: number) {
    this.loading.set(true);
    this.dataService.getPlanillaPorPeriodo(periodoId).subscribe({
      next: (res) => {
        this.resumenPlanilla.set(res);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.toast.error(err?.error?.detail || 'Error al cargar la planilla seleccionada');
      },
    });
  }

  // --- CIERRE FORMAL DE PLANILLA ---
  abrirModalCierre() {
    this.confirmarPendientes.set(false);
    this.observacionesCierre.set('');
    this.showModalCierre.set(true);
  }

  confirmarCierre() {
    const pid = this.selectedPeriodoId();
    if (!pid) return;

    const resumen = this.resumenPlanilla();
    if (resumen && resumen.total_saldo_pendiente > 0 && !this.confirmarPendientes()) {
      this.toast.warning('Debe marcar la casilla de confirmación para cerrar con pagos pendientes.');
      return;
    }

    this.loading.set(true);
    this.showModalCierre.set(false);

    this.dataService
      .cerrarPlanilla(pid, {
        confirmar_con_pendientes: this.confirmarPendientes(),
        observaciones: this.observacionesCierre() || 'Cierre formal de planilla mensual',
      })
      .subscribe({
        next: (resActualizada) => {
          this.resumenPlanilla.set(resActualizada);
          this.toast.success(`Planilla ${resActualizada.periodo.descripcion} cerrada exitosamente.`);
          this.loading.set(false);
          // Recargar lista de períodos para reflejar el estado cerrado
          this.dataService.getPeriodosPlanilla().subscribe({
            next: (pers) => this.periodos.set(pers),
          });
        },
        error: (err) => {
          this.loading.set(false);
          this.toast.error(err?.error?.detail || 'Error al cerrar la planilla');
        },
      });
  }

  // --- REAPERTURA ADMINISTRATIVA DE PLANILLA ---
  abrirModalReapertura() {
    this.motivoReapertura.set('');
    this.showModalReapertura.set(true);
  }

  confirmarReapertura() {
    const pid = this.selectedPeriodoId();
    const motivo = this.motivoReapertura().trim();
    if (!pid) return;
    if (motivo.length < 5) {
      this.toast.warning('Debe ingresar un motivo justificado (mínimo 5 caracteres).');
      return;
    }

    this.loading.set(true);
    this.showModalReapertura.set(false);

    this.dataService
      .reabrirPlanilla(pid, {
        motivo: motivo,
      })
      .subscribe({
        next: (resActualizada) => {
          this.resumenPlanilla.set(resActualizada);
          this.toast.success(`Planilla ${resActualizada.periodo.descripcion} reabierta exitosamente.`);
          this.loading.set(false);
          // Recargar lista de períodos
          this.dataService.getPeriodosPlanilla().subscribe({
            next: (pers) => this.periodos.set(pers),
          });
        },
        error: (err) => {
          this.loading.set(false);
          this.toast.error(err?.error?.detail || 'Error al reabrir la planilla');
        },
      });
  }

  // --- DETALLE / FICHA DE TRABAJADOR ---
  verDetalleTrabajador(item: PlanillaItem) {
    this.selectedItemDetalle.set(item);
    this.showModalDetalleTrabajador.set(true);
  }

  irAPagosTrabajador(item: PlanillaItem) {
    // Redirigir al módulo de pagos con el período
    this.router.navigate(['/dashboard/pagos']);
  }

  // --- ACTUALIZACIÓN INTERACTIVA DE DÍAS TRABAJADOS (RF-Problema 1) ---
  actualizarDias(item: PlanillaItem, event: any) {
    const nuevosDias = parseInt(event?.target?.value ?? event, 10);
    if (isNaN(nuevosDias) || nuevosDias < 1 || nuevosDias > 30) {
      this.toast.warning('Los días trabajados deben estar entre 1 y 30 días.');
      return;
    }
    const pid = this.selectedPeriodoId();
    if (!pid) return;

    this.dataService.actualizarDiasTrabajados(pid, item.trabajador_id, nuevosDias).subscribe({
      next: (itemActualizado) => {
        const current = this.resumenPlanilla();
        if (current) {
          const idx = current.items.findIndex((i) => i.trabajador_id === item.trabajador_id);
          if (idx !== -1) {
            current.items[idx] = itemActualizado;
            this.recalcularTotalesPlanilla(current);
            this.resumenPlanilla.set({ ...current });
          }
        }
        this.toast.success(
          `Días de ${item.nombre_completo} actualizados a ${nuevosDias} (Total Ganado: Bs ${itemActualizado.total_ganado.toFixed(2)})`
        );
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al actualizar días trabajados');
      },
    });
  }

  private recalcularTotalesPlanilla(resumen: PlanillaResumen) {
    let totBase = 0;
    let totGanado = 0;
    let totAnt18 = 0;
    let totAntPost18 = 0;
    let totAnt = 0;
    let totAntSig = 0;
    let totQ = 0;
    let totAj = 0;
    let totBruto = 0;
    let totLiq = 0;
    let totPag = 0;
    let totSaldo = 0;

    for (const it of resumen.items) {
      totBase += it.sueldo_base;
      totGanado += it.total_ganado;
      totAnt18 += it.anticipos_antes_18;
      totAntPost18 += it.anticipos_post_18;
      totAnt += it.total_anticipos;
      totAntSig += (it.anticipos_siguiente_periodo || 0);
      totQ += it.pago_quincena;
      totAj += it.ajustes;
      totBruto += it.total_ganado_bruto;
      totLiq += it.liquido_pagable;
      totPag += it.total_pagado;
      totSaldo += it.saldo_pendiente;
    }

    resumen.total_sueldo_base = totBase;
    resumen.total_ganado = totGanado;
    resumen.total_anticipos_antes_18 = totAnt18;
    resumen.total_anticipos_post_18 = totAntPost18;
    resumen.total_anticipos = totAnt;
    resumen.total_anticipos_siguiente_periodo = totAntSig;
    resumen.total_pagos_quincena = totQ;
    resumen.total_ajustes = totAj;
    resumen.total_ganado_bruto = totBruto;
    resumen.total_liquido_pagable = totLiq;
    resumen.total_pagado = totPag;
    resumen.total_saldo_pendiente = totSaldo;
  }

  // --- EXPORTACIÓN E IMPRESIÓN ---
  imprimirPlanilla() {
    window.print();
  }

  exportarCSV() {
    const resumen = this.resumenPlanilla();
    if (!resumen || !resumen.items.length) {
      this.toast.warning('No hay datos para exportar.');
      return;
    }

    const headers = [
      'N°',
      'Trabajador',
      'Carné Identidad',
      'Área',
      'Cargo',
      'Haber Básico (Bs)',
      'Días Trabajados',
      'Total Ganado Proporcional (Bs)',
      'Anticipos <= Día 18 (Bs)',
      'Pago Quincena (Bs)',
      'Anticipos > Día 18 (Bs)',
      'Total Anticipos Mes (Bs)',
      'Anticipos Sig. Período Día 1-5 (Bs)',
      'Ajustes/Bonos (Bs)',
      'Líquido Pagable (Bs)',
      'Total Pagado (Bs)',
      'Saldo Pendiente (Bs)',
      'Estado',
    ];

    const rows = resumen.items.map((it, idx) => [
      idx + 1,
      `"${it.nombre_completo}"`,
      `"${it.ci || ''}"`,
      `"${it.area}"`,
      `"${it.cargo}"`,
      it.sueldo_base.toFixed(2),
      it.dias_trabajados,
      it.total_ganado.toFixed(2),
      it.anticipos_antes_18.toFixed(2),
      it.pago_quincena.toFixed(2),
      it.anticipos_post_18.toFixed(2),
      it.total_anticipos.toFixed(2),
      (it.anticipos_siguiente_periodo || 0).toFixed(2),
      it.ajustes.toFixed(2),
      it.liquido_pagable.toFixed(2),
      it.total_pagado.toFixed(2),
      it.saldo_pendiente.toFixed(2),
      `"${it.estado_pago}"`,
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,\uFEFF' +
      headers.join(',') +
      '\n' +
      rows.map((r) => r.join(',')).join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute(
      'download',
      `Planilla_Salarial_${resumen.periodo.descripcion.replace(/\s+/g, '_')}.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    this.toast.success('Archivo CSV descargado correctamente.');
  }
}

