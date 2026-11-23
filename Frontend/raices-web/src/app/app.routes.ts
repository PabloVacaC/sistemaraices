import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent),
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () => import('./pages/resumen/resumen.component').then(m => m.ResumenComponent)
      },
      {
        path: 'usuarios',
        loadComponent: () => import('./pages/usuarios/usuarios.component').then(m => m.UsuariosComponent)
      },
      {
        path: 'trabajadores',
        loadComponent: () => import('./pages/trabajadores/trabajadores.component').then(m => m.TrabajadoresComponent)
      },
      {
        path: 'inventario',
        loadComponent: () => import('./pages/inventario/inventario.component').then(m => m.InventarioComponent)
      },
      {
        path: 'ganaderia',
        loadComponent: () => import('./pages/ganaderia/ganaderia.component').then(m => m.GanaderiaComponent)
      },
      {
        path: 'potreros',
        loadComponent: () => import('./pages/potreros/potreros.component').then(m => m.PotrerosComponent)
      },
      {
        path: 'sanidad',
        loadComponent: () => import('./pages/sanidad/sanidad.component').then(m => m.SanidadComponent)
      },
      {
        path: 'agricultura',
        loadComponent: () => import('./pages/agricultura/agricultura.component').then(m => m.AgriculturaComponent)
      },
      {
        path: 'apicultura',
        loadComponent: () => import('./pages/apicultura/apicultura.component').then(m => m.ApiculturaComponent)
      },
      {
        path: 'planilla',
        loadComponent: () => import('./pages/planilla/planilla.component').then(m => m.PlanillaComponent)
      },
      {
        path: 'pagos',
        loadComponent: () => import('./pages/pagos/pagos.component').then(m => m.PagosComponent)
      },
      {
        path: 'contabilidad',
        loadComponent: () => import('./pages/contabilidad/contabilidad.component').then(m => m.ContabilidadComponent)
      },
      {
        path: 'bitacora',
        loadComponent: () => import('./pages/bitacora/bitacora.component').then(m => m.BitacoraComponent)
      }
    ]
  },
  {
    path: '',
    redirectTo: '/login',
    pathMatch: 'full'
  },
  {
    path: '**',
    redirectTo: '/login'
  }
];
