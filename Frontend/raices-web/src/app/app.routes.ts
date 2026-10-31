import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { LoginComponent } from './pages/login/login.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { ResumenComponent } from './pages/resumen/resumen.component';
import { UsuariosComponent } from './pages/usuarios/usuarios.component';
import { TrabajadoresComponent } from './pages/trabajadores/trabajadores.component';
import { BitacoraComponent } from './pages/bitacora/bitacora.component';
import { PagosComponent } from './pages/pagos/pagos.component';
import { InventarioComponent } from './pages/inventario/inventario.component';
import { PlanillaComponent } from './pages/planilla/planilla.component';
import { ContabilidadComponent } from './pages/contabilidad/contabilidad.component';

export const routes: Routes = [
  {
    path: 'login',
    component: LoginComponent
  },
  {
    path: 'dashboard',
    component: DashboardComponent,
    canActivate: [authGuard],
    children: [
      {
        path: '',
        component: ResumenComponent
      },
      {
        path: 'usuarios',
        component: UsuariosComponent
      },
      {
        path: 'trabajadores',
        component: TrabajadoresComponent
      },
      {
        path: 'inventario',
        component: InventarioComponent
      },
      {
        path: 'planilla',
        component: PlanillaComponent
      },
      {
        path: 'pagos',
        component: PagosComponent
      },
      {
        path: 'contabilidad',
        component: ContabilidadComponent
      },
      {
        path: 'bitacora',
        component: BitacoraComponent
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
