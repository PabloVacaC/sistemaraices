import {
  Component,
  OnInit,
  AfterViewInit,
  OnDestroy,
  inject,
  signal,
  computed,
  ChangeDetectorRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import * as L from 'leaflet';

import { DataService } from '../../core/services/data.service';
import { AuthService } from '../../core/services/auth.service';
import {
  AreaAgricola,
  CicloAgricola,
  ActividadPreparacion,
  ActividadManejo,
  CosechaRegistro,
  AgriculturaKPIs,
  AreaAgricolaCreatePayload,
  CicloAgricolaCreatePayload,
  SiembraUpdatePayload,
  ActividadManejoCreatePayload,
  CosechaCreatePayload,
} from '../../core/models/types';

@Component({
  selector: 'app-agricultura',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './agricultura.component.html',
  styleUrls: ['./agricultura.component.scss'],
})
export class AgriculturaComponent implements OnInit, AfterViewInit, OnDestroy {
  private dataService = inject(DataService);
  auth = inject(AuthService);
  private cdr = inject(ChangeDetectorRef);

  // Estados de carga
  cargando = signal<boolean>(false);
  guardando = signal<boolean>(false);

  // Datos principales
  kpis = signal<AgriculturaKPIs | null>(null);
  areas = signal<AreaAgricola[]>([]);
  areaSeleccionada = signal<AreaAgricola | null>(null);
  historialCiclos = signal<CicloAgricola[]>([]);

  // Panel lateral (Offcanvas / Drawer)
  drawerAbierto = signal<boolean>(false);
  tabDrawer = signal<'ciclo' | 'actividades' | 'historial' | 'editar'>('ciclo');

  // Modo dibujo de polígono satelital
  modoDibujoActivo = signal<boolean>(false);
  verticesDibujados = signal<L.LatLng[]>([]);
  polygonPreviewLayer: L.Polygon | null = null;
  drawingMarkers: L.Marker[] = [];

  // Modales
  modalCrearAreaAbierto = signal<boolean>(false);
  modalEditarAreaAbierto = signal<boolean>(false);
  modalEliminarAreaAbierto = signal<boolean>(false);
  modalIniciarCicloAbierto = signal<boolean>(false);
  modalSiembraAbierto = signal<boolean>(false);
  modalManejoAbierto = signal<boolean>(false);
  modalCosechaAbierto = signal<boolean>(false);
  modalFinalizarCicloAbierto = signal<boolean>(false);

  // Formularios
  areaForm = {
    id: 0,
    codigo: '',
    nombre: '',
    superficie_ha: 0,
    color_hex: '#10B981',
    observaciones: '',
    poligono_geojson: '',
  };

  cicloForm = {
    cultivo: 'Soya',
    variedad_hibrido: '',
    campana: 'Verano 2025/2026',
    fecha_inicio: this.getFechaHoy(),
    superficie_utilizada_ha: 0,
    observaciones: '',
  };

  siembraForm = {
    cultivo: '',
    variedad_hibrido: '',
    fecha_siembra: this.getFechaHoy(),
    superficie_sembrada_ha: 0,
    observaciones: '',
  };

  manejoForm = {
    fecha: this.getFechaHoy(),
    tipo_actividad: 'FUMIGACION',
    producto_utilizado: '',
    dosis_por_ha: 2,
    superficie_aplicada_ha: 0,
    cantidad_aplicada: 0,
    unidad_medida: 'LT',
    observaciones: '',
  };

  cosechaForm = {
    fecha_cosecha: this.getFechaHoy(),
    fecha_fin_cosecha: '',
    cultivo_cosechado: '',
    superficie_cosechada_ha: 0,
    rendimiento_por_ha: 3,
    cantidad_producida: 0,
    unidad_medida: 'TN',
    observaciones: '',
  };

  // Toast
  toast = signal<{ mensaje: string; tipo: 'success' | 'error' | 'warning' | 'info' } | null>(null);
  private toastTimeout: any;

  // Capa Satelital activa
  capaSatelitalSeleccionada = signal<'google' | 'esri'>('google');

  // Mapa Leaflet
  private map: L.Map | null = null;
  private areasLayerGroup = L.layerGroup();
  private labelsLayerGroup = L.layerGroup();

  private googleHybridLayer = L.tileLayer(
    'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    { maxZoom: 20, attribution: 'Google Satellite Hybrid' }
  );
  private esriSatelliteLayer = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { maxZoom: 19, attribution: 'Esri World Imagery' }
  );
  private esriLabelsLayer = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
    { maxZoom: 19, opacity: 0.85 }
  );

  private readonly defaultCenter: L.LatLngExpression = [-17.921000, -62.246000];
  private readonly defaultZoom: number = 15;

  // Catálogo de cultivos comunes
  cultivosDisponibles = ['Soya', 'Maíz', 'Sorgo', 'Trigo', 'Girasol', 'Chía', 'Sésamo', 'Arroz', 'Pasto / Forraje', 'Otro'];

  // Tipos de actividades de manejo
  tiposManejo = [
    { valor: 'FUMIGACION', etiqueta: 'Fumigación General' },
    { valor: 'HERBICIDA', etiqueta: 'Herbicida (Control Malezas)' },
    { valor: 'INSECTICIDA', etiqueta: 'Insecticida (Plagas)' },
    { valor: 'FUNGICIDA', etiqueta: 'Fungicida (Enfermedades)' },
    { valor: 'FERTILIZACION', etiqueta: 'Fertilización de Base / Suelo' },
    { valor: 'APLICACION_FOLIAR', etiqueta: 'Nutrición / Abono Foliar' },
    { valor: 'OTRO', etiqueta: 'Otro Manejo Agrícola' },
  ];

  // Avance de preparación computado
  progresoPreparacion = computed(() => {
    const ciclo = this.areaSeleccionada()?.ciclo_activo;
    if (!ciclo || !ciclo.actividades_preparacion || ciclo.actividades_preparacion.length === 0) {
      return { total: 0, completadas: 0, porcentaje: 0 };
    }
    const total = ciclo.actividades_preparacion.length;
    const completadas = ciclo.actividades_preparacion.filter((a) => a.completada).length;
    const porcentaje = Math.round((completadas / total) * 100);
    return { total, completadas, porcentaje };
  });

  ngOnInit(): void {
    this.cargarDatosIniciales();
  }

  ngAfterViewInit(): void {
    this.inicializarMapa();
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
    }
  }

  getFechaHoy(): string {
    const d = new Date();
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  mostrarToast(mensaje: string, tipo: 'success' | 'error' | 'warning' | 'info' = 'info'): void {
    if (this.toastTimeout) clearTimeout(this.toastTimeout);
    this.toast.set({ mensaje, tipo });
    this.toastTimeout = setTimeout(() => {
      this.toast.set(null);
    }, 4000);
  }

  // =========================================================================
  // CARGA DE DATOS
  // =========================================================================

  cargarDatosIniciales(): void {
    this.cargando.set(true);
    this.dataService.getAgriculturaKPIs().subscribe({
      next: (k) => this.kpis.set(k),
      error: () => {},
    });

    this.dataService.getAreasAgricolas().subscribe({
      next: (lista) => {
        this.areas.set(lista);
        this.renderizarAreasEnMapa();
        this.cargando.set(false);
      },
      error: () => {
        this.cargando.set(false);
        this.mostrarToast('Error al cargar parcelas agrícolas.', 'error');
      },
    });
  }

  // =========================================================================
  // INICIALIZACIÓN DEL MAPA SATELITAL (LEAFLET)
  // =========================================================================

  private inicializarMapa(): void {
    const mapContainer = document.getElementById('mapa-agricultura');
    if (!mapContainer) return;

    this.map = L.map('mapa-agricultura', {
      center: this.defaultCenter,
      zoom: this.defaultZoom,
      zoomControl: false,
    });

    L.control.zoom({ position: 'topleft' }).addTo(this.map);

    // Capa satelital por defecto
    this.googleHybridLayer.addTo(this.map);

    this.areasLayerGroup.addTo(this.map);
    this.labelsLayerGroup.addTo(this.map);

    // Eventos de clic en mapa para trazado poligonal
    this.map.on('click', (e: L.LeafletMouseEvent) => {
      if (this.modoDibujoActivo()) {
        this.agregarVerticeDibujo(e.latlng);
      }
    });

    // Renderizar áreas cargadas
    if (this.areas().length > 0) {
      this.renderizarAreasEnMapa();
    }
  }

  cambiarCapaSatelital(capa: 'google' | 'esri'): void {
    if (!this.map) return;
    this.capaSatelitalSeleccionada.set(capa);

    if (capa === 'google') {
      if (this.map.hasLayer(this.esriSatelliteLayer)) this.map.removeLayer(this.esriSatelliteLayer);
      if (this.map.hasLayer(this.esriLabelsLayer)) this.map.removeLayer(this.esriLabelsLayer);
      this.googleHybridLayer.addTo(this.map);
    } else {
      if (this.map.hasLayer(this.googleHybridLayer)) this.map.removeLayer(this.googleHybridLayer);
      this.esriSatelliteLayer.addTo(this.map);
      this.esriLabelsLayer.addTo(this.map);
    }
  }

  // =========================================================================
  // RENDERIZADO DE PARCELAS AGRÍCOLAS EN EL MAPA
  // =========================================================================

  private renderizarAreasEnMapa(): void {
    if (!this.map) return;

    this.areasLayerGroup.clearLayers();
    this.labelsLayerGroup.clearLayers();

    const bounds = L.latLngBounds([]);

    this.areas().forEach((area) => {
      if (!area.poligono_geojson) return;

      try {
        const coordsRaw = JSON.parse(area.poligono_geojson);
        let latLngs: [number, number][] = [];

        // Soporte tanto para formato plano [[lat, lng], ...] como GeoJSON [[[lng, lat], ...]]
        if (Array.isArray(coordsRaw)) {
          if (Array.isArray(coordsRaw[0]) && Array.isArray(coordsRaw[0][0])) {
            // GeoJSON Polygon coordinates [ring]
            latLngs = coordsRaw[0].map((pt: number[]) => [pt[1], pt[0]]);
          } else {
            // [[lat, lng], ...]
            latLngs = coordsRaw.map((pt: number[]) => [pt[0], pt[1]]);
          }
        }

        if (latLngs.length < 3) return;

        // Color dinámico según fase activa
        const color = this.obtenerColorPorFase(area);

        const polygon = L.polygon(latLngs, {
          color: color,
          weight: 2.5,
          opacity: 0.95,
          fillColor: color,
          fillOpacity: 0.38,
        });

        // Interacción al hacer clic en la parcela
        polygon.on('click', () => {
          this.seleccionarArea(area);
        });

        polygon.bindTooltip(
          `<strong>${area.nombre}</strong><br><span style="font-size:11px;">${area.superficie_ha} ha &bull; ${this.obtenerEtiquetaFase(area)}</span>`,
          { sticky: true, direction: 'top' }
        );

        this.areasLayerGroup.addLayer(polygon);
        bounds.extend(polygon.getBounds());

        // Etiqueta permanente en centroide
        if (area.centroide_lat && area.centroide_lng) {
          const badgeHtml = `
            <div class="parcela-map-badge" style="border-left: 4px solid ${color};">
              <span class="badge-title">${area.nombre}</span>
              <span class="badge-sub">${area.superficie_ha} ha &bull; ${area.ciclo_activo ? area.ciclo_activo.cultivo : 'Sin ciclo'}</span>
            </div>
          `;
          const badgeIcon = L.divIcon({
            className: 'custom-area-badge',
            html: badgeHtml,
            iconSize: [140, 36],
            iconAnchor: [70, 18],
          });
          const marker = L.marker([Number(area.centroide_lat), Number(area.centroide_lng)], {
            icon: badgeIcon,
            interactive: true,
          });
          marker.on('click', () => this.seleccionarArea(area));
          this.labelsLayerGroup.addLayer(marker);
        }
      } catch (err) {
        console.error('Error parseando polígono de área:', area.codigo, err);
      }
    });

    if (bounds.isValid() && this.areas().length > 0) {
      this.map.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 });
    }
  }

  obtenerColorPorFase(area: AreaAgricola): string {
    const c = area.ciclo_activo;
    if (!c || c.estado !== 'ACTIVO') return '#94A3B8'; // Gris (Sin ciclo activo / Barbecho)

    switch (c.fase_actual) {
      case 'PREPARACION':
        return '#F59E0B'; // Ámbar (Preparación de suelo)
      case 'SIEMBRA':
        return '#3B82F6'; // Azul (Siembra realizada)
      case 'MANEJO':
        return '#10B981'; // Verde Esmeralda (Desarrollo y aplicaciones)
      case 'COSECHA':
        return '#8B5CF6'; // Púrpura (En plena cosecha)
      case 'FINALIZADO':
        return '#64748B'; // Pizarra
      default:
        return '#10B981';
    }
  }

  obtenerEtiquetaFase(area: AreaAgricola): string {
    const c = area.ciclo_activo;
    if (!c || c.estado !== 'ACTIVO') return 'En Descanso / Barbecho';
    switch (c.fase_actual) {
      case 'PREPARACION':
        return `Prep. Terreno (${c.cultivo})`;
      case 'SIEMBRA':
        return `Sembrado (${c.cultivo})`;
      case 'MANEJO':
        return `Desarrollo / Fumigación (${c.cultivo})`;
      case 'COSECHA':
        return `Cosecha en Curso (${c.cultivo})`;
      case 'FINALIZADO':
        return `Ciclo Finalizado (${c.cultivo})`;
      default:
        return c.cultivo;
    }
  }

  // =========================================================================
  // TRAZADO POLIGONAL Y DELIMITACIÓN DE PARCELAS (RF-2)
  // =========================================================================

  iniciarModoDibujo(): void {
    this.cerrarDrawer();
    this.limpiarCapasDibujo();
    this.modoDibujoActivo.set(true);
    this.verticesDibujados.set([]);
    if (this.map) {
      this.map.doubleClickZoom.disable();
    }
    this.mostrarToast(
      'Modo Delimitación Activo: Haga clic en el mapa satelital para trazar los vértices de la parcela.',
      'info'
    );
  }

  private agregarVerticeDibujo(latlng: L.LatLng): void {
    if (!this.map) return;

    this.verticesDibujados.update((v) => [...v, latlng]);
    const currentVertices = this.verticesDibujados();
    const index = currentVertices.length;

    // Marcador visual de vértice
    const marker = L.marker(latlng, {
      icon: L.divIcon({
        className: 'vertex-pin-marker',
        html: `<div class="vertex-pin"><span>${index}</span></div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      }),
      interactive: false,
    }).addTo(this.map);
    this.drawingMarkers.push(marker);

    // Previsualización de línea o polígono
    if (this.polygonPreviewLayer) {
      this.polygonPreviewLayer.setLatLngs(currentVertices);
    } else if (currentVertices.length >= 2) {
      this.polygonPreviewLayer = L.polygon(currentVertices, {
        color: '#10B981',
        weight: 2.5,
        dashArray: '6, 6',
        fillColor: '#10B981',
        fillOpacity: 0.35,
        interactive: false,
      }).addTo(this.map);
    }

    this.cdr.markForCheck();
  }

  deshacerUltimoVertice(): void {
    if (this.verticesDibujados().length === 0) return;
    this.verticesDibujados.update((v) => v.slice(0, -1));
    const lastMarker = this.drawingMarkers.pop();
    if (lastMarker && this.map) {
      this.map.removeLayer(lastMarker);
    }
    if (this.polygonPreviewLayer) {
      this.polygonPreviewLayer.setLatLngs(this.verticesDibujados());
    }
    this.cdr.markForCheck();
  }

  cancelarDibujo(): void {
    this.limpiarCapasDibujo();
    this.modoDibujoActivo.set(false);
    this.verticesDibujados.set([]);
    if (this.map) {
      this.map.doubleClickZoom.enable();
    }
    this.cdr.markForCheck();
  }

  private limpiarCapasDibujo(): void {
    if (!this.map) return;
    if (this.polygonPreviewLayer) {
      this.map.removeLayer(this.polygonPreviewLayer);
      this.polygonPreviewLayer = null;
    }
    this.drawingMarkers.forEach((m) => this.map!.removeLayer(m));
    this.drawingMarkers = [];
  }

  // Cálculo geodésico esférico WGS84 para hectáreas exactas
  calcularSuperficieHectareas(vertices: L.LatLng[]): number {
    if (vertices.length < 3) return 0;
    const R = 6378137; // Radio terrestre en metros
    let area = 0;
    const len = vertices.length;
    for (let i = 0; i < len; i++) {
      const p1 = vertices[i];
      const p2 = vertices[(i + 1) % len];
      const p1LatRad = (p1.lat * Math.PI) / 180;
      const p2LatRad = (p2.lat * Math.PI) / 180;
      const dLngRad = ((p2.lng - p1.lng) * Math.PI) / 180;
      area += dLngRad * (2 + Math.sin(p1LatRad) + Math.sin(p2LatRad));
    }
    area = Math.abs((area * R * R) / 2.0); // m²
    const ha = area / 10000;
    return Math.round(ha * 100) / 100;
  }

  finalizarTrazadoYCompletarFormulario(): void {
    const vertices = this.verticesDibujados();
    if (vertices.length < 3) {
      this.mostrarToast('Debe marcar al menos 3 vértices para formar una parcela delimitada.', 'warning');
      return;
    }

    const haCalculada = this.calcularSuperficieHectareas(vertices);
    const coordsPlain = vertices.map((pt) => [
      Number(pt.lat.toFixed(6)),
      Number(pt.lng.toFixed(6)),
    ]);

    this.areaForm = {
      id: 0,
      codigo: '',
      nombre: `Parcela Lote ${this.areas().length + 1}`,
      superficie_ha: haCalculada,
      color_hex: '#10B981',
      observaciones: '',
      poligono_geojson: JSON.stringify(coordsPlain),
    };

    this.modalCrearAreaAbierto.set(true);
    if (this.map) {
      this.map.doubleClickZoom.enable();
    }
  }

  guardarNuevaArea(): void {
    if (!this.areaForm.nombre.trim()) {
      this.mostrarToast('El nombre de la parcela es obligatorio.', 'warning');
      return;
    }

    this.guardando.set(true);
    const payload: AreaAgricolaCreatePayload = {
      nombre: this.areaForm.nombre.trim(),
      superficie_ha: this.areaForm.superficie_ha,
      poligono_geojson: this.areaForm.poligono_geojson,
      color_hex: this.areaForm.color_hex,
      observaciones: this.areaForm.observaciones || null,
    };

    this.dataService.createAreaAgricola(payload).subscribe({
      next: (nueva) => {
        this.guardando.set(false);
        this.modalCrearAreaAbierto.set(false);
        this.limpiarCapasDibujo();
        this.modoDibujoActivo.set(false);
        this.verticesDibujados.set([]);
        this.mostrarToast(`Parcela '${nueva.nombre}' creada con ${nueva.superficie_ha} ha.`, 'success');
        this.cargarDatosIniciales();
        this.seleccionarArea(nueva);
      },
      error: () => {
        this.guardando.set(false);
        this.mostrarToast('Error al guardar el área agrícola.', 'error');
      },
    });
  }

  // =========================================================================
  // GESTIÓN DEL DRAWER LATERAL Y ÁREA SELECCIONADA
  // =========================================================================

  seleccionarArea(area: AreaAgricola): void {
    this.areaSeleccionada.set(area);
    this.tabDrawer.set('ciclo');
    this.drawerAbierto.set(true);

    // Cargar historial de ciclos de esta parcela
    this.cargarHistorialArea(area.id);

    // Centrar mapa suavemente
    if (this.map && area.centroide_lat && area.centroide_lng) {
      this.map.flyTo([Number(area.centroide_lat), Number(area.centroide_lng)], 16, { duration: 0.8 });
    }
  }

  cerrarDrawer(): void {
    this.drawerAbierto.set(false);
    this.areaSeleccionada.set(null);
  }

  cargarHistorialArea(areaId: number): void {
    this.dataService.getHistorialAreaAgricola(areaId).subscribe({
      next: (hist) => this.historialCiclos.set(hist),
      error: () => {},
    });
  }

  abrirEditarArea(): void {
    const a = this.areaSeleccionada();
    if (!a) return;
    this.areaForm = {
      id: a.id,
      codigo: a.codigo,
      nombre: a.nombre,
      superficie_ha: a.superficie_ha,
      color_hex: a.color_hex,
      observaciones: a.observaciones || '',
      poligono_geojson: a.poligono_geojson || '',
    };
    this.modalEditarAreaAbierto.set(true);
  }

  guardarEdicionArea(): void {
    const a = this.areaSeleccionada();
    if (!a) return;

    this.guardando.set(true);
    this.dataService
      .updateAreaAgricola(a.id, {
        nombre: this.areaForm.nombre.trim(),
        superficie_ha: this.areaForm.superficie_ha,
        observaciones: this.areaForm.observaciones || null,
      })
      .subscribe({
        next: (act) => {
          this.guardando.set(false);
          this.modalEditarAreaAbierto.set(false);
          this.mostrarToast(`Parcela '${act.nombre}' actualizada.`, 'success');
          this.cargarDatosIniciales();
          this.seleccionarArea(act);
        },
        error: () => {
          this.guardando.set(false);
          this.mostrarToast('Error al actualizar la parcela.', 'error');
        },
      });
  }

  confirmarEliminarArea(): void {
    const a = this.areaSeleccionada();
    if (!a) return;

    this.guardando.set(true);
    this.dataService.deleteAreaAgricola(a.id).subscribe({
      next: () => {
        this.guardando.set(false);
        this.modalEliminarAreaAbierto.set(false);
        this.cerrarDrawer();
        this.mostrarToast(`Parcela '${a.nombre}' desactivada.`, 'success');
        this.cargarDatosIniciales();
      },
      error: () => {
        this.guardando.set(false);
        this.mostrarToast('Error al desactivar la parcela.', 'error');
      },
    });
  }

  // =========================================================================
  // GESTIÓN DEL CICLO AGRÍCOLA (INICIO Y FASES)
  // =========================================================================

  abrirModalIniciarCiclo(): void {
    const a = this.areaSeleccionada();
    if (!a) return;

    if (a.ciclo_activo) {
      this.mostrarToast(
        `Esta parcela ya cuenta con un ciclo activo (${a.ciclo_activo.cultivo} - ${a.ciclo_activo.campana}). Debe finalizarlo antes de iniciar otro.`,
        'warning'
      );
      return;
    }

    this.cicloForm = {
      cultivo: 'Soya',
      variedad_hibrido: '',
      campana: 'Verano 2025/2026',
      fecha_inicio: this.getFechaHoy(),
      superficie_utilizada_ha: a.superficie_ha,
      observaciones: '',
    };
    this.modalIniciarCicloAbierto.set(true);
  }

  guardarNuevoCiclo(): void {
    const a = this.areaSeleccionada();
    if (!a) return;

    if (!this.cicloForm.cultivo) {
      this.mostrarToast('Seleccione el cultivo a sembrar.', 'warning');
      return;
    }

    this.guardando.set(true);
    const payload: CicloAgricolaCreatePayload = {
      cultivo: this.cicloForm.cultivo,
      variedad_hibrido: this.cicloForm.variedad_hibrido || null,
      campana: this.cicloForm.campana.trim(),
      fecha_inicio: this.cicloForm.fecha_inicio,
      superficie_utilizada_ha: this.cicloForm.superficie_utilizada_ha || a.superficie_ha,
      observaciones: this.cicloForm.observaciones || null,
    };

    this.dataService.iniciarCicloAgricola(a.id, payload).subscribe({
      next: () => {
        this.guardando.set(false);
        this.modalIniciarCicloAbierto.set(false);
        this.mostrarToast(`Campaña iniciada para ${payload.cultivo} en ${a.nombre}.`, 'success');
        this.recargarAreaSeleccionada(a.id);
      },
      error: (err) => {
        this.guardando.set(false);
        const msg = err.error?.detail || 'Error al iniciar el ciclo agrícola.';
        this.mostrarToast(msg, 'error');
      },
    });
  }

  avanzarFase(nuevaFase: string): void {
    const ciclo = this.areaSeleccionada()?.ciclo_activo;
    if (!ciclo) return;

    this.dataService.cambiarFaseCicloAgricola(ciclo.id, nuevaFase).subscribe({
      next: () => {
        this.mostrarToast(`Fase actualizada a: ${nuevaFase}`, 'success');
        this.recargarAreaSeleccionada(this.areaSeleccionada()!.id);
      },
      error: () => this.mostrarToast('Error al cambiar de fase.', 'error'),
    });
  }

  private recargarAreaSeleccionada(areaId: number): void {
    this.dataService.getAreaAgricolaById(areaId).subscribe({
      next: (act) => {
        this.areaSeleccionada.set(act);
        this.cargarDatosIniciales();
        this.cargarHistorialArea(areaId);
      },
    });
  }

  // =========================================================================
  // FASE 1: PREPARACIÓN
  // =========================================================================

  toggleActividadPreparacion(act: ActividadPreparacion): void {
    const ciclo = this.areaSeleccionada()?.ciclo_activo;
    if (!ciclo) return;

    const nuevoEstado = !act.completada;
    this.dataService
      .actualizarActividadPreparacion(ciclo.id, act.id, { completada: nuevoEstado })
      .subscribe({
        next: (actualizada) => {
          act.completada = actualizada.completada;
          this.cdr.markForCheck();
        },
        error: () => this.mostrarToast('Error al actualizar labor de preparación.', 'error'),
      });
  }

  // =========================================================================
  // FASE 2: SIEMBRA
  // =========================================================================

  abrirModalSiembra(): void {
    const ciclo = this.areaSeleccionada()?.ciclo_activo;
    if (!ciclo) return;

    this.siembraForm = {
      cultivo: ciclo.cultivo,
      variedad_hibrido: ciclo.variedad_hibrido || '',
      fecha_siembra: this.getFechaHoy(),
      superficie_sembrada_ha: ciclo.superficie_utilizada_ha,
      observaciones: '',
    };
    this.modalSiembraAbierto.set(true);
  }

  guardarSiembra(): void {
    const ciclo = this.areaSeleccionada()?.ciclo_activo;
    if (!ciclo) return;

    this.guardando.set(true);
    const payload: SiembraUpdatePayload = {
      cultivo: this.siembraForm.cultivo,
      variedad_hibrido: this.siembraForm.variedad_hibrido || null,
      fecha_siembra: this.siembraForm.fecha_siembra,
      superficie_sembrada_ha: this.siembraForm.superficie_sembrada_ha,
      observaciones: this.siembraForm.observaciones || null,
    };

    this.dataService.actualizarSiembra(ciclo.id, payload).subscribe({
      next: () => {
        this.guardando.set(false);
        this.modalSiembraAbierto.set(false);
        this.mostrarToast('Siembra registrada. El ciclo avanzó a Fase de Manejo / Desarrollo.', 'success');
        this.recargarAreaSeleccionada(this.areaSeleccionada()!.id);
      },
      error: () => {
        this.guardando.set(false);
        this.mostrarToast('Error al registrar datos de siembra.', 'error');
      },
    });
  }

  // =========================================================================
  // FASE 3: FUMIGACIÓN Y MANEJO
  // =========================================================================

  abrirModalManejo(): void {
    const ha = Number(
      this.areaSeleccionada()?.ciclo_activo?.superficie_utilizada_ha ||
      this.areaSeleccionada()?.superficie_ha ||
      0
    );
    const dosisDefault = 2;
    const totalCalc = ha > 0 ? Number((dosisDefault * ha).toFixed(2)) : dosisDefault;

    this.manejoForm = {
      fecha: this.getFechaHoy(),
      tipo_actividad: 'FUMIGACION',
      producto_utilizado: '',
      dosis_por_ha: dosisDefault,
      superficie_aplicada_ha: ha,
      cantidad_aplicada: totalCalc,
      unidad_medida: 'LT',
      observaciones: '',
    };
    this.modalManejoAbierto.set(true);
  }

  onDosisCambiada(): void {
    const ha = Number(this.manejoForm.superficie_aplicada_ha) || 0;
    const dosis = Number(this.manejoForm.dosis_por_ha) || 0;
    this.manejoForm.cantidad_aplicada = Number((dosis * ha).toFixed(2));
  }

  onSuperficieManejoCambiada(): void {
    const ha = Number(this.manejoForm.superficie_aplicada_ha) || 0;
    const dosis = Number(this.manejoForm.dosis_por_ha) || 0;
    this.manejoForm.cantidad_aplicada = Number((dosis * ha).toFixed(2));
  }

  onCantidadTotalCambiada(): void {
    const ha = Number(this.manejoForm.superficie_aplicada_ha) || 0;
    const total = Number(this.manejoForm.cantidad_aplicada) || 0;
    if (ha > 0) {
      this.manejoForm.dosis_por_ha = Number((total / ha).toFixed(3));
    }
  }

  guardarManejo(): void {
    const ciclo = this.areaSeleccionada()?.ciclo_activo;
    if (!ciclo) return;

    if (!this.manejoForm.producto_utilizado.trim()) {
      this.mostrarToast('Especifique el producto aplicado.', 'warning');
      return;
    }

    this.guardando.set(true);
    const payload: ActividadManejoCreatePayload = {
      fecha: this.manejoForm.fecha,
      tipo_actividad: this.manejoForm.tipo_actividad,
      producto_utilizado: this.manejoForm.producto_utilizado.trim(),
      cantidad_aplicada: Number(this.manejoForm.cantidad_aplicada),
      unidad_medida: this.manejoForm.unidad_medida,
      dosis_por_ha: this.manejoForm.dosis_por_ha ? Number(this.manejoForm.dosis_por_ha) : null,
      superficie_aplicada_ha: this.manejoForm.superficie_aplicada_ha ? Number(this.manejoForm.superficie_aplicada_ha) : null,
      observaciones: this.manejoForm.observaciones || null,
    };

    this.dataService.crearActividadManejo(ciclo.id, payload).subscribe({
      next: () => {
        this.guardando.set(false);
        this.modalManejoAbierto.set(false);
        this.mostrarToast('Aplicación fitosanitaria / fertilización registrada.', 'success');
        this.recargarAreaSeleccionada(this.areaSeleccionada()!.id);
      },
      error: () => {
        this.guardando.set(false);
        this.mostrarToast('Error al registrar actividad de manejo.', 'error');
      },
    });
  }

  eliminarManejo(actId: number): void {
    const ciclo = this.areaSeleccionada()?.ciclo_activo;
    if (!ciclo) return;

    this.dataService.eliminarActividadManejo(ciclo.id, actId).subscribe({
      next: () => {
        this.mostrarToast('Aplicación eliminada.', 'info');
        this.recargarAreaSeleccionada(this.areaSeleccionada()!.id);
      },
      error: () => this.mostrarToast('Error al eliminar actividad.', 'error'),
    });
  }

  // =========================================================================
  // FASE 4: COSECHA Y CIERRE
  // =========================================================================

  abrirModalCosecha(): void {
    const ciclo = this.areaSeleccionada()?.ciclo_activo;
    if (!ciclo) return;

    const sup = Number(ciclo.superficie_utilizada_ha || this.areaSeleccionada()?.superficie_ha || 0);
    const rendDefault = 3;
    const totalProd = sup > 0 ? Number((rendDefault * sup).toFixed(2)) : 0;

    this.cosechaForm = {
      fecha_cosecha: this.getFechaHoy(),
      fecha_fin_cosecha: '',
      cultivo_cosechado: ciclo.cultivo,
      superficie_cosechada_ha: sup,
      rendimiento_por_ha: rendDefault,
      cantidad_producida: totalProd,
      unidad_medida: 'TN',
      observaciones: '',
    };
    this.modalCosechaAbierto.set(true);
  }

  onRendimientoCosechaCambiado(): void {
    const ha = Number(this.cosechaForm.superficie_cosechada_ha) || 0;
    const rend = Number(this.cosechaForm.rendimiento_por_ha) || 0;
    this.cosechaForm.cantidad_producida = Number((rend * ha).toFixed(2));
  }

  onSuperficieCosechaCambiada(): void {
    const ha = Number(this.cosechaForm.superficie_cosechada_ha) || 0;
    const rend = Number(this.cosechaForm.rendimiento_por_ha) || 0;
    this.cosechaForm.cantidad_producida = Number((rend * ha).toFixed(2));
  }

  onCantidadProducidaCambiada(): void {
    const ha = Number(this.cosechaForm.superficie_cosechada_ha) || 0;
    const total = Number(this.cosechaForm.cantidad_producida) || 0;
    if (ha > 0) {
      this.cosechaForm.rendimiento_por_ha = Number((total / ha).toFixed(2));
    }
  }

  guardarCosecha(): void {
    const ciclo = this.areaSeleccionada()?.ciclo_activo;
    if (!ciclo) return;

    if (this.cosechaForm.superficie_cosechada_ha <= 0) {
      this.mostrarToast('La superficie cosechada debe ser mayor a 0 ha.', 'warning');
      return;
    }
    if (this.cosechaForm.cantidad_producida <= 0) {
      this.mostrarToast('La cantidad producida debe ser mayor a 0.', 'warning');
      return;
    }

    this.guardando.set(true);
    const payload: CosechaCreatePayload = {
      fecha_cosecha: this.cosechaForm.fecha_cosecha,
      fecha_fin_cosecha: this.cosechaForm.fecha_fin_cosecha || null,
      cultivo_cosechado: this.cosechaForm.cultivo_cosechado,
      superficie_cosechada_ha: this.cosechaForm.superficie_cosechada_ha,
      cantidad_producida: this.cosechaForm.cantidad_producida,
      unidad_medida: this.cosechaForm.unidad_medida,
      observaciones: this.cosechaForm.observaciones || null,
    };

    this.dataService.registrarCosecha(ciclo.id, payload).subscribe({
      next: (cos) => {
        this.guardando.set(false);
        this.modalCosechaAbierto.set(false);
        this.mostrarToast(
          `Cosecha registrada: ${cos.cantidad_producida} ${cos.unidad_medida} (${cos.rendimiento_calculado_ha} ${cos.unidad_medida}/ha).`,
          'success'
        );
        this.recargarAreaSeleccionada(this.areaSeleccionada()!.id);
      },
      error: () => {
        this.guardando.set(false);
        this.mostrarToast('Error al registrar datos de cosecha.', 'error');
      },
    });
  }

  confirmarFinalizarCiclo(): void {
    const ciclo = this.areaSeleccionada()?.ciclo_activo;
    if (!ciclo) return;

    this.guardando.set(true);
    this.dataService.finalizarCicloAgricola(ciclo.id).subscribe({
      next: (fin) => {
        this.guardando.set(false);
        this.modalFinalizarCicloAbierto.set(false);
        this.mostrarToast(
          `Campaña finalizada exitosamente. Rendimiento consolidado: ${fin.rendimiento_promedio_ha || 0} ${fin.unidad_cosecha || 'TN'}/ha.`,
          'success'
        );
        this.recargarAreaSeleccionada(this.areaSeleccionada()!.id);
      },
      error: () => {
        this.guardando.set(false);
        this.mostrarToast('Error al finalizar el ciclo agrícola.', 'error');
      },
    });
  }
}
