import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DataService } from '../../core/services/data.service';
import { ToastService } from '../../core/services/toast.service';
import { Bitacora } from '../../core/models/types';

@Component({
  selector: 'app-bitacora',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="bitacora-page">
      <div class="page-header">
        <div>
          <h1>Bitácora de Auditoría y Trazabilidad</h1>
          <p class="subtitle">
            Registro cronológico e inmutable de todas las acciones y operaciones realizadas en la base de datos.
          </p>
        </div>
        <button class="btn btn-secondary" (click)="cargarBitacora()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
            <path d="M3 3v5h5"/>
            <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
            <path d="M16 21h5v-5"/>
          </svg>
          <span>Actualizar Registro</span>
        </button>
      </div>

      <div class="card table-card">
        <div class="card-header">
          <div>
            <h3>Eventos Recientes del Sistema</h3>
            <p>Se muestran las últimas {{ registros().length }} operaciones registradas</p>
          </div>
        </div>

        <div class="table-responsive">
          <table class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Fecha y Hora</th>
                <th>Módulo</th>
                <th>Acción</th>
                <th>Descripción</th>
                <th>Usuario Responsable (CI)</th>
              </tr>
            </thead>
            <tbody>
              @for (b of registros(); track b.id) {
                <tr>
                  <td><span class="id-badge">#{{ b.id }}</span></td>
                  <td>
                    <div class="timestamp-cell">
                      <strong>{{ b.fecha }}</strong>
                      <small>{{ b.hora }}</small>
                    </div>
                  </td>
                  <td>
                    <span class="badge badge-slate">{{ b.modulo }}</span>
                  </td>
                  <td>
                    <span class="badge" [ngClass]="getAccionBadgeClass(b.accion)">
                      {{ b.accion }}
                    </span>
                  </td>
                  <td>
                    <span class="desc-text">{{ b.descripcion }}</span>
                  </td>
                  <td>
                    <span class="ci-tag">{{ b.usuario_ci || 'Sistema / Inicial' }}</span>
                  </td>
                </tr>
              } @empty {
                <tr>
                  <td colspan="6" class="empty-state">
                    No hay registros en la bitácora todavía.
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .bitacora-page {
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
    }

    .table-card {
      padding: 0;
    }

    .id-badge {
      font-family: monospace;
      font-size: 0.775rem;
      color: var(--text-muted);
    }

    .timestamp-cell {
      display: flex;
      flex-direction: column;
      line-height: 1.25;

      strong {
        font-size: 0.825rem;
        color: var(--text-primary);
      }
      small {
        font-size: 0.725rem;
        color: var(--text-muted);
      }
    }

    .desc-text {
      font-size: 0.85rem;
      color: var(--text-primary);
    }

    .ci-tag {
      font-family: monospace;
      font-size: 0.775rem;
      color: var(--text-secondary);
      background-color: var(--bg-muted);
      padding: 2px 6px;
      border-radius: var(--radius-xs);
    }

    .empty-state {
      text-align: center;
      padding: 36px 16px;
      color: var(--text-muted);
    }
  `]
})
export class BitacoraComponent implements OnInit {
  private dataService = inject(DataService);
  private toast = inject(ToastService);

  public registros = signal<Bitacora[]>([]);

  ngOnInit(): void {
    this.cargarBitacora();
  }

  cargarBitacora(): void {
    this.dataService.getBitacora(100).subscribe({
      next: (data) => this.registros.set(data),
      error: () => this.toast.error('Error al cargar la bitácora')
    });
  }

  getAccionBadgeClass(accion: string): string {
    switch (accion.toUpperCase()) {
      case 'CREAR':
      case 'REGISTRAR':
        return 'badge-emerald';
      case 'MODIFICAR':
      case 'EDITAR':
        return 'badge-blue';
      case 'CAMBIAR_ESTADO':
      case 'INACTIVAR':
        return 'badge-amber';
      case 'LOGIN':
        return 'badge-slate';
      default:
        return 'badge-slate';
    }
  }
}
