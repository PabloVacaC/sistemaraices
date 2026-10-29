import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="login-wrapper">
      <div class="login-container">
        <!-- Brand Header -->
        <div class="brand-box">
          <div class="logo-mark">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
          </div>
          <h1>SISTEMAS RAÍCES</h1>
          <p class="subtitle">Plataforma Empresarial y Gestión de Recursos</p>
        </div>

        <!-- Quick Superadmin Fill Banner -->
        <div class="demo-chip" (click)="fillSuperAdmin()">
          <div class="chip-dot"></div>
          <div class="chip-text">
            <strong>Super Administrador</strong> (Clic para autocompletar)
          </div>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="m9 18 6-6-6-6"/>
          </svg>
        </div>

        <!-- Login Card -->
        <div class="card login-card">
          <form (ngSubmit)="onSubmit()">
            <div class="form-group">
              <label for="email">Correo Electrónico</label>
              <input
                id="email"
                type="email"
                class="form-control"
                placeholder="ejemplo@raices.com"
                [(ngModel)]="email"
                name="email"
                required
                autocomplete="username"
              />
            </div>

            <div class="form-group">
              <div class="password-label-row">
                <label for="password">Contraseña</label>
                <button
                  type="button"
                  class="btn-text"
                  (click)="showPassword = !showPassword"
                >
                  {{ showPassword ? 'Ocultar' : 'Mostrar' }}
                </button>
              </div>
              <input
                id="password"
                [type]="showPassword ? 'text' : 'password'"
                class="form-control"
                placeholder="Ingresa tu contraseña"
                [(ngModel)]="password"
                name="password"
                required
                autocomplete="current-password"
              />
            </div>

            @if (errorMessage()) {
              <div class="error-banner">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="12"/>
                  <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <span>{{ errorMessage() }}</span>
              </div>
            }

            <button
              type="submit"
              class="btn btn-primary btn-submit"
              [disabled]="loading() || !email || !password"
            >
              @if (loading()) {
                <span class="spinner"></span>
                Iniciando sesión...
              } @else {
                <span>Ingresar al Sistema</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              }
            </button>
          </form>
        </div>

        <!-- Footer Notice -->
        <p class="login-footer">
          Conexión cifrada a PostgreSQL &bull; Control RBAC &bull; Versión 1.0.0
        </p>
      </div>
    </div>
  `,
  styles: [`
    .login-wrapper {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: radial-gradient(circle at 50% 0%, #f8fafc 0%, #ffffff 100%);
      padding: 24px;
    }

    .login-container {
      width: 100%;
      max-width: 440px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }

    .brand-box {
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;

      .logo-mark {
        width: 48px;
        height: 48px;
        background-color: var(--primary);
        color: #ffffff;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
      }

      h1 {
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: var(--text-primary);
      }

      .subtitle {
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin-top: 4px;
      }
    }

    .demo-chip {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 14px;
      background-color: #ffffff;
      border: 1px solid var(--accent-emerald-border);
      border-radius: var(--radius-md);
      cursor: pointer;
      box-shadow: var(--shadow-xs);
      transition: all var(--transition-fast);

      &:hover {
        background-color: var(--accent-emerald-bg);
        transform: translateY(-1px);
        box-shadow: var(--shadow-sm);
      }

      .chip-dot {
        width: 8px;
        height: 8px;
        background-color: var(--accent-emerald);
        border-radius: 50%;
        box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.15);
      }

      .chip-text {
        flex: 1;
        font-size: 0.8rem;
        color: var(--text-primary);
        strong {
          color: var(--accent-emerald);
        }
      }

      svg {
        color: var(--accent-emerald);
      }
    }

    .login-card {
      padding: 28px;
      box-shadow: var(--shadow-md);
      border: 1px solid var(--border-default);
    }

    .password-label-row {
      display: flex;
      align-items: center;
      justify-content: space-between;

      .btn-text {
        background: none;
        border: none;
        color: var(--text-muted);
        font-size: 0.75rem;
        font-weight: 500;
        cursor: pointer;
        padding: 0;
        &:hover {
          color: var(--text-primary);
        }
      }
    }

    .error-banner {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      background-color: var(--accent-rose-bg);
      border: 1px solid var(--accent-rose-border);
      border-radius: var(--radius-md);
      color: var(--accent-rose);
      font-size: 0.8125rem;
      margin-bottom: 16px;
    }

    .btn-submit {
      width: 100%;
      padding: 11px;
      font-size: 0.925rem;
      font-weight: 600;
      margin-top: 6px;
    }

    .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-top-color: #ffffff;
      border-radius: 50%;
      animation: spin 0.6s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .login-footer {
      text-align: center;
      font-size: 0.75rem;
      color: var(--text-muted);
    }
  `]
})
export class LoginComponent {
  private auth = inject(AuthService);
  private toast = inject(ToastService);
  private router = inject(Router);

  public email = '';
  public password = '';
  public showPassword = false;
  public loading = signal(false);
  public errorMessage = signal<string | null>(null);

  fillSuperAdmin() {
    this.email = 'juanpablovacacarvalho@gmail.com';
    this.password = '123456';
    this.errorMessage.set(null);
  }

  onSubmit() {
    if (!this.email || !this.password) return;

    this.loading.set(true);
    this.errorMessage.set(null);

    this.auth.login(this.email, this.password).subscribe({
      next: (res) => {
        this.loading.set(false);
        this.toast.success(`¡Bienvenido, ${res.user.nombre} ${res.user.apellido}!`);
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading.set(false);
        const detail = err.error?.detail || 'Error al iniciar sesión. Verifica tus credenciales.';
        this.errorMessage.set(detail);
        this.toast.error(detail);
      }
    });
  }
}
