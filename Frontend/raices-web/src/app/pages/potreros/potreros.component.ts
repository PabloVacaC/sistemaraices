import {
  Component,
  OnInit,
  OnDestroy,
  AfterViewInit,
  signal,
  computed,
  inject,
  ElementRef,
  ViewChild,
  NgZone,
  ChangeDetectorRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DataService } from '../../core/services/data.service';
import { AuthService } from '../../core/services/auth.service';
import {
  Potrero,
  MovimientoGanado,
  AnimalPuntoMapa,
  MapaDistribucion,
  Animal,
  AnimalPerfil,
} from '../../core/models/types';
import * as L from 'leaflet';

@Component({
  selector: 'app-potreros',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './potreros.component.html',
  styleUrls: ['./potreros.component.scss'],
})
export class PotrerosComponent implements OnInit, AfterViewInit, OnDestroy {
  dataService = inject(DataService);
  auth = inject(AuthService);
  private ngZone = inject(NgZone);
  private cdr = inject(ChangeDetectorRef);
  Math = Math;

  @ViewChild('mapContainer', { static: false }) mapContainer!: ElementRef<HTMLDivElement>;

  // Estado reactivo con Signals
  cargando = signal<boolean>(true);
  guardando = signal<boolean>(false);
  potreros = signal<Potrero[]>([]);
  animalesPuntos = signal<AnimalPuntoMapa[]>([]);
  totalCabezasActivas = signal<number>(0);

  // Potrero seleccionado para el drawer lateral
  potreroSeleccionado = signal<Potrero | null>(null);
  cargandoAnimalesPotrero = signal<boolean>(false);
  animalesPotreroSeleccionado = signal<Animal[]>([]);
  filtroAnimalesTexto = signal<string>('');
  animalesSeleccionadosIds = signal<number[]>([]);

  // Modales
  modalMovimientoAbierto = signal<boolean>(false);
  modalCrearPotreroAbierto = signal<boolean>(false);
  modalEditarPotreroAbierto = signal<boolean>(false);
  modalHistorialAbierto = signal<boolean>(false);
  modalPerfilAnimalAbierto = signal<boolean>(false);
  modalDetalleMovimientoAbierto = signal<boolean>(false);
  modalAnularMovimientoAbierto = signal<boolean>(false);

  // Datos para movimiento en curso
  movimientoData = {
    tipo_operacion: 'ARRASTRE_MAPA' as 'ARRASTRE_MAPA' | 'MANUAL_INDIVIDUAL' | 'MANUAL_GRUPAL',
    potrero_origen_id: 0,
    potrero_origen_nombre: '',
    potrero_destino_id: 0,
    potrero_destino_nombre: '',
    animales: [] as { id: number; codigo: string; arete: string | null; nombre?: string | null }[],
    fecha_movimiento: this.getFechaHoy(),
    motivo: 'Rotación de pasturas',
    responsable: '',
    observaciones: '',
  };

  motivosPredefinidos = [
    'Rotación de pasturas',
    'Ingreso a confinamiento / engorde',
    'Pesaje y control sanitario',
    'Maternidad / Parición',
    'Aislamiento sanitario / Cuarentena',
    'Destete de terneros',
    'Manejo de reproductores / Celo',
    'Mantenimiento de potrero',
    'Otro motivo',
  ];

  // Datos para creación / edición de potrero
  potreroForm = {
    id: 0,
    nombre: '',
    tipo_area: 'POTRERO',
    superficie_ha: null as number | null,
    capacidad_cabezas: 50,
    color_hex: '#10b981',
    observaciones: '',
    poligono_geojson: '',
    vertices: [] as [number, number][], // [lat, lng]
  };

  coloresDisponibles = [
    { hex: '#10b981', label: 'Esmeralda (Nativo)' },
    { hex: '#3b82f6', label: 'Azul Zafiro' },
    { hex: '#8b5cf6', label: 'Púrpura' },
    { hex: '#f59e0b', label: 'Ámbar (Corrales)' },
    { hex: '#ef4444', label: 'Rojo (Cuarentena)' },
    { hex: '#06b6d4', label: 'Cian (Agua / Bebederos)' },
    { hex: '#ec4899', label: 'Rosa (Maternidad)' },
  ];

  // Modo dibujo de polígono
  modoDibujoActivo = signal<boolean>(false);
  verticesDibujados = signal<L.LatLng[]>([]);
  polygonPreviewLayer: L.Polygon | null = null;
  drawingMarkers: L.Marker[] = [];

  // Historial de movimientos
  movimientosHistorial = signal<MovimientoGanado[]>([]);
  movimientoSeleccionadoDetalle = signal<MovimientoGanado | null>(null);
  movimientoAAnular = signal<MovimientoGanado | null>(null);
  motivoAnulacion = signal<string>('');

  // Perfil 360 de animal
  perfilAnimalSeleccionado = signal<AnimalPerfil | null>(null);
  perfilTabActiva = signal<'info' | 'pesajes' | 'movimientos' | 'familia'>('info');
  historialMovimientosAnimal = signal<any[]>([]);

  // Notificaciones Toast
  toastMensaje = signal<string | null>(null);
  toastTipo = signal<'success' | 'warning' | 'error' | 'info'>('info');

  // Capa Satelital activa (Google vs Esri)
  capaSatelitalSeleccionada = signal<'google' | 'esri'>('google');

  // Mapa Leaflet y Capas
  private map: L.Map | null = null;
  private potrerosLayerGroup = L.layerGroup();
  private markersLayerGroup = L.layerGroup();
  private badgesLayerGroup = L.layerGroup();
  private animalMarkersMap = new Map<number, L.Marker>();

  // Proveedores de teselas satelitales
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

  // Coordenadas predeterminadas (-17.923267, -62.246458)
  private readonly defaultCenter: L.LatLngExpression = [-17.923267, -62.246458];
  private readonly defaultZoom: number = 15;

  // Filtro de animales en drawer computado
  animalesPotreroFiltrados = computed(() => {
    const txt = this.filtroAnimalesTexto().toLowerCase().trim();
    const list = this.animalesPotreroSeleccionado();
    if (!txt) return list;
    return list.filter(
      (a) =>
        a.codigo_interno.toLowerCase().includes(txt) ||
        (a.numero_arete && a.numero_arete.toLowerCase().includes(txt)) ||
        (a.nombre && a.nombre.toLowerCase().includes(txt)) ||
        a.raza.toLowerCase().includes(txt)
    );
  });

  // Alerta de sobrecapacidad computada
  sobrecapacidadDestino = computed(() => {
    const destinoId = this.movimientoData.potrero_destino_id;
    if (!destinoId) return null;
    const destino = this.potreros().find((p) => p.id === destinoId);
    if (!destino) return null;
    const cabezasAMover = this.movimientoData.animales.length;
    const totalResultante = destino.total_animales + cabezasAMover;
    if (totalResultante > destino.capacidad_cabezas) {
      return {
        capacidad: destino.capacidad_cabezas,
        resultante: totalResultante,
        exceso: totalResultante - destino.capacidad_cabezas,
      };
    }
    return null;
  });

  ngOnInit(): void {
    this.cargarDatosDistribucion();
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

  // =========================================================================
  // MAPA SATELITAL (LEAFLET + ESRI WORLD IMAGERY)
  // =========================================================================
  private inicializarMapa(): void {
    if (!this.mapContainer?.nativeElement) return;

    // Crear mapa Leaflet
    this.map = L.map(this.mapContainer.nativeElement, {
      center: this.defaultCenter,
      zoom: this.defaultZoom,
      zoomControl: false,
      attributionControl: false,
    });

    // Control de zoom en esquina superior izquierda
    L.control.zoom({ position: 'topleft' }).addTo(this.map);

    // Activar capa satelital inicial (Google Hybrid por defecto para mayor actualización en zonas rurales)
    this.googleHybridLayer.addTo(this.map);

    // Añadir grupos de capas
    this.potrerosLayerGroup.addTo(this.map);
    this.badgesLayerGroup.addTo(this.map);
    this.markersLayerGroup.addTo(this.map);

    // Listener de zoom para Zoom Progresivo Inteligente (RF-016)
    this.map.on('zoomend', () => {
      this.actualizarVisibilidadPorZoom();
    });

    // Click en el mapa para modo dibujo de polígonos
    this.map.on('click', (e: L.LeafletMouseEvent) => {
      if (this.modoDibujoActivo()) {
        this.ngZone.run(() => {
          this.agregarVerticeDibujo(e.latlng);
          this.cdr.markForCheck();
          this.cdr.detectChanges();
        });
      }
    });

    // Doble clic para finalizar y asignar datos si ya hay 3 o más vértices
    this.map.on('dblclick', (e: L.LeafletMouseEvent) => {
      if (this.modoDibujoActivo()) {
        L.DomEvent.stopPropagation(e);
        this.ngZone.run(() => {
          if (this.verticesDibujados().length >= 3) {
            this.finalizarTrazadoYCompletarFormulario();
          }
        });
      }
    });

    // Si los datos ya cargaron, renderizar
    if (this.potreros().length > 0) {
      this.renderizarMapaCompleto();
    }
  }

  cambiarCapaSatelital(tipo: 'google' | 'esri'): void {
    if (!this.map) return;
    this.capaSatelitalSeleccionada.set(tipo);

    if (tipo === 'google') {
      if (this.map.hasLayer(this.esriSatelliteLayer)) this.map.removeLayer(this.esriSatelliteLayer);
      if (this.map.hasLayer(this.esriLabelsLayer)) this.map.removeLayer(this.esriLabelsLayer);
      if (!this.map.hasLayer(this.googleHybridLayer)) this.googleHybridLayer.addTo(this.map);
      this.mostrarToast('Cambiado a Google Satélite Híbrido.', 'info');
    } else {
      if (this.map.hasLayer(this.googleHybridLayer)) this.map.removeLayer(this.googleHybridLayer);
      if (!this.map.hasLayer(this.esriSatelliteLayer)) this.esriSatelliteLayer.addTo(this.map);
      if (!this.map.hasLayer(this.esriLabelsLayer)) this.esriLabelsLayer.addTo(this.map);
      this.mostrarToast('Cambiado a Esri World Imagery Satelital.', 'info');
    }
  }

  cargarDatosDistribucion(centrarEncuadre: boolean = true): void {
    this.cargando.set(true);
    this.dataService.getMapaDistribucion().subscribe({
      next: (data: MapaDistribucion) => {
        this.potreros.set(data.potreros || []);
        this.animalesPuntos.set(data.animales || []);
        this.totalCabezasActivas.set(data.total_cabezas_activas || 0);
        this.cargando.set(false);

        if (this.map) {
          this.renderizarMapaCompleto(centrarEncuadre);
        }
      },
      error: (err) => {
        this.cargando.set(false);
        this.mostrarToast('Error al cargar la cartografía de potreros y ganado.', 'error');
      },
    });
  }

  private renderizarMapaCompleto(ajustarEncuadre: boolean = false): void {
    if (!this.map) return;

    this.potrerosLayerGroup.clearLayers();
    this.badgesLayerGroup.clearLayers();
    this.markersLayerGroup.clearLayers();
    this.animalMarkersMap.clear();

    const bounds = L.latLngBounds([]);

    // 1. Renderizar Polígonos de Potreros y Corrales
    this.potreros().forEach((potrero) => {
      try {
        const geojson = JSON.parse(potrero.poligono_geojson);
        const coords = geojson.coordinates;
        if (!coords || coords.length === 0) return;

        // Leaflet polygon espera [[lat, lng], ...]
        const ring = Array.isArray(coords[0][0]) ? coords[0] : coords;
        const latLngs: L.LatLngExpression[] = ring.map((pt: [number, number]) => [pt[1], pt[0]]);

        const polygon = L.polygon(latLngs, {
          color: potrero.color_hex || '#10b981',
          weight: 2,
          opacity: 0.9,
          fillColor: potrero.color_hex || '#10b981',
          fillOpacity: 0.25,
          className: 'potrero-polygon',
        });

        // Hover y click
        polygon.on('mouseover', () => {
          if (!this.modoDibujoActivo()) {
            polygon.setStyle({ fillOpacity: 0.45, weight: 3 });
          }
        });
        polygon.on('mouseout', () => {
          if (!this.modoDibujoActivo()) {
            polygon.setStyle({ fillOpacity: 0.25, weight: 2 });
          }
        });
        polygon.on('click', (ev: L.LeafletMouseEvent) => {
          if (this.modoDibujoActivo()) {
            L.DomEvent.stopPropagation(ev);
            this.ngZone.run(() => {
              this.agregarVerticeDibujo(ev.latlng);
              this.cdr.markForCheck();
              this.cdr.detectChanges();
            });
            return;
          }
          this.seleccionarPotrero(potrero);
        });

        this.potrerosLayerGroup.addLayer(polygon);
        bounds.extend(polygon.getBounds());

        // Badge con nombre y cabezas flotando sobre el centroide (visible en zoom < 16)
        const cLat = Number(potrero.centroide_lat) || polygon.getBounds().getCenter().lat;
        const cLng = Number(potrero.centroide_lng) || polygon.getBounds().getCenter().lng;

        const badgeIcon = L.divIcon({
          className: 'custom-potrero-badge',
          html: `
            <div class="potrero-badge" style="border-left: 4px solid ${potrero.color_hex};">
              <span class="badge-title">${potrero.nombre}</span>
              <span class="badge-count">${potrero.total_animales} cab.</span>
            </div>
          `,
          iconSize: [120, 36],
          iconAnchor: [60, 18],
        });

        const badgeMarker = L.marker([cLat, cLng], {
          icon: badgeIcon,
          interactive: true,
        });
        badgeMarker.on('click', () => this.seleccionarPotrero(potrero));
        this.badgesLayerGroup.addLayer(badgeMarker);
      } catch (e) {
        console.error('Error parseando GeoJSON de potrero', potrero.nombre, e);
      }
    });

    // 2. Renderizar Puntos Individuales de Ganado con Drag & Drop (RF-015, RF-018)
    this.animalesPuntos().forEach((animal) => {
      const marker = this.crearMarkerAnimal(animal);
      this.markersLayerGroup.addLayer(marker);
      this.animalMarkersMap.set(animal.id, marker);
    });

    // Zoom Progresivo
    this.actualizarVisibilidadPorZoom();

    // 3. Ajustar Encuadre (fitBounds) automático si es la carga inicial o si hay polígonos
    if (ajustarEncuadre && bounds.isValid()) {
      this.map.fitBounds(bounds, { padding: [50, 50], maxZoom: 16 });
    }
  }

  private crearMarkerAnimal(animal: AnimalPuntoMapa): L.Marker {
    const isMacho = animal.sexo === 'MACHO';
    const iconSymbol = isMacho ? '🐂' : '🐄';
    const labelText = animal.numero_arete || animal.codigo_interno;

    const divHtml = `
      <div class="animal-map-dot ${isMacho ? 'macho' : 'hembra'}" title="${animal.codigo_interno} (${animal.numero_arete || 'S/N'})">
        <span class="dot-icon">${iconSymbol}</span>
        <span class="dot-label">${labelText}</span>
      </div>
    `;

    const customIcon = L.divIcon({
      className: 'animal-marker-wrapper',
      html: divHtml,
      iconSize: [60, 24],
      iconAnchor: [30, 12],
    });

    const marker = L.marker([animal.lat, animal.lng], {
      icon: customIcon,
      draggable: true,
      title: `${animal.codigo_interno} - ${animal.raza}`,
    });

    // Popup rápido con información y acciones
    const popupContent = `
      <div class="animal-popup-card">
        <div class="popup-header">
          <span class="popup-tag">${animal.codigo_interno}</span>
          <span class="popup-arete">${animal.numero_arete ? 'Arete: ' + animal.numero_arete : 'Sin Arete'}</span>
        </div>
        <div class="popup-body">
          <p><strong>Raza:</strong> ${animal.raza}</p>
          <p><strong>Sexo:</strong> ${animal.sexo}</p>
          <p><strong>Peso actual:</strong> ${animal.peso_actual ? animal.peso_actual + ' kg' : 'Sin pesaje'}</p>
          <p><strong>Ubicación:</strong> ${animal.potrero_nombre}</p>
        </div>
        <div class="popup-actions">
          <button class="btn-popup-perfil" data-animal-id="${animal.id}">Ver Perfil 360°</button>
          <button class="btn-popup-mover" data-animal-id="${animal.id}">Trasladar</button>
        </div>
      </div>
    `;
    marker.bindPopup(popupContent, { minWidth: 200, className: 'clean-popup' });

    marker.on('click', (ev: L.LeafletMouseEvent) => {
      if (this.modoDibujoActivo()) {
        marker.closePopup();
        L.DomEvent.stopPropagation(ev);
        this.ngZone.run(() => {
          this.agregarVerticeDibujo(ev.latlng);
          this.cdr.markForCheck();
          this.cdr.detectChanges();
        });
      }
    });

    marker.on('popupopen', () => {
      setTimeout(() => {
        const btnPerfil = document.querySelector(`.btn-popup-perfil[data-animal-id="${animal.id}"]`);
        if (btnPerfil) {
          btnPerfil.addEventListener('click', () => {
            marker.closePopup();
            this.abrirPerfilAnimal(animal.id);
          });
        }
        const btnMover = document.querySelector(`.btn-popup-mover[data-animal-id="${animal.id}"]`);
        if (btnMover) {
          btnMover.addEventListener('click', () => {
            marker.closePopup();
            this.iniciarMovimientoManualIndividual(animal);
          });
        }
      }, 50);
    });

    // =====================================================================
    // EVENTO DRAG & DROP INDIVIDUAL (RF-018 - RF-023)
    // =====================================================================
    let latLngOriginal = L.latLng(animal.lat, animal.lng);

    marker.on('dragstart', () => {
      latLngOriginal = marker.getLatLng();
    });

    marker.on('dragend', (e) => {
      const droppedLatLng = marker.getLatLng();
      const potreroDestino = this.detectarPotreroEnPunto(droppedLatLng.lat, droppedLatLng.lng);

      // 1. Soltado fuera de todo potrero
      if (!potreroDestino) {
        marker.setLatLng(latLngOriginal);
        this.mostrarToast(
          'Ubicación no válida: debe soltar el animal dentro de un potrero o corral registrado.',
          'warning'
        );
        return;
      }

      // 2. Soltado en el mismo potrero de origen
      if (potreroDestino.id === animal.potrero_id) {
        marker.setLatLng(latLngOriginal);
        this.mostrarToast(`El animal ya se encuentra en '${potreroDestino.nombre}'.`, 'info');
        return;
      }

      // 3. Soltado en un potrero destino diferente -> Abrir Modal de Confirmación
      this.abrirModalMovimientoArrastre(animal, potreroDestino, latLngOriginal, marker);
    });

    return marker;
  }

  private actualizarVisibilidadPorZoom(): void {
    if (!this.map) return;
    const zoom = this.map.getZoom();

    if (zoom < 16) {
      // Zoom lejano: ocultar marcadores individuales, mostrar insignias de potrero
      if (this.map.hasLayer(this.markersLayerGroup)) {
        this.map.removeLayer(this.markersLayerGroup);
      }
      if (!this.map.hasLayer(this.badgesLayerGroup)) {
        this.map.addLayer(this.badgesLayerGroup);
      }
    } else {
      // Zoom cercano: mostrar puntos individuales de ganado, ocultar insignias de potrero
      if (!this.map.hasLayer(this.markersLayerGroup)) {
        this.map.addLayer(this.markersLayerGroup);
      }
      if (this.map.hasLayer(this.badgesLayerGroup)) {
        this.map.removeLayer(this.badgesLayerGroup);
      }
    }
  }

  // =========================================================================
  // ALGORITMO RAY-CASTING (POINT-IN-POLYGON) EN FRONTEND
  // =========================================================================
  detectarPotreroEnPunto(lat: number, lng: number): Potrero | null {
    for (const potrero of this.potreros()) {
      try {
        const geo = JSON.parse(potrero.poligono_geojson);
        const coords = geo.coordinates;
        if (!coords || coords.length === 0) continue;
        const ring = Array.isArray(coords[0][0]) ? coords[0] : coords;

        if (this.puntoEnPoligono(lat, lng, ring)) {
          return potrero;
        }
      } catch (e) {
        // Ignorar error de parsing
      }
    }
    return null;
  }

  private puntoEnPoligono(lat: number, lng: number, ring: [number, number][]): boolean {
    const n = ring.length;
    let inside = false;
    let p1x = ring[0][0]; // lng
    let p1y = ring[0][1]; // lat

    for (let i = 1; i <= n; i++) {
      const p2x = ring[i % n][0];
      const p2y = ring[i % n][1];

      if (Math.min(p1y, p2y) < lat && lat <= Math.max(p1y, p2y)) {
        if (lng <= Math.max(p1x, p2x)) {
          const xinters = p1y !== p2y ? ((lat - p1y) * (p2x - p1x)) / (p2y - p1y) + p1x : p1x;
          if (p1x === p2x || lng <= xinters) {
            inside = !inside;
          }
        }
      }
      p1x = p2x;
      p1y = p2y;
    }
    return inside;
  }

  // =========================================================================
  // GESTIÓN DEL DRAWER LATERAL DE POTRERO
  // =========================================================================
  seleccionarPotrero(potrero: Potrero): void {
    this.potreroSeleccionado.set(potrero);
    this.animalesSeleccionadosIds.set([]);
    this.filtroAnimalesTexto.set('');
    this.cargandoAnimalesPotrero.set(true);

    this.dataService.getPotrero(potrero.id).subscribe({
      next: (detalle) => {
        this.animalesPotreroSeleccionado.set(detalle.animales || []);
        this.cargandoAnimalesPotrero.set(false);
      },
      error: () => {
        this.cargandoAnimalesPotrero.set(false);
      },
    });
  }

  cerrarDrawerPotrero(): void {
    this.potreroSeleccionado.set(null);
    this.animalesSeleccionadosIds.set([]);
  }

  centrarEnPotrero(potrero: Potrero): void {
    if (!this.map) return;
    try {
      const geo = JSON.parse(potrero.poligono_geojson);
      const ring = Array.isArray(geo.coordinates[0][0]) ? geo.coordinates[0] : geo.coordinates;
      const latLngs: L.LatLngExpression[] = ring.map((pt: [number, number]) => [pt[1], pt[0]]);
      const poly = L.polygon(latLngs);
      this.map.fitBounds(poly.getBounds(), { padding: [60, 60], maxZoom: 17 });
    } catch (e) {
      if (potrero.centroide_lat && potrero.centroide_lng) {
        this.map.setView([Number(potrero.centroide_lat), Number(potrero.centroide_lng)], 17);
      }
    }
  }

  toggleSeleccionAnimal(id: number): void {
    const actuales = [...this.animalesSeleccionadosIds()];
    const idx = actuales.indexOf(id);
    if (idx >= 0) {
      actuales.splice(idx, 1);
    } else {
      actuales.push(id);
    }
    this.animalesSeleccionadosIds.set(actuales);
  }

  toggleSeleccionarTodos(): void {
    const filtrados = this.animalesPotreroFiltrados();
    if (this.animalesSeleccionadosIds().length === filtrados.length) {
      this.animalesSeleccionadosIds.set([]);
    } else {
      this.animalesSeleccionadosIds.set(filtrados.map((a) => a.id));
    }
  }

  // =========================================================================
  // TRASLADOS Y MOVIMIENTOS DE GANADO
  // =========================================================================
  private markerEnArrastre: L.Marker | null = null;
  private latLngOriginalArrastre: L.LatLng | null = null;

  abrirModalMovimientoArrastre(
    animal: AnimalPuntoMapa,
    potreroDestino: Potrero,
    latLngOrig: L.LatLng,
    marker: L.Marker
  ): void {
    this.markerEnArrastre = marker;
    this.latLngOriginalArrastre = latLngOrig;

    this.movimientoData = {
      tipo_operacion: 'ARRASTRE_MAPA',
      potrero_origen_id: animal.potrero_id,
      potrero_origen_nombre: animal.potrero_nombre,
      potrero_destino_id: potreroDestino.id,
      potrero_destino_nombre: potreroDestino.nombre,
      animales: [
        {
          id: animal.id,
          codigo: animal.codigo_interno,
          arete: animal.numero_arete || null,
          nombre: animal.nombre,
        },
      ],
      fecha_movimiento: this.getFechaHoy(),
      motivo: 'Rotación de pasturas',
      responsable: '',
      observaciones: '',
    };

    this.modalMovimientoAbierto.set(true);
  }

  iniciarMovimientoManualIndividual(animal: AnimalPuntoMapa): void {
    this.movimientoData = {
      tipo_operacion: 'MANUAL_INDIVIDUAL',
      potrero_origen_id: animal.potrero_id,
      potrero_origen_nombre: animal.potrero_nombre,
      potrero_destino_id: 0,
      potrero_destino_nombre: '',
      animales: [
        {
          id: animal.id,
          codigo: animal.codigo_interno,
          arete: animal.numero_arete || null,
          nombre: animal.nombre,
        },
      ],
      fecha_movimiento: this.getFechaHoy(),
      motivo: 'Rotación de pasturas',
      responsable: '',
      observaciones: '',
    };
    this.modalMovimientoAbierto.set(true);
  }

  abrirModalMovimientoMasivo(): void {
    const potOrigen = this.potreroSeleccionado();
    if (!potOrigen) return;

    const ids = this.animalesSeleccionadosIds();
    if (ids.length === 0) {
      this.mostrarToast('Seleccione al menos un animal para trasladar.', 'warning');
      return;
    }

    const animalesSeleccionados = this.animalesPotreroSeleccionado()
      .filter((a) => ids.includes(a.id))
      .map((a) => ({
        id: a.id,
        codigo: a.codigo_interno,
        arete: a.numero_arete || null,
        nombre: a.nombre,
      }));

    this.movimientoData = {
      tipo_operacion: 'MANUAL_GRUPAL',
      potrero_origen_id: potOrigen.id,
      potrero_origen_nombre: potOrigen.nombre,
      potrero_destino_id: 0,
      potrero_destino_nombre: '',
      animales: animalesSeleccionados,
      fecha_movimiento: this.getFechaHoy(),
      motivo: 'Rotación de pasturas',
      responsable: '',
      observaciones: '',
    };
    this.modalMovimientoAbierto.set(true);
  }

  cancelarMovimiento(): void {
    if (this.markerEnArrastre && this.latLngOriginalArrastre) {
      this.markerEnArrastre.setLatLng(this.latLngOriginalArrastre);
    }
    this.markerEnArrastre = null;
    this.latLngOriginalArrastre = null;
    this.modalMovimientoAbierto.set(false);
  }

  confirmarMovimiento(): void {
    if (!this.movimientoData.potrero_destino_id) {
      this.mostrarToast('Debe seleccionar el potrero o corral de destino.', 'warning');
      return;
    }

    this.guardando.set(true);
    const payload = {
      potrero_origen_id: this.movimientoData.potrero_origen_id,
      potrero_destino_id: this.movimientoData.potrero_destino_id,
      animales_ids: this.movimientoData.animales.map((a) => a.id),
      fecha_movimiento: this.movimientoData.fecha_movimiento,
      tipo_operacion: this.movimientoData.tipo_operacion,
      motivo: this.movimientoData.motivo,
      responsable: this.movimientoData.responsable,
      observaciones: this.movimientoData.observaciones,
    };

    this.dataService.crearMovimientoGanado(payload).subscribe({
      next: (mov) => {
        this.guardando.set(false);
        this.modalMovimientoAbierto.set(false);
        this.markerEnArrastre = null;
        this.latLngOriginalArrastre = null;
        this.mostrarToast(
          `Traslado registrado con éxito (${mov.numero_comprobante}). ${mov.cantidad_animales} cabezas movidas.`,
          'success'
        );

        // Recargar datos y refrescar potrero seleccionado si estaba abierto
        this.cargarDatosDistribucion(false);
        if (this.potreroSeleccionado()) {
          const actId = this.potreroSeleccionado()!.id;
          const actPot = this.potreros().find((p) => p.id === actId);
          if (actPot) {
            this.seleccionarPotrero(actPot);
          } else {
            this.cerrarDrawerPotrero();
          }
        }
      },
      error: (err) => {
        this.guardando.set(false);
        if (this.markerEnArrastre && this.latLngOriginalArrastre) {
          this.markerEnArrastre.setLatLng(this.latLngOriginalArrastre);
        }
        const msg = err.error?.detail || 'Error al registrar el movimiento de ganado.';
        this.mostrarToast(msg, 'error');
      },
    });
  }

  // =========================================================================
  // DELIMITACIÓN Y CREACIÓN DE NUEVO POTRERO / CORRAL
  // =========================================================================
  iniciarDelimitacionNuevoPotrero(): void {
    this.cerrarDrawerPotrero();
    this.potreroForm = {
      id: 0,
      nombre: '',
      tipo_area: 'POTRERO',
      superficie_ha: null,
      capacidad_cabezas: 50,
      color_hex: '#10b981',
      observaciones: '',
      poligono_geojson: '',
      vertices: [],
    };
    this.verticesDibujados.set([]);
    this.limpiarCapasDibujo();
    this.modoDibujoActivo.set(true);
    if (this.map) {
      this.map.doubleClickZoom.disable();
    }
    this.mostrarToast(
      'Modo delimitación activado: haga clic sobre el mapa satelital para trazar los vértices del nuevo potrero/corral.',
      'info'
    );
  }

  private agregarVerticeDibujo(latlng: L.LatLng): void {
    this.verticesDibujados.update((v) => [...v, latlng]);
    const currentVertices = this.verticesDibujados();
    const vertIndex = currentVertices.length;
    const isFirst = vertIndex === 1;

    // Marcador de vértice con punto interactivo
    const dotIcon = L.divIcon({
      className: 'vertex-dot-icon',
      html: `<div class="vertex-dot ${isFirst ? 'vertex-dot-first' : ''}" title="${isFirst ? 'Vértice #1 (Haga clic para cerrar el polígono)' : 'Vértice #' + vertIndex}">${vertIndex}</div>`,
      iconSize: [26, 26],
      iconAnchor: [13, 13],
    });
    const marker = L.marker(latlng, {
      icon: dotIcon,
      interactive: isFirst,
      title: `Vértice #${vertIndex}`,
    }).addTo(this.map!);

    // Si hace clic en el vértice inicial (#1) cuando ya hay 3 o más vértices, cierra y finaliza automáticamente
    if (isFirst) {
      marker.on('click', (ev) => {
        L.DomEvent.stopPropagation(ev);
        this.ngZone.run(() => {
          if (this.verticesDibujados().length >= 3) {
            this.finalizarTrazadoYCompletarFormulario();
          } else {
            this.mostrarToast('Marque al menos 3 vértices perimetrales antes de cerrar el polígono.', 'info');
          }
        });
      });
    }

    this.drawingMarkers.push(marker);

    // Dibujar o actualizar polígono preliminar (interactive: false para nunca bloquear clics sobre el mapa)
    if (this.polygonPreviewLayer) {
      this.polygonPreviewLayer.setLatLngs(currentVertices);
    } else if (currentVertices.length >= 2) {
      this.polygonPreviewLayer = L.polygon(currentVertices, {
        color: this.potreroForm.color_hex,
        weight: 2,
        dashArray: '5, 5',
        fillColor: this.potreroForm.color_hex,
        fillOpacity: 0.35,
        interactive: false,
      }).addTo(this.map!);
    }

    this.cdr.markForCheck();
    this.cdr.detectChanges();
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
    this.cdr.detectChanges();
  }

  cancelarDibujo(): void {
    this.limpiarCapasDibujo();
    this.modoDibujoActivo.set(false);
    this.verticesDibujados.set([]);
    if (this.map) {
      this.map.doubleClickZoom.enable();
    }
    this.cdr.markForCheck();
    this.cdr.detectChanges();
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

  finalizarTrazadoYCompletarFormulario(): void {
    const vertices = this.verticesDibujados();
    if (vertices.length < 3) {
      this.mostrarToast('Debe marcar al menos 3 vértices para formar un polígono perimetral cerrado.', 'warning');
      return;
    }

    // Convertir a GeoJSON: [[[lng, lat], ..., [lng, lat]]]
    const ring = vertices.map((pt) => [
      Number(pt.lng.toFixed(6)),
      Number(pt.lat.toFixed(6)),
    ]);
    // Cerrar el polígono
    ring.push([ring[0][0], ring[0][1]]);

    const geojsonObj = {
      type: 'Polygon',
      coordinates: [ring],
    };

    this.potreroForm.poligono_geojson = JSON.stringify(geojsonObj);
    this.modalCrearPotreroAbierto.set(true);
    if (this.map) {
      this.map.doubleClickZoom.enable();
    }
  }

  guardarNuevoPotrero(): void {
    if (!this.potreroForm.nombre.trim()) {
      this.mostrarToast('El nombre del potrero o corral es obligatorio.', 'warning');
      return;
    }

    this.guardando.set(true);
    const payload = {
      nombre: this.potreroForm.nombre.trim(),
      tipo_area: this.potreroForm.tipo_area,
      capacidad_cabezas: this.potreroForm.capacidad_cabezas || 50,
      color_hex: this.potreroForm.color_hex || '#10b981',
      poligono_geojson: this.potreroForm.poligono_geojson,
      superficie_ha: this.potreroForm.superficie_ha || null,
      observaciones: this.potreroForm.observaciones || null,
    };

    this.dataService.crearPotrero(payload).subscribe({
      next: (nuevo) => {
        this.guardando.set(false);
        this.modalCrearPotreroAbierto.set(false);
        this.modoDibujoActivo.set(false);
        this.verticesDibujados.set([]);
        if (this.map) {
          this.map.doubleClickZoom.enable();
        }
        this.limpiarCapasDibujo();
        this.mostrarToast(`Área '${nuevo.nombre}' (${nuevo.codigo}) creada con éxito.`, 'success');
        this.cargarDatosDistribucion(false);
      },
      error: (err) => {
        this.guardando.set(false);
        const msg = err.error?.detail || 'Error al guardar el nuevo potrero.';
        this.mostrarToast(msg, 'error');
      },
    });
  }

  // =========================================================================
  // EDICIÓN Y DESACTIVACIÓN DE POTREROS
  // =========================================================================
  abrirModalEditarPotrero(potrero: Potrero): void {
    this.potreroForm = {
      id: potrero.id,
      nombre: potrero.nombre,
      tipo_area: potrero.tipo_area,
      superficie_ha: potrero.superficie_ha || null,
      capacidad_cabezas: potrero.capacidad_cabezas,
      color_hex: potrero.color_hex,
      observaciones: potrero.observaciones || '',
      poligono_geojson: potrero.poligono_geojson,
      vertices: [],
    };
    this.modalEditarPotreroAbierto.set(true);
  }

  guardarEdicionPotrero(): void {
    if (!this.potreroForm.nombre.trim()) {
      this.mostrarToast('El nombre es obligatorio.', 'warning');
      return;
    }

    this.guardando.set(true);
    const payload = {
      nombre: this.potreroForm.nombre.trim(),
      tipo_area: this.potreroForm.tipo_area,
      capacidad_cabezas: this.potreroForm.capacidad_cabezas,
      color_hex: this.potreroForm.color_hex,
      superficie_ha: this.potreroForm.superficie_ha,
      observaciones: this.potreroForm.observaciones,
    };

    this.dataService.actualizarPotrero(this.potreroForm.id, payload).subscribe({
      next: (actualizado) => {
        this.guardando.set(false);
        this.modalEditarPotreroAbierto.set(false);
        this.mostrarToast(`Potrero '${actualizado.nombre}' actualizado correctamente.`, 'success');
        this.cargarDatosDistribucion(false);
        if (this.potreroSeleccionado()?.id === actualizado.id) {
          this.seleccionarPotrero(actualizado);
        }
      },
      error: (err) => {
        this.guardando.set(false);
        const msg = err.error?.detail || 'Error al actualizar el potrero.';
        this.mostrarToast(msg, 'error');
      },
    });
  }

  desactivarPotrero(potrero: Potrero): void {
    if (potrero.total_animales > 0) {
      this.mostrarToast(
        `No puede desactivar '${potrero.nombre}' porque contiene ${potrero.total_animales} animal(es) activo(s). Trasládelos primero.`,
        'warning'
      );
      return;
    }

    if (!confirm(`¿Está seguro de desactivar '${potrero.nombre}'? Dejará de aparecer en el mapa.`)) {
      return;
    }

    this.dataService.desactivarPotrero(potrero.id).subscribe({
      next: () => {
        this.mostrarToast(`Potrero '${potrero.nombre}' desactivado.`, 'info');
        this.cerrarDrawerPotrero();
        this.cargarDatosDistribucion(false);
      },
      error: (err) => {
        const msg = err.error?.detail || 'No se pudo desactivar el potrero.';
        this.mostrarToast(msg, 'error');
      },
    });
  }

  // =========================================================================
  // HISTORIAL DE MOVIMIENTOS Y ANULACIONES
  // =========================================================================
  abrirHistorialMovimientos(): void {
    this.modalHistorialAbierto.set(true);
    this.cargarHistorialMovimientos();
  }

  cargarHistorialMovimientos(): void {
    this.dataService.getMovimientosGanado().subscribe({
      next: (movs) => {
        this.movimientosHistorial.set(movs || []);
      },
      error: () => {
        this.mostrarToast('Error al cargar historial de movimientos.', 'error');
      },
    });
  }

  verDetalleMovimiento(mov: MovimientoGanado): void {
    this.movimientoSeleccionadoDetalle.set(mov);
    this.modalDetalleMovimientoAbierto.set(true);
  }

  iniciarAnulacionMovimiento(mov: MovimientoGanado): void {
    this.movimientoAAnular.set(mov);
    this.motivoAnulacion.set('');
    this.modalAnularMovimientoAbierto.set(true);
  }

  confirmarAnulacionMovimiento(): void {
    const mov = this.movimientoAAnular();
    if (!mov) return;
    const mot = this.motivoAnulacion().trim();
    if (!mot) {
      this.mostrarToast('Debe ingresar el motivo de anulación.', 'warning');
      return;
    }

    this.guardando.set(true);
    this.dataService.anularMovimientoGanado(mov.id, mot).subscribe({
      next: () => {
        this.guardando.set(false);
        this.modalAnularMovimientoAbierto.set(false);
        this.mostrarToast(
          `Comprobante ${mov.numero_comprobante} anulado con éxito. Animales revertidos a su potrero anterior.`,
          'success'
        );
        this.cargarHistorialMovimientos();
        this.cargarDatosDistribucion(false);
      },
      error: (err) => {
        this.guardando.set(false);
        const msg = err.error?.detail || 'No fue posible anular el movimiento.';
        this.mostrarToast(msg, 'error');
      },
    });
  }

  // =========================================================================
  // PERFIL 360° DE ANIMAL
  // =========================================================================
  abrirPerfilAnimal(animalId: number): void {
    this.perfilAnimalSeleccionado.set(null);
    this.perfilTabActiva.set('info');
    this.modalPerfilAnimalAbierto.set(true);

    this.dataService.getAnimalPerfil(animalId).subscribe({
      next: (perfil) => {
        this.perfilAnimalSeleccionado.set(perfil);
      },
      error: () => {
        this.mostrarToast('Error al obtener datos del animal.', 'error');
      },
    });

    this.dataService.getHistorialMovimientosAnimal(animalId).subscribe({
      next: (movs) => {
        this.historialMovimientosAnimal.set(movs || []);
      },
    });
  }

  cerrarPerfilAnimal(): void {
    this.modalPerfilAnimalAbierto.set(false);
    this.perfilAnimalSeleccionado.set(null);
  }

  // =========================================================================
  // HELPERS Y TOAST
  // =========================================================================
  mostrarToast(mensaje: string, tipo: 'success' | 'warning' | 'error' | 'info' = 'info'): void {
    this.toastMensaje.set(mensaje);
    this.toastTipo.set(tipo);
    setTimeout(() => {
      this.toastMensaje.set(null);
    }, 4500);
  }
}
