import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="dashboard-layout">
      <!-- Mobile Backdrop -->
      @if (mobileMenuOpen()) {
        <div class="mobile-backdrop" (click)="mobileMenuOpen.set(false)"></div>
      }

      <!-- Sidebar -->
      <aside class="sidebar" [class.mobile-open]="mobileMenuOpen()">
        <div class="sidebar-header">
          <div class="brand">
            <div class="logo-box">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
              </svg>
            </div>
            <div class="brand-text">
              <h2>RAÍCES</h2>
              <span>ERP & Recursos</span>
            </div>
          </div>
          <button class="btn-close-mobile" (click)="mobileMenuOpen.set(false)">✕</button>
        </div>

        <nav class="sidebar-nav">
          <div class="nav-section-title">MÓDULOS DEL SISTEMA</div>

          <a
            routerLink="/dashboard"
            routerLinkActive="active"
            [routerLinkActiveOptions]="{ exact: true }"
            class="nav-item"
            (click)="mobileMenuOpen.set(false)"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect width="7" height="9" x="3" y="3" rx="1"/>
              <rect width="7" height="5" x="14" y="3" rx="1"/>
              <rect width="7" height="9" x="14" y="12" rx="1"/>
              <rect width="7" height="5" x="3" y="16" rx="1"/>
            </svg>
            <span>Panel General</span>
          </a>

          @if (auth.hasPermission('GESTION_USUARIOS')) {
            <a
              routerLink="/dashboard/usuarios"
              routerLinkActive="active"
              class="nav-item"
              (click)="mobileMenuOpen.set(false)"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              <span>Gestión de Usuarios</span>
            </a>
          }

          @if (auth.hasPermission('GESTION_TRABAJADORES')) {
            <a
              routerLink="/dashboard/trabajadores"
              routerLinkActive="active"
              class="nav-item"
              (click)="mobileMenuOpen.set(false)"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect width="20" height="14" x="2" y="7" rx="2" ry="2"/>
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
              </svg>
              <span>Gestión de Trabajadores</span>
            </a>
          }

          @if (auth.hasPermission('PAGOS_ANTICIPOS_VER') || auth.hasPermission('GESTION_TRABAJADORES')) {
            <a
              routerLink="/dashboard/pagos"
              routerLinkActive="active"
              class="nav-item"
              id="nav-pagos-anticipos"
              (click)="mobileMenuOpen.set(false)"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect width="20" height="12" x="2" y="6" rx="2"/>
                <circle cx="12" cy="12" r="2"/>
                <path d="M6 12h.01M18 12h.01"/>
              </svg>
              <span>Pagos y Anticipos</span>
            </a>
          }

          @if (auth.hasPermission('INVENTARIO_VER')) {
            <a
              routerLink="/dashboard/inventario"
              routerLinkActive="active"
              class="nav-item"
              id="nav-inventario"
              (click)="mobileMenuOpen.set(false)"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>
                <path d="m3.3 7 8.7 5 8.7-5"/>
                <path d="M12 22V12"/>
              </svg>
              <span>Inventario</span>
            </a>
          }

          @if (auth.hasPermission('PAGOS_ANTICIPOS_VER') || auth.hasPermission('INVENTARIO_VER') || auth.hasPermission('GESTION_USUARIOS')) {
            <a
              routerLink="/dashboard/contabilidad"
              routerLinkActive="active"
              class="nav-item"
              id="nav-contabilidad"
              (click)="mobileMenuOpen.set(false)"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="1" x2="12" y2="23"/>
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
              </svg>
              <span>Contabilidad</span>
            </a>
          }

          @if (auth.hasPermission('VER_BITACORA')) {
            <a
              routerLink="/dashboard/bitacora"
              routerLinkActive="active"
              class="nav-item"
              (click)="mobileMenuOpen.set(false)"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 8v4l3 3"/>
                <circle cx="12" cy="12" r="9"/>
              </svg>
              <span>Bitácora de Auditoría</span>
            </a>
          }
        </nav>

        <div class="sidebar-footer">
          <div class="user-badge-card">
            <div class="user-avatar">
              {{ getUserInitials() }}
            </div>
            <div class="user-meta">
              <span class="user-name">{{ auth.currentUser()?.nombre }} {{ auth.currentUser()?.apellido }}</span>
              <span class="badge badge-emerald">{{ auth.currentUser()?.rol || 'Usuario' }}</span>
            </div>
          </div>
          <button class="btn btn-secondary btn-logout" (click)="onLogout()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>
            </svg>
            <span>Cerrar Sesión</span>
          </button>
        </div>
      </aside>

      <!-- Main Section -->
      <div class="main-wrapper">
        <!-- Top Navigation Bar -->
        <header class="top-nav">
          <div class="nav-left">
            <button class="btn-hamburger" (click)="mobileMenuOpen.set(true)">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="4" x2="20" y1="12" y2="12"/>
                <line x1="4" x2="20" y1="6" y2="6"/>
                <line x1="4" x2="20" y1="18" y2="18"/>
              </svg>
            </button>
            <div class="breadcrumb">
              <span class="crumb-root">Sistemas Raíces</span>
              <span class="crumb-separator">/</span>
              <span class="crumb-current">Panel de Control</span>
            </div>
          </div>

          <div class="nav-right">
            <div class="user-pill">
              <div class="pill-avatar">{{ getUserInitials() }}</div>
              <div class="pill-info">
                <strong>{{ auth.currentUser()?.nombre }}</strong>
                <small>{{ auth.currentUser()?.email }}</small>
              </div>
            </div>
          </div>
        </header>

        <!-- Dynamic Content Outlet -->
        <main class="content-body">
          <router-outlet></router-outlet>
        </main>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-layout {
      display: flex;
      min-height: 100vh;
      background-color: var(--bg-subtle);
    }

    .mobile-backdrop {
      position: fixed;
      inset: 0;
      background-color: rgba(15, 23, 42, 0.4);
      backdrop-filter: blur(4px);
      z-index: 40;
    }

    /* Sidebar */
    .sidebar {
      width: 260px;
      background-color: #ffffff;
      border-right: 1px solid var(--border-default);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
      z-index: 50;
      transition: transform var(--transition-normal);

      @media (max-width: 900px) {
        position: fixed;
        top: 0;
        bottom: 0;
        left: 0;
        transform: translateX(-100%);
        box-shadow: var(--shadow-lg);

        &.mobile-open {
          transform: translateX(0);
        }
      }
    }

    .sidebar-header {
      padding: 20px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--border-subtle);

      .brand {
        display: flex;
        align-items: center;
        gap: 10px;

        .logo-box {
          width: 36px;
          height: 36px;
          background-color: var(--primary);
          color: #ffffff;
          border-radius: var(--radius-md);
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .brand-text {
          h2 {
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: -0.01em;
            color: var(--text-primary);
            line-height: 1.1;
          }
          span {
            font-size: 0.725rem;
            color: var(--text-muted);
          }
        }
      }

      .btn-close-mobile {
        display: none;
        background: none;
        border: none;
        font-size: 1.2rem;
        color: var(--text-muted);
        cursor: pointer;

        @media (max-width: 900px) {
          display: block;
        }
      }
    }

    .sidebar-nav {
      padding: 18px 12px;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 4px;

      .nav-section-title {
        font-size: 0.6875rem;
        font-weight: 600;
        text-transform: uppercase;
        color: var(--text-muted);
        letter-spacing: 0.08em;
        padding: 8px 12px 6px;
      }

      .nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 9px 14px;
        color: var(--text-secondary);
        font-size: 0.875rem;
        font-weight: 500;
        border-radius: var(--radius-md);
        text-decoration: none;
        transition: all var(--transition-fast);

        &:hover {
          background-color: var(--bg-subtle);
          color: var(--text-primary);
        }

        &.active {
          background-color: #0f172a;
          color: #ffffff;
          box-shadow: var(--shadow-xs);

          svg {
            color: #ffffff;
          }
        }
      }
    }

    .sidebar-footer {
      padding: 16px;
      border-top: 1px solid var(--border-subtle);
      display: flex;
      flex-direction: column;
      gap: 12px;

      .user-badge-card {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px;
        background-color: var(--bg-subtle);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);

        .user-avatar {
          width: 34px;
          height: 34px;
          background-color: #e2e8f0;
          color: #0f172a;
          border-radius: 50%;
          font-weight: 600;
          font-size: 0.8rem;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .user-meta {
          display: flex;
          flex-direction: column;
          gap: 2px;
          overflow: hidden;

          .user-name {
            font-size: 0.825rem;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
        }
      }

      .btn-logout {
        width: 100%;
        padding: 8px;
        font-size: 0.825rem;
      }
    }

    /* Main Section */
    .main-wrapper {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
      overflow-x: hidden;
    }

    .top-nav {
      height: 60px;
      background-color: #ffffff;
      border-bottom: 1px solid var(--border-default);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      gap: 16px;

      .nav-left {
        display: flex;
        align-items: center;
        gap: 14px;

        .btn-hamburger {
          display: none;
          background: none;
          border: 1px solid var(--border-default);
          border-radius: var(--radius-sm);
          padding: 6px;
          cursor: pointer;
          color: var(--text-secondary);

          @media (max-width: 900px) {
            display: flex;
            align-items: center;
            justify-content: center;
          }
        }

        .breadcrumb {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.85rem;

          .crumb-root {
            color: var(--text-muted);
          }
          .crumb-separator {
            color: var(--border-default);
          }
          .crumb-current {
            font-weight: 600;
            color: var(--text-primary);
          }
        }
      }

      .nav-right {
        display: flex;
        align-items: center;
        gap: 18px;

        .system-status {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.775rem;
          color: var(--accent-emerald);
          background-color: var(--accent-emerald-bg);
          padding: 4px 10px;
          border-radius: var(--radius-full);
          border: 1px solid var(--accent-emerald-border);

          .status-dot {
            width: 6px;
            height: 6px;
            background-color: var(--accent-emerald);
            border-radius: 50%;
          }
        }

        .user-pill {
          display: flex;
          align-items: center;
          gap: 8px;

          .pill-avatar {
            width: 32px;
            height: 32px;
            background-color: #0f172a;
            color: #ffffff;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 600;
          }

          .pill-info {
            display: flex;
            flex-direction: column;
            line-height: 1.2;

            @media (max-width: 640px) {
              display: none;
            }

            strong {
              font-size: 0.825rem;
              color: var(--text-primary);
            }
            small {
              font-size: 0.725rem;
              color: var(--text-muted);
            }
          }
        }
      }
    }

    .content-body {
      flex: 1;
      padding: 28px;

      @media (max-width: 640px) {
        padding: 16px;
      }
    }
  `]
})
export class DashboardComponent {
  public auth = inject(AuthService);
  private toast = inject(ToastService);
  private router = inject(Router);

  public mobileMenuOpen = signal(false);

  getUserInitials(): string {
    const u = this.auth.currentUser();
    if (!u) return 'U';
    const first = u.nombre?.[0] || '';
    const last = u.apellido?.[0] || '';
    return (first + last).toUpperCase();
  }

  onLogout(): void {
    this.toast.info('Sesión finalizada exitosamente');
    this.auth.logout();
  }
}
