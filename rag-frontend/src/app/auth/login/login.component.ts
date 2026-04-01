import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpClient, HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  cin = '';
  password = '';
  loading = false;
  error = '';

  constructor(private http: HttpClient, private router: Router) {}

  login() {
    this.error = '';
    if (!this.cin || !this.password) {
      this.error = 'CIN et mot de passe obligatoires.';
      return;
    }
    this.loading = true;
    this.http.post<any>('http://localhost:8000/auth/login', {
      cin: this.cin,
      password: this.password
    }).subscribe({
      next: (res) => {
        this.loading = false;
        localStorage.setItem('token', res.access_token);
        localStorage.setItem('user', JSON.stringify(res.user));
        this.router.navigate(['/chat']);
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.detail || 'Erreur de connexion.';
      }
    });
  }

  goToRegister() {
    this.router.navigate(['/register']);
  }
}