import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [CommonModule, HttpClientModule, FormsModule],
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css']
})
export class AdminComponent implements OnInit {

  activeTab = 'stats';
  stats: any = {};
  users: any[] = [];
  uploadMessage = '';
  uploadError   = '';
  uploading     = false;
  selectedFile: File | null = null;
  adminUser: any = {};

  constructor(private http: HttpClient, private router: Router) {}

  ngOnInit() {
    this.adminUser = JSON.parse(localStorage.getItem('admin_user') || '{}');
    this.loadStats();
    this.loadUsers();
  }

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('admin_token') || '';
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  loadStats() {
    this.http.get<any>('http://localhost:8000/admin/stats', {
      headers: this.getHeaders()
    }).subscribe({ next: (data) => this.stats = data });
  }

  loadUsers() {
    this.http.get<any[]>('http://localhost:8000/admin/users', {
      headers: this.getHeaders()
    }).subscribe({ next: (data) => this.users = data });
  }

  toggleUser(user: any) {
    this.http.put<any>(`http://localhost:8000/admin/users/${user.id}/toggle`, {}, {
      headers: this.getHeaders()
    }).subscribe({
      next: (res) => {
        user.is_active = res.is_active;
      }
    });
  }

  deleteUser(user: any) {
    if (!confirm(`Supprimer ${user.nom} ?`)) return;
    this.http.delete(`http://localhost:8000/admin/users/${user.id}`, {
      headers: this.getHeaders()
    }).subscribe({
      next: () => {
        this.users = this.users.filter(u => u.id !== user.id);
      }
    });
  }

  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
  }

  uploadPDF() {
    if (!this.selectedFile) return;
    this.uploading     = true;
    this.uploadMessage = '';
    this.uploadError   = '';

    const formData = new FormData();
    formData.append('file', this.selectedFile);

    this.http.post<any>('http://localhost:8000/admin/upload-pdf', formData, {
      headers: new HttpHeaders({
        Authorization: `Bearer ${localStorage.getItem('admin_token') || ''}`
      })
    }).subscribe({
      next: (res) => {
        this.uploading     = false;
        this.uploadMessage = res.message;
        this.selectedFile  = null;
      },
      error: (err) => {
        this.uploading   = false;
        this.uploadError = err.error?.detail || 'Erreur upload';
      }
    });
  }

  logout() {
  localStorage.removeItem('admin_token');
  localStorage.removeItem('admin_user');
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  this.router.navigate(['/login']);
}
}