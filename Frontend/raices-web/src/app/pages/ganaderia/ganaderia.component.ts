import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DataService } from '../../core/services/data.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import {
  Animal,
  AnimalPerfil,
  PesajeGanado,
  HistorialArete,
  NacimientoGanado,
  CompraGanado,
  CompraGanadoDetallePayload,
  VentaGanado,
  BajaGanado,
  GanaderiaKPIs,
  AnimalCreatePayload,
  AnimalUpdatePayload,
  PesajeCreatePayload,
  NacimientoCreatePayload,
  CompraGanadoCreatePayload,
  VentaGanadoCreatePayload,
  BajaGanadoCreatePayload,
  Potrero,
  HistorialSanitarioAnimal,
} from '../../core/models/types';

interface CompraItemForm {
  tipo_ganado: string;
  raza: string;
  sexo: string;
  fecha_nacimiento?: string;
  edad_estimada_meses?: number;
  numero_arete?: string;
  peso?: number;
  precio_compra: number;
  modalidad_precio: string;
  potrero_id?: number | null;
  ubicacion: string;
  observaciones?: string;
}

interface VentaItemForm {
  animal_id: number;
  animal?: Animal;
  precio: number;
  modalidad_precio: string;
}

@Component({
  selector: 'app-ganaderia',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './ganaderia.component.html',
  styleUrls: ['./ganaderia.component.css']
})
export class GanaderiaComponent implements OnInit {
  private dataService = inject(DataService);
  public auth = inject(AuthService);
  private toast = inject(ToastService);

  // Estados generales
  loading = signal<boolean>(false);
  activeTab = signal<'TODOS' | 'REGISTRADOS' | 'NACIMIENTOS' | 'COMPRAS' | 'VENTAS' | 'BAJAS'>('TODOS');
  kpis = signal<GanaderiaKPIs | null>(null);

  // Listas de datos
  animales = signal<Animal[]>([]);
  potreros = signal<Potrero[]>([]);
  nacimientos = signal<NacimientoGanado[]>([]);
  compras = signal<CompraGanado[]>([]);
  ventas = signal<VentaGanado[]>([]);
  bajas = signal<BajaGanado[]>([]);

  // Filtros
  searchTerm = signal<string>('');
  filtroEstado = signal<string>('TODOS');
  filtroSexo = signal<string>('TODOS');
  filtroCategoria = signal<string>('TODOS');
  filtroTipoGanado = signal<string>('TODOS');
  filtroPotrero = signal<string>('TODOS');

  // Animal seleccionado / Perfil 360
  selectedAnimalPerfil = signal<AnimalPerfil | null>(null);
  historialSanitarioAnimal = signal<HistorialSanitarioAnimal | null>(null);
  showPerfilModal = signal<boolean>(false);
  activePerfilTab = signal<'general' | 'pesajes' | 'genealogia' | 'procedencia' | 'historial_aretes' | 'sanidad'>('general');

  // Modal Nuevo / Editar Animal
  showAnimalModal = signal<boolean>(false);
  isEditingAnimal = signal<boolean>(false);
  editingAnimalId = signal<number | null>(null);
  originalArete = signal<string | null>(null);
  animalForm: AnimalCreatePayload & { motivo_cambio_arete?: string; potrero_id?: number | null } = this.initAnimalForm();

  // Modal Pesaje
  showPesajeModal = signal<boolean>(false);
  targetAnimalPesaje = signal<Animal | null>(null);
  pesajeForm: PesajeCreatePayload = {
    fecha_pesaje: this.getTodayDate(),
    peso: 0,
    notas: ''
  };

  // Modal Nacimiento / Parto
  showNacimientoModal = signal<boolean>(false);
  nacimientoForm: NacimientoCreatePayload & { cria_potrero_id?: number | null } = this.initNacimientoForm();

  // Modal Compra
  showCompraModal = signal<boolean>(false);
  potreroMasivoCompra = signal<number | null>(null);
  compraCabecera = {
    proveedor: '',
    fecha_compra: this.getTodayDate(),
    numero_documento: '',
    costos_adicionales: 0,
    costo_transporte: 0,
    observaciones: ''
  };
  compraDetalles: CompraItemForm[] = [];

  // Modal Venta
  showVentaModal = signal<boolean>(false);
  ventaCabecera = {
    cliente: '',
    fecha_venta: this.getTodayDate(),
    modalidad_venta: 'POR_ANIMAL',
    metodo_pago: 'EFECTIVO',
    costo_transporte: 0,
    descuento: 0,
    numero_documento: '',
    observaciones: ''
  };
  ventaItems: VentaItemForm[] = [];

  // Modal Baja
  showBajaModal = signal<boolean>(false);
  bajaForm: BajaGanadoCreatePayload = {
    animal_id: 0,
    tipo_baja: 'MUERTE',
    fecha_baja: this.getTodayDate(),
    causa_diagnostico: '',
    necropsia_realizada: false,
    destino_cuerpo: 'ENTIERRO',
    valor_estimado_perdida: 0,
    observaciones: ''
  };

  // Modal Anulaciones (Venta o Baja)
  showAnularModal = signal<boolean>(false);
  anularTipo = signal<'VENTA' | 'BAJA'>('VENTA');
  anularId = signal<number | null>(null);
  anularMotivo = signal<string>('');

  // Opciones predefinidas
  readonly TIPOS_GANADO = ['BOVINO', 'EQUINO', 'OVINO', 'PORCINO', 'CAPRINO', 'OTRO'];
  readonly RAZAS_BOVINO = ['NELORE', 'BRAHMAN', 'BRANGUS', 'BRAFORD', 'GIROLANDO', 'HOLSTEIN', 'CRIOLLO', 'MESTIZO', 'SENEPOL', 'ANGUS', 'OTRA'];
  readonly CATEGORIAS = ['TERNERO / TERNERA', 'DESMAMANTE', 'VAQUILLA', 'NOVILLO', 'VACA', 'TORO', 'BUEY', 'REPRODUCTOR'];
  readonly UBICACIONES = ['POTRERO 1', 'POTRERO 2', 'POTRERO 3', 'POTRERO DON CESAR', 'POTRERO DON FELIPE', 'CORRAL DE MANEJO', 'CORRAL DE ENGORDE', 'MATERNIDAD', 'CUARENTENA'];
  readonly TIPOS_BAJA = ['MUERTE', 'DESCARTE', 'ROBO', 'EXTRAVIO', 'SACRIFICIO_EMERGENCIA', 'OTRO'];

  // Animales filtrados en tiempo real
  animalesFiltrados = computed(() => {
    let list = this.animales();
    const tab = this.activeTab();

    if (tab === 'REGISTRADOS') {
      list = list.filter(a => a.procedencia === 'REGISTRADO' || a.procedencia === 'REGISTRO_MANUAL');
    } else if (tab === 'NACIMIENTOS') {
      list = list.filter(a => a.procedencia === 'NACIMIENTO');
    } else if (tab === 'COMPRAS') {
      list = list.filter(a => a.procedencia === 'COMPRA');
    }

    const estado = this.filtroEstado();
    if (estado !== 'TODOS') {
      list = list.filter(a => (a.estado || '').toUpperCase() === estado.toUpperCase());
    }

    const sexo = this.filtroSexo();
    if (sexo !== 'TODOS') {
      list = list.filter(a => (a.sexo || '').toUpperCase() === sexo.toUpperCase());
    }

    const cat = this.filtroCategoria();
    if (cat !== 'TODOS') {
      list = list.filter(a => a.categoria === cat);
    }

    const tipo = this.filtroTipoGanado();
    if (tipo !== 'TODOS') {
      list = list.filter(a => ((a.tipo_ganado || (a as any).tipo || '')).toUpperCase() === tipo.toUpperCase());
    }

    const pot = this.filtroPotrero();
    if (pot !== 'TODOS') {
      list = list.filter(a => String(a.potrero_id) === pot || (a.ubicacion && a.ubicacion.toLowerCase() === pot.toLowerCase()));
    }

    const term = this.searchTerm().trim().toLowerCase();
    if (term) {
      list = list.filter(a =>
        (a.codigo_interno && a.codigo_interno.toLowerCase().includes(term)) ||
        (a.numero_arete && a.numero_arete.toLowerCase().includes(term)) ||
        (a.nombre && a.nombre.toLowerCase().includes(term)) ||
        (a.raza && a.raza.toLowerCase().includes(term)) ||
        (a.ubicacion && a.ubicacion.toLowerCase().includes(term))
      );
    }

    return list;
  });

  // Lista de madres posibles (hembras)
  madresDisponibles = computed(() => {
    return this.animales().filter(a => a.sexo === 'HEMBRA');
  });

  // Lista de padres posibles (machos)
  padresDisponibles = computed(() => {
    return this.animales().filter(a => a.sexo === 'MACHO');
  });

  // Animales candidatos para venta o baja (deben estar ACTIVOS y tener NÚMERO DE ARETE según RF-010)
  animalesAptosParaSalida = computed(() => {
    return this.animales().filter(a => a.estado === 'ACTIVO' && a.numero_arete && a.numero_arete.trim() !== '');
  });

  // Total acumulado en compra modal
  totalCompraCalculado = computed(() => {
    const subtotal = this.compraDetalles.reduce((acc, it) => acc + (Number(it.precio_compra) || 0), 0);
    return subtotal + (Number(this.compraCabecera.costos_adicionales) || 0) + (Number(this.compraCabecera.costo_transporte) || 0);
  });

  // Total acumulado en venta modal
  totalVentaCalculado = computed(() => {
    const subtotal = this.ventaItems.reduce((acc, it) => acc + (Number(it.precio) || 0), 0);
    const desc = Number(this.ventaCabecera.descuento) || 0;
    const transp = Number(this.ventaCabecera.costo_transporte) || 0;
    return Math.max(0, subtotal - desc + transp);
  });

  ngOnInit(): void {
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.loading.set(true);
    this.cargarPotreros();

    this.dataService.getGanaderiaKPIs().subscribe({
      next: (res) => this.kpis.set(res),
      error: (err) => console.error('Error al cargar KPIs de ganadería:', err)
    });

    this.dataService.getAnimales().subscribe({
      next: (res) => {
        this.animales.set(res);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.toast.error('Error al cargar la lista de ganado: ' + (err.error?.detail || err.message));
      }
    });
  }

  cargarPotreros(): void {
    this.dataService.getPotreros().subscribe({
      next: (res) => {
        const activos = (res || []).filter(p => p.estado === 'ACTIVO');
        this.potreros.set(activos);
      },
      error: (err) => console.error('Error al cargar potreros:', err)
    });
  }

  cargarNacimientos(): void {
    this.dataService.getNacimientos().subscribe({
      next: (res) => this.nacimientos.set(res),
      error: () => {}
    });
  }

  cargarCompras(): void {
    this.dataService.getComprasGanado().subscribe({
      next: (res) => this.compras.set(res),
      error: () => {}
    });
  }

  cargarVentas(): void {
    this.dataService.getVentasGanado().subscribe({
      next: (res) => this.ventas.set(res),
      error: () => {}
    });
  }

  cargarBajas(): void {
    this.dataService.getBajasGanado().subscribe({
      next: (res) => this.bajas.set(res),
      error: () => {}
    });
  }

  setTab(tab: 'TODOS' | 'REGISTRADOS' | 'NACIMIENTOS' | 'COMPRAS' | 'VENTAS' | 'BAJAS'): void {
    this.activeTab.set(tab);
    if (tab === 'NACIMIENTOS' && this.nacimientos().length === 0) {
      this.cargarNacimientos();
    } else if (tab === 'COMPRAS' && this.compras().length === 0) {
      this.cargarCompras();
    } else if (tab === 'VENTAS' && this.ventas().length === 0) {
      this.cargarVentas();
    } else if (tab === 'BAJAS' && this.bajas().length === 0) {
      this.cargarBajas();
    }
  }

  // ==========================================
  // PERFIL 360° DEL ANIMAL
  // ==========================================
  verPerfilAnimal(animalId: number): void {
    this.loading.set(true);
    this.dataService.getAnimalPerfil(animalId).subscribe({
      next: (res: any) => {
        const rawAnimal = res.animal || res;
        const normalizedAnimal: Animal = {
          id: rawAnimal.id,
          codigo_interno: rawAnimal.codigo_interno,
          numero_arete: rawAnimal.numero_arete,
          nombre: rawAnimal.nombre,
          tipo_ganado: rawAnimal.tipo_ganado || rawAnimal.tipo || 'Bovino',
          raza: rawAnimal.raza || 'Nelore',
          sexo: (rawAnimal.sexo || 'HEMBRA').toUpperCase(),
          fecha_nacimiento: rawAnimal.fecha_nacimiento,
          edad_estimada_meses: rawAnimal.edad_estimada_meses ?? rawAnimal.edad_meses ?? 0,
          peso_inicial: rawAnimal.peso_inicial,
          peso_actual: rawAnimal.peso_actual,
          fecha_ultimo_pesaje: rawAnimal.fecha_ultimo_pesaje,
          categoria: rawAnimal.categoria || 'General',
          estado: rawAnimal.estado || 'ACTIVO',
          ubicacion: rawAnimal.ubicacion || 'Potrero 1',
          observaciones: rawAnimal.observaciones,
          procedencia: rawAnimal.procedencia || 'REGISTRO_MANUAL',
          madre_id: rawAnimal.madre_id,
          madre_codigo: rawAnimal.madre_codigo || (res.madre ? res.madre.codigo_interno : null),
          madre_arete: rawAnimal.madre_arete || (res.madre ? res.madre.numero_arete : null),
          padre_id: rawAnimal.padre_id,
          padre_codigo: rawAnimal.padre_codigo || (res.padre ? res.padre.codigo_interno : null),
          padre_arete: rawAnimal.padre_arete || (res.padre ? res.padre.numero_arete : null),
          fecha_registro: rawAnimal.fecha_registro || rawAnimal.fecha_creacion,
        };

        const pesajesList = res.pesajes || res.historial_pesajes || [];
        const aretesList = res.historial_aretes || [];
        const hijosList = res.hijos || [];
        const partosList = res.partos_madre || [];
        const detCompra = res.detalles_compra || (res.detalles_operaciones ? res.detalles_operaciones.compra : null);
        const detVenta = res.detalles_venta || (res.detalles_operaciones ? res.detalles_operaciones.venta : null);
        const detBaja = res.detalles_baja || (res.detalles_operaciones ? res.detalles_operaciones.baja : null);

        const perfilFinal: AnimalPerfil = {
          animal: normalizedAnimal,
          pesajes: pesajesList,
          historial_aretes: aretesList,
          madre: res.madre || null,
          padre: res.padre || null,
          hijos: hijosList,
          partos_madre: partosList,
          detalles_compra: detCompra,
          detalles_venta: detVenta,
          detalles_baja: detBaja,
        };

        this.selectedAnimalPerfil.set(perfilFinal);
        this.activePerfilTab.set('general');
        this.showPerfilModal.set(true);
        this.loading.set(false);

        // Cargar historial sanitario y períodos de retiro (SPEC-003)
        this.dataService.getHistorialSanitarioAnimal(animalId).subscribe({
          next: (san) => this.historialSanitarioAnimal.set(san),
          error: () => this.historialSanitarioAnimal.set(null),
        });
      },
      error: (err) => {
        this.loading.set(false);
        this.toast.error('No se pudo cargar el perfil del animal: ' + (err.error?.detail || err.message));
      }
    });
  }

  cerrarPerfil(): void {
    this.showPerfilModal.set(false);
    this.selectedAnimalPerfil.set(null);
  }

  // ==========================================
  // REGISTRAR / EDITAR ANIMAL
  // ==========================================
  initAnimalForm(): AnimalCreatePayload & { motivo_cambio_arete?: string; potrero_id?: number | null } {
    const defaultPot = this.potreros()[0];
    return {
      numero_arete: '',
      nombre: '',
      tipo_ganado: 'BOVINO',
      raza: 'NELORE',
      sexo: 'HEMBRA',
      fecha_nacimiento: '',
      edad_estimada_meses: null,
      peso_inicial: null,
      categoria: 'VAQUILLA',
      estado: 'ACTIVO',
      potrero_id: defaultPot?.id || null,
      ubicacion: defaultPot?.nombre || 'Potrero 1',
      observaciones: '',
      procedencia: 'REGISTRADO',
      madre_id: null,
      padre_id: null,
      motivo_cambio_arete: ''
    };
  }

  onPotreroSeleccionado(potId: any): void {
    const idNum = Number(potId);
    const pot = this.potreros().find(p => p.id === idNum);
    if (pot) {
      this.animalForm.potrero_id = pot.id;
      this.animalForm.ubicacion = pot.nombre;
    }
  }

  abrirModalNuevoAnimal(): void {
    this.isEditingAnimal.set(false);
    this.editingAnimalId.set(null);
    this.originalArete.set(null);
    this.animalForm = this.initAnimalForm();
    this.showAnimalModal.set(true);
  }

  abrirModalEditarAnimal(animal: Animal): void {
    this.isEditingAnimal.set(true);
    this.editingAnimalId.set(animal.id);
    this.originalArete.set(animal.numero_arete || null);

    let potId = animal.potrero_id || null;
    if (!potId && animal.ubicacion) {
      const match = this.potreros().find(p => p.nombre.toLowerCase() === animal.ubicacion.toLowerCase());
      if (match) potId = match.id;
    }

    this.animalForm = {
      numero_arete: animal.numero_arete || '',
      nombre: animal.nombre || '',
      tipo_ganado: animal.tipo_ganado,
      raza: animal.raza,
      sexo: animal.sexo,
      fecha_nacimiento: animal.fecha_nacimiento || '',
      edad_estimada_meses: animal.edad_estimada_meses,
      peso_inicial: animal.peso_inicial,
      categoria: animal.categoria || '',
      estado: animal.estado,
      potrero_id: potId,
      ubicacion: animal.ubicacion,
      observaciones: animal.observaciones || '',
      procedencia: animal.procedencia,
      madre_id: animal.madre_id,
      padre_id: animal.padre_id,
      motivo_cambio_arete: ''
    };
    this.showAnimalModal.set(true);
  }

  guardarAnimal(): void {
    if (!this.animalForm.raza || !this.animalForm.sexo || (!this.animalForm.ubicacion && !this.animalForm.potrero_id)) {
      this.toast.error('Complete los campos obligatorios (Raza, Sexo y Ubicación).');
      return;
    }

    const payload: AnimalCreatePayload = {
      ...this.animalForm,
      potrero_id: this.animalForm.potrero_id ? Number(this.animalForm.potrero_id) : null,
      numero_arete: this.animalForm.numero_arete?.trim() || null,
      nombre: this.animalForm.nombre?.trim() || null,
      fecha_nacimiento: this.animalForm.fecha_nacimiento || null,
      edad_estimada_meses: this.animalForm.edad_estimada_meses ? Number(this.animalForm.edad_estimada_meses) : null,
      peso_inicial: this.animalForm.peso_inicial ? Number(this.animalForm.peso_inicial) : null,
      madre_id: this.animalForm.madre_id ? Number(this.animalForm.madre_id) : null,
      padre_id: this.animalForm.padre_id ? Number(this.animalForm.padre_id) : null,
      observaciones: this.animalForm.observaciones?.trim() || null
    };

    this.loading.set(true);
    if (this.isEditingAnimal()) {
      const animalId = this.editingAnimalId()!;
      const updatePayload: AnimalUpdatePayload = {
        ...payload,
        motivo_cambio_arete: this.animalForm.motivo_cambio_arete?.trim() || null
      };

      this.dataService.actualizarAnimal(animalId, updatePayload).subscribe({
        next: (updated) => {
          this.loading.set(false);
          this.toast.success(`Animal ${updated.codigo_interno} actualizado correctamente.`);
          this.showAnimalModal.set(false);
          this.cargarDatos();
          if (this.showPerfilModal() && this.selectedAnimalPerfil()?.animal.id === animalId) {
            this.verPerfilAnimal(animalId);
          }
        },
        error: (err) => {
          this.loading.set(false);
          this.toast.error('Error al actualizar animal: ' + (err.error?.detail || err.message));
        }
      });
    } else {
      this.dataService.crearAnimal(payload).subscribe({
        next: (created) => {
          this.loading.set(false);
          this.toast.success(`Animal registrado con código ${created.codigo_interno}.`);
          this.showAnimalModal.set(false);
          this.cargarDatos();
        },
        error: (err) => {
          this.loading.set(false);
          this.toast.error('Error al registrar animal: ' + (err.error?.detail || err.message));
        }
      });
    }
  }

  // ==========================================
  // PESAJE
  // ==========================================
  abrirModalPesaje(animal: Animal): void {
    this.targetAnimalPesaje.set(animal);
    this.pesajeForm = {
      fecha_pesaje: this.getTodayDate(),
      peso: animal.peso_actual || 0,
      notas: ''
    };
    this.showPesajeModal.set(true);
  }

  guardarPesaje(): void {
    const animal = this.targetAnimalPesaje();
    if (!animal) return;

    if (!this.pesajeForm.fecha_pesaje || !this.pesajeForm.peso || this.pesajeForm.peso <= 0) {
      this.toast.error('Ingrese una fecha válida y un peso mayor a cero.');
      return;
    }

    this.loading.set(true);
    this.dataService.registrarPesaje(animal.id, {
      fecha_pesaje: this.pesajeForm.fecha_pesaje,
      peso: Number(this.pesajeForm.peso),
      notas: this.pesajeForm.notas?.trim() || null
    }).subscribe({
      next: (pesaje) => {
        this.loading.set(false);
        this.toast.success(`Pesaje registrado: ${pesaje.peso} kg.`);
        this.showPesajeModal.set(false);
        this.cargarDatos();
        if (this.showPerfilModal() && this.selectedAnimalPerfil()?.animal.id === animal.id) {
          this.verPerfilAnimal(animal.id);
        }
      },
      error: (err) => {
        this.loading.set(false);
        this.toast.error('Error al registrar pesaje: ' + (err.error?.detail || err.message));
      }
    });
  }

  eliminarPesaje(pesajeId: number): void {
    if (!confirm('¿Está seguro de eliminar este registro de pesaje?')) return;

    this.loading.set(true);
    this.dataService.eliminarPesaje(pesajeId).subscribe({
      next: () => {
        this.loading.set(false);
        this.toast.success('Pesaje eliminado.');
        this.cargarDatos();
        const currentPerfil = this.selectedAnimalPerfil();
        if (currentPerfil) {
          this.verPerfilAnimal(currentPerfil.animal.id);
        }
      },
      error: (err) => {
        this.loading.set(false);
        this.toast.error('Error al eliminar pesaje: ' + (err.error?.detail || err.message));
      }
    });
  }

  // ==========================================
  // NACIMIENTO / PARTO
  // ==========================================
  initNacimientoForm(): NacimientoCreatePayload & { cria_potrero_id?: number | null } {
    const defaultPot = this.potreros()[0];
    return {
      madre_id: 0,
      padre_id: null,
      fecha_parto: this.getTodayDate(),
      condicion_cria: 'VIVA',
      observaciones: '',
      cria_tipo_ganado: 'BOVINO',
      cria_raza: 'NELORE',
      cria_sexo: 'HEMBRA',
      cria_peso_nacer: null,
      cria_numero_arete: '',
      cria_potrero_id: defaultPot?.id || null,
      cria_ubicacion: defaultPot?.nombre || 'Potrero 1'
    };
  }

  onCriaPotreroSeleccionado(potId: any): void {
    const idNum = Number(potId);
    const pot = this.potreros().find(p => p.id === idNum);
    if (pot) {
      this.nacimientoForm.cria_potrero_id = pot.id;
      this.nacimientoForm.cria_ubicacion = pot.nombre;
    }
  }

  onMadreSeleccionada(): void {
    const madre = this.madresDisponibles().find(m => m.id === Number(this.nacimientoForm.madre_id));
    if (madre) {
      if (madre.raza) this.nacimientoForm.cria_raza = madre.raza;
      if (madre.potrero_id) {
        this.nacimientoForm.cria_potrero_id = madre.potrero_id;
        this.nacimientoForm.cria_ubicacion = madre.ubicacion;
      }
    }
  }

  abrirModalNacimiento(): void {
    this.nacimientoForm = this.initNacimientoForm();
    this.showNacimientoModal.set(true);
  }

  guardarNacimiento(): void {
    if (!this.nacimientoForm.madre_id || !this.nacimientoForm.fecha_parto) {
      this.toast.error('Debe seleccionar a la madre y la fecha del parto.');
      return;
    }

    const payload: NacimientoCreatePayload = {
      ...this.nacimientoForm,
      madre_id: Number(this.nacimientoForm.madre_id),
      padre_id: this.nacimientoForm.padre_id ? Number(this.nacimientoForm.padre_id) : null,
      cria_peso_nacer: this.nacimientoForm.cria_peso_nacer ? Number(this.nacimientoForm.cria_peso_nacer) : null,
      cria_numero_arete: this.nacimientoForm.cria_numero_arete?.trim() || null,
      cria_potrero_id: this.nacimientoForm.cria_potrero_id ? Number(this.nacimientoForm.cria_potrero_id) : null,
      observaciones: this.nacimientoForm.observaciones?.trim() || null
    };

    this.loading.set(true);
    this.dataService.crearNacimiento(payload).subscribe({
      next: (nac) => {
        this.loading.set(false);
        const comp = nac.codigo_parto || (nac as any).numero_comprobante || '';
        this.toast.success(`Parto ${comp} registrado exitosamente.`);
        this.showNacimientoModal.set(false);
        this.cargarDatos();
        this.cargarNacimientos();
      },
      error: (err) => {
        this.loading.set(false);
        this.toast.error('Error al registrar parto: ' + (err.error?.detail || err.message));
      }
    });
  }

  // ==========================================
  // COMPRA DE GANADO
  // ==========================================
  abrirModalCompra(): void {
    this.compraCabecera = {
      proveedor: '',
      fecha_compra: this.getTodayDate(),
      numero_documento: '',
      costos_adicionales: 0,
      costo_transporte: 0,
      observaciones: ''
    };
    this.compraDetalles = [this.crearItemCompraVacio()];
    this.showCompraModal.set(true);
  }

  crearItemCompraVacio(): CompraItemForm {
    const defaultPot = this.potreros()[0];
    return {
      tipo_ganado: 'BOVINO',
      raza: 'NELORE',
      sexo: 'HEMBRA',
      fecha_nacimiento: '',
      edad_estimada_meses: 12,
      numero_arete: '',
      peso: 250,
      precio_compra: 3500,
      modalidad_precio: 'POR_ANIMAL',
      potrero_id: defaultPot?.id || null,
      ubicacion: defaultPot?.nombre || 'Potrero 1',
      observaciones: ''
    };
  }

  onCompraItemPotreroChange(item: CompraItemForm, potId: any): void {
    const idNum = Number(potId);
    const pot = this.potreros().find(p => p.id === idNum);
    if (pot) {
      item.potrero_id = pot.id;
      item.ubicacion = pot.nombre;
    }
  }

  aplicarPotreroMasivo(): void {
    const potId = this.potreroMasivoCompra();
    if (!potId) return;
    const pot = this.potreros().find(p => p.id === Number(potId));
    if (!pot) return;
    this.compraDetalles.forEach(d => {
      d.potrero_id = pot.id;
      d.ubicacion = pot.nombre;
    });
    this.toast.info(`Se asignó '${pot.nombre}' a todas las filas de la compra.`);
  }

  agregarFilaCompra(): void {
    this.compraDetalles.push(this.crearItemCompraVacio());
  }

  removerFilaCompra(index: number): void {
    if (this.compraDetalles.length <= 1) {
      this.toast.error('La compra debe contener al menos un animal.');
      return;
    }
    this.compraDetalles.splice(index, 1);
  }

  guardarCompra(): void {
    if (!this.compraCabecera.proveedor.trim()) {
      this.toast.error('Ingrese el nombre del proveedor.');
      return;
    }
    if (this.compraDetalles.length === 0) {
      this.toast.error('Agregue al menos un animal a la compra.');
      return;
    }

    const payload: CompraGanadoCreatePayload = {
      proveedor: this.compraCabecera.proveedor.trim(),
      fecha_compra: this.compraCabecera.fecha_compra,
      numero_documento: this.compraCabecera.numero_documento.trim() || null,
      costos_adicionales: Number(this.compraCabecera.costos_adicionales) || 0,
      costo_transporte: Number(this.compraCabecera.costo_transporte) || 0,
      observaciones: this.compraCabecera.observaciones.trim() || null,
      detalles: this.compraDetalles.map(d => ({
        tipo_ganado: d.tipo_ganado,
        raza: d.raza,
        sexo: d.sexo,
        fecha_nacimiento: d.fecha_nacimiento || null,
        edad_estimada_meses: d.edad_estimada_meses ? Number(d.edad_estimada_meses) : null,
        numero_arete: d.numero_arete?.trim() || null,
        peso: d.peso ? Number(d.peso) : null,
        precio_compra: Number(d.precio_compra) || 0,
        modalidad_precio: d.modalidad_precio,
        potrero_id: d.potrero_id ? Number(d.potrero_id) : null,
        ubicacion: d.ubicacion,
        observaciones: d.observaciones?.trim() || null
      }))
    };

    this.loading.set(true);
    this.dataService.crearCompraGanado(payload).subscribe({
      next: (cmp) => {
        this.loading.set(false);
        this.toast.success(`Compra ${cmp.numero_comprobante} registrada (${cmp.cantidad_cabezas} cabezas).`);
        this.showCompraModal.set(false);
        this.cargarDatos();
        this.cargarCompras();
      },
      error: (err) => {
        this.loading.set(false);
        this.toast.error('Error al registrar compra: ' + (err.error?.detail || err.message));
      }
    });
  }

  // ==========================================
  // VENTA DE GANADO
  // ==========================================
  abrirModalVenta(): void {
    this.ventaCabecera = {
      cliente: '',
      fecha_venta: this.getTodayDate(),
      modalidad_venta: 'POR_ANIMAL',
      metodo_pago: 'EFECTIVO',
      costo_transporte: 0,
      descuento: 0,
      numero_documento: '',
      observaciones: ''
    };
    this.ventaItems = [];
    this.showVentaModal.set(true);
  }

  toggleAnimalEnVenta(animal: Animal): void {
    if (!animal.numero_arete || animal.numero_arete.trim() === '') {
      this.toast.error('Regla RF-010: No se puede vender un animal sin número de arete oficial.');
      return;
    }

    const index = this.ventaItems.findIndex(i => i.animal_id === animal.id);
    if (index >= 0) {
      this.ventaItems.splice(index, 1);
    } else {
      this.ventaItems.push({
        animal_id: animal.id,
        animal: animal,
        precio: 4000,
        modalidad_precio: this.ventaCabecera.modalidad_venta
      });
    }
  }

  isAnimalSeleccionadoVenta(animalId: number): boolean {
    return this.ventaItems.some(i => i.animal_id === animalId);
  }

  guardarVenta(): void {
    if (!this.ventaCabecera.cliente.trim()) {
      this.toast.error('Ingrese el nombre del cliente o comprador.');
      return;
    }
    if (this.ventaItems.length === 0) {
      this.toast.error('Seleccione al menos un animal con arete para la venta.');
      return;
    }

    const payload: VentaGanadoCreatePayload = {
      cliente: this.ventaCabecera.cliente.trim(),
      fecha_venta: this.ventaCabecera.fecha_venta,
      modalidad_venta: this.ventaCabecera.modalidad_venta,
      metodo_pago: this.ventaCabecera.metodo_pago,
      costo_transporte: Number(this.ventaCabecera.costo_transporte) || 0,
      descuento: Number(this.ventaCabecera.descuento) || 0,
      numero_documento: this.ventaCabecera.numero_documento.trim() || null,
      observaciones: this.ventaCabecera.observaciones.trim() || null,
      animales: this.ventaItems.map(it => ({
        animal_id: it.animal_id,
        precio: Number(it.precio) || 0,
        modalidad_precio: it.modalidad_precio || this.ventaCabecera.modalidad_venta
      }))
    };

    this.loading.set(true);
    this.dataService.crearVentaGanado(payload).subscribe({
      next: (vnt) => {
        this.loading.set(false);
        this.toast.success(`Venta ${vnt.numero_comprobante} registrada exitosamente.`);
        this.showVentaModal.set(false);
        this.cargarDatos();
        this.cargarVentas();
      },
      error: (err) => {
        this.loading.set(false);
        this.toast.error('Error al registrar venta: ' + (err.error?.detail || err.message));
      }
    });
  }

  // ==========================================
  // BAJA DE GANADO
  // ==========================================
  abrirModalBaja(): void {
    this.bajaForm = {
      animal_id: 0,
      tipo_baja: 'MUERTE',
      fecha_baja: this.getTodayDate(),
      causa_diagnostico: '',
      necropsia_realizada: false,
      destino_cuerpo: 'ENTIERRO',
      valor_estimado_perdida: 0,
      observaciones: ''
    };
    this.showBajaModal.set(true);
  }

  guardarBaja(): void {
    if (!this.bajaForm.animal_id || this.bajaForm.animal_id === 0) {
      this.toast.error('Seleccione el animal al que se dará de baja.');
      return;
    }
    if (!this.bajaForm.fecha_baja) {
      this.toast.error('Ingrese la fecha de la baja.');
      return;
    }

    const payload: BajaGanadoCreatePayload = {
      ...this.bajaForm,
      animal_id: Number(this.bajaForm.animal_id),
      causa_diagnostico: this.bajaForm.causa_diagnostico?.trim() || null,
      destino_cuerpo: this.bajaForm.destino_cuerpo?.trim() || null,
      valor_estimado_perdida: Number(this.bajaForm.valor_estimado_perdida) || 0,
      observaciones: this.bajaForm.observaciones?.trim() || null
    };

    this.loading.set(true);
    this.dataService.crearBajaGanado(payload).subscribe({
      next: (baj) => {
        this.loading.set(false);
        this.toast.success(`Acta de baja ${baj.numero_acta} registrada.`);
        this.showBajaModal.set(false);
        this.cargarDatos();
        this.cargarBajas();
      },
      error: (err) => {
        this.loading.set(false);
        this.toast.error('Error al registrar baja: ' + (err.error?.detail || err.message));
      }
    });
  }

  // ==========================================
  // ANULACIONES
  // ==========================================
  abrirModalAnular(tipo: 'VENTA' | 'BAJA', id: number): void {
    this.anularTipo.set(tipo);
    this.anularId.set(id);
    this.anularMotivo.set('');
    this.showAnularModal.set(true);
  }

  confirmarAnulacion(): void {
    const id = this.anularId();
    const motivo = this.anularMotivo().trim();
    if (!id || !motivo) {
      this.toast.error('Debe ingresar el motivo de la anulación.');
      return;
    }

    this.loading.set(true);
    if (this.anularTipo() === 'VENTA') {
      this.dataService.anularVentaGanado(id, motivo).subscribe({
        next: () => {
          this.loading.set(false);
          this.toast.success('Venta anulada. Los animales han retornado al estado ACTIVO.');
          this.showAnularModal.set(false);
          this.cargarDatos();
          this.cargarVentas();
        },
        error: (err) => {
          this.loading.set(false);
          this.toast.error('Error al anular venta: ' + (err.error?.detail || err.message));
        }
      });
    } else {
      this.dataService.anularBajaGanado(id, motivo).subscribe({
        next: () => {
          this.loading.set(false);
          this.toast.success('Baja anulada. El animal ha retornado al estado ACTIVO.');
          this.showAnularModal.set(false);
          this.cargarDatos();
          this.cargarBajas();
        },
        error: (err) => {
          this.loading.set(false);
          this.toast.error('Error al anular baja: ' + (err.error?.detail || err.message));
        }
      });
    }
  }

  // Helpers
  getTodayDate(): string {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, '0');
    const d = String(now.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }
}
