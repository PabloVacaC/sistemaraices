import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { DataService } from '../../core/services/data.service';
import { Bitacora } from '../../core/models/types';

@Component({
  selector: 'app-resumen',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="resumen-page">
      <!-- Welcome Hero Banner -->
      <div class="welcome-hero">
        <div class="hero-content">
          <div class="badge-role">
            <span class="pulse-dot"></span>
            <span>Sesión Activa: {{ auth.currentUser()?.rol || 'Super Administrador' }}</span>
          </div>
          <h1>Hola, {{ auth.currentUser()?.nombre }} {{ auth.currentUser()?.apellido }} 👋</h1>
          <p class="hero-desc">
            Bienvenido al panel de control de <strong>Sistemas Raíces</strong>. Tienes acceso completo para gestionar usuarios, asignar permisos, registrar colaboradores y auditar la base de datos.
          </p>
        </div>
      </div>

      <!-- Quick Action Cards -->
      <div class="modules-grid">
        <div class="card module-card">
          <div class="module-icon icon-users">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </div>
          <div class="module-body">
            <h3>Gestión de Usuarios</h3>
            <p>Crea personas que utilizarán el sistema, define sus roles y asigna los permisos exactos a qué ventanas tendrán acceso.</p>
            <a routerLink="/dashboard/usuarios" class="btn btn-secondary btn-sm module-btn">
              <span>Abrir Usuarios</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </a>
          </div>
        </div>

        <div class="card module-card">
          <div class="module-icon icon-workers">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect width="20" height="14" x="2" y="7" rx="2" ry="2"/>
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
            </svg>
          </div>
          <div class="module-body">
            <h3>Gestión de Trabajadores</h3>
            <p>Registra, consulta, edita e inactiva colaboradores de la empresa. Gestiona su cargo, sueldo base, área y contactos de emergencia.</p>
            <a routerLink="/dashboard/trabajadores" class="btn btn-secondary btn-sm module-btn">
              <span>Abrir Trabajadores</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </a>
          </div>
        </div>

        <div class="card module-card">
          <div class="module-icon icon-audit">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 8v4l3 3"/>
              <circle cx="12" cy="12" r="9"/>
            </svg>
          </div>
          <div class="module-body">
            <h3>Bitácora de Auditoría</h3>
            <p>Monitorea en tiempo real quién realizó cambios, cuándo se crearon o modificaron registros y el historial completo.</p>
            <a routerLink="/dashboard/bitacora" class="btn btn-secondary btn-sm module-btn">
              <span>Ver Bitácora</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </a>
          </div>
        </div>
      </div>

      <!-- Recent System Events -->
      <div class="card recent-events-card">
        <div class="card-header">
          <div>
            <h3>Actividad Reciente en el Sistema</h3>
            <p>Operaciones automáticas registradas en la tabla de bitácora</p>
          </div>
        </div>
        <div class="events-list">
          @for (e of ultimosEventos(); track e.id) {
            <div class="event-row">
              <div class="event-indicator"></div>
              <div class="event-meta">
                <strong>{{ e.modulo }} &bull; {{ e.accion }}</strong>
                <p>{{ e.descripcion }}</p>
              </div>
              <div class="event-time">
                <span>{{ e.fecha }}</span>
                <small>{{ e.hora }}</small>
              </div>
            </div>
          } @empty {
            <p class="empty-text">Sin registros recientes.</p>
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .resumen-page {
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    .welcome-hero {
      background-color: #ffffff;
      border: 1px solid var(--border-default);
      border-radius: var(--radius-xl);
      padding: 32px;
      box-shadow: var(--shadow-sm);

      .badge-role {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: var(--accent-emerald-bg);
        color: var(--accent-emerald);
        border: 1px solid var(--accent-emerald-border);
        font-size: 0.775rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: var(--radius-full);
        margin-bottom: 14px;

        .pulse-dot {
          width: 6px;
          height: 6px;
          background-color: var(--accent-emerald);
          border-radius: 50%;
        }
      }

      h1 {
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: var(--text-primary);
        line-height: 1.2;
      }

      .hero-desc {
        font-size: 0.95rem;
        color: var(--text-secondary);
        margin-top: 8px;
        max-width: 640px;
        line-height: 1.5;
      }

      .hero-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 18px;
      }
    }

    .modules-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
    }

    .module-card {
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;

      .module-icon {
        width: 44px;
        height: 44px;
        border-radius: var(--radius-lg);
        display: flex;
        align-items: center;
        justify-content: center;

        &.icon-users {
          background-color: #eff6ff;
          color: #2563eb;
        }

        &.icon-workers {
          background-color: #ecfdf5;
          color: #059669;
        }

        &.icon-audit {
          background-color: #faf5ff;
          color: #9333ea;
        }
      }

      .module-body {
        display: flex;
        flex-direction: column;
        gap: 8px;

        h3 {
          font-size: 1.1rem;
          font-weight: 600;
          color: var(--text-primary);
        }

        p {
          font-size: 0.85rem;
          color: var(--text-secondary);
          line-height: 1.45;
          min-height: 54px;
        }

        .module-btn {
          align-self: flex-start;
          margin-top: 8px;
        }
      }
    }

    .recent-events-card {
      padding: 0;

      .events-list {
        display: flex;
        flex-direction: column;
      }

      .event-row {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 14px 20px;
        border-bottom: 1px solid var(--border-subtle);

        &:last-child {
          border-bottom: none;
        }

        .event-indicator {
          width: 8px;
          height: 8px;
          background-color: #0f172a;
          border-radius: 50%;
        }

        .event-meta {
          flex: 1;
          display: flex;
          flex-direction: column;
          line-height: 1.3;

          strong {
            font-size: 0.85rem;
            color: var(--text-primary);
          }

          p {
            font-size: 0.8rem;
            color: var(--text-secondary);
          }
        }

        .event-time {
          display: flex;
          flex-direction: column;
          text-align: right;
          line-height: 1.25;

          span {
            font-size: 0.8rem;
            color: var(--text-primary);
            font-weight: 500;
          }

          small {
            font-size: 0.725rem;
            color: var(--text-muted);
          }
        }
      }

      .empty-text {
        padding: 24px;
        text-align: center;
        color: var(--text-muted);
      }
    }
  `]
})
export class ResumenComponent implements OnInit {
  public auth = inject(AuthService);
  private dataService = inject(DataService);

  public ultimosEventos = signal<Bitacora[]>([]);

  ngOnInit(): void {
    this.dataService.getBitacora(5).subscribe({
      next: (events) => this.ultimosEventos.set(events),
      error: () => {}
    });
  }
}
