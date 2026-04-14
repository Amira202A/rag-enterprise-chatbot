import { Routes } from '@angular/router';
import { AuthUnifiedComponent } from './auth-unified/auth-unified.component';
import { adminGuard } from './admin/admin.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: AuthUnifiedComponent },
  { path: 'register', component: AuthUnifiedComponent },

  {
    path: 'chat',
    loadComponent: () => import('./chat/chat.component').then(m => m.ChatComponent)
    // 🔥 supprimé canActivate temporairement
  },

  {
    path: 'admin',
    loadComponent: () => import('./admin/admin.component').then(m => m.AdminComponent),
    canActivate: [adminGuard]
  },

  {
    path: 'admin/login',
    loadComponent: () => import('./admin/admin-login/admin-login.component').then(m => m.AdminLoginComponent)
  }
];