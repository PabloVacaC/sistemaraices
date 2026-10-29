import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DataService } from '../../core/services/data.service';
import { ToastService } from '../../core/services/toast.service';
import { Usuario, Rol, Permiso } from '../../core/models/types';

@Component({
  selector: 'app-usuarios',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="usuarios-page">
      <!-- Page Header -->
      <div class="page-header">
        <div>
          <h1>Gestión de Usuarios y Accesos</h1>
          <p class="subtitle">
            Administra los usuarios del sistema, sus roles y define a qué ventanas y funciones tienen permiso.
          </p>
        </div>
        <div class="header-actions">
          <button class="btn btn-secondary" (click)="openRoleModal()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>
            </svg>
            <span>+ Nuevo Rol</span>
          </button>
          <button class="btn btn-primary" (click)="openUserModal()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <line x1="19" x2="19" y1="8" y2="14"/>
              <line x1="22" x2="16" y1="11" y2="11"/>
            </svg>
            <span>+ Registrar Usuario</span>
          </button>
        </div>
      </div>

      <!-- Quick Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <span class="stat-label">Total Usuarios</span>
          <span class="stat-value">{{ usuarios().length }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Usuarios Activos</span>
          <span class="stat-value text-emerald">{{ activosCount() }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Usuarios Inactivos</span>
          <span class="stat-value text-rose">{{ inactivosCount() }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Roles Configurados</span>
          <span class="stat-value">{{ roles().length }}</span>
        </div>
      </div>

      <!-- Filter & Search Bar -->
      <div class="filter-card">
        <div class="search-box">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.3-4.3"/>
          </svg>
          <input
            type="text"
            placeholder="Buscar por CI, nombre, apellido o correo..."
            [ngModel]="searchQuery()"
            (ngModelChange)="searchQuery.set($event)"
          />
        </div>

        <div class="filter-selects">
          <select [ngModel]="roleFilter()" (ngModelChange)="roleFilter.set($event)" class="form-control">
            <option value="">Todos los roles</option>
            @for (r of roles(); track r.id) {
              <option [value]="r.id">{{ r.rol }}</option>
            }
          </select>

          <select [ngModel]="statusFilter()" (ngModelChange)="statusFilter.set($event)" class="form-control">
            <option value="ALL">Todos los estados</option>
            <option value="ACTIVE">Solo Activos</option>
            <option value="INACTIVE">Solo Inactivos</option>
          </select>
        </div>
      </div>

      <!-- Users Table Card -->
      <div class="card table-card">
        <div class="table-responsive">
          <table class="table">
            <thead>
              <tr>
                <th>CI</th>
                <th>Usuario</th>
                <th>Contacto</th>
                <th>Rol Asignado</th>
                <th>Ventanas / Permisos</th>
                <th>Estado</th>
                <th style="text-align: right;">Acciones</th>
              </tr>
            </thead>
            <tbody>
              @for (u of filteredUsuarios(); track u.ci) {
                <tr>
                  <td>
                    <span class="ci-badge">{{ u.ci }}</span>
                  </td>
                  <td>
                    <div class="user-cell">
                      <div class="user-avatar-small">
                        {{ u.nombre[0] }}{{ u.apellido[0] }}
                      </div>
                      <div class="user-cell-meta">
                        <strong>{{ u.nombre }} {{ u.apellido }}</strong>
                        <small>{{ u.email }}</small>
                      </div>
                    </div>
                  </td>
                  <td>
                    <div class="contact-meta">
                      <span>{{ u.telefono || 'Sin teléfono' }}</span>
                      <small>{{ u.direccion || 'Sin dirección' }}</small>
                    </div>
                  </td>
                  <td>
                    <span class="badge badge-slate">
                      {{ u.rol?.rol || 'Sin Rol' }}
                    </span>
                  </td>
                  <td>
                    <div class="permissions-pill-list">
                      @if (u.rol?.niveljerarquico === 1) {
                        <span class="badge badge-emerald">Acceso Total</span>
                      } @else {
                        @for (p of u.rol?.permisos; track p.id) {
                          <span class="badge badge-blue">{{ getPermisoLabel(p.permisos) }}</span>
                        }
                      }
                    </div>
                  </td>
                  <td>
                    @if (u.estado) {
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
                      <button
                        class="btn btn-secondary btn-sm"
                        title="Editar Usuario"
                        (click)="openUserModal(u)"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                        </svg>
                        <span>Editar</span>
                      </button>

                      <button
                        class="btn btn-sm"
                        [ngClass]="u.estado ? 'btn-danger' : 'btn-success'"
                        (click)="openConfirmToggle(u)"
                      >
                        {{ u.estado ? 'Inactivar' : 'Activar' }}
                      </button>
                    </div>
                  </td>
                </tr>
              } @empty {
                <tr>
                  <td colspan="7" class="empty-state">
                    No se encontraron usuarios registrados o coincidentes con los filtros.
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>

      <!-- MODAL: CREAR / EDITAR USUARIO -->
      @if (showUserModal()) {
        <div class="modal-backdrop" (click)="closeUserModal()">
          <div class="modal-dialog modal-lg" (click)="$event.stopPropagation()">
            <div class="modal-header">
              <h3>{{ isEditingUser() ? 'Modificar Usuario' : 'Registrar Nuevo Usuario' }}</h3>
              <button class="btn-close" (click)="closeUserModal()">✕</button>
            </div>

            <div class="modal-content">
              <form (ngSubmit)="saveUser()">
                <div class="form-grid">
                  <!-- CI -->
                  <div class="form-group">
                    <label>Cédula de Identidad (CI) *</label>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Ej. 8492019"
                      [(ngModel)]="userForm.ci"
                      name="ci"
                      [disabled]="isEditingUser()"
                      required
                    />
                  </div>

                  <!-- Email -->
                  <div class="form-group">
                    <label>Correo Electrónico *</label>
                    <input
                      type="email"
                      class="form-control"
                      placeholder="usuario@raices.com"
                      [(ngModel)]="userForm.email"
                      name="email"
                      required
                    />
                  </div>

                  <!-- Nombres -->
                  <div class="form-group">
                    <label>Nombres *</label>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Ej. Juan"
                      [(ngModel)]="userForm.nombre"
                      name="nombre"
                      required
                    />
                  </div>

                  <!-- Apellidos -->
                  <div class="form-group">
                    <label>Apellidos *</label>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Ej. Pérez"
                      [(ngModel)]="userForm.apellido"
                      name="apellido"
                      required
                    />
                  </div>

                  <!-- Contraseña -->
                  <div class="form-group">
                    <label>{{ isEditingUser() ? 'Nueva Contraseña (dejar en blanco para conservar)' : 'Contraseña de Acceso *' }}</label>
                    <input
                      type="password"
                      class="form-control"
                      placeholder="Mínimo 6 caracteres"
                      [(ngModel)]="userForm.contrasena"
                      name="contraseña"
                      [required]="!isEditingUser()"
                    />
                  </div>

                  <!-- Rol -->
                  <div class="form-group">
                    <label>Rol de Usuario *</label>
                    <select
                      class="form-control"
                      [(ngModel)]="userForm.rol_id"
                      name="rol_id"
                      required
                    >
                      <option [ngValue]="null" disabled>Selecciona un rol</option>
                      @for (r of roles(); track r.id) {
                        <option [ngValue]="r.id">{{ r.rol }} (Nivel {{ r.niveljerarquico }})</option>
                      }
                    </select>
                  </div>

                  <!-- Género -->
                  <div class="form-group">
                    <label>Género</label>
                    <select class="form-control" [(ngModel)]="userForm.genero" name="genero">
                      <option value="">No especificado</option>
                      <option value="Masculino">Masculino</option>
                      <option value="Femenino">Femenino</option>
                      <option value="Otro">Otro</option>
                    </select>
                  </div>

                  <!-- Teléfono -->
                  <div class="form-group">
                    <label>Teléfono / Celular</label>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Ej. 78901234"
                      [(ngModel)]="userForm.telefono"
                      name="telefono"
                    />
                  </div>

                  <!-- Fecha Nacimiento -->
                  <div class="form-group">
                    <label>Fecha de Nacimiento</label>
                    <input
                      type="date"
                      class="form-control"
                      [(ngModel)]="userForm.fechanacimiento"
                      name="fechanacimiento"
                    />
                  </div>

                  <!-- Dirección -->
                  <div class="form-group">
                    <label>Dirección</label>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Calle, Barrio, Ciudad..."
                      [(ngModel)]="userForm.direccion"
                      name="direccion"
                    />
                  </div>
                </div>

                <!-- Preview de Permisos del Rol Seleccionado -->
                @if (selectedRolePermissions().length > 0) {
                  <div class="role-permissions-preview">
                    <h4>Ventanas y Acciones habilitadas para este usuario:</h4>
                    <div class="preview-tags">
                      @for (perm of selectedRolePermissions(); track perm) {
                        <span class="badge badge-blue">✓ {{ getPermisoLabel(perm) }}</span>
                      }
                    </div>
                  </div>
                }

                <div class="modal-footer">
                  <button type="button" class="btn btn-secondary" (click)="closeUserModal()">
                    Cancelar
                  </button>
                  <button type="submit" class="btn btn-primary" [disabled]="savingUser()">
                    {{ savingUser() ? 'Guardando...' : (isEditingUser() ? 'Actualizar Usuario' : 'Crear Usuario') }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      }

      <!-- MODAL: CREAR NUEVO ROL CON PERMISOS -->
      @if (showRoleModal()) {
        <div class="modal-backdrop" (click)="closeRoleModal()">
          <div class="modal-dialog" (click)="$event.stopPropagation()">
            <div class="modal-header">
              <h3>Crear Nuevo Rol y Asignar Ventanas</h3>
              <button class="btn-close" (click)="closeRoleModal()">✕</button>
            </div>

            <div class="modal-content">
              <form (ngSubmit)="saveRole()">
                <div class="form-group">
                  <label>Nombre del Rol *</label>
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Ej. Jefe de Almacén, Supervisor..."
                    [(ngModel)]="roleForm.rol"
                    name="rol"
                    required
                  />
                </div>

                <div class="form-group">
                  <label>Nivel Jerárquico * (1: Máximo, 2: Medio, 3: Operativo)</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    class="form-control"
                    [(ngModel)]="roleForm.niveljerarquico"
                    name="niveljerarquico"
                    required
                  />
                </div>

                <div class="form-group">
                  <label>Descripción</label>
                  <textarea
                    class="form-control"
                    placeholder="Describe las responsabilidades del rol..."
                    [(ngModel)]="roleForm.descripcion"
                    name="descripcion"
                  ></textarea>
                </div>

                <div class="permissions-selection-box">
                  <label>Selecciona las ventanas y acciones permitidas:</label>
                  <div class="checkbox-grid">
                    @for (perm of permisos(); track perm.id) {
                      <label class="checkbox-card">
                        <input
                          type="checkbox"
                          [checked]="isPermisoSelected(perm.id)"
                          (change)="togglePermisoSelection(perm.id)"
                        />
                        <div class="checkbox-meta">
                          <strong>{{ getPermisoLabel(perm.permisos) }}</strong>
                          <small>{{ perm.permisos }}</small>
                        </div>
                      </label>
                    }
                  </div>
                </div>

                <div class="modal-footer">
                  <button type="button" class="btn btn-secondary" (click)="closeRoleModal()">
                    Cancelar
                  </button>
                  <button type="submit" class="btn btn-primary" [disabled]="savingRole() || !roleForm.rol">
                    {{ savingRole() ? 'Creando...' : 'Guardar Rol' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      }

      <!-- MODAL: CONFIRMAR INACTIVAR / ACTIVAR USUARIO -->
      @if (showConfirmModal() && userToToggle()) {
        <div class="modal-backdrop" (click)="closeConfirmModal()">
          <div class="modal-dialog" style="max-width: 440px;" (click)="$event.stopPropagation()">
            <div class="modal-header">
              <h3>{{ userToToggle()!.estado ? '¿Inactivar Usuario?' : '¿Activar Usuario?' }}</h3>
              <button class="btn-close" (click)="closeConfirmModal()">✕</button>
            </div>
            <div class="modal-content">
              <p style="font-size: 0.95rem; color: var(--text-secondary); line-height: 1.5;">
                ¿Estás seguro de que deseas {{ userToToggle()!.estado ? 'inactivar' : 'activar' }} al usuario
                <strong>{{ userToToggle()!.nombre }} {{ userToToggle()!.apellido }}</strong> (CI: {{ userToToggle()!.ci }})?
              </p>
              <p style="font-size: 0.825rem; color: var(--text-muted); margin-top: 8px;">
                {{ userToToggle()!.estado ? 'El usuario no podrá acceder ni iniciar sesión en el sistema mientras se encuentre inactivo.' : 'El usuario podrá acceder al sistema normalmente.' }}
              </p>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" (click)="closeConfirmModal()">Cancelar</button>
              <button
                type="button"
                class="btn"
                [ngClass]="userToToggle()!.estado ? 'btn-danger' : 'btn-success'"
                [disabled]="togglingStatus()"
                (click)="confirmToggle()"
              >
                {{ togglingStatus() ? 'Procesando...' : (userToToggle()!.estado ? 'Sí, Inactivar' : 'Sí, Activar') }}
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .usuarios-page {
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

        svg {
          color: var(--text-muted);
        }

        input {
          border: none;
          background: transparent;
          outline: none;
          width: 100%;
          font-size: 0.875rem;
          color: var(--text-primary);

          &::placeholder {
            color: var(--text-muted);
          }
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

    .user-cell {
      display: flex;
      align-items: center;
      gap: 12px;

      .user-avatar-small {
        width: 32px;
        height: 32px;
        background-color: #f1f5f9;
        color: #0f172a;
        border: 1px solid var(--border-default);
        border-radius: 50%;
        font-weight: 600;
        font-size: 0.775rem;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .user-cell-meta {
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

    .contact-meta {
      display: flex;
      flex-direction: column;
      line-height: 1.25;
      font-size: 0.825rem;

      small {
        color: var(--text-muted);
        font-size: 0.725rem;
      }
    }

    .permissions-pill-list {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      max-width: 280px;
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

    .form-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 14px;

      @media (max-width: 640px) {
        grid-template-columns: 1fr;
      }
    }

    .role-permissions-preview {
      margin-top: 18px;
      padding: 14px;
      background-color: var(--bg-subtle);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);

      h4 {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 8px;
      }

      .preview-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }
    }

    .permissions-selection-box {
      margin-top: 14px;

      label {
        font-size: 0.8125rem;
        font-weight: 600;
        color: var(--text-secondary);
        display: block;
        margin-bottom: 8px;
      }

      .checkbox-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
        gap: 8px;
        max-height: 220px;
        overflow-y: auto;
        padding: 4px;
      }

      .checkbox-card {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 8px 10px;
        background-color: var(--bg-subtle);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-sm);
        cursor: pointer;
        transition: background-color var(--transition-fast);

        &:hover {
          background-color: #ffffff;
          border-color: var(--border-default);
        }

        input {
          margin-top: 3px;
        }

        .checkbox-meta {
          display: flex;
          flex-direction: column;
          line-height: 1.2;

          strong {
            font-size: 0.8rem;
            color: var(--text-primary);
          }
          small {
            font-size: 0.7rem;
            color: var(--text-muted);
          }
        }
      }
    }
  `]
})
export class UsuariosComponent implements OnInit {
  private dataService = inject(DataService);
  private toast = inject(ToastService);

  public usuarios = signal<Usuario[]>([]);
  public roles = signal<Rol[]>([]);
  public permisos = signal<Permiso[]>([]);

  public searchQuery = signal<string>('');
  public roleFilter = signal<string>('');
  public statusFilter = signal<string>('ALL');

  public showUserModal = signal(false);
  public isEditingUser = signal(false);
  public savingUser = signal(false);

  public showRoleModal = signal(false);
  public savingRole = signal(false);

  public showConfirmModal = signal(false);
  public userToToggle = signal<Usuario | null>(null);
  public togglingStatus = signal(false);

  // Forms state
  public userForm: any = {
    ci: '',
    nombre: '',
    apellido: '',
    email: '',
    contrasena: '',
    rol_id: null,
    genero: '',
    fechanacimiento: '',
    telefono: '',
    direccion: '',
    estado: true
  };

  public roleForm: any = {
    rol: '',
    niveljerarquico: 2,
    descripcion: '',
    permiso_ids: []
  };

  ngOnInit(): void {
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.dataService.getUsers().subscribe({
      next: (data) => this.usuarios.set(data),
      error: (err) => this.toast.error('Error al cargar usuarios')
    });

    this.dataService.getRoles().subscribe({
      next: (data) => this.roles.set(data),
      error: (err) => this.toast.error('Error al cargar roles')
    });

    this.dataService.getPermisos().subscribe({
      next: (data) => this.permisos.set(data),
      error: (err) => this.toast.error('Error al cargar permisos')
    });
  }

  public activosCount = computed(() => this.usuarios().filter(u => u.estado).length);
  public inactivosCount = computed(() => this.usuarios().filter(u => !u.estado).length);

  public filteredUsuarios = computed(() => {
    let list = this.usuarios();
    const rawQuery = this.searchQuery().trim();

    if (rawQuery) {
      const normalizeText = (text: string) =>
        (text || '')
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '')
          .toLowerCase();

      const queryNormalized = normalizeText(rawQuery);
      const queryTerms = queryNormalized.split(/\s+/).filter(Boolean);

      list = list.filter(u => {
        const nombre = u.nombre || '';
        const apellido = u.apellido || '';
        const ci = u.ci || '';
        const email = u.email || '';
        const telefono = u.telefono || '';
        const rol = u.rol?.rol || '';

        const searchableString = normalizeText(`${nombre} ${apellido} ${apellido} ${nombre} ${ci} ${email} ${telefono} ${rol}`);

        return queryTerms.every(term => searchableString.includes(term));
      });
    }

    const currentRole = this.roleFilter();
    if (currentRole) {
      const rId = Number(currentRole);
      list = list.filter(u => u.rol_id === rId);
    }

    const currentStatus = this.statusFilter();
    if (currentStatus === 'ACTIVE') {
      list = list.filter(u => u.estado);
    } else if (currentStatus === 'INACTIVE') {
      list = list.filter(u => !u.estado);
    }

    return list;
  });

  public selectedRolePermissions = computed(() => {
    const rolId = this.userForm.rol_id;
    if (!rolId) return [];
    const r = this.roles().find(x => x.id === Number(rolId));
    if (!r) return [];
    if (r.niveljerarquico === 1) return ['Acceso Total al Sistema'];
    return r.permisos.map(p => p.permisos);
  });

  getPermisoLabel(permisoStr: string): string {
    const map: Record<string, string> = {
      'GESTION_USUARIOS': 'Ver Usuarios',
      'CREAR_USUARIO': 'Crear Usuarios',
      'EDITAR_USUARIO': 'Modificar Usuarios',
      'ESTADO_USUARIO': 'Activar/Inactivar Usuarios',
      'GESTION_ROLES': 'Configurar Roles y Permisos',
      'GESTION_TRABAJADORES': 'Ver Trabajadores',
      'REGISTRAR_TRABAJADOR': 'Registrar Trabajador',
      'EDITAR_TRABAJADOR': 'Modificar Trabajador',
      'INACTIVAR_TRABAJADOR': 'Inactivar Trabajador',
      'GESTION_AREAS': 'Gestionar Áreas',
      'VER_BITACORA': 'Ver Bitácora de Auditoría'
    };
    return map[permisoStr] || permisoStr;
  }

  // --- Modal Usuario ---
  openUserModal(user?: Usuario): void {
    if (user) {
      this.isEditingUser.set(true);
      this.userForm = {
        ci: user.ci,
        nombre: user.nombre,
        apellido: user.apellido,
        email: user.email,
        contrasena: '',
        rol_id: user.rol_id,
        genero: user.genero || '',
        fechanacimiento: user.fechanacimiento || '',
        telefono: user.telefono || '',
        direccion: user.direccion || '',
        estado: user.estado
      };
    } else {
      this.isEditingUser.set(false);
      this.userForm = {
        ci: '',
        nombre: '',
        apellido: '',
        email: '',
        contrasena: '',
        rol_id: this.roles()[0]?.id || null,
        genero: '',
        fechanacimiento: '',
        telefono: '',
        direccion: '',
        estado: true
      };
    }
    this.showUserModal.set(true);
  }

  closeUserModal(): void {
    this.showUserModal.set(false);
  }

  saveUser(): void {
    this.savingUser.set(true);
    const payload: any = {
      ci: this.userForm.ci,
      nombre: this.userForm.nombre,
      apellido: this.userForm.apellido,
      email: this.userForm.email,
      rol_id: Number(this.userForm.rol_id),
      genero: this.userForm.genero || null,
      fechanacimiento: this.userForm.fechanacimiento || null,
      telefono: this.userForm.telefono || null,
      direccion: this.userForm.direccion || null,
      estado: this.userForm.estado
    };
    if (this.userForm.contrasena && this.userForm.contrasena.trim()) {
      payload.contraseña = this.userForm.contrasena;
    }

    if (this.isEditingUser()) {
      this.dataService.updateUser(this.userForm.ci, payload).subscribe({
        next: () => {
          this.savingUser.set(false);
          this.toast.success(`Usuario ${this.userForm.nombre} actualizado`);
          this.closeUserModal();
          this.cargarDatos();
        },
        error: (err) => {
          this.savingUser.set(false);
          this.toast.error(err.error?.detail || 'Error al actualizar usuario');
        }
      });
    } else {
      this.dataService.createUser(payload).subscribe({
        next: () => {
          this.savingUser.set(false);
          this.toast.success(`Usuario ${this.userForm.nombre} creado exitosamente`);
          this.closeUserModal();
          this.cargarDatos();
        },
        error: (err) => {
          this.savingUser.set(false);
          this.toast.error(err.error?.detail || 'Error al crear usuario');
        }
      });
    }
  }

  openConfirmToggle(user: Usuario): void {
    this.userToToggle.set(user);
    this.showConfirmModal.set(true);
  }

  closeConfirmModal(): void {
    this.showConfirmModal.set(false);
    this.userToToggle.set(null);
  }

  confirmToggle(): void {
    const user = this.userToToggle();
    if (!user) return;

    this.togglingStatus.set(true);
    this.dataService.toggleUserStatus(user.ci).subscribe({
      next: (updated) => {
        this.togglingStatus.set(false);
        this.closeConfirmModal();
        const msg = updated.estado ? 'Usuario activado con éxito' : 'Usuario inactivado con éxito';
        this.toast.info(msg);
        this.cargarDatos();
      },
      error: (err) => {
        this.togglingStatus.set(false);
        this.toast.error(err.error?.detail || 'Error al cambiar estado');
      }
    });
  }

  // --- Modal Rol ---
  openRoleModal(): void {
    this.roleForm = {
      rol: '',
      niveljerarquico: 2,
      descripcion: '',
      permiso_ids: []
    };
    this.showRoleModal.set(true);
  }

  closeRoleModal(): void {
    this.showRoleModal.set(false);
  }

  isPermisoSelected(id: number): boolean {
    return this.roleForm.permiso_ids.includes(id);
  }

  togglePermisoSelection(id: number): void {
    const list = this.roleForm.permiso_ids as number[];
    if (list.includes(id)) {
      this.roleForm.permiso_ids = list.filter(x => x !== id);
    } else {
      this.roleForm.permiso_ids = [...list, id];
    }
  }

  saveRole(): void {
    this.savingRole.set(true);
    this.dataService.createRole(this.roleForm).subscribe({
      next: (newRole) => {
        this.savingRole.set(false);
        this.toast.success(`Rol "${newRole.rol}" creado exitosamente`);
        this.closeRoleModal();
        this.cargarDatos();
      },
      error: (err) => {
        this.savingRole.set(false);
        this.toast.error(err.error?.detail || 'Error al crear rol');
      }
    });
  }
}
