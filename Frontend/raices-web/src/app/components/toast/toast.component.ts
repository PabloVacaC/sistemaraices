import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ToastService } from '../../core/services/toast.service';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="toast-container">
      @for (t of toastService.toasts(); track t.id) {
        <div class="toast-item" [ngClass]="'toast-' + t.type">
          <div class="toast-icon">
            @if (t.type === 'success') {
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 6 9 17l-5-5"/>
              </svg>
            } @else if (t.type === 'error') {
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#e11d48" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            } @else {
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
              </svg>
            }
          </div>
          <div class="toast-message">{{ t.message }}</div>
          <button class="toast-close" (click)="toastService.dismiss(t.id)">✕</button>
        </div>
      }
    </div>
  `,
  styles: [`
    .toast-message {
      flex: 1;
      font-size: 0.85rem;
      color: #0f172a;
      line-height: 1.4;
    }
    .toast-icon {
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .toast-close {
      background: none;
      border: none;
      color: #94a3b8;
      font-size: 0.9rem;
      cursor: pointer;
      padding: 2px 6px;
      border-radius: 4px;
      transition: color 150ms ease;
      &:hover {
        color: #0f172a;
      }
    }
  `]
})
export class ToastComponent {
  public toastService = inject(ToastService);
}
