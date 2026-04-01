import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpClient, HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css']
})
export class RegisterComponent {
  nom = '';
  cin = '';
  email = '';

  loading = false;
  error = '';
  success = '';

  constructor(private http: HttpClient, private router: Router) {}

  register() {
    this.error = '';
    this.success = '';

    if (!this.nom || !this.cin || !this.email) {
      this.error = 'Tous les champs sont obligatoires.';
      return;
    }

    this.loading = true;

    this.http.post<any>('http://localhost:8000/auth/register', {
      nom: this.nom,
      cin: this.cin,
      email: this.email
    }).subscribe({
      next: (res) => {
        this.loading = false;
        this.success = `✅ ${res.message}`;

        setTimeout(() => {
          this.router.navigate(['/login']);
        }, 3000);
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.detail || "Erreur lors de l'inscription.";
      }
    });
  }

  goToLogin() {
    this.router.navigate(['/login']);
  }
}