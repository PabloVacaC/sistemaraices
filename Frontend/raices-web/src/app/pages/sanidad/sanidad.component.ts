import { Component, OnInit, signal, computed, inject, ChangeDetectorRef, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DataService } from '../../core/services/data.service';
import { AuthService } from '../../core/services/auth.service';
import {
  SanidadKPIs,
  SanidadOperacion,
  SanidadOperacionDetalle,
  SanidadVacuna,
  SanidadMedicamento,
  AlertaRetiro,
  Potrero,
  Animal,
  Trabajador,
  ProductoAlmacen,
  SanidadOperacionCreatePayload,
  AnimalOperacionItemPayload,
} from '../../core/models/types';

@Component({
  selector: 'app-sanidad',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './sanidad.component.html',
  styleUrls: ['./sanidad.component.scss'],
})
export class SanidadComponent implements OnInit {
  dataService = inject(DataService);
  auth = inject(AuthService);
  cdr = inject(ChangeDetectorRef);

  // Estados de carga
  cargando = signal<boolean>(false);
  guardando = signal<boolean>(false);

  // Datos principales
  kpis = signal<SanidadKPIs | null>(null);
  operaciones = signal<SanidadOperacion[]>([]);
  vacunas = signal<SanidadVacuna[]>([]);
  medicamentos = signal<SanidadMedicamento[]>([]);
  alertasRetiro = signal<AlertaRetiro[]>([]);
  potreros = signal<Potrero[]>([]);
  animalesHato = signal<Animal[]>([]);
  trabajadores = signal<Trabajador[]>([]);
  almacenItems = signal<ProductoAlmacen[]>([]);

  // Navegación de pestañas
  pestanaActiva = signal<'OPERACIONES' | 'CATALOGOS' | 'ALERTAS_RETIRO'>('OPERACIONES');
  subpestanaCatalogo = signal<'VACUNAS' | 'MEDICAMENTOS'>('VACUNAS');

  // Filtros de operaciones
  filtroTipo = signal<string>('TODOS');
  filtroPotrero = signal<number | null>(null);
  filtroEstado = signal<string>('TODOS');
  filtroBusqueda = signal<string>('');

  // Modo Manga / Trabajo en Corral (< 768px o activado manualmente)
  esModoManga = signal<boolean>(false);
  mangaBusquedaArete = signal<string>('');

  // Formulario de Nueva Operación Sanitaria
  modalOperacionAbierto = signal<boolean>(false);
  operacionForm: {
    tipo_operacion: string;
    fecha_aplicacion: string;
    fecha_programada: string;
    potrero_origen_id: number | null;
    tipo_insumo: 'VACUNA' | 'MEDICAMENTO';
    vacuna_id: number | null;
    medicamento_id: number | null;
    lote_producto: string;
    fecha_vencimiento_producto: string;
    diagnostico: string;
    sintomas: string;
    trabajador_id: number | null;
    veterinario_nombre: string;
    costo_total_estimado: number | null;
    descontar_inventario: boolean;
    trasladar_a_cuarentena: boolean;
    potrero_cuarentena_id: number | null;
    observaciones: string;
    dosis_general: number | null;
    unidad_general: string;
  } = this.getOperacionFormDefault();

  // Lista de animales seleccionados para la operación en curso
  animalesOperacion = signal<{
    animal: Animal;
    seleccionado: boolean;
    dosis: number | null;
    unidad: string;
    estado_aplicacion: 'APLICADO' | 'PENDIENTE' | 'RECHAZADO';
    reaccion_adversa: string;
    observaciones: string;
  }[]>([]);

  // Modal Detalle de Operación
  modalDetalleAbierto = signal<boolean>(false);
  operacionDetalleActual = signal<SanidadOperacion | null>(null);

  // Modal Seguimiento Clínico
  modalSeguimientoAbierto = signal<boolean>(false);
  detalleSeleccionadoParaSeguimiento = signal<SanidadOperacionDetalle | null>(null);
  seguimientoForm = {
    fecha_seguimiento: this.getFechaHoy(),
    estado_salud: 'FAVORABLE',
    temperatura_c: null as number | null,
    peso_actual_kg: null as number | null,
    observaciones: '',
  };

  // Modal Vacuna
  modalVacunaAbierto = signal<boolean>(false);
  vacunaEditandoId = signal<number | null>(null);
  vacunaForm = {
    codigo: '',
    nombre: '',
    nombre_comercial: '',
    enfermedad_objetivo: '',
    especie: 'BOVINO',
    dosis_defecto_ml: 2.0 as number | null,
    via_administracion: 'SUBCUTANEA',
    dias_retiro_carne: 21,
    dias_retiro_leche: 0,
    requiere_refuerzo: false,
    dias_refuerzo: null as number | null,
    estado: 'ACTIVO',
    observaciones: '',
  };

  // Modal Medicamento
  modalMedicamentoAbierto = signal<boolean>(false);
  medicamentoEditandoId = signal<number | null>(null);
  medicamentoForm = {
    codigo: '',
    nombre: '',
    nombre_comercial: '',
    tipo_farmaco: 'ANTIBIOTICO',
    principio_activo: '',
    concentracion: '',
    unidad_medida: 'ML',
    via_administracion: 'INTRAMUSCULAR',
    dias_retiro_carne: 28,
    dias_retiro_leche: 7,
    almacen_id: null as number | null,
    estado: 'ACTIVO',
    observaciones: '',
  };

  // Modal Anular
  modalAnularAbierto = signal<boolean>(false);
  operacionAAnular = signal<SanidadOperacion | null>(null);
  motivoAnulacion = signal<string>('');

  // Toast
  toast = signal<{ mensaje: string; tipo: 'success' | 'error' | 'warning' | 'info' } | null>(null);
  private toastTimeout: any;

  // Filtros computados
  operacionesFiltradas = computed(() => {
    let list = this.operaciones();
    const t = this.filtroTipo();
    if (t !== 'TODOS') {
      list = list.filter((o) => o.tipo_operacion === t);
    }
    const pot = this.filtroPotrero();
    if (pot) {
      list = list.filter((o) => o.potrero_origen_id === pot);
    }
    const est = this.filtroEstado();
    if (est !== 'TODOS') {
      list = list.filter((o) => o.estado === est);
    }
    const q = this.filtroBusqueda().toLowerCase().trim();
    if (q) {
      list = list.filter(
        (o) =>
          o.numero_comprobante.toLowerCase().includes(q) ||
          (o.diagnostico && o.diagnostico.toLowerCase().includes(q)) ||
          (o.veterinario_nombre && o.veterinario_nombre.toLowerCase().includes(q)) ||
          (o.producto_aplicado && o.producto_aplicado.toLowerCase().includes(q)) ||
          (o.trabajador_nombre && o.trabajador_nombre.toLowerCase().includes(q))
      );
    }
    return list;
  });

  // Resumen reactivo de animales en la jornada en curso
  resumenJornada = computed(() => {
    const list = this.animalesOperacion().filter((a) => a.seleccionado);
    const aplicados = list.filter((a) => a.estado_aplicacion === 'APLICADO').length;
    const pendientes = list.filter((a) => a.estado_aplicacion === 'PENDIENTE').length;
    const rechazados = list.filter((a) => a.estado_aplicacion === 'RECHAZADO').length;
    return {
      total: list.length,
      aplicados,
      pendientes,
      rechazados,
    };
  });

  // Animales filtrados para el Modo Manga / Buscador Rápido
  animalesOperacionFiltradosManga = computed(() => {
    const q = this.mangaBusquedaArete().toLowerCase().trim();
    const list = this.animalesOperacion();
    if (!q) return list;
    return list.filter(
      (item) =>
        item.animal.codigo_interno.toLowerCase().includes(q) ||
        (item.animal.numero_arete && item.animal.numero_arete.toLowerCase().includes(q)) ||
        (item.animal.nombre && item.animal.nombre.toLowerCase().includes(q)) ||
        item.animal.raza.toLowerCase().includes(q)
    );
  });

  @HostListener('window:resize')
  onResize(): void {
    if (window.innerWidth < 768 && !this.esModoManga()) {
      this.esModoManga.set(true);
    }
  }

  ngOnInit(): void {
    if (window.innerWidth < 768) {
      this.esModoManga.set(true);
    }
    this.cargarDatosIniciales();
  }

  getFechaHoy(): string {
    const d = new Date();
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  private getOperacionFormDefault() {
    return {
      tipo_operacion: 'VACUNACION_GRUPAL',
      fecha_aplicacion: this.getFechaHoy(),
      fecha_programada: '',
      potrero_origen_id: null,
      tipo_insumo: 'VACUNA' as 'VACUNA' | 'MEDICAMENTO',
      vacuna_id: null,
      medicamento_id: null,
      lote_producto: '',
      fecha_vencimiento_producto: '',
      diagnostico: '',
      sintomas: '',
      trabajador_id: null,
      veterinario_nombre: '',
      costo_total_estimado: null,
      descontar_inventario: false,
      trasladar_a_cuarentena: false,
      potrero_cuarentena_id: null,
      observaciones: '',
      dosis_general: 2.0,
      unidad_general: 'ML',
    };
  }

  cargarDatosIniciales(): void {
    this.cargando.set(true);

    // Cargar KPIs
    this.dataService.getSanidadKPIs().subscribe({
      next: (k) => this.kpis.set(k),
      error: () => {},
    });

    // Cargar Operaciones
    this.dataService.getOperacionesSanitarias().subscribe({
      next: (ops) => {
        this.operaciones.set(ops);
        this.cargando.set(false);
      },
      error: () => {
        this.cargando.set(false);
        this.mostrarToast('Error al cargar historial de operaciones sanitarias.', 'error');
      },
    });

    // Cargar Catálogos
    this.dataService.getVacunas().subscribe({
      next: (v) => this.vacunas.set(v),
    });
    this.dataService.getMedicamentos().subscribe({
      next: (m) => this.medicamentos.set(m),
    });

    // Cargar Alertas de Retiro
    this.dataService.getAlertasRetiro().subscribe({
      next: (a) => this.alertasRetiro.set(a),
    });

    // Cargar Potreros
    this.dataService.getPotreros().subscribe({
      next: (p) => this.potreros.set(p.filter((pot) => pot.estado === 'ACTIVO')),
    });

    // Cargar Animales activos para selección
    this.dataService.getAnimales({ estado: 'ACTIVO', limit: 500 }).subscribe({
      next: (ans) => {
        this.animalesHato.set(ans);
        if (this.modalOperacionAbierto()) {
          this.poblarAnimalesParaOperacion();
        }
      },
      error: (err) => {
        console.error('Error al cargar animales activos del hato:', err);
      },
    });

    // Cargar Trabajadores
    this.dataService.getTrabajadores().subscribe({
      next: (trabs) => this.trabajadores.set(trabs.filter((t) => t.estado)),
    });

    // Cargar Almacén (para descuento de inventario)
    this.dataService.getProductosAlmacen().subscribe({
      next: (items) => this.almacenItems.set(items),
    });
  }

  cambiarPestana(p: 'OPERACIONES' | 'CATALOGOS' | 'ALERTAS_RETIRO'): void {
    this.pestanaActiva.set(p);
  }

  toggleModoManga(): void {
    this.esModoManga.update((v) => !v);
    this.mostrarToast(
      this.esModoManga()
        ? 'Modo Manga Activado: Botones táctiles de 48px y checklist rápido.'
        : 'Modo Estándar Activado.',
      'info'
    );
  }

  // =========================================================================
  // GESTIÓN DE OPERACIÓN SANITARIA (CREACIÓN)
  // =========================================================================

  abrirModalNuevaOperacion(tipoInicial: string = 'VACUNACION_GRUPAL'): void {
    this.operacionForm = this.getOperacionFormDefault();
    this.operacionForm.tipo_operacion = tipoInicial;
    this.operacionForm.tipo_insumo = tipoInicial.includes('VACUNA') ? 'VACUNA' : 'MEDICAMENTO';

    // Auto-seleccionar primer insumo si existe
    if (this.operacionForm.tipo_insumo === 'VACUNA' && this.vacunas().length > 0) {
      this.operacionForm.vacuna_id = this.vacunas()[0].id;
      this.onCambioVacuna();
    } else if (this.operacionForm.tipo_insumo === 'MEDICAMENTO' && this.medicamentos().length > 0) {
      this.operacionForm.medicamento_id = this.medicamentos()[0].id;
      this.onCambioMedicamento();
    }

    // Inicializar lista de animales
    this.poblarAnimalesParaOperacion();
    this.modalOperacionAbierto.set(true);
  }

  onTipoOperacionChange(): void {
    const t = this.operacionForm.tipo_operacion;
    if (t.includes('VACUNA')) {
      this.operacionForm.tipo_insumo = 'VACUNA';
      if (!this.operacionForm.vacuna_id && this.vacunas().length > 0) {
        this.operacionForm.vacuna_id = this.vacunas()[0].id;
      }
      this.onCambioVacuna();
    } else {
      this.operacionForm.tipo_insumo = 'MEDICAMENTO';
      if (!this.operacionForm.medicamento_id && this.medicamentos().length > 0) {
        this.operacionForm.medicamento_id = this.medicamentos()[0].id;
      }
      this.onCambioMedicamento();
    }
  }

  onCambioVacuna(): void {
    const v = this.vacunas().find((x) => x.id === this.operacionForm.vacuna_id);
    if (v) {
      this.operacionForm.dosis_general = Number(v.dosis_defecto_ml) || 2.0;
      this.operacionForm.unidad_general = 'ML';
      this.aplicarDosisGeneralATodos();
    }
  }

  onCambioMedicamento(): void {
    const m = this.medicamentos().find((x) => x.id === this.operacionForm.medicamento_id);
    if (m) {
      this.operacionForm.unidad_general = m.unidad_medida || 'ML';
      this.aplicarDosisGeneralATodos();
    }
  }

  poblarAnimalesParaOperacion(): void {
    const raw: any = this.operacionForm.potrero_origen_id;
    const potreroId =
      raw !== null && raw !== undefined && raw !== '' && raw !== 'null'
        ? Number(raw)
        : null;

    const potreroObj = potreroId ? this.potreros().find((p) => Number(p.id) === potreroId) : null;
    const potreroNombre = potreroObj?.nombre?.trim().toLowerCase();

    let pool = this.animalesHato();

    if (potreroId) {
      pool = pool.filter((a) => {
        // 1. Coincidencia directa por potrero_id numérico
        if (a.potrero_id !== null && a.potrero_id !== undefined && Number(a.potrero_id) === potreroId) {
          return true;
        }
        // 2. Coincidencia por nombre de potrero en a.ubicacion
        if (potreroNombre && a.ubicacion && a.ubicacion.trim().toLowerCase() === potreroNombre) {
          return true;
        }
        return false;
      });
    }

    const items = pool.map((an) => ({
      animal: an,
      seleccionado: true, // Por defecto se seleccionan todos los del potrero
      dosis: this.operacionForm.dosis_general,
      unidad: this.operacionForm.unidad_general,
      estado_aplicacion: 'APLICADO' as 'APLICADO' | 'PENDIENTE' | 'RECHAZADO',
      reaccion_adversa: '',
      observaciones: '',
    }));
    this.animalesOperacion.set(items);
    this.cdr.markForCheck();
  }

  onPotreroOrigenChange(): void {
    this.poblarAnimalesParaOperacion();
  }

  seleccionarTodosAnimales(marcar: boolean): void {
    this.animalesOperacion.update((list) =>
      list.map((item) => ({ ...item, seleccionado: marcar }))
    );
  }

  aplicarDosisGeneralATodos(): void {
    const d = this.operacionForm.dosis_general;
    const u = this.operacionForm.unidad_general;
    this.animalesOperacion.update((list) =>
      list.map((item) => ({ ...item, dosis: d, unidad: u }))
    );
  }

  // Métodos rápidos para Modo Manga (1 solo toque)
  mangaMarcarEstado(item: any, nuevoEstado: 'APLICADO' | 'PENDIENTE' | 'RECHAZADO'): void {
    item.estado_aplicacion = nuevoEstado;
    item.seleccionado = true;
    this.cdr.markForCheck();
  }

  guardarOperacionSanitaria(): void {
    const seleccionados = this.animalesOperacion().filter((a) => a.seleccionado);
    if (seleccionados.length === 0) {
      this.mostrarToast('Debe seleccionar al menos 1 animal para registrar la operación.', 'warning');
      return;
    }

    if (this.operacionForm.tipo_insumo === 'VACUNA' && !this.operacionForm.vacuna_id) {
      this.mostrarToast('Seleccione una vacuna válida.', 'warning');
      return;
    }

    if (this.operacionForm.tipo_insumo === 'MEDICAMENTO' && !this.operacionForm.medicamento_id) {
      this.mostrarToast('Seleccione un medicamento válido.', 'warning');
      return;
    }

    const payload: SanidadOperacionCreatePayload = {
      tipo_operacion: this.operacionForm.tipo_operacion,
      fecha_aplicacion: this.operacionForm.fecha_aplicacion,
      fecha_programada: this.operacionForm.fecha_programada || null,
      potrero_origen_id: this.operacionForm.potrero_origen_id,
      vacuna_id: this.operacionForm.tipo_insumo === 'VACUNA' ? this.operacionForm.vacuna_id : null,
      medicamento_id: this.operacionForm.tipo_insumo === 'MEDICAMENTO' ? this.operacionForm.medicamento_id : null,
      lote_producto: this.operacionForm.lote_producto || null,
      fecha_vencimiento_producto: this.operacionForm.fecha_vencimiento_producto || null,
      diagnostico: this.operacionForm.diagnostico || null,
      sintomas: this.operacionForm.sintomas || null,
      trabajador_id: this.operacionForm.trabajador_id,
      veterinario_nombre: this.operacionForm.veterinario_nombre || null,
      costo_total_estimado: this.operacionForm.costo_total_estimado,
      descontar_inventario: this.operacionForm.descontar_inventario,
      trasladar_a_cuarentena: this.operacionForm.trasladar_a_cuarentena,
      potrero_cuarentena_id: this.operacionForm.potrero_cuarentena_id,
      observaciones: this.operacionForm.observaciones || null,
      animales: seleccionados.map((item) => ({
        animal_id: item.animal.id,
        dosis_aplicada: item.dosis,
        unidad_medida: item.unidad,
        estado_aplicacion: item.estado_aplicacion,
        reaccion_adversa: item.reaccion_adversa || null,
        observaciones: item.observaciones || null,
      })),
    };

    this.guardando.set(true);
    this.dataService.crearOperacionSanitaria(payload).subscribe({
      next: (res) => {
        this.guardando.set(false);
        this.modalOperacionAbierto.set(false);
        this.mostrarToast(`Operación '${res.numero_comprobante}' registrada con éxito.`, 'success');
        this.cargarDatosIniciales();
      },
      error: (err) => {
        this.guardando.set(false);
        const msg = err.error?.detail || 'Error al guardar la operación sanitaria.';
        this.mostrarToast(msg, 'error');
      },
    });
  }

  // =========================================================================
  // DETALLES Y SEGUIMIENTO CLÍNICO
  // =========================================================================

  verDetalleOperacion(op: SanidadOperacion): void {
    this.cargando.set(true);
    this.dataService.getOperacionSanitaria(op.id).subscribe({
      next: (det) => {
        this.operacionDetalleActual.set(det);
        this.cargando.set(false);
        this.modalDetalleAbierto.set(true);
      },
      error: () => {
        this.cargando.set(false);
        this.mostrarToast('Error al consultar el detalle de la operación.', 'error');
      },
    });
  }

  abrirModalSeguimiento(det: SanidadOperacionDetalle): void {
    this.detalleSeleccionadoParaSeguimiento.set(det);
    this.seguimientoForm = {
      fecha_seguimiento: this.getFechaHoy(),
      estado_salud: 'FAVORABLE',
      temperatura_c: null,
      peso_actual_kg: null,
      observaciones: '',
    };
    this.modalSeguimientoAbierto.set(true);
  }

  guardarSeguimientoClinico(): void {
    const det = this.detalleSeleccionadoParaSeguimiento();
    if (!det) return;

    this.guardando.set(true);
    this.dataService.registrarSeguimientoClinico(det.id, this.seguimientoForm).subscribe({
      next: () => {
        this.guardando.set(false);
        this.modalSeguimientoAbierto.set(false);
        this.mostrarToast('Control de evolución clínica registrado.', 'success');
        // Recargar detalle
        if (this.operacionDetalleActual()) {
          this.verDetalleOperacion(this.operacionDetalleActual()!);
        }
      },
      error: (err) => {
        this.guardando.set(false);
        const msg = err.error?.detail || 'Error al registrar el seguimiento.';
        this.mostrarToast(msg, 'error');
      },
    });
  }

  abrirModalAnular(op: SanidadOperacion): void {
    this.operacionAAnular.set(op);
    this.motivoAnulacion.set('');
    this.modalAnularAbierto.set(true);
  }

  confirmarAnulacion(): void {
    const op = this.operacionAAnular();
    const motivo = this.motivoAnulacion().trim();
    if (!op || motivo.length < 5) {
      this.mostrarToast('Debe ingresar un motivo de anulación válido (mínimo 5 caracteres).', 'warning');
      return;
    }

    this.guardando.set(true);
    this.dataService.anularOperacionSanitaria(op.id, motivo).subscribe({
      next: () => {
        this.guardando.set(false);
        this.modalAnularAbierto.set(false);
        if (this.modalDetalleAbierto()) {
          this.modalDetalleAbierto.set(false);
        }
        this.mostrarToast(`Operación ${op.numero_comprobante} anulada con éxito.`, 'info');
        this.cargarDatosIniciales();
      },
      error: (err) => {
        this.guardando.set(false);
        const msg = err.error?.detail || 'Error al anular la operación.';
        this.mostrarToast(msg, 'error');
      },
    });
  }

  // =========================================================================
  // GESTIÓN DE CATÁLOGOS (VACUNAS / MEDICAMENTOS)
  // =========================================================================

  abrirModalVacuna(vacuna?: SanidadVacuna): void {
    if (vacuna) {
      this.vacunaEditandoId.set(vacuna.id);
      this.vacunaForm = {
        codigo: vacuna.codigo,
        nombre: vacuna.nombre,
        nombre_comercial: vacuna.nombre_comercial || '',
        enfermedad_objetivo: vacuna.enfermedad_objetivo,
        especie: vacuna.especie,
        dosis_defecto_ml: vacuna.dosis_defecto_ml || 2.0,
        via_administracion: vacuna.via_administracion,
        dias_retiro_carne: vacuna.dias_retiro_carne,
        dias_retiro_leche: vacuna.dias_retiro_leche,
        requiere_refuerzo: vacuna.requiere_refuerzo,
        dias_refuerzo: vacuna.dias_refuerzo || null,
        estado: vacuna.estado,
        observaciones: vacuna.observaciones || '',
      };
    } else {
      this.vacunaEditandoId.set(null);
      const nextNum = this.vacunas().length + 1;
      this.vacunaForm = {
        codigo: `VAC-${String(nextNum).padStart(3, '0')}`,
        nombre: '',
        nombre_comercial: '',
        enfermedad_objetivo: '',
        especie: 'BOVINO',
        dosis_defecto_ml: 2.0,
        via_administracion: 'SUBCUTANEA',
        dias_retiro_carne: 21,
        dias_retiro_leche: 0,
        requiere_refuerzo: false,
        dias_refuerzo: null,
        estado: 'ACTIVO',
        observaciones: '',
      };
    }
    this.modalVacunaAbierto.set(true);
  }

  guardarVacuna(): void {
    if (!this.vacunaForm.nombre.trim() || !this.vacunaForm.enfermedad_objetivo.trim()) {
      this.mostrarToast('El nombre y la enfermedad objetivo son obligatorios.', 'warning');
      return;
    }

    this.guardando.set(true);
    const id = this.vacunaEditandoId();
    if (id) {
      this.dataService.actualizarVacuna(id, this.vacunaForm).subscribe({
        next: () => {
          this.guardando.set(false);
          this.modalVacunaAbierto.set(false);
          this.mostrarToast('Vacuna actualizada con éxito.', 'success');
          this.cargarDatosIniciales();
        },
        error: (err) => {
          this.guardando.set(false);
          this.mostrarToast(err.error?.detail || 'Error al actualizar vacuna.', 'error');
        },
      });
    } else {
      this.dataService.crearVacuna(this.vacunaForm).subscribe({
        next: () => {
          this.guardando.set(false);
          this.modalVacunaAbierto.set(false);
          this.mostrarToast('Vacuna registrada en el catálogo.', 'success');
          this.cargarDatosIniciales();
        },
        error: (err) => {
          this.guardando.set(false);
          this.mostrarToast(err.error?.detail || 'Error al crear vacuna.', 'error');
        },
      });
    }
  }

  alternarEstadoVacuna(v: SanidadVacuna): void {
    this.dataService.alternarEstadoVacuna(v.id).subscribe({
      next: (res) => {
        v.estado = res.estado;
        this.mostrarToast(`Vacuna '${v.nombre}' cambiada a ${res.estado}.`, 'info');
      },
    });
  }

  abrirModalMedicamento(med?: SanidadMedicamento): void {
    if (med) {
      this.medicamentoEditandoId.set(med.id);
      this.medicamentoForm = {
        codigo: med.codigo,
        nombre: med.nombre,
        nombre_comercial: med.nombre_comercial || '',
        tipo_farmaco: med.tipo_farmaco,
        principio_activo: med.principio_activo || '',
        concentracion: med.concentracion || '',
        unidad_medida: med.unidad_medida,
        via_administracion: med.via_administracion,
        dias_retiro_carne: med.dias_retiro_carne,
        dias_retiro_leche: med.dias_retiro_leche,
        almacen_id: med.almacen_id || null,
        estado: med.estado,
        observaciones: med.observaciones || '',
      };
    } else {
      this.medicamentoEditandoId.set(null);
      const nextNum = this.medicamentos().length + 1;
      this.medicamentoForm = {
        codigo: `MED-${String(nextNum).padStart(3, '0')}`,
        nombre: '',
        nombre_comercial: '',
        tipo_farmaco: 'ANTIBIOTICO',
        principio_activo: '',
        concentracion: '',
        unidad_medida: 'ML',
        via_administracion: 'INTRAMUSCULAR',
        dias_retiro_carne: 28,
        dias_retiro_leche: 7,
        almacen_id: null,
        estado: 'ACTIVO',
        observaciones: '',
      };
    }
    this.modalMedicamentoAbierto.set(true);
  }

  guardarMedicamento(): void {
    if (!this.medicamentoForm.nombre.trim()) {
      this.mostrarToast('El nombre del medicamento es obligatorio.', 'warning');
      return;
    }

    this.guardando.set(true);
    const id = this.medicamentoEditandoId();
    if (id) {
      this.dataService.actualizarMedicamento(id, this.medicamentoForm).subscribe({
        next: () => {
          this.guardando.set(false);
          this.modalMedicamentoAbierto.set(false);
          this.mostrarToast('Medicamento actualizado con éxito.', 'success');
          this.cargarDatosIniciales();
        },
        error: (err) => {
          this.guardando.set(false);
          this.mostrarToast(err.error?.detail || 'Error al actualizar medicamento.', 'error');
        },
      });
    } else {
      this.dataService.crearMedicamento(this.medicamentoForm).subscribe({
        next: () => {
          this.guardando.set(false);
          this.modalMedicamentoAbierto.set(false);
          this.mostrarToast('Medicamento registrado en el catálogo.', 'success');
          this.cargarDatosIniciales();
        },
        error: (err) => {
          this.guardando.set(false);
          this.mostrarToast(err.error?.detail || 'Error al crear medicamento.', 'error');
        },
      });
    }
  }

  alternarEstadoMedicamento(m: SanidadMedicamento): void {
    this.dataService.alternarEstadoMedicamento(m.id).subscribe({
      next: (res) => {
        m.estado = res.estado;
        this.mostrarToast(`Medicamento '${m.nombre}' cambiado a ${res.estado}.`, 'info');
      },
    });
  }

  mostrarToast(mensaje: string, tipo: 'success' | 'error' | 'warning' | 'info' = 'info'): void {
    if (this.toastTimeout) clearTimeout(this.toastTimeout);
    this.toast.set({ mensaje, tipo });
    this.toastTimeout = setTimeout(() => {
      this.toast.set(null);
    }, 4500);
  }
}
