import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DataService } from '../../core/services/data.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import {
  ProductoAlmacen,
  ProductoAlmacenDetalle,
  CompraAlmacen,
  MovimientoAlmacen,
  GastoMenor,
  ReporteAlmacenResumen,
  ReporteGastosResumen,
  Trabajador,
  Area,
} from '../../core/models/types';

@Component({
  selector: 'app-inventario',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './inventario.component.html',
  styleUrls: ['./inventario.component.css']
})
export class InventarioComponent implements OnInit {
  private dataService = inject(DataService);
  public auth = inject(AuthService);
  private toast = inject(ToastService);

  // Estados de navegación
  loading = signal<boolean>(false);
  activeTab = signal<'almacen' | 'gastos' | 'reportes'>('almacen');
  activeDetailSubTab = signal<'compras' | 'movimientos'>('compras');

  // Datos de Almacén
  productos = signal<ProductoAlmacen[]>([]);
  filtroBusquedaAlmacen = signal<string>('');
  filtroEstadoStock = signal<string>('TODOS');
  filtroUnidadControl = signal<string>('TODOS');
  reporteAlmacen = signal<ReporteAlmacenResumen | null>(null);

  // Producto seleccionado para ficha detallada
  productoDetalle = signal<ProductoAlmacenDetalle | null>(null);
  showDetalleModal = signal<boolean>(false);

  // Datos de Gastos Menores
  gastos = signal<GastoMenor[]>([]);
  filtroBusquedaGastos = signal<string>('');
  filtroAreaGastos = signal<number | null>(null);
  filtroEstadoGastos = signal<string>('TODOS');
  reporteGastos = signal<ReporteGastosResumen | null>(null);

  // Catálogos
  trabajadores = signal<Trabajador[]>([]);
  areas = signal<Area[]>([]);

  // Modales
  showNuevoProductoModal = signal<boolean>(false);
  showNuevaCompraModal = signal<boolean>(false);
  showNuevaSalidaModal = signal<boolean>(false);
  showAjusteModal = signal<boolean>(false);
  showNuevoGastoModal = signal<boolean>(false);
  showAnulacionModal = signal<boolean>(false);

  // Autocompletado para compras posteriores
  searchAutocompleteQuery = signal<string>('');
  autocompleteResults = signal<any[]>([]);
  selectedProductoCompra = signal<any | null>(null);

  // Selector con búsqueda para Trabajador Receptor en Salidas
  searchTrabajadorQuery = signal<string>('');
  showTrabajadorDropdown = signal<boolean>(false);
  selectedTrabajadorSalida = signal<Trabajador | null>(null);

  filteredTrabajadoresSalida = computed(() => {
    const list = this.trabajadores();
    const query = this.searchTrabajadorQuery().trim();
    if (!query) {
      return list.slice(0, 30);
    }

    const normalize = (val: string) =>
      (val || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase();

    const normalizedQuery = normalize(query);
    const terms = normalizedQuery.split(/\s+/).filter(Boolean);

    return list.filter(t => {
      const fullText = normalize(
        `${t.nombres || ''} ${t.apellidos || ''} ${t.apellidos || ''} ${t.nombres || ''} ${t.ci || ''} ${t.cargo || ''} ${t.area?.nombre || ''}`
      );
      return terms.every(term => fullText.includes(term));
    });
  });

  // Formulario: Nuevo Producto con Primera Compra
  nuevoProductoForm = {
    nombre: '',
    stock_minimo: 10,
    descripcion: '',
    foto: '' as string,
    cantidad_comprada: null as number | null,
    precio_total: null as number | null,
    fecha_compra: new Date().toISOString().substring(0, 10),
    proveedor: '',
  };

  // Formulario: Compra Posterior
  compraPosteriorForm = {
    almacen_id: null as number | null,
    cantidad_comprada: null as number | null,
    precio_total: null as number | null,
    fecha_compra: new Date().toISOString().substring(0, 10),
    proveedor: '',
  };

  // Formulario: Salida / Entrega
  salidaForm = {
    almacen_id: null as number | null,
    cantidad: null as number | null,
    trabajador_id: null as number | null,
    area_id: null as number | null,
    motivo: '',
    vehiculo_maquinaria: '',
    fecha_movimiento: new Date().toISOString().substring(0, 10),
    observaciones: ''
  };

  // Formulario: Ajuste de Stock
  ajusteForm = {
    almacen_id: null as number | null,
    tipo_ajuste: 'POSITIVO' as 'POSITIVO' | 'NEGATIVO',
    cantidad: null as number | null,
    motivo: '',
    observaciones: ''
  };

  // Formulario: Gasto Menor
  gastoForm = {
    id: null as number | null,
    nombre: '',
    descripcion: '',
    foto_comprobante: '' as string,
    importe_total: null as number | null,
    fecha_gasto: new Date().toISOString().substring(0, 10),
    area_id: null as number | null,
    trabajador_responsable_id: null as number | null,
    metodo_pago: 'EFECTIVO',
    proveedor: '',
    numero_comprobante_fiscal: ''
  };

  // Datos para Anulación Auditada
  anulacionData = signal<{
    tipo: 'MOVIMIENTO' | 'GASTO';
    id: number;
    comprobante: string;
    descripcion: string;
    motivo: string;
  } | null>(null);

  // Unidades de medida sugeridas
  unidadesControlSugeridas = [
    'Litros',
    'Kilogramos',
    'Gramos',
    'Unidades',
    'Metros',
    'Metros cúbicos',
    'Rollos',
    'Barriles'
  ];

  ngOnInit(): void {
    this.cargarCatalogos();
    this.cargarProductosAlmacen();
    this.cargarGastosMenores();
    this.cargarReportes();
  }

  // ==========================================
  // CARGA DE DATOS
  // ==========================================

  cargarCatalogos(): void {
    this.dataService.getTrabajadores(undefined, undefined, true).subscribe({
      next: (data) => this.trabajadores.set(data),
      error: () => {}
    });
    this.dataService.getAreas().subscribe({
      next: (data) => this.areas.set(data),
      error: () => {}
    });
  }

  cargarProductosAlmacen(): void {
    this.loading.set(true);
    this.dataService.getProductosAlmacen(
      this.filtroBusquedaAlmacen(),
      this.filtroEstadoStock(),
      this.filtroUnidadControl() !== 'TODOS' ? this.filtroUnidadControl() : undefined
    ).subscribe({
      next: (prods) => {
        this.productos.set(prods);
        this.loading.set(false);
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al cargar productos de almacén');
        this.loading.set(false);
      }
    });
  }

  cargarGastosMenores(): void {
    this.dataService.getGastosMenores({
      busqueda: this.filtroBusquedaGastos(),
      area_id: this.filtroAreaGastos() || undefined,
      estado: this.filtroEstadoGastos() !== 'TODOS' ? this.filtroEstadoGastos() : undefined
    }).subscribe({
      next: (data) => this.gastos.set(data),
      error: () => {}
    });
  }

  cargarReportes(): void {
    this.dataService.getReporteAlmacen().subscribe({
      next: (rep) => this.reporteAlmacen.set(rep),
      error: () => {}
    });
    this.dataService.getReporteGastos().subscribe({
      next: (rep) => this.reporteGastos.set(rep),
      error: () => {}
    });
  }

  // ==========================================
  // PRODUCTOS: GESTIÓN Y FICHA DETALLADA
  // ==========================================

  abrirDetalleProducto(p: ProductoAlmacen): void {
    this.loading.set(true);
    this.dataService.getProductoDetalle(p.id).subscribe({
      next: (det) => {
        this.productoDetalle.set(det);
        this.activeDetailSubTab.set('compras');
        this.showDetalleModal.set(true);
        this.loading.set(false);
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al obtener detalle del producto');
        this.loading.set(false);
      }
    });
  }

  abrirModalNuevoProducto(): void {
    this.nuevoProductoForm = {
      nombre: '',
      stock_minimo: 10,
      descripcion: '',
      foto: '',
      cantidad_comprada: null,
      precio_total: null,
      fecha_compra: new Date().toISOString().substring(0, 10),
      proveedor: '',
    };
    this.showNuevoProductoModal.set(true);
  }

  calcularIngresoPrimeraCompra(): { cantidadControl: number; precioUnitario: number } {
    const cant = Number(this.nuevoProductoForm.cantidad_comprada) || 0;
    const total = Number(this.nuevoProductoForm.precio_total) || 0;
    const cantidadControl = cant;
    const precioUnitario = cantidadControl > 0 ? Math.round((total / cantidadControl) * 100) / 100 : 0;
    return { cantidadControl, precioUnitario };
  }

  guardarNuevoProducto(): void {
    const f = this.nuevoProductoForm;
    if (!f.nombre.trim()) {
      this.toast.warning('Ingresa el nombre del producto.');
      return;
    }
    if (!f.cantidad_comprada || f.cantidad_comprada <= 0) {
      this.toast.warning('La cantidad de la primera compra debe ser mayor a cero.');
      return;
    }
    if (f.precio_total === null || f.precio_total < 0) {
      this.toast.warning('Ingresa el precio total de la compra.');
      return;
    }

    this.loading.set(true);
    const payload = {
      nombre: f.nombre.trim(),
      stock_minimo: Number(f.stock_minimo) || 0,
      descripcion: f.descripcion.trim() || null,
      foto: f.foto || null,
      unidad_control: 'Unidades',
      cantidad_comprada: Number(f.cantidad_comprada),
      unidad_compra: 'Unidades',
      equivalencia_unidad: 1,
      precio_total: Number(f.precio_total),
      fecha_compra: f.fecha_compra,
      proveedor: f.proveedor.trim() || null,
      numero_factura: null,
      observaciones: null
    };

    this.dataService.crearProductoConPrimeraCompra(payload).subscribe({
      next: (prod) => {
        this.toast.success(`Producto registrado con éxito: ${prod.codigo} - ${prod.nombre}`);
        this.showNuevoProductoModal.set(false);
        this.loading.set(false);
        this.cargarProductosAlmacen();
        this.cargarReportes();
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al registrar producto');
        this.loading.set(false);
      }
    });
  }

  // ==========================================
  // COMPRAS POSTERIORES (PRODUCTOS EXISTENTES)
  // ==========================================

  abrirModalNuevaCompra(productoInicial?: ProductoAlmacen): void {
    this.searchAutocompleteQuery.set('');
    this.autocompleteResults.set([]);
    this.compraPosteriorForm = {
      almacen_id: productoInicial ? productoInicial.id : null,
      cantidad_comprada: null,
      precio_total: null,
      fecha_compra: new Date().toISOString().substring(0, 10),
      proveedor: '',
    };
    if (productoInicial) {
      this.selectedProductoCompra.set(productoInicial);
    } else {
      this.selectedProductoCompra.set(null);
    }
    this.showNuevaCompraModal.set(true);
  }

  onSearchAutocomplete(term: string): void {
    this.searchAutocompleteQuery.set(term);
    if (!term || term.trim().length < 1) {
      this.autocompleteResults.set([]);
      return;
    }
    this.dataService.buscarProductosAlmacen(term.trim()).subscribe({
      next: (results) => this.autocompleteResults.set(results),
      error: () => {}
    });
  }

  seleccionarProductoParaCompra(p: any): void {
    this.selectedProductoCompra.set(p);
    this.compraPosteriorForm.almacen_id = p.id;
    this.autocompleteResults.set([]);
    this.searchAutocompleteQuery.set(`${p.codigo} - ${p.nombre}`);
  }

  calcularIngresoCompraPosterior(): { cantidadControl: number; precioUnitario: number; variacion: number | null } {
    const cant = Number(this.compraPosteriorForm.cantidad_comprada) || 0;
    const total = Number(this.compraPosteriorForm.precio_total) || 0;
    const cantidadControl = cant;
    const precioUnitario = cantidadControl > 0 ? Math.round((total / cantidadControl) * 100) / 100 : 0;

    let variacion = null;
    const p = this.selectedProductoCompra();
    if (p && p.precio_ultima_compra && Number(p.precio_ultima_compra) > 0 && precioUnitario > 0) {
      const prev = Number(p.precio_ultima_compra);
      variacion = Math.round(((precioUnitario - prev) / prev) * 10000) / 100;
    }
    return { cantidadControl, precioUnitario, variacion };
  }

  calcularNuevoStockPosterior(): number {
    const actual = Number(this.selectedProductoCompra()?.stock_actual || 0);
    const ingreso = this.calcularIngresoCompraPosterior().cantidadControl;
    return Math.round((actual + ingreso) * 100) / 100;
  }

  guardarCompraPosterior(): void {
    const f = this.compraPosteriorForm;
    if (!f.almacen_id) {
      this.toast.warning('Selecciona el producto que se está comprando.');
      return;
    }
    if (!f.cantidad_comprada || f.cantidad_comprada <= 0) {
      this.toast.warning('La cantidad comprada debe ser mayor a cero.');
      return;
    }
    if (f.precio_total === null || f.precio_total < 0) {
      this.toast.warning('Ingresa el precio total de la compra.');
      return;
    }

    this.loading.set(true);
    const payload = {
      almacen_id: f.almacen_id,
      cantidad_comprada: Number(f.cantidad_comprada),
      unidad_compra: 'Unidades',
      equivalencia_unidad: 1,
      precio_total: Number(f.precio_total),
      fecha_compra: f.fecha_compra,
      proveedor: f.proveedor.trim() || null,
      numero_factura: null,
      observaciones: null
    };

    this.dataService.registrarCompraPosterior(payload).subscribe({
      next: (compra) => {
        this.toast.success(`Compra registrada exitosamente: ${compra.numero_comprobante}`);
        this.showNuevaCompraModal.set(false);
        this.loading.set(false);
        this.cargarProductosAlmacen();
        this.cargarReportes();
        if (this.showDetalleModal() && this.productoDetalle()?.id === f.almacen_id) {
          this.abrirDetalleProducto(this.productoDetalle()!);
        }
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al registrar compra posterior');
        this.loading.set(false);
      }
    });
  }

  // ==========================================
  // SALIDAS / ENTREGAS DEL ALMACÉN
  // ==========================================

  abrirModalSalida(producto?: ProductoAlmacen): void {
    const primerTrabajador = this.trabajadores()[0] || null;
    this.salidaForm = {
      almacen_id: producto ? producto.id : (this.productos()[0]?.id || null),
      cantidad: null,
      trabajador_id: primerTrabajador ? primerTrabajador.id : null,
      area_id: primerTrabajador?.area_id || this.areas()[0]?.id || null,
      motivo: '',
      vehiculo_maquinaria: '',
      fecha_movimiento: new Date().toISOString().substring(0, 10),
      observaciones: ''
    };
    if (primerTrabajador) {
      this.selectedTrabajadorSalida.set(primerTrabajador);
      this.searchTrabajadorQuery.set(`${primerTrabajador.nombres} ${primerTrabajador.apellidos}${primerTrabajador.ci ? ' (CI: ' + primerTrabajador.ci + ')' : ''}`);
    } else {
      this.selectedTrabajadorSalida.set(null);
      this.searchTrabajadorQuery.set('');
    }
    this.showTrabajadorDropdown.set(false);
    this.showNuevaSalidaModal.set(true);
  }

  onSearchTrabajador(term: string): void {
    this.searchTrabajadorQuery.set(term);
    this.showTrabajadorDropdown.set(true);
    if (this.selectedTrabajadorSalida()) {
      const current = this.selectedTrabajadorSalida()!;
      const expectedName = `${current.nombres} ${current.apellidos}`.toLowerCase();
      if (!term.toLowerCase().includes(expectedName)) {
        this.selectedTrabajadorSalida.set(null);
        this.salidaForm.trabajador_id = null;
      }
    }
  }

  seleccionarTrabajadorSalida(t: Trabajador): void {
    this.selectedTrabajadorSalida.set(t);
    this.salidaForm.trabajador_id = t.id;
    this.searchTrabajadorQuery.set(`${t.nombres} ${t.apellidos}${t.ci ? ' (CI: ' + t.ci + ')' : ''}`);
    this.showTrabajadorDropdown.set(false);
    if (t.area_id) {
      this.salidaForm.area_id = t.area_id;
    }
  }

  limpiarTrabajadorSalida(): void {
    this.selectedTrabajadorSalida.set(null);
    this.salidaForm.trabajador_id = null;
    this.searchTrabajadorQuery.set('');
    this.showTrabajadorDropdown.set(true);
  }

  onTrabajadorBlur(): void {
    setTimeout(() => {
      this.showTrabajadorDropdown.set(false);
    }, 200);
  }

  getProductoSeleccionadoSalida(): ProductoAlmacen | undefined {
    return this.productos().find(p => p.id === Number(this.salidaForm.almacen_id));
  }

  guardarSalida(): void {
    const f = this.salidaForm;
    if (!f.almacen_id) {
      this.toast.warning('Selecciona el producto a retirar.');
      return;
    }
    const prod = this.getProductoSeleccionadoSalida();
    if (!prod) {
      this.toast.error('Producto no encontrado');
      return;
    }
    if (!f.cantidad || f.cantidad <= 0) {
      this.toast.warning('Ingresa una cantidad mayor a cero.');
      return;
    }
    if (f.cantidad > prod.stock_actual) {
      this.toast.error(`Stock insuficiente. Existencias disponibles: ${prod.stock_actual} ${prod.unidad_control}. Cantidad solicitada: ${f.cantidad} ${prod.unidad_control}.`);
      return;
    }
    if (!f.trabajador_id) {
      this.toast.warning('Selecciona al trabajador que recibe el producto.');
      return;
    }
    if (!f.area_id) {
      this.toast.warning('Selecciona el área de destino.');
      return;
    }
    if (!f.motivo.trim()) {
      this.toast.warning('Ingresa el motivo de la salida.');
      return;
    }

    this.loading.set(true);
    const payload = {
      almacen_id: Number(f.almacen_id),
      cantidad: Number(f.cantidad),
      trabajador_id: Number(f.trabajador_id),
      area_id: Number(f.area_id),
      motivo: f.motivo.trim(),
      vehiculo_maquinaria: f.vehiculo_maquinaria.trim() || null,
      fecha_movimiento: f.fecha_movimiento,
      observaciones: f.observaciones.trim() || null
    };

    this.dataService.registrarSalidaAlmacen(payload).subscribe({
      next: (mov) => {
        this.toast.success(`Salida registrada con éxito: ${mov.numero_comprobante} (-${mov.cantidad_salida} ${prod.unidad_control})`);
        this.showNuevaSalidaModal.set(false);
        this.loading.set(false);
        this.cargarProductosAlmacen();
        this.cargarReportes();
        if (this.showDetalleModal() && this.productoDetalle()?.id === f.almacen_id) {
          this.abrirDetalleProducto(this.productoDetalle()!);
        }
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al registrar salida de almacén');
        this.loading.set(false);
      }
    });
  }

  // ==========================================
  // AJUSTES DE INVENTARIO AUDITADOS
  // ==========================================

  abrirModalAjuste(producto?: ProductoAlmacen): void {
    this.ajusteForm = {
      almacen_id: producto ? producto.id : (this.productos()[0]?.id || null),
      tipo_ajuste: 'POSITIVO',
      cantidad: null,
      motivo: '',
      observaciones: ''
    };
    this.showAjusteModal.set(true);
  }

  guardarAjuste(): void {
    const f = this.ajusteForm;
    if (!f.almacen_id || !f.cantidad || f.cantidad <= 0) {
      this.toast.warning('Indica producto y cantidad de ajuste válida.');
      return;
    }
    if (!f.motivo.trim()) {
      this.toast.warning('El motivo del ajuste es obligatorio.');
      return;
    }

    this.loading.set(true);
    const payload = {
      almacen_id: Number(f.almacen_id),
      tipo_ajuste: f.tipo_ajuste,
      cantidad: Number(f.cantidad),
      motivo: f.motivo.trim(),
      observaciones: f.observaciones.trim() || null
    };

    this.dataService.registrarAjusteStock(payload).subscribe({
      next: (mov) => {
        this.toast.success(`Ajuste de inventario aplicado: ${mov.numero_comprobante}`);
        this.showAjusteModal.set(false);
        this.loading.set(false);
        this.cargarProductosAlmacen();
        this.cargarReportes();
        if (this.showDetalleModal() && this.productoDetalle()?.id === f.almacen_id) {
          this.abrirDetalleProducto(this.productoDetalle()!);
        }
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al aplicar ajuste');
        this.loading.set(false);
      }
    });
  }

  // ==========================================
  // ANULACIÓN DE MOVIMIENTOS
  // ==========================================

  solicitarAnulacionMovimiento(mov: MovimientoAlmacen): void {
    this.anulacionData.set({
      tipo: 'MOVIMIENTO',
      id: mov.id,
      comprobante: mov.numero_comprobante,
      descripcion: `${mov.tipo_movimiento} de ${mov.cantidad} unidades (${mov.motivo})`,
      motivo: ''
    });
    this.showAnulacionModal.set(true);
  }

  confirmarAnulacion(): void {
    const d = this.anulacionData();
    if (!d || !d.motivo.trim()) {
      this.toast.warning('Debes ingresar un motivo de anulación justificatorio.');
      return;
    }

    this.loading.set(true);
    this.showAnulacionModal.set(false);

    if (d.tipo === 'MOVIMIENTO') {
      this.dataService.anularMovimientoAlmacen(d.id, d.motivo.trim()).subscribe({
        next: (res) => {
          this.toast.success(res.mensaje || 'Movimiento anulado correctamente');
          this.loading.set(false);
          this.cargarProductosAlmacen();
          this.cargarReportes();
          if (this.showDetalleModal() && this.productoDetalle()) {
            this.abrirDetalleProducto(this.productoDetalle()!);
          }
        },
        error: (err) => {
          this.toast.error(err?.error?.detail || 'Error al anular movimiento');
          this.loading.set(false);
        }
      });
    } else {
      this.dataService.anularGastoMenor(d.id, d.motivo.trim()).subscribe({
        next: (res) => {
          this.toast.success(res.mensaje || 'Gasto menor anulado correctamente');
          this.loading.set(false);
          this.cargarGastosMenores();
          this.cargarReportes();
        },
        error: (err) => {
          this.toast.error(err?.error?.detail || 'Error al anular gasto menor');
          this.loading.set(false);
        }
      });
    }
  }

  // ==========================================
  // GASTOS MENORES
  // ==========================================

  abrirModalNuevoGasto(): void {
    this.gastoForm = {
      id: null,
      nombre: '',
      descripcion: '',
      foto_comprobante: '',
      importe_total: null,
      fecha_gasto: new Date().toISOString().substring(0, 10),
      area_id: this.areas()[0]?.id || null,
      trabajador_responsable_id: null,
      metodo_pago: 'EFECTIVO',
      proveedor: '',
      numero_comprobante_fiscal: ''
    };
    this.showNuevoGastoModal.set(true);
  }

  guardarGastoMenor(): void {
    const f = this.gastoForm;
    if (!f.nombre.trim()) {
      this.toast.warning('Ingresa el nombre o concepto del gasto.');
      return;
    }
    if (!f.importe_total || f.importe_total <= 0) {
      this.toast.warning('El importe debe ser mayor a cero.');
      return;
    }

    this.loading.set(true);
    const payload = {
      nombre: f.nombre.trim(),
      descripcion: f.descripcion.trim() || null,
      foto_comprobante: f.foto_comprobante || null,
      importe_total: Number(f.importe_total),
      fecha_gasto: f.fecha_gasto,
      area_id: f.area_id ? Number(f.area_id) : null,
      trabajador_responsable_id: f.trabajador_responsable_id ? Number(f.trabajador_responsable_id) : null,
      metodo_pago: f.metodo_pago,
      proveedor: f.proveedor.trim() || null,
      numero_comprobante_fiscal: f.numero_comprobante_fiscal.trim() || null
    };

    this.dataService.crearGastoMenor(payload).subscribe({
      next: (g) => {
        this.toast.success(`Gasto menor registrado: ${g.numero_comprobante} (Bs ${g.importe_total})`);
        this.showNuevoGastoModal.set(false);
        this.loading.set(false);
        this.cargarGastosMenores();
        this.cargarReportes();
      },
      error: (err) => {
        this.toast.error(err?.error?.detail || 'Error al registrar gasto');
        this.loading.set(false);
      }
    });
  }

  solicitarAnulacionGasto(g: GastoMenor): void {
    this.anulacionData.set({
      tipo: 'GASTO',
      id: g.id,
      comprobante: g.numero_comprobante,
      descripcion: `Gasto: '${g.nombre}' por Bs ${g.importe_total}`,
      motivo: ''
    });
    this.showAnulacionModal.set(true);
  }

  // ==========================================
  // CAPTURA DE FOTOS / IMÁGENES (CÁMARA Y ARCHIVOS)
  // ==========================================

  onImageFileSelected(event: any, target: 'producto' | 'gasto'): void {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      this.toast.warning('Por favor selecciona un archivo de imagen válido (JPG, PNG, WEBP).');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      this.toast.warning('La imagen supera el límite de 5 MB. Selecciona una imagen más ligera.');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const base64 = reader.result as string;
      if (target === 'producto') {
        this.nuevoProductoForm.foto = base64;
      } else {
        this.gastoForm.foto_comprobante = base64;
      }
    };
    reader.readAsDataURL(file);
  }

  removerFoto(target: 'producto' | 'gasto'): void {
    if (target === 'producto') {
      this.nuevoProductoForm.foto = '';
    } else {
      this.gastoForm.foto_comprobante = '';
    }
  }

  // ==========================================
  // UTILITARIOS Y HELPERS DE FORMATO
  // ==========================================

  getInitials(name?: string): string {
    if (!name || !name.trim()) return 'U';
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return parts[0].substring(0, 2).toUpperCase();
  }

  formatBs(amount?: number | null): string {
    if (amount === undefined || amount === null) return '0.00';
    return Number(amount).toLocaleString('es-BO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
}
