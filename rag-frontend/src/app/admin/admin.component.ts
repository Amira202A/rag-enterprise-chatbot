import { Component, OnInit, OnDestroy, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';

interface AdminMessage {
  role: 'user' | 'bot';
  content: string;
  timestamp: string;
}

interface AdminConversation {
  id: string;
  title: string;
  messages: AdminMessage[];
}

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [CommonModule, HttpClientModule, FormsModule],
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css']
})
export class AdminComponent implements OnInit, OnDestroy {

  @ViewChild('adminScrollRef') adminScrollRef!: ElementRef;

  activeTab = 'analytics';
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

  kmeansActive    = false;
  kmeansNClusters = 0;

  searchQuery     = '';
  employeeResults: any[] = [];
  addingEmployee  = '';
  addSuccess      = '';
  addError        = '';

  selectedCsv: File | null = null;
  importingCsv  = false;
  importSuccess = '';

  showEditModal   = false;
  showCreateModal = false;
  modalLoading    = false;
  modalError      = '';
  modalSuccess    = '';
  selectedUserId  = 0;

  editForm = { nom: '', prenom: '', email: '', departments: [] as string[] };
  createForm = { nom: '', prenom: '', cin: '', email: '', departments: [] as string[] };

  showEditEmpModal = false;
  editEmpForm: any = {};
  editEmpCin       = '';
  editEmpLoading   = false;
  editEmpError     = '';
  editEmpSuccess   = '';

  // ── Analytics ──
  analyticsData: any    = {};
  convEvolution: any    = {};
  messagesStats: any    = {};
  deptDistribution: any = {};
  topKeywords: any      = {};
  satisfaction: any     = {};
  ragDocs: any          = {};
  heatmap: any          = {};
  fallbackRate: any     = {};
  langDistrib: any      = {};
  selectedPeriod        = 'week';
  analyticsLoading      = false;
  private charts: any   = {};
  private chartJsLoaded = false;

  // ── Admin Chatbot ──
  adminConversations: AdminConversation[] = [];
  activeAdminConvId: string | null = null;
  activeAdminConvTitle = '';
  adminCurrentMessages: AdminMessage[] = [];
  adminChatMessage = '';
  adminTyping = false;
  chatSearchQuery = '';

  // Voice
  private adminRecognition: any = null;
  adminListening = false;
  private adminFinalTranscript = '';
  private adminInterimTranscript = '';
  private adminShouldRestart = false;
  private adminIsRestarting = false;
  private adminSilenceTimer: any = null;
  private readonly SILENCE_DELAY = 1800;
  private adminAudioContext: AudioContext | null = null;
  private adminAnalyser: AnalyserNode | null = null;
  private adminMediaStream: MediaStream | null = null;
  private adminAnimFrame: number | null = null;
  adminWaveformBars: number[] = Array(20).fill(2);

  constructor(
    private http: HttpClient,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.adminUser = JSON.parse(localStorage.getItem('admin_user') || '{}');
    this.loadStats();
    this.loadUsers();
    this.loadDocuments();
    this.checkKmeansStatus();
    this.loadChartJs();
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
    }
  }

  ngOnDestroy() {
    this.stopAdminVoice();
    window.speechSynthesis?.cancel();
  }

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('admin_token') || '';
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  // ─────────────── CHART.JS ───────────────

  private loadChartJs() {
    if ((window as any).Chart) { this.chartJsLoaded = true; return; }
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
    script.onload = () => { this.chartJsLoaded = true; };
    document.head.appendChild(script);
  }

  // ─────────────── TABS ───────────────

  setTab(tab: string) {
    this.activeTab = tab;
    if (tab === 'analytics') setTimeout(() => this.loadAnalytics(), 150);
    if (tab === 'add') this.searchEmployees();
    if (tab === 'chat') this.loadAdminConversations();
  }

  // ─────────────── DATA ───────────────

  loadStats() {
    this.http.get<any>('http://localhost:8000/admin/stats', { headers: this.getHeaders() })
      .subscribe({ next: d => this.stats = d });
  }

  loadUsers() {
    this.http.get<any[]>('http://localhost:8000/admin/users', { headers: this.getHeaders() })
      .subscribe({
        next: data => {
          this.users = data.map(u => ({ ...u, departments: u.departments || [], showDepts: false }));
        }
      });
  }

  loadDocuments() {
    this.http.get<any[]>('http://localhost:8000/admin/documents', { headers: this.getHeaders() })
      .subscribe({ next: d => this.documents = d });
  }

  checkKmeansStatus() {
    this.http.get<any>('http://localhost:8000/clustering/status', { headers: this.getHeaders() })
      .subscribe(res => { this.kmeansActive = res.trained; this.kmeansNClusters = res.n_clusters || 0; });
  }

  // ─────────────── ADMIN CHATBOT ───────────────

  get filteredAdminConversations(): AdminConversation[] {
    if (!this.chatSearchQuery.trim()) return this.adminConversations;
    const q = this.chatSearchQuery.toLowerCase();
    return this.adminConversations.filter(c => c.title.toLowerCase().includes(q));
  }

  loadAdminConversations() {
    this.http.get<any[]>('http://localhost:8000/chat/conversations', { headers: this.getHeaders() })
      .subscribe({
        next: (convs) => {
          this.adminConversations = (convs || []).map(c => ({
            id: c.id, title: c.title, messages: c.messages || []
          }));
          this.cdr.detectChanges();
        },
        error: () => {}
      });
  }

  createAdminConversation() {
    this.http.post<any>('http://localhost:8000/chat/conversation', {}, { headers: this.getHeaders() })
      .subscribe({
        next: (res) => {
          if (!res?.conversation_id) return;
          const newConv: AdminConversation = {
            id: res.conversation_id,
            title: 'Nouvelle conversation',
            messages: []
          };
          this.adminConversations.unshift(newConv);
          this.activeAdminConvId = newConv.id;
          this.activeAdminConvTitle = newConv.title;
          this.adminCurrentMessages = [];
          this.cdr.detectChanges();
        }
      });
  }

  selectAdminConversation(conv: AdminConversation) {
    this.activeAdminConvId    = conv.id;
    this.activeAdminConvTitle = conv.title;
    this.adminCurrentMessages = conv.messages || [];
    this.cdr.detectChanges();
    setTimeout(() => this.scrollAdminChat(), 100);
  }

  onAdminEnter() {
    if (this.adminListening) this.stopAdminVoice();
    this.sendAdminMessage();
  }

  sendAdminMessage() {
    const input = this.adminChatMessage.trim();
    if (!input || this.adminTyping) return;

    if (!this.activeAdminConvId) {
      this.http.post<any>('http://localhost:8000/chat/conversation', {}, { headers: this.getHeaders() })
        .subscribe({
          next: (res) => {
            if (!res?.conversation_id) return;
            const newConv: AdminConversation = {
              id: res.conversation_id,
              title: input.slice(0, 28),
              messages: []
            };
            this.adminConversations.unshift(newConv);
            this.activeAdminConvId    = newConv.id;
            this.activeAdminConvTitle = newConv.title;
            this.adminCurrentMessages = [];
            this.cdr.detectChanges();
            this._sendAdminMsgNow(input);
          }
        });
      return;
    }
    this._sendAdminMsgNow(input);
  }

  private _sendAdminMsgNow(input: string) {
    if (this.adminListening) this.stopAdminVoice();
    window.speechSynthesis?.cancel();

    const msg: AdminMessage = {
      role: 'user', content: input,
      timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    };

    this.adminCurrentMessages.push(msg);
    this.adminChatMessage       = '';
    this.adminFinalTranscript   = '';
    this.adminInterimTranscript = '';
    this.adminTyping = true;
    this.cdr.detectChanges();
    this.scrollAdminChat();

    this.http.post<any>(
      'http://localhost:8000/chat/message',
      { conversation_id: this.activeAdminConvId, message: input },
      { headers: this.getHeaders() }
    ).subscribe({
      next: (res) => {
        const botMsg: AdminMessage = {
          role: 'bot',
          content: res?.answer || res?.response || 'Pas de réponse',
          timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
        };
        this.adminCurrentMessages.push(botMsg);

        const conv = this.adminConversations.find(c => c.id === this.activeAdminConvId);
        if (conv) conv.messages = this.adminCurrentMessages;

        this.adminTyping = false;
        this.cdr.detectChanges();
        this.scrollAdminChat();
      },
      error: (err) => {
        this.adminCurrentMessages.push({
          role: 'bot',
          content: `Erreur serveur (${err?.status || '??'})`,
          timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
        });
        this.adminTyping = false;
        this.cdr.detectChanges();
        this.scrollAdminChat();
      }
    });
  }

  scrollAdminChat() {
    setTimeout(() => {
      if (this.adminScrollRef) {
        this.adminScrollRef.nativeElement.scrollTop =
          this.adminScrollRef.nativeElement.scrollHeight;
      }
    }, 100);
  }

  adminSpeak(text: string) {
    window.speechSynthesis?.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang  = 'fr-FR';
    const voices    = window.speechSynthesis.getVoices();
    const voice     = voices.find(v => v.lang.startsWith('fr'));
    if (voice) utterance.voice = voice;
    window.speechSynthesis.speak(utterance);
  }

  // ─────────────── ADMIN VOICE ───────────────

  toggleAdminVoice() {
    this.adminListening ? this.stopAdminVoice() : this.startAdminVoice();
  }

  private adminPlayBip(type: 'start' | 'stop') {
    try {
      const ctx  = new AudioContext();
      const osc  = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain); gain.connect(ctx.destination);
      osc.frequency.value = type === 'start' ? 880 : 440;
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
      osc.start(ctx.currentTime); osc.stop(ctx.currentTime + 0.15);
      osc.onended = () => ctx.close();
    } catch (e) {}
  }

  private async startAdminWaveform() {
    try {
      this.adminMediaStream  = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.adminAudioContext = new AudioContext();
      this.adminAnalyser     = this.adminAudioContext.createAnalyser();
      this.adminAnalyser.fftSize = 64;
      const src = this.adminAudioContext.createMediaStreamSource(this.adminMediaStream);
      src.connect(this.adminAnalyser);
      this.drawAdminWaveform();
    } catch (e) {}
  }

  private drawAdminWaveform() {
    if (!this.adminAnalyser || !this.adminListening) return;
    const data = new Uint8Array(this.adminAnalyser.frequencyBinCount);
    this.adminAnalyser.getByteFrequencyData(data);
    const step = Math.floor(data.length / 20);
    this.adminWaveformBars = Array.from({ length: 20 }, (_, i) => {
      const val = data[i * step] / 255;
      return Math.max(2, Math.round(val * 40));
    });
    this.adminAnimFrame = requestAnimationFrame(() => this.drawAdminWaveform());
  }

  private stopAdminWaveform() {
    if (this.adminAnimFrame) cancelAnimationFrame(this.adminAnimFrame);
    this.adminAnimFrame = null;
    this.adminMediaStream?.getTracks().forEach(t => t.stop());
    this.adminAudioContext?.close();
    this.adminAudioContext = null;
    this.adminAnalyser     = null;
    this.adminMediaStream  = null;
    this.adminWaveformBars = Array(20).fill(2);
  }

  private resetAdminSilenceTimer() {
    if (this.adminSilenceTimer) clearTimeout(this.adminSilenceTimer);
    this.adminSilenceTimer = setTimeout(() => {
      if (this.adminChatMessage?.trim() && this.adminListening) {
        this.stopAdminVoice();
        this.sendAdminMessage();
      }
    }, this.SILENCE_DELAY);
  }

  private clearAdminSilenceTimer() {
    if (this.adminSilenceTimer) clearTimeout(this.adminSilenceTimer);
    this.adminSilenceTimer = null;
  }

  async startAdminVoice() {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { alert('Utilise Google Chrome pour le micro'); return; }

    this.adminFinalTranscript   = '';
    this.adminInterimTranscript = '';
    this.adminShouldRestart     = true;
    this.adminIsRestarting      = false;

    this.adminPlayBip('start');
    await this.startAdminWaveform();

    this.adminRecognition = new SR();
    this.adminRecognition.lang           = 'fr-FR';
    this.adminRecognition.continuous     = true;
    this.adminRecognition.interimResults = true;
    this.adminRecognition.maxAlternatives = 1;

    this.adminRecognition.onstart = () => {
      this.adminListening      = true;
      this.adminIsRestarting   = false;
      this.adminInterimTranscript = '';
      this.cdr.detectChanges();
    };

    this.adminRecognition.onresult = (event: any) => {
      this.adminInterimTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const text = event.results[i][0].transcript;
        if (event.results[i].isFinal) this.adminFinalTranscript += text + ' ';
        else this.adminInterimTranscript += text;
      }
      this.adminChatMessage = (this.adminFinalTranscript + this.adminInterimTranscript).trim();
      this.resetAdminSilenceTimer();
      this.cdr.detectChanges();
    };

    this.adminRecognition.onerror = (event: any) => {
      if (event.error === 'not-allowed') {
        alert('Permission micro refusée');
        this.adminShouldRestart = false;
        this.adminListening     = false;
        this.stopAdminWaveform();
        this.cdr.detectChanges();
        return;
      }
      if (event.error !== 'no-speech') {
        this.adminShouldRestart = false;
        this.adminListening     = false;
        this.stopAdminWaveform();
        this.cdr.detectChanges();
      }
    };

    this.adminRecognition.onend = () => {
      if (this.adminShouldRestart && this.adminListening && !this.adminIsRestarting) {
        this.adminIsRestarting = true;
        setTimeout(() => {
          if (this.adminShouldRestart && this.adminListening) {
            try { this.adminRecognition.start(); }
            catch (e) { this.adminListening = false; this.stopAdminWaveform(); }
          }
          this.adminIsRestarting = false;
        }, 300);
      } else {
        this.adminListening = false;
        this.stopAdminWaveform();
        this.cdr.detectChanges();
      }
    };

    this.adminRecognition.start();
  }

  stopAdminVoice() {
    this.adminShouldRestart = false;
    this.adminListening     = false;
    this.adminIsRestarting  = false;
    this.clearAdminSilenceTimer();
    this.stopAdminWaveform();
    if (this.adminRecognition) {
      try { this.adminRecognition.stop(); } catch {}
      this.adminRecognition = null;
    }
    this.adminPlayBip('stop');
    this.cdr.detectChanges();
  }

  // ─────────────── USERS ───────────────

  toggleUser(user: any) {
    this.http.put<any>(`http://localhost:8000/admin/users/${user.id}/toggle`, {}, { headers: this.getHeaders() })
      .subscribe({ next: res => user.is_active = res.is_active });
  }

  deleteUser(user: any) {
    if (!confirm(`Supprimer ${user.nom} ?`)) return;
    this.http.delete(`http://localhost:8000/admin/users/${user.id}`, { headers: this.getHeaders() })
      .subscribe({ next: () => this.users = this.users.filter(u => u.id !== user.id) });
  }

  toggleDepartment(user: any, dept: string, checked: boolean) {
    if (!user.departments) user.departments = [];
    if (checked) { if (!user.departments.includes(dept)) user.departments.push(dept); }
    else { user.departments = user.departments.filter((d: string) => d !== dept); }
    this.http.put(`http://localhost:8000/admin/users/${user.id}/departments`,
      { departments: user.departments }, { headers: this.getHeaders() }).subscribe();
  }

  openEditModal(user: any) {
    this.selectedUserId = user.id;
    this.editForm = { nom: user.nom || '', prenom: user.prenom || '', email: user.email || '', departments: [...(user.departments || [])] };
    this.modalError = ''; this.modalSuccess = '';
    this.showEditModal = true;
  }

  openCreateModal() {
    this.createForm = { nom: '', prenom: '', cin: '', email: '', departments: [] };
    this.modalError = ''; this.modalSuccess = '';
    this.showCreateModal = true;
  }

  closeModals() {
    this.showEditModal = false; this.showCreateModal = false;
    this.modalError = ''; this.modalSuccess = '';
  }

  toggleEditDept(dept: string) {
    const i = this.editForm.departments.indexOf(dept);
    i >= 0 ? this.editForm.departments.splice(i, 1) : this.editForm.departments.push(dept);
  }

  toggleCreateDept(dept: string) {
    const i = this.createForm.departments.indexOf(dept);
    i >= 0 ? this.createForm.departments.splice(i, 1) : this.createForm.departments.push(dept);
  }

  saveEdit() {
    this.modalLoading = true; this.modalError = '';
    this.http.put<any>(`http://localhost:8000/admin/users/${this.selectedUserId}`, this.editForm, { headers: this.getHeaders() })
      .subscribe({
        next: res => { this.modalLoading = false; this.modalSuccess = res.message; this.loadUsers(); setTimeout(() => this.closeModals(), 1500); },
        error: err => { this.modalLoading = false; this.modalError = err.error?.detail || 'Erreur'; }
      });
  }

  saveCreate() {
    this.modalLoading = true; this.modalError = '';
    if (!this.createForm.nom || !this.createForm.prenom || !this.createForm.cin || !this.createForm.email) {
      this.modalError = 'Tous les champs sont obligatoires'; this.modalLoading = false; return;
    }
    this.http.post<any>('http://localhost:8000/admin/users/create', this.createForm, { headers: this.getHeaders() })
      .subscribe({
        next: res => { this.modalLoading = false; this.modalSuccess = res.message; this.loadUsers(); setTimeout(() => this.closeModals(), 2000); },
        error: err => { this.modalLoading = false; this.modalError = err.error?.detail || 'Erreur'; }
      });
  }

  // ─────────────── DOCUMENTS ───────────────

  onFileSelected(event: any) { this.selectedFile = event.target.files[0]; }

  uploadPDF() {
    if (!this.selectedFile) return;
    const formData = new FormData();
    formData.append('file', this.selectedFile);
    formData.append('department', this.uploadDepartment);
    this.uploading = true;
    this.http.post<any>('http://localhost:8000/admin/upload-pdf', formData, { headers: this.getHeaders() })
      .subscribe({ next: () => { this.uploading = false; this.selectedFile = null; this.loadDocuments(); }, error: () => this.uploading = false });
  }

  deleteDocument(source: string) {
    if (!confirm(`Supprimer "${source}" ?`)) return;
    this.http.delete(`http://localhost:8000/admin/documents/${encodeURIComponent(source)}`, { headers: this.getHeaders() })
      .subscribe(() => this.loadDocuments());
  }

  // ─────────────── EMPLOYEES ───────────────

  searchEmployees() {
    const q = encodeURIComponent(this.searchQuery);
    this.http.get<any[]>(`http://localhost:8000/employees/search?q=${q}`, { headers: this.getHeaders() })
      .subscribe(data => this.employeeResults = data);
  }

  clearSearch() { this.searchQuery = ''; this.employeeResults = []; }

  addEmployee(emp: any) {
    this.addingEmployee = emp.cin;
    this.http.post<any>('http://localhost:8000/employees/add', emp, { headers: this.getHeaders() })
      .subscribe({ next: res => { this.addingEmployee = ''; this.addSuccess = res.message; this.loadUsers(); }, error: () => this.addingEmployee = '' });
  }

  onCsvSelected(event: any) { this.selectedCsv = event.target.files[0]; }

  importCsv() {
    if (!this.selectedCsv) return;
    const formData = new FormData();
    formData.append('file', this.selectedCsv);
    this.importingCsv = true;
    this.http.post<any>('http://localhost:8000/employees/import-csv', formData, { headers: this.getHeaders() })
      .subscribe({ next: res => { this.importingCsv = false; this.importSuccess = res.message; this.searchEmployees(); }, error: () => this.importingCsv = false });
  }

  openEditEmpModal(emp: any) {
    this.editEmpCin  = emp.cin;
    this.editEmpForm = { nom: emp.nom, prenom: emp.prenom, email: emp.email, matricule: emp.matricule || '', num_poste: emp.num_poste || '', unit_label: emp.unit_label || '', subsidiary_label: emp.subsidiary_label || '' };
    this.editEmpError = ''; this.editEmpSuccess = '';
    this.showEditEmpModal = true;
  }

  closeEditEmpModal() { this.showEditEmpModal = false; this.editEmpError = ''; this.editEmpSuccess = ''; }

  saveEditEmp() {
    this.editEmpLoading = true; this.editEmpError = '';
    this.http.put<any>(`http://localhost:8000/employees/update/${this.editEmpCin}`, this.editEmpForm, { headers: this.getHeaders() })
      .subscribe({
        next: res => { this.editEmpLoading = false; this.editEmpSuccess = res.message; this.searchEmployees(); this.loadUsers(); setTimeout(() => this.closeEditEmpModal(), 1500); },
        error: err => { this.editEmpLoading = false; this.editEmpError = err.error?.detail || 'Erreur'; }
      });
  }

  exportCsv() { window.open('http://localhost:8000/employees/export-csv', '_blank'); }

  logout() { localStorage.clear(); this.router.navigate(['/login']); }

  // ─────────────── ANALYTICS ───────────────

  loadAnalytics() {
    if (!this.chartJsLoaded) { setTimeout(() => this.loadAnalytics(), 300); return; }
    this.analyticsLoading = true;
    const h = this.getHeaders();
    const p = this.selectedPeriod;

    this.http.get<any>('http://localhost:8000/analytics/summary', { headers: h }).subscribe(d => { this.analyticsData = d; });
    this.http.get<any>(`http://localhost:8000/analytics/conversations-evolution?period=${p}`, { headers: h }).subscribe(d => { this.convEvolution = d; this.renderLineChart(); });
    this.http.get<any>(`http://localhost:8000/analytics/messages-stats?period=${p}`, { headers: h }).subscribe(d => { this.messagesStats = d; this.renderBarMessages(); });
    this.http.get<any>('http://localhost:8000/analytics/department-distribution', { headers: h }).subscribe(d => { this.deptDistribution = d; this.renderDeptChart(); });
    this.http.get<any>('http://localhost:8000/analytics/top-keywords', { headers: h }).subscribe(d => { this.topKeywords = d; this.renderKeywordsChart(); });
    this.http.get<any>('http://localhost:8000/analytics/satisfaction', { headers: h }).subscribe(d => { this.satisfaction = d; this.renderSatisfactionChart(); });
    this.http.get<any>('http://localhost:8000/analytics/rag-documents', { headers: h }).subscribe(d => { this.ragDocs = d; this.renderRagChart(); });
    this.http.get<any>('http://localhost:8000/analytics/heatmap', { headers: h }).subscribe(d => { this.heatmap = d; this.renderHeatmap(); });
    this.http.get<any>('http://localhost:8000/analytics/fallback-rate', { headers: h }).subscribe(d => { this.fallbackRate = d; this.renderFallbackChart(); });
    this.http.get<any>('http://localhost:8000/analytics/language-distribution', { headers: h }).subscribe(d => { this.langDistrib = d; this.renderLangChart(); this.analyticsLoading = false; });
  }

  changePeriod(period: string) { this.selectedPeriod = period; this.loadAnalytics(); }

  private destroyChart(id: string) { if (this.charts[id]) { this.charts[id].destroy(); delete this.charts[id]; } }

  private renderLineChart() {
    setTimeout(() => {
      this.destroyChart('line');
      const ctx = document.getElementById('lineChart') as HTMLCanvasElement;
      if (!ctx || !this.convEvolution.labels) return;
      this.charts['line'] = new (window as any).Chart(ctx, {
        type: 'line',
        data: { labels: this.convEvolution.labels, datasets: [{ label: 'Conversations', data: this.convEvolution.data, borderColor: '#6366f1', backgroundColor: 'rgba(99,102,241,0.08)', borderWidth: 2.5, tension: 0.4, fill: true, pointBackgroundColor: '#6366f1', pointRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { color: '#94a3b8', font: { size: 11 } } }, x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 11 } } } } }
      });
    }, 200);
  }

  private renderBarMessages() {
    setTimeout(() => {
      this.destroyChart('barMsg');
      const ctx = document.getElementById('barMessages') as HTMLCanvasElement;
      if (!ctx) return;
      this.charts['barMsg'] = new (window as any).Chart(ctx, {
        type: 'bar',
        data: { labels: ['Utilisateur', 'Bot'], datasets: [{ data: [this.messagesStats.user_messages || 0, this.messagesStats.bot_messages || 0], backgroundColor: ['rgba(99,102,241,0.8)', 'rgba(34,197,94,0.8)'], borderRadius: 8, borderSkipped: false }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { color: '#94a3b8', font: { size: 11 } } }, x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 12 } } } } }
      });
    }, 200);
  }

  private renderDeptChart() {
    setTimeout(() => {
      this.destroyChart('dept');
      const ctx = document.getElementById('deptChart') as HTMLCanvasElement;
      if (!ctx || !this.deptDistribution.labels) return;
      this.charts['dept'] = new (window as any).Chart(ctx, {
        type: 'doughnut',
        data: { labels: this.deptDistribution.labels, datasets: [{ data: this.deptDistribution.data, backgroundColor: ['#6366f1','#22c55e','#f59e0b','#ef4444','#14b8a6'], borderWidth: 0, hoverOffset: 8 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '65%', plugins: { legend: { position: 'bottom', labels: { color: '#64748b', font: { size: 11 }, padding: 16 } } } }
      });
    }, 200);
  }

  private renderKeywordsChart() {
    setTimeout(() => {
      this.destroyChart('keywords');
      const ctx = document.getElementById('keywordsChart') as HTMLCanvasElement;
      if (!ctx || !this.topKeywords.labels) return;
      this.charts['keywords'] = new (window as any).Chart(ctx, {
        type: 'bar',
        data: { labels: this.topKeywords.labels, datasets: [{ data: this.topKeywords.data, backgroundColor: 'rgba(99,102,241,0.75)', borderRadius: 6, borderSkipped: false }] },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { color: '#94a3b8', font: { size: 11 } } }, y: { grid: { display: false }, ticks: { color: '#374151', font: { size: 12 } } } } }
      });
    }, 200);
  }

  private renderSatisfactionChart() {
    setTimeout(() => {
      this.destroyChart('satisfaction');
      const ctx = document.getElementById('satisfactionChart') as HTMLCanvasElement;
      if (!ctx) return;
      const rate = this.satisfaction.satisfaction_rate || 0;
      this.charts['satisfaction'] = new (window as any).Chart(ctx, {
        type: 'doughnut',
        data: { datasets: [{ data: [rate, 100 - rate], backgroundColor: ['#22c55e', '#f1f5f9'], borderWidth: 0 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '75%', rotation: -90, circumference: 180, plugins: { legend: { display: false } } }
      });
    }, 200);
  }

  private renderRagChart() {
    setTimeout(() => {
      this.destroyChart('rag');
      const ctx = document.getElementById('ragChart') as HTMLCanvasElement;
      if (!ctx || !this.ragDocs.labels) return;
      this.charts['rag'] = new (window as any).Chart(ctx, {
        type: 'bar',
        data: { labels: this.ragDocs.labels, datasets: [{ label: 'Chunks', data: this.ragDocs.data, backgroundColor: 'rgba(245,158,11,0.8)', borderRadius: 6, borderSkipped: false }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { color: '#94a3b8', font: { size: 11 } } }, x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 11 }, maxRotation: 30 } } } }
      });
    }, 200);
  }

  private renderHeatmap() {
    setTimeout(() => {
      const canvas = document.getElementById('heatmapCanvas') as HTMLCanvasElement;
      if (!canvas || !this.heatmap.matrix) return;
      const ctx = canvas.getContext('2d')!;
      const matrix = this.heatmap.matrix;
      const days = this.heatmap.days || [];
      const cellW = 28, cellH = 28, padL = 80, padT = 30;
      canvas.width  = padL + 24 * cellW + 20;
      canvas.height = padT + days.length * cellH + 20;
      const maxVal = Math.max(...matrix.flat(), 1);
      ctx.font = '10px Inter'; ctx.fillStyle = '#94a3b8';
      for (let h = 0; h < 24; h++) {
        if (h % 3 === 0) ctx.fillText(`${h}h`, padL + h * cellW + 4, 20);
      }
      matrix.forEach((row: number[], di: number) => {
        ctx.font = '11px Inter'; ctx.fillStyle = '#64748b';
        ctx.fillText(days[di]?.substring(0, 3) || '', 0, padT + di * cellH + 19);
        row.forEach((val: number, hi: number) => {
          const alpha = 0.07 + (val / maxVal) * 0.85;
          ctx.fillStyle = `rgba(99,102,241,${alpha})`;
          ctx.beginPath();
          (ctx as any).roundRect(padL + hi * cellW + 2, padT + di * cellH + 2, cellW - 4, cellH - 4, 4);
          ctx.fill();
        });
      });
    }, 300);
  }

  private renderFallbackChart() {
    setTimeout(() => {
      this.destroyChart('fallback');
      const ctx = document.getElementById('fallbackChart') as HTMLCanvasElement;
      if (!ctx) return;
      this.charts['fallback'] = new (window as any).Chart(ctx, {
        type: 'doughnut',
        data: { labels: ['Réussite', 'Fallback'], datasets: [{ data: [this.fallbackRate.success_rate || 0, this.fallbackRate.fallback_rate || 0], backgroundColor: ['#22c55e', '#ef4444'], borderWidth: 0, hoverOffset: 6 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '65%', plugins: { legend: { position: 'bottom', labels: { color: '#64748b', font: { size: 11 }, padding: 14 } } } }
      });
    }, 200);
  }

  private renderLangChart() {
    setTimeout(() => {
      this.destroyChart('lang');
      const ctx = document.getElementById('langChart') as HTMLCanvasElement;
      if (!ctx || !this.langDistrib.labels) return;
      this.charts['lang'] = new (window as any).Chart(ctx, {
        type: 'pie',
        data: { labels: this.langDistrib.labels, datasets: [{ data: this.langDistrib.data, backgroundColor: ['#6366f1','#22c55e','#f59e0b','#ef4444'], borderWidth: 0, hoverOffset: 8 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#64748b', font: { size: 11 }, padding: 14 } } } }
      });
    }, 200);
  }
}