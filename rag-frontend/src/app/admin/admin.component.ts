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

  allDepartments = ['IT', 'RH', 'Marketing', 'Finance', 'Direction', 'Général'];

  // ── KMeans ──
  nClusters = 10;
  kmeansActive = false;
  kmeansNClusters = 0;

  // ── Recherche employés ──
  searchQuery = '';
  employeeResults: any[] = [];
  addingEmployee = '';
  addSuccess = '';
  addError = '';

  // ── Import CSV ──
  selectedCsv: File | null = null;
  importingCsv = false;
  importSuccess = '';

  // ───────── MODALS ─────────
  showEditModal   = false;
  showCreateModal = false;
  modalLoading    = false;
  modalError      = '';
  modalSuccess    = '';
  selectedUserId  = 0;

  editForm = {
    nom: '', prenom: '', email: '',
    departments: [] as string[]
  };

  createForm = {
    nom: '', prenom: '', cin: '', email: '',
    departments: [] as string[]
  };

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

  // ───────── LOAD DATA ─────────

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
        this.users = data.map(u => ({
          ...u,
          departments: u.departments || [],
          showDepts: false
        }));
      }
    });
  }

  loadDocuments() {
    this.http.get<any[]>('http://localhost:8000/admin/documents', {
      headers: this.getHeaders()
    }).subscribe({
      next: (data) => this.documents = data
    });
  }

  // ───────── USERS ─────────

  toggleUser(user: any) {
    this.http.put<any>(`http://localhost:8000/admin/users/${user.id}/toggle`, {}, {
      headers: this.getHeaders()
    }).subscribe({
      next: (res) => user.is_active = res.is_active
    });
  }

  deleteUser(user: any) {
    if (!confirm(`Supprimer ${user.nom} ?`)) return;

    this.http.delete(`http://localhost:8000/admin/users/${user.id}`, {
      headers: this.getHeaders()
    }).subscribe({
      next: () => this.users = this.users.filter(u => u.id !== user.id)
    });
  }

  // ✅ FIX IMPORTANT (plus d’event fake)
  toggleDepartment(user: any, dept: string, checked: boolean) {
    if (!user.departments) user.departments = [];

    if (checked) {
      if (!user.departments.includes(dept)) {
        user.departments.push(dept);
      }
    } else {
      user.departments = user.departments.filter((d: string) => d !== dept);
    }

    this.http.put(
      `http://localhost:8000/admin/users/${user.id}/departments`,
      { departments: user.departments },
      { headers: this.getHeaders() }
    ).subscribe();
  }

  // ✅ FIX dropdown propre
  toggleDeptDropdown(user: any) {
    this.users.forEach(u => u.showDepts = false);
    user.showDepts = !user.showDepts;
  }

  // ───────── MODALS ─────────

  openEditModal(user: any) {
    this.selectedUserId = user.id;

    this.editForm = {
      nom: user.nom || '',
      prenom: user.prenom || '',
      email: user.email || '',
      departments: [...(user.departments || [])]
    };

    this.modalError = '';
    this.modalSuccess = '';
    this.showEditModal = true;
  }

  openCreateModal() {
    this.createForm = {
      nom: '', prenom: '', cin: '', email: '',
      departments: []
    };

    this.modalError = '';
    this.modalSuccess = '';
    this.showCreateModal = true;
  }

  closeModals() {
    this.showEditModal = false;
    this.showCreateModal = false;
    this.modalError = '';
    this.modalSuccess = '';
  }

  toggleEditDept(dept: string) {
    const i = this.editForm.departments.indexOf(dept);
    i >= 0
      ? this.editForm.departments.splice(i, 1)
      : this.editForm.departments.push(dept);
  }

  toggleCreateDept(dept: string) {
    const i = this.createForm.departments.indexOf(dept);
    i >= 0
      ? this.createForm.departments.splice(i, 1)
      : this.createForm.departments.push(dept);
  }

  saveEdit() {
    this.modalLoading = true;
    this.modalError = '';

    this.http.put<any>(
      `http://localhost:8000/admin/users/${this.selectedUserId}`,
      this.editForm,
      { headers: this.getHeaders() }
    ).subscribe({
      next: (res) => {
        this.modalLoading = false;
        this.modalSuccess = res.message;
        this.loadUsers();
        setTimeout(() => this.closeModals(), 1500);
      },
      error: (err) => {
        this.modalLoading = false;
        this.modalError = err.error?.detail || 'Erreur modification';
      }
    });
  }

  saveCreate() {
    this.modalLoading = true;
    this.modalError = '';

    if (!this.createForm.nom || !this.createForm.prenom ||
        !this.createForm.cin || !this.createForm.email) {
      this.modalError = 'Tous les champs sont obligatoires';
      this.modalLoading = false;
      return;
    }

    this.http.post<any>(
      'http://localhost:8000/admin/users/create',
      this.createForm,
      { headers: this.getHeaders() }
    ).subscribe({
      next: (res) => {
        this.modalLoading = false;
        this.modalSuccess = res.message;
        this.loadUsers();
        setTimeout(() => this.closeModals(), 2000);
      },
      error: (err) => {
        this.modalLoading = false;
        this.modalError = err.error?.detail || 'Erreur création';
      }
    });
  }

  // ───────── AUTRES ─────────

  logout() {
    localStorage.clear();
    this.router.navigate(['/login']);
  }

  checkKmeansStatus() {
    this.http.get<any>('http://localhost:8000/clustering/status', {
      headers: this.getHeaders()
    }).subscribe(res => {
      this.kmeansActive = res.trained;
      this.kmeansNClusters = res.n_clusters || 0;
    });
  }

  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
  }

  uploadPDF() {
    if (!this.selectedFile) return;

    const formData = new FormData();
    formData.append('file', this.selectedFile);
    formData.append('department', this.uploadDepartment);

    this.uploading = true;

    this.http.post<any>('http://localhost:8000/admin/upload-pdf', formData, {
      headers: this.getHeaders()
    }).subscribe({
      next: () => {
        this.uploading = false;
        this.selectedFile = null;
        this.loadDocuments();
      },
      error: () => this.uploading = false
    });
  }

  deleteDocument(source: string) {
    if (!confirm(`Supprimer "${source}" ?`)) return;

    this.http.delete(
      `http://localhost:8000/admin/documents/${encodeURIComponent(source)}`,
      { headers: this.getHeaders() }
    ).subscribe(() => this.loadDocuments());
  }

  // ───────── EMPLOYEES ─────────

  searchEmployees() {
    const q = encodeURIComponent(this.searchQuery);

    this.http.get<any[]>(
      `http://localhost:8000/employees/search?q=${q}`,
      { headers: this.getHeaders() }
    ).subscribe(data => this.employeeResults = data);
  }

  clearSearch() {
    this.searchQuery = '';
    this.employeeResults = [];
  }

  addEmployee(emp: any) {
    this.addingEmployee = emp.cin;

    this.http.post<any>('http://localhost:8000/employees/add', emp, {
      headers: this.getHeaders()
    }).subscribe({
      next: (res) => {
        this.addingEmployee = '';
        this.addSuccess = res.message;
        this.loadUsers();
      },
      error: () => this.addingEmployee = ''
    });
  }

  onCsvSelected(event: any) {
    this.selectedCsv = event.target.files[0];
  }

  importCsv() {
    if (!this.selectedCsv) return;

    const formData = new FormData();
    formData.append('file', this.selectedCsv);

    this.importingCsv = true;

    this.http.post<any>(
      'http://localhost:8000/employees/import-csv',
      formData,
      { headers: this.getHeaders() }
    ).subscribe({
      next: (res) => {
        this.importingCsv = false;
        this.importSuccess = res.message;
        this.searchEmployees();
      },
      error: () => this.importingCsv = false
    });
  }

}