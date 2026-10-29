import { Injectable, signal, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { LoginResponse, UserSummary } from '../models/types';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);

  private readonly API_URL = 'http://localhost:8000/api';
  private readonly TOKEN_KEY = 'raices_token';
  private readonly USER_KEY = 'raices_user';

  public token = signal<string | null>(
    sessionStorage.getItem(this.TOKEN_KEY) || localStorage.getItem(this.TOKEN_KEY)
  );
  public currentUser = signal<UserSummary | null>(
    this.loadUserFromStorage()
  );

  private loadUserFromStorage(): UserSummary | null {
    const raw = sessionStorage.getItem(this.USER_KEY) || localStorage.getItem(this.USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  public getHeaders(): HttpHeaders {
    const t = this.token();
    let headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    if (t) {
      headers = headers.set('Authorization', `Bearer ${t}`);
    }
    return headers;
  }

  public login(email: string, contrasena: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.API_URL}/auth/login`, {
      email,
      contraseña: contrasena
    }).pipe(
      tap(res => {
        this.token.set(res.access_token);
        this.currentUser.set(res.user);
        // Se almacena en sessionStorage para que la sesión se mantenga activa durante todo
        // el uso continuo y se destruya de forma limpia al cerrar la pestaña/navegador (X)
        sessionStorage.setItem(this.TOKEN_KEY, res.access_token);
        sessionStorage.setItem(this.USER_KEY, JSON.stringify(res.user));
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
      })
    );
  }

  public logout(): void {
    this.token.set(null);
    this.currentUser.set(null);
    sessionStorage.removeItem(this.TOKEN_KEY);
    sessionStorage.removeItem(this.USER_KEY);
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.router.navigate(['/login']);
  }

  public isAuthenticated(): boolean {
    return !!this.token();
  }

  public isSuperAdmin(): boolean {
    const u = this.currentUser();
    return u?.niveljerarquico === 1 || u?.rol === 'Super Administrador';
  }

  public hasPermission(permiso: string): boolean {
    const u = this.currentUser();
    if (!u) return false;
    if (this.isSuperAdmin()) return true;
    return u.permisos?.includes(permiso) ?? false;
  }
}
