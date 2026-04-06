import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpClient, HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-admin-login',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './admin-login.component.html',
  styleUrls: ['./admin-login.component.css']
})
export class AdminLoginComponent {
  cin          = '';
  password     = '';
  loading      = false;
  error        = '';
  showPassword = false;

  constructor(private http: HttpClient, private router: Router) {}

  login() {
    this.error = '';
    if (!this.cin || !this.password) {
      this.error = 'CIN et mot de passe obligatoires.';
      return;
    }
    this.loading = true;
    this.http.post<any>('http://localhost:8000/auth/admin/login', {
      cin: this.cin, password: this.password
    }).subscribe({
      next: (res) => {
        this.loading = false;
        localStorage.setItem('admin_token', res.access_token);
        localStorage.setItem('admin_user', JSON.stringify(res.user));
        this.router.navigate(['/admin']);
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.detail || 'Erreur de connexion.';
      }
    });
  }
}