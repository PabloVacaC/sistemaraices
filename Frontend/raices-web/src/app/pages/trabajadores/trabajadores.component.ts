import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DataService } from '../../core/services/data.service';
import { ToastService } from '../../core/services/toast.service';
import { Trabajador, Area, ContactoEmergencia } from '../../core/models/types';

@Component({
  selector: 'app-trabajadores',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="trabajadores-page">
      <!-- Header -->
      <div class="page-header">
        <div>
          <h1>Gestión de Trabajadores</h1>
          <p class="subtitle">
            Administra el expediente laboral de tus colaboradores, sus áreas y contactos de emergencia.
          </p>
        </div>
        <div class="header-actions">
          <button class="btn btn-secondary" (click)="openAreaModal()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect width="18" height="18" x="3" y="3" rx="2"/>
              <line x1="12" x2="12" y1="8" y2="16"/>
              <line x1="8" x2="16" y1="12" y2="12"/>
            </svg>
            <span>+ Nueva Área</span>
          </button>
          <button class="btn btn-primary" (click)="openFormModal()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <line x1="19" x2="19" y1="8" y2="14"/>
              <line x1="22" x2="16" y1="11" y2="11"/>
            </svg>
            <span>+ Registrar Trabajador</span>
          </button>
        </div>
      </div>

      <!-- Quick Metrics -->
      <div class="stats-grid">
        <div class="stat-card">
          <span class="stat-label">Total Colaboradores</span>
          <span class="stat-value">{{ trabajadores().length }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Personal Activo</span>
          <span class="stat-value text-emerald">{{ activosCount() }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Personal Inactivo</span>
          <span class="stat-value text-rose">{{ inactivosCount() }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Áreas Operativas</span>
          <span class="stat-value">{{ areas().length }}</span>
        </div>
      </div>

      <!-- Filters & Search -->
      <div class="filter-card">
        <div class="search-box">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.3-4.3"/>
          </svg>
          <input
            type="text"
            placeholder="Buscar por nombre, apellidos, CI o cargo..."
            [ngModel]="searchQuery()"
            (ngModelChange)="searchQuery.set($event)"
          />
        </div>

        <div class="filter-selects">
          <select [ngModel]="areaFilter()" (ngModelChange)="areaFilter.set($event)" class="form-control">
            <option value="">Todas las áreas</option>
            @for (a of areas(); track a.id) {
              <option [value]="a.id">{{ a.nombre }}</option>
            }
          </select>

          <select [ngModel]="statusFilter()" (ngModelChange)="statusFilter.set($event)" class="form-control">
            <option value="ALL">Todos los estados</option>
            <option value="ACTIVE">Solo Activos</option>
            <option value="INACTIVE">Solo Inactivos</option>
          </select>
        </div>
      </div>

      <!-- Workers Table -->
      <div class="card table-card">
        <div class="table-responsive">
          <table class="table">
            <thead>
              <tr>
                <th>CI</th>
                <th>Colaborador</th>
                <th>Cargo</th>
                <th>Área</th>
                <th>Sueldo Base</th>
                <th>Fecha Ingreso</th>
                <th>Emergencia</th>
                <th>Estado</th>
                <th style="text-align: right;">Acciones</th>
              </tr>
            </thead>
            <tbody>
              @for (t of filteredTrabajadores(); track t.id) {
                <tr>
                  <td>
                    <span class="ci-badge">{{ t.ci || 'Sin CI' }}</span>
                  </td>
                  <td>
                    <div class="worker-cell">
                      <div class="avatar-box">
                        {{ t.nombres[0] }}{{ t.apellidos[0] }}
                      </div>
                      <div class="worker-meta">
                        <strong>{{ t.nombres }} {{ t.apellidos }}</strong>
                        <small>{{ t.celular || 'Sin celular' }}</small>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span class="cargo-text">{{ t.cargo }}</span>
                  </td>
                  <td>
                    <span class="badge badge-slate">
                      {{ t.area?.nombre || 'General' }}
                    </span>
                  </td>
                  <td>
                    <strong class="salary-text">{{ formatSalary(t.sueldoBase) }}</strong>
                  </td>
                  <td>
                    <span class="date-text">{{ t.fecha_ingreso }}</span>
                  </td>
                  <td>
                    @if (t.contactos_emergencia && t.contactos_emergencia.length > 0) {
                      <span class="badge badge-blue">
                        {{ t.contactos_emergencia.length }} Contacto(s)
                      </span>
                    } @else {
                      <span class="text-muted" style="font-size: 0.775rem;">Ninguno</span>
                    }
                  </td>
                  <td>
                    @if (t.estado) {
                      <span class="badge badge-emerald">
                        <span class="dot-active"></span> Activo
                      </span>
                    } @else {
                      <span class="badge badge-rose">
                        <span class="dot-inactive"></span> Inactivo
                      </span>
                    }
                  </td>
                  <td style="text-align: right;">
                    <div class="actions-group">
                      <!-- Consultar -->
                      <button
                        class="btn btn-secondary btn-sm"
                        title="Consultar Detalle"
                        (click)="openDetailModal(t)"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
                          <circle cx="12" cy="12" r="3"/>
                        </svg>
                        <span>Consultar</span>
                      </button>

                      <!-- Editar -->
                      <button
                        class="btn btn-secondary btn-sm"
                        title="Editar Trabajador"
                        (click)="openFormModal(t)"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                        </svg>
                        <span>Editar</span>
                      </button>

                      <!-- Inactivar / Activar -->
                      <button
                        class="btn btn-sm"
                        [ngClass]="t.estado ? 'btn-danger' : 'btn-success'"
                        (click)="openConfirmToggle(t)"
                      >
                        {{ t.estado ? 'Inactivar' : 'Activar' }}
                      </button>
                    </div>
                  </td>
                </tr>
              } @empty {
                <tr>
                  <td colspan="9" class="empty-state">
                    No se encontraron trabajadores registrados con los criterios seleccionados.
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>

      <!-- MODAL: REGISTRAR / EDITAR TRABAJADOR -->
      @if (showFormModal()) {
        <div class="modal-backdrop" (click)="closeFormModal()">
          <div class="modal-dialog modal-lg" (click)="$event.stopPropagation()">
            <div class="modal-header">
              <h3>{{ isEditing() ? 'Editar Expediente de Trabajador' : 'Registrar Nuevo Trabajador' }}</h3>
              <button class="btn-close" (click)="closeFormModal()">✕</button>
            </div>

            <div class="modal-content">
              <form (ngSubmit)="saveTrabajador()">
                <!-- Sección 1: Datos Personales -->
                <div class="section-title">1. DATOS PERSONALES</div>
                <div class="form-grid">
                  <div class="form-group">
                    <label>Cédula de Identidad (CI)</label>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Ej. 7891234"
                      [(ngModel)]="form.ci"
                      name="ci"
                    />
                  </div>

                  <div class="form-group">
                    <label>Teléfono / Celular</label>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Ej. 70012345"
                      [(ngModel)]="form.celular"
                      name="celular"
                    />
                  </div>

                  <div class="form-group">
                    <label>Nombres *</label>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Nombres completos"
                      [(ngModel)]="form.nombres"
                      name="nombres"
                      required
                    />
                  </div>

                  <div class="form-group">
                    <label>Apellidos *</label>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Apellidos completos"
                      [(ngModel)]="form.apellidos"
                      name="apellidos"
                      required
                    />
                  </div>
                </div>

                <!-- Sección 2: Datos Laborales -->
                <div class="section-title">2. DATOS LABORALES & COMPENSACIÓN</div>
                <div class="form-grid">
                  <div class="form-group">
                    <label>Cargo / Puesto *</label>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Ej. Desarrollador Senior, Analista..."
                      [(ngModel)]="form.cargo"
                      name="cargo"
                      required
                    />
                  </div>

                  <div class="form-group">
                    <label>Sueldo Base (Bs.) *</label>
                    <input
                      type="number"
                      step="0.01"
                      class="form-control"
                      placeholder="0.00"
                      [(ngModel)]="form.sueldoBase"
                      name="sueldoBase"
                      required
                    />
                  </div>

                  <div class="form-group">
                    <label>Área de Trabajo</label>
                    <select class="form-control" [(ngModel)]="form.area_id" name="area_id">
                      <option [ngValue]="null">Selecciona un área...</option>
                      @for (a of areas(); track a.id) {
                        <option [ngValue]="a.id">{{ a.nombre }}</option>
                      }
                    </select>
                  </div>

                  <div class="form-group">
                    <label>Fecha de Ingreso *</label>
                    <input
                      type="date"
                      class="form-control"
                      [(ngModel)]="form.fecha_ingreso"
                      name="fecha_ingreso"
                      required
                    />
                  </div>
                </div>

                <!-- Sección 3: Contactos de Emergencia -->
                <div class="section-header-row">
                  <div class="section-title" style="margin-bottom: 0;">3. CONTACTO DE EMERGENCIA</div>
                  <button type="button" class="btn btn-secondary btn-sm" (click)="addContacto()">
                    + Agregar Contacto
                  </button>
                </div>

                <div class="contactos-list">
                  @for (c of form.contactos; track $index) {
                    <div class="contacto-item-card">
                      <div class="form-group" style="margin-bottom: 0;">
                        <label>Nombre Completo</label>
                        <input
                          type="text"
                          class="form-control"
                          placeholder="Nombre del familiar"
                          [(ngModel)]="c.nombrecompleto"
                          [name]="'c_nom_' + $index"
                          required
                        />
                      </div>
                      <div class="form-group" style="margin-bottom: 0;">
                        <label>Parentesco</label>
                        <input
                          type="text"
                          class="form-control"
                          placeholder="Ej. Esposa, Madre, Hermano"
                          [(ngModel)]="c.parentesco"
                          [name]="'c_par_' + $index"
                          required
                        />
                      </div>
                      <div class="form-group" style="margin-bottom: 0;">
                        <label>Celular</label>
                        <input
                          type="text"
                          class="form-control"
                          placeholder="Ej. 71234567"
                          [(ngModel)]="c.celular"
                          [name]="'c_cel_' + $index"
                          required
                        />
                      </div>
                      <button
                        type="button"
                        class="btn btn-danger btn-icon"
                        style="margin-top: 22px;"
                        title="Quitar contacto"
                        (click)="removeContacto($index)"
                      >
                        ✕
                      </button>
                    </div>
                  } @empty {
                    <div class="no-contactos">
                      <span>No se han registrado contactos de emergencia aún.</span>
                    </div>
                  }
                </div>

                <div class="modal-footer" style="margin-top: 24px;">
                  <button type="button" class="btn btn-secondary" (click)="closeFormModal()">
                    Cancelar
                  </button>
                  <button type="submit" class="btn btn-primary" [disabled]="saving() || !form.nombres || !form.apellidos || !form.cargo">
                    {{ saving() ? 'Guardando...' : (isEditing() ? 'Actualizar Trabajador' : 'Registrar Trabajador') }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      }

      <!-- MODAL: CONSULTAR DETALLE DEL TRABAJADOR -->
      @if (showDetailModal() && selectedTrabajador()) {
        <div class="modal-backdrop" (click)="closeDetailModal()">
          <div class="modal-dialog" (click)="$event.stopPropagation()">
            <div class="modal-header">
              <h3>Expediente del Colaborador</h3>
              <button class="btn-close" (click)="closeDetailModal()">✕</button>
            </div>

            <div class="modal-content">
              <div class="detail-profile-hero">
                <div class="profile-avatar">
                  {{ selectedTrabajador()!.nombres[0] }}{{ selectedTrabajador()!.apellidos[0] }}
                </div>
                <div class="profile-info">
                  <h2>{{ selectedTrabajador()!.nombres }} {{ selectedTrabajador()!.apellidos }}</h2>
                  <span class="profile-cargo">{{ selectedTrabajador()!.cargo }}</span>
                  <div class="profile-badges">
                    <span class="badge badge-slate">Área: {{ selectedTrabajador()!.area?.nombre || 'General' }}</span>
                    @if (selectedTrabajador()!.estado) {
                      <span class="badge badge-emerald">Activo</span>
                    } @else {
                      <span class="badge badge-rose">Inactivo</span>
                    }
                  </div>
                </div>
              </div>

              <div class="detail-info-grid">
                <div class="info-block">
                  <span class="info-label">Cédula de Identidad</span>
                  <strong class="info-val">{{ selectedTrabajador()!.ci || 'No registrada' }}</strong>
                </div>
                <div class="info-block">
                  <span class="info-label">Teléfono Móvil</span>
                  <strong class="info-val">{{ selectedTrabajador()!.celular || 'No registrado' }}</strong>
                </div>
                <div class="info-block">
                  <span class="info-label">Fecha de Ingreso</span>
                  <strong class="info-val">{{ selectedTrabajador()!.fecha_ingreso }}</strong>
                </div>
                <div class="info-block">
                  <span class="info-label">Sueldo Base</span>
                  <strong class="info-val text-emerald">{{ formatSalary(selectedTrabajador()!.sueldoBase) }}</strong>
                </div>
              </div>

              <!-- Contactos de Emergencia -->
              <div class="emergency-section">
                <h4>Contactos de Emergencia Registrados</h4>
                @if (selectedTrabajador()!.contactos_emergencia && selectedTrabajador()!.contactos_emergencia.length > 0) {
                  <div class="emergency-cards">
                    @for (ec of selectedTrabajador()!.contactos_emergencia; track ec.id) {
                      <div class="emergency-card">
                        <div class="ec-icon">
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                          </svg>
                        </div>
                        <div class="ec-meta">
                          <strong>{{ ec.nombrecompleto }}</strong>
                          <span>{{ ec.parentesco }} &bull; {{ ec.celular }}</span>
                        </div>
                      </div>
                    }
                  </div>
                } @else {
                  <p class="text-muted" style="font-size: 0.85rem;">No cuenta con contactos de emergencia asociados.</p>
                }
              </div>

              <div class="modal-footer">
                <button class="btn btn-secondary" (click)="closeDetailModal()">Cerrar</button>
                <button
                  class="btn"
                  [ngClass]="selectedTrabajador()!.estado ? 'btn-danger' : 'btn-success'"
                  (click)="openConfirmToggle(selectedTrabajador()!)"
                >
                  {{ selectedTrabajador()!.estado ? 'Inactivar Colaborador' : 'Activar Colaborador' }}
                </button>
                <button class="btn btn-primary" (click)="openFormModal(selectedTrabajador()!); closeDetailModal()">
                  Editar Expediente
                </button>
              </div>
            </div>
          </div>
        </div>
      }

      <!-- MODAL: NUEVA ÁREA -->
      @if (showAreaModal()) {
        <div class="modal-backdrop" (click)="closeAreaModal()">
          <div class="modal-dialog" (click)="$event.stopPropagation()">
            <div class="modal-header">
              <h3>Crear Nueva Área de Trabajo</h3>
              <button class="btn-close" (click)="closeAreaModal()">✕</button>
            </div>
            <div class="modal-content">
              <form (ngSubmit)="saveArea()">
                <div class="form-group">
                  <label>Nombre del Área *</label>
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Ej. Control de Calidad, Almacenes..."
                    [(ngModel)]="areaForm.nombre"
                    name="nombre_area"
                    required
                  />
                </div>
                <div class="form-group">
                  <label>Descripción</label>
                  <textarea
                    class="form-control"
                    placeholder="Objetivo o descripción del área..."
                    [(ngModel)]="areaForm.descripcion"
                    name="desc_area"
                  ></textarea>
                </div>
                <div class="modal-footer">
                  <button type="button" class="btn btn-secondary" (click)="closeAreaModal()">Cancelar</button>
                  <button type="submit" class="btn btn-primary" [disabled]="savingArea() || !areaForm.nombre">
                    {{ savingArea() ? 'Guardando...' : 'Crear Área' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      }

      <!-- MODAL: CONFIRMACIÓN INACTIVAR / ACTIVAR -->
      @if (showConfirmModal() && itemToToggle()) {
        <div class="modal-backdrop" (click)="closeConfirmModal()">
          <div class="modal-dialog" style="max-width: 440px;" (click)="$event.stopPropagation()">
            <div class="modal-header">
              <h3>{{ itemToToggle()!.estado ? '¿Inactivar Colaborador?' : '¿Activar Colaborador?' }}</h3>
              <button class="btn-close" (click)="closeConfirmModal()">✕</button>
            </div>
            <div class="modal-content">
              <p style="font-size: 0.95rem; color: var(--text-secondary); line-height: 1.5;">
                ¿Estás seguro de que deseas {{ itemToToggle()!.estado ? 'inactivar' : 'activar' }} a
                <strong>{{ itemToToggle()!.nombres }} {{ itemToToggle()!.apellidos }}</strong>?
              </p>
              <p style="font-size: 0.825rem; color: var(--text-muted); margin-top: 8px;">
                {{ itemToToggle()!.estado ? 'El colaborador no figurará como activo en el sistema hasta que vuelva a ser reactivado.' : 'El colaborador recuperará su estado activo en el sistema.' }}
              </p>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" (click)="closeConfirmModal()">Cancelar</button>
              <button
                type="button"
                class="btn"
                [ngClass]="itemToToggle()!.estado ? 'btn-danger' : 'btn-success'"
                [disabled]="togglingStatus()"
                (click)="confirmToggle()"
              >
                {{ togglingStatus() ? 'Procesando...' : (itemToToggle()!.estado ? 'Sí, Inactivar' : 'Sí, Activar') }}
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .trabajadores-page {
      display: flex;
      flex-direction: column;
      gap: 22px;
    }

    .page-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;

      h1 {
        font-size: 1.45rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: var(--text-primary);
      }

      .subtitle {
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin-top: 3px;
      }

      .header-actions {
        display: flex;
        gap: 10px;
      }
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 14px;
    }

    .stat-card {
      background-color: #ffffff;
      border: 1px solid var(--border-default);
      border-radius: var(--radius-lg);
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      box-shadow: var(--shadow-xs);

      .stat-label {
        font-size: 0.775rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
      }

      .stat-value {
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        color: var(--text-primary);

        &.text-emerald { color: var(--accent-emerald); }
        &.text-rose { color: var(--accent-rose); }
      }
    }

    .filter-card {
      background-color: #ffffff;
      border: 1px solid var(--border-default);
      border-radius: var(--radius-lg);
      padding: 14px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      flex-wrap: wrap;
      box-shadow: var(--shadow-xs);

      .search-box {
        display: flex;
        align-items: center;
        gap: 10px;
        flex: 1;
        min-width: 260px;
        background-color: var(--bg-subtle);
        border: 1px solid var(--border-default);
        border-radius: var(--radius-md);
        padding: 8px 14px;

        svg { color: var(--text-muted); }

        input {
          border: none;
          background: transparent;
          outline: none;
          width: 100%;
          font-size: 0.875rem;
          color: var(--text-primary);
        }
      }

      .filter-selects {
        display: flex;
        gap: 10px;

        select {
          min-width: 160px;
          padding: 8px 12px;
        }
      }
    }

    .table-card {
      padding: 0;
    }

    .ci-badge {
      font-family: monospace;
      font-weight: 600;
      font-size: 0.825rem;
      color: var(--text-secondary);
      background-color: var(--bg-muted);
      padding: 2px 6px;
      border-radius: var(--radius-xs);
    }

    .worker-cell {
      display: flex;
      align-items: center;
      gap: 12px;

      .avatar-box {
        width: 32px;
        height: 32px;
        background-color: #eff6ff;
        color: #1d4ed8;
        border: 1px solid #bfdbfe;
        border-radius: 50%;
        font-weight: 600;
        font-size: 0.775rem;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .worker-meta {
        display: flex;
        flex-direction: column;
        line-height: 1.25;

        strong {
          font-size: 0.875rem;
          color: var(--text-primary);
        }
        small {
          font-size: 0.75rem;
          color: var(--text-muted);
        }
      }
    }

    .cargo-text {
      font-weight: 500;
      color: var(--text-primary);
    }

    .salary-text {
      font-family: monospace;
      font-size: 0.9rem;
      color: var(--text-primary);
    }

    .date-text {
      font-size: 0.825rem;
      color: var(--text-secondary);
    }

    .dot-active {
      width: 6px;
      height: 6px;
      background-color: var(--accent-emerald);
      border-radius: 50%;
      display: inline-block;
    }

    .dot-inactive {
      width: 6px;
      height: 6px;
      background-color: var(--accent-rose);
      border-radius: 50%;
      display: inline-block;
    }

    .actions-group {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 6px;
    }

    .empty-state {
      text-align: center;
      padding: 36px 16px;
      color: var(--text-muted);
      font-size: 0.9rem;
    }

    /* Modal Styling */
    .section-title {
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--text-muted);
      margin-bottom: 12px;
      margin-top: 6px;
    }

    .section-header-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 14px;
      margin-bottom: 12px;
    }

    .form-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 14px;

      @media (max-width: 640px) {
        grid-template-columns: 1fr;
      }
    }

    .contactos-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .contacto-item-card {
      display: grid;
      grid-template-columns: 2fr 1.5fr 1.5fr auto;
      gap: 10px;
      align-items: center;
      padding: 10px 12px;
      background-color: var(--bg-subtle);
      border: 1px solid var(--border-default);
      border-radius: var(--radius-md);

      @media (max-width: 640px) {
        grid-template-columns: 1fr;
      }
    }

    .no-contactos {
      padding: 16px;
      text-align: center;
      border: 1px dashed var(--border-default);
      border-radius: var(--radius-md);
      color: var(--text-muted);
      font-size: 0.825rem;
    }

    /* Detail View Styling */
    .detail-profile-hero {
      display: flex;
      align-items: center;
      gap: 16px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border-subtle);

      .profile-avatar {
        width: 64px;
        height: 64px;
        background-color: var(--primary);
        color: #ffffff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.35rem;
        font-weight: 700;
      }

      .profile-info {
        display: flex;
        flex-direction: column;
        gap: 4px;

        h2 {
          font-size: 1.25rem;
          font-weight: 700;
          color: var(--text-primary);
          letter-spacing: -0.015em;
        }

        .profile-cargo {
          font-size: 0.9rem;
          color: var(--text-secondary);
        }

        .profile-badges {
          display: flex;
          gap: 6px;
          margin-top: 4px;
        }
      }
    }

    .detail-info-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 14px;
      padding: 20px 0;
      border-bottom: 1px solid var(--border-subtle);

      .info-block {
        display: flex;
        flex-direction: column;
        gap: 2px;

        .info-label {
          font-size: 0.75rem;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .info-val {
          font-size: 0.925rem;
          color: var(--text-primary);

          &.text-emerald { color: var(--accent-emerald); }
        }
      }
    }

    .emergency-section {
      padding: 20px 0;

      h4 {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 12px;
      }

      .emergency-cards {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .emergency-card {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 14px;
        background-color: var(--bg-subtle);
        border: 1px solid var(--border-default);
        border-radius: var(--radius-md);

        .ec-icon {
          color: var(--accent-blue);
        }

        .ec-meta {
          display: flex;
          flex-direction: column;
          line-height: 1.25;

          strong {
            font-size: 0.875rem;
            color: var(--text-primary);
          }
          span {
            font-size: 0.775rem;
            color: var(--text-secondary);
          }
        }
      }
    }
  `]
})
export class TrabajadoresComponent implements OnInit {
  private dataService = inject(DataService);
  private toast = inject(ToastService);

  public trabajadores = signal<Trabajador[]>([]);
  public areas = signal<Area[]>([]);

  public searchQuery = signal<string>('');
  public areaFilter = signal<string>('');
  public statusFilter = signal<string>('ALL');

  public showFormModal = signal(false);
  public isEditing = signal(false);
  public saving = signal(false);

  public showDetailModal = signal(false);
  public selectedTrabajador = signal<Trabajador | null>(null);

  public showAreaModal = signal(false);
  public savingArea = signal(false);

  public showConfirmModal = signal(false);
  public itemToToggle = signal<Trabajador | null>(null);
  public togglingStatus = signal(false);

  // Forms
  public form: any = {
    id: null,
    ci: '',
    nombres: '',
    apellidos: '',
    fotografia: '',
    celular: '',
    fecha_ingreso: new Date().toISOString().substring(0, 10),
    cargo: '',
    sueldoBase: 0,
    area_id: null,
    contactos: []
  };

  public areaForm = {
    nombre: '',
    descripcion: ''
  };

  ngOnInit(): void {
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.dataService.getTrabajadores().subscribe({
      next: (data) => this.trabajadores.set(data),
      error: () => this.toast.error('Error al cargar trabajadores')
    });

    this.dataService.getAreas().subscribe({
      next: (data) => this.areas.set(data),
      error: () => this.toast.error('Error al cargar áreas')
    });
  }

  public activosCount = computed(() => this.trabajadores().filter(t => t.estado).length);
  public inactivosCount = computed(() => this.trabajadores().filter(t => !t.estado).length);

  public filteredTrabajadores = computed(() => {
    let list = this.trabajadores();
    const rawQuery = this.searchQuery().trim();

    if (rawQuery) {
      const normalizeText = (text: string) =>
        (text || '')
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '')
          .toLowerCase();

      const queryNormalized = normalizeText(rawQuery);
      const queryTerms = queryNormalized.split(/\s+/).filter(Boolean);

      list = list.filter(t => {
        const nombres = t.nombres || '';
        const apellidos = t.apellidos || '';
        const ci = t.ci || '';
        const cargo = t.cargo || '';
        const area = t.area?.nombre || '';

        const searchableString = normalizeText(`${nombres} ${apellidos} ${apellidos} ${nombres} ${ci} ${cargo} ${area}`);

        return queryTerms.every(term => searchableString.includes(term));
      });
    }

    const currentArea = this.areaFilter();
    if (currentArea) {
      const aId = Number(currentArea);
      list = list.filter(t => t.area_id === aId);
    }

    const currentStatus = this.statusFilter();
    if (currentStatus === 'ACTIVE') {
      list = list.filter(t => t.estado);
    } else if (currentStatus === 'INACTIVE') {
      list = list.filter(t => !t.estado);
    }

    return list;
  });

  formatSalary(amount: number): string {
    return new Intl.NumberFormat('es-BO', { style: 'currency', currency: 'BOB' }).format(amount);
  }

  // Form Modal
  openFormModal(trab?: Trabajador): void {
    if (trab) {
      this.isEditing.set(true);
      this.form = {
        id: trab.id,
        ci: trab.ci || '',
        nombres: trab.nombres,
        apellidos: trab.apellidos,
        fotografia: trab.fotografia || '',
        celular: trab.celular || '',
        fecha_ingreso: trab.fecha_ingreso,
        cargo: trab.cargo,
        sueldoBase: trab.sueldoBase,
        area_id: trab.area_id || null,
        contactos: (trab.contactos_emergencia || []).map(c => ({
          nombrecompleto: c.nombrecompleto,
          parentesco: c.parentesco,
          celular: c.celular
        }))
      };
    } else {
      this.isEditing.set(false);
      this.form = {
        id: null,
        ci: '',
        nombres: '',
        apellidos: '',
        fotografia: '',
        celular: '',
        fecha_ingreso: new Date().toISOString().substring(0, 10),
        cargo: '',
        sueldoBase: 3500,
        area_id: this.areas()[0]?.id || null,
        contactos: []
      };
    }
    this.showFormModal.set(true);
  }

  closeFormModal(): void {
    this.showFormModal.set(false);
  }

  addContacto(): void {
    this.form.contactos.push({
      nombrecompleto: '',
      parentesco: '',
      celular: ''
    });
  }

  removeContacto(index: number): void {
    this.form.contactos.splice(index, 1);
  }

  saveTrabajador(): void {
    this.saving.set(true);
    if (this.isEditing()) {
      this.dataService.updateTrabajador(this.form.id, this.form).subscribe({
        next: () => {
          this.saving.set(false);
          this.toast.success(`Trabajador ${this.form.nombres} actualizado`);
          this.closeFormModal();
          this.cargarDatos();
        },
        error: (err) => {
          this.saving.set(false);
          this.toast.error(err.error?.detail || 'Error al actualizar trabajador');
        }
      });
    } else {
      this.dataService.createTrabajador(this.form).subscribe({
        next: () => {
          this.saving.set(false);
          this.toast.success(`Trabajador ${this.form.nombres} registrado con éxito`);
          this.closeFormModal();
          this.cargarDatos();
        },
        error: (err) => {
          this.saving.set(false);
          this.toast.error(err.error?.detail || 'Error al registrar trabajador');
        }
      });
    }
  }

  openConfirmToggle(trab: Trabajador): void {
    this.itemToToggle.set(trab);
    this.showConfirmModal.set(true);
  }

  closeConfirmModal(): void {
    this.showConfirmModal.set(false);
    this.itemToToggle.set(null);
  }

  confirmToggle(): void {
    const trab = this.itemToToggle();
    if (!trab) return;

    this.togglingStatus.set(true);
    this.dataService.toggleTrabajadorStatus(trab.id).subscribe({
      next: (updated) => {
        this.togglingStatus.set(false);
        this.closeConfirmModal();
        const msg = updated.estado ? 'Trabajador activado con éxito' : 'Trabajador inactivado con éxito';
        this.toast.info(msg);
        this.cargarDatos();
        if (this.selectedTrabajador() && this.selectedTrabajador()!.id === updated.id) {
          this.selectedTrabajador.set(updated);
        }
      },
      error: (err) => {
        this.togglingStatus.set(false);
        this.toast.error(err.error?.detail || 'Error al modificar estado');
      }
    });
  }

  // Detail Modal
  openDetailModal(trab: Trabajador): void {
    this.selectedTrabajador.set(trab);
    this.showDetailModal.set(true);
  }

  closeDetailModal(): void {
    this.showDetailModal.set(false);
    this.selectedTrabajador.set(null);
  }

  // Area Modal
  openAreaModal(): void {
    this.areaForm = { nombre: '', descripcion: '' };
    this.showAreaModal.set(true);
  }

  closeAreaModal(): void {
    this.showAreaModal.set(false);
  }

  saveArea(): void {
    this.savingArea.set(true);
    this.dataService.createArea(this.areaForm).subscribe({
      next: (nueva) => {
        this.savingArea.set(false);
        this.toast.success(`Área "${nueva.nombre}" creada exitosamente`);
        this.closeAreaModal();
        this.cargarDatos();
      },
      error: (err) => {
        this.savingArea.set(false);
        this.toast.error(err.error?.detail || 'Error al crear área');
      }
    });
  }
}
