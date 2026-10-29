import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DataService } from '../../core/services/data.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import {
  Area,
  ContabilidadReporteMensual,
  ContabilidadReporteAnual,
  MovimientoContable,
  DesglosePorArea,
  MesComparativoAnual,
} from '../../core/models/types';

@Component({
  selector: 'app-contabilidad',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './contabilidad.component.html',
  styleUrls: ['./contabilidad.component.css']
})
export class ContabilidadComponent implements OnInit {
  private dataService = inject(DataService);
  public auth = inject(AuthService);
  private toast = inject(ToastService);

  // Estados principales
  loading = signal<boolean>(false);
  activeTab = signal<'mensual' | 'anual' | 'libro_diario'>('mensual');

  // Filtros de tiempo y centros de costos
  mesesList = [
    { num: 1, nombre: 'Enero' },
    { num: 2, nombre: 'Febrero' },
    { num: 3, nombre: 'Marzo' },
    { num: 4, nombre: 'Abril' },
    { num: 5, nombre: 'Mayo' },
    { num: 6, nombre: 'Junio' },
    { num: 7, nombre: 'Julio' },
    { num: 8, nombre: 'Agosto' },
    { num: 9, nombre: 'Septiembre' },
    { num: 10, nombre: 'Octubre' },
    { num: 11, nombre: 'Noviembre' },
    { num: 12, nombre: 'Diciembre' },
  ];

  aniosDisponibles = signal<number[]>([new Date().getFullYear()]);
  selectedMes = signal<number>(new Date().getMonth() + 1);
  selectedAnio = signal<number>(new Date().getFullYear());
  selectedAreaId = signal<number | null>(null);

  // Áreas / Centros de costo
  areas = signal<Area[]>([]);

  // Datos del reporte
  reporteMensual = signal<ContabilidadReporteMensual | null>(null);
  reporteAnual = signal<ContabilidadReporteAnual | null>(null);

  // Filtros en el Libro Diario
  searchJournal = signal<string>('');
  categoriaFilter = signal<string>('TODAS');
  metodoPagoFilter = signal<string>('TODOS');

  // Movimientos filtrados para el Libro Diario
  movimientosFiltrados = computed(() => {
    const rep = this.reporteMensual();
    if (!rep || !rep.movimientos) return [];

    let list = rep.movimientos;
    const cat = this.categoriaFilter();
    if (cat !== 'TODAS') {
      list = list.filter(m => m.tipo_categoria === cat);
    }

    const mp = this.metodoPagoFilter();
    if (mp !== 'TODOS') {
      list = list.filter(m => (m.metodo_pago || '').toUpperCase() === mp.toUpperCase());
    }

    const q = this.searchJournal().trim().toLowerCase();
    if (q) {
      list = list.filter(m =>
        (m.numero_comprobante || '').toLowerCase().includes(q) ||
        (m.beneficiario_proveedor || '').toLowerCase().includes(q) ||
        (m.concepto || '').toLowerCase().includes(q) ||
        (m.area_nombre || '').toLowerCase().includes(q) ||
        (m.tipo_label || '').toLowerCase().includes(q)
      );
    }

    return list;
  });

  // Total acumulado de la lista filtrada del Libro Diario
  totalMovimientosFiltrados = computed(() => {
    return this.movimientosFiltrados().reduce((acc, m) => acc + Number(m.monto || 0), 0);
  });

  // Métodos de pago memoizados para evitar recalcular en ciclos de detección de cambios
  metodosPagoArray = computed(() => {
    const rep = this.reporteMensual();
    if (!rep || !rep.metodos_pago_resumen) return [];
    return Object.entries(rep.metodos_pago_resumen).map(([metodo, total]) => ({
      metodo,
      total: Number(total)
    }));
  });

  ngOnInit(): void {
    this.cargarAreas();
    this.cargarAniosDisponibles();
    this.cargarReporte();
  }

  cargarAreas(): void {
    this.dataService.getAreas().subscribe({
      next: (data) => this.areas.set(data),
      error: () => this.toast.error('Error al cargar áreas de la empresa')
    });
  }

  cargarAniosDisponibles(): void {
    this.dataService.getContabilidadAnios().subscribe({
      next: (anios) => {
        if (anios && anios.length > 0) {
          this.aniosDisponibles.set(anios);
          if (!anios.includes(this.selectedAnio())) {
            this.selectedAnio.set(anios[0]);
          }
        }
      },
      error: () => {}
    });
  }

  onMesChange(mes: number): void {
    this.selectedMes.set(Number(mes));
    this.reporteMensual.set(null);
    this.cargarReporte();
  }

  onAnioChange(anio: number): void {
    this.selectedAnio.set(Number(anio));
    this.reporteMensual.set(null);
    this.reporteAnual.set(null);
    this.cargarReporte();
  }

  onAreaChange(areaId: any): void {
    this.selectedAreaId.set(areaId ? Number(areaId) : null);
    this.reporteMensual.set(null);
    this.reporteAnual.set(null);
    this.cargarReporte();
  }

  cargarReporte(): void {
    const tab = this.activeTab();
    if (tab === 'mensual' || tab === 'libro_diario') {
      this.cargarReporteMensual();
    } else if (tab === 'anual') {
      this.cargarReporteAnual();
    }
  }

  cambiarTab(tab: 'mensual' | 'anual' | 'libro_diario'): void {
    this.activeTab.set(tab);
    if (tab === 'anual' && !this.reporteAnual()) {
      this.cargarReporteAnual();
    } else if ((tab === 'mensual' || tab === 'libro_diario') && !this.reporteMensual()) {
      this.cargarReporteMensual();
    }
  }

  cargarReporteMensual(): void {
    this.loading.set(true);
    this.dataService.getContabilidadMensual(
      this.selectedMes(),
      this.selectedAnio(),
      this.selectedAreaId() || undefined
    ).subscribe({
      next: (rep) => {
        this.reporteMensual.set(rep);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.toast.error(err.error?.detail || 'Error al obtener reporte mensual de contabilidad');
      }
    });
  }

  cargarReporteAnual(): void {
    this.loading.set(true);
    this.dataService.getContabilidadAnual(
      this.selectedAnio(),
      this.selectedAreaId() || undefined
    ).subscribe({
      next: (rep) => {
        this.reporteAnual.set(rep);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.toast.error(err.error?.detail || 'Error al obtener balance anual consolidado');
      }
    });
  }

  getMetodosPagoArray(metodosObj?: { [key: string]: number }): { metodo: string; total: number }[] {
    if (!metodosObj) return [];
    return Object.entries(metodosObj).map(([metodo, total]) => ({
      metodo,
      total: Number(total)
    }));
  }

  getMesNombre(mesNum: number): string {
    const m = this.mesesList.find(x => x.num === mesNum);
    return m ? m.nombre : `Mes ${mesNum}`;
  }

  imprimirReporte(): void {
    window.print();
  }
}

