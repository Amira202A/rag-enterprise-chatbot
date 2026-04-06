import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { CanActivateFn } from '@angular/router';

export const adminGuard: CanActivateFn = () => {
  const router = inject(Router);
  const user   = JSON.parse(localStorage.getItem('admin_user') || '{}');
  if (user?.is_admin) return true;
  router.navigate(['/admin/login']);
  return false;
};