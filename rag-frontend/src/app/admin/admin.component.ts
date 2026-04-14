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
  documents: any[] = [];
  uploadMessage = '';
  uploadError   = '';
  uploading     = false;
  selectedFile: File | null = null;
  adminUser: any = {};

  uploadDepartment = 'IT';

  // ✅ LISTE DES DÉPARTEMENTS
  allDepartments = ['IT', 'RH', 'Marketing', 'Finance', 'Direction',"Général"];

  // ✅ K-Means simplifié
  nClusters        = 10;
  kmeansStatus     = 'Vérification...';
  kmeansActive     = false;
  kmeansNClusters  = 0;
  clusterStats: any[] = [];

  constructor(private http: HttpClient, private router: Router) {}

  ngOnInit() {
    this.adminUser = JSON.parse(localStorage.getItem('admin_user') || '{}');
    this.loadStats();
    this.loadUsers();
    this.loadDocuments();
    this.checkKmeansStatus();
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
    }).subscribe({ 
      next: (data) => {
        // ✅ sécurité : toujours avoir un tableau
        this.users = data.map(u => ({
          ...u,
          departments: u.departments || []
        }));
      }
    });
  }

  loadDocuments() {
    this.http.get<any[]>('http://localhost:8000/admin/documents', {
      headers: this.getHeaders()
    }).subscribe({
      next: (data) => {
        this.documents = data;

        const totalChunks = data.reduce((sum, d) => sum + d.chunks, 0);

        if      (totalChunks < 500)  this.nClusters = 5;
        else if (totalChunks < 2000) this.nClusters = 10;
        else if (totalChunks < 5000) this.nClusters = 20;
        else                         this.nClusters = 30;

        console.log(`💡 Suggestion: ${this.nClusters} clusters pour ${totalChunks} chunks`);
      },
      error: (err) => console.error('Erreur documents:', err)
    });
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

  // ❌ ANCIEN (single department) — supprimé
  // updateDepartment(...) {}

  // ✅ NOUVEAU: gestion multi-départements
  toggleDepartment(user: any, dept: string, event: any) {
    if (!user.departments) user.departments = [];

    if (event.target.checked) {
      // ➕ Ajouter
      if (!user.departments.includes(dept)) {
        user.departments.push(dept);
      }
    } else {
      // ➖ Supprimer
      user.departments = user.departments.filter((d: string) => d !== dept);
    }

    // ✅ Sync backend
    this.http.put(
      `http://localhost:8000/admin/users/${user.id}/departments`,
      { departments: user.departments },
      { headers: this.getHeaders() }
    ).subscribe({
      next: () => console.log(`✅ Départements mis à jour pour ${user.nom}`),
      error: (err) => console.error('Erreur:', err)
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
    formData.append('department', this.uploadDepartment);

    this.http.post<any>('http://localhost:8000/admin/upload-pdf', formData, {
      headers: new HttpHeaders({
        Authorization: `Bearer ${localStorage.getItem('admin_token') || ''}`
      })
    }).subscribe({
      next: (res) => {
        this.uploading     = false;
        this.uploadMessage = res.message;
        this.selectedFile  = null;
        this.loadDocuments();
      },
      error: (err) => {
        this.uploading   = false;
        this.uploadError = err.error?.detail || 'Erreur upload';
      }
    });
  }

  checkKmeansStatus() {
    this.http.get<any>('http://localhost:8000/clustering/status', {
      headers: this.getHeaders()
    }).subscribe({
      next: (res) => {
        this.kmeansActive    = res.trained;
        this.kmeansNClusters = res.n_clusters || 0;
      }
    });
  }

  deleteDocument(source: string) {
    if (!confirm(`Supprimer "${source}" ?`)) return;
    this.http.delete(`http://localhost:8000/admin/documents/${encodeURIComponent(source)}`, {
      headers: this.getHeaders()
    }).subscribe({
      next: () => {
        this.loadDocuments();
      },
      error: (err) => console.error('Erreur suppression:', err)
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