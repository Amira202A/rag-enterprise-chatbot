import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpClient, HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-auth-unified',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './auth-unified.component.html',
  styleUrls: ['./auth-unified.component.css']
})
export class AuthUnifiedComponent implements OnInit {

  // ── Login ──
  cinFocused   = false;
  pwFocused    = false;
  cin          = '';
  password     = '';
  showPassword = false;
  loading      = false;
  error        = '';

  // ── Change Password Modal ──
  showChangeModal   = false;
  oldPwFocused      = false;
  newPwFocused      = false;
  confirmPwFocused  = false;
  oldPassword       = '';
  newPassword       = '';
  confirmPassword   = '';
  showOldPw         = false;
  showNewPw         = false;
  showConfirmPw     = false;
  changeLoading     = false;
  changeError       = '';
  changeSuccess     = '';

  // ── Forgot Password ──
  showForgotModal  = false;
  forgotStep       = 1;
  forgotCin        = '';
  forgotEmailHint  = '';
  otpCode          = '';
  forgotNewPw      = '';
  forgotConfirmPw  = '';
  showForgotNewPw  = false;
  showForgotConfPw = false;
  forgotLoading    = false;
  forgotError      = '';
  forgotSuccess    = '';
  otpTimer         = 0;
  private otpInterval: any;

  private pendingUser: any = null;
  private pendingToken     = '';

  constructor(
    private http: HttpClient,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.initParticles();
  }

  // ── Particles ──
  initParticles() {
    setTimeout(() => {
      const canvas = document.getElementById('particles') as HTMLCanvasElement;
      if (!canvas) return;
      const ctx = canvas.getContext('2d')!;
      let W = canvas.width  = window.innerWidth;
      let H = canvas.height = window.innerHeight;
      const pts: any[] = Array.from({ length: 70 }, () => ({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * 0.45,
        vy: (Math.random() - 0.5) * 0.45,
        r: Math.random() * 1.4 + 0.4,
        a: Math.random() * 0.4 + 0.15
      }));

      const draw = () => {
        ctx.clearRect(0, 0, W, H);
        for (const p of pts) {
          p.x += p.vx;
          p.y += p.vy;
          if (p.x < 0 || p.x > W) p.vx *= -1;
          if (p.y < 0 || p.y > H) p.vy *= -1;
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(147,197,253,${p.a})`;
          ctx.fill();
        }
        for (let i = 0; i < pts.length; i++) {
          for (let j = i + 1; j < pts.length; j++) {
            const dx = pts[i].x - pts[j].x;
            const dy = pts[i].y - pts[j].y;
            const d  = Math.sqrt(dx * dx + dy * dy);
            if (d < 110) {
              ctx.beginPath();
              ctx.moveTo(pts[i].x, pts[i].y);
              ctx.lineTo(pts[j].x, pts[j].y);
              ctx.strokeStyle = `rgba(147,197,253,${0.07 * (1 - d / 110)})`;
              ctx.lineWidth = 0.5;
              ctx.stroke();
            }
          }
        }
        requestAnimationFrame(draw);
      };

      draw();

      window.addEventListener('resize', () => {
        W = canvas.width  = window.innerWidth;
        H = canvas.height = window.innerHeight;
      });
    }, 100);
  }

  // ── LOGIN ──
  login() {
    this.error = '';
    if (!this.cin || !this.password) {
      this.error = 'CIN et mot de passe obligatoires.';
      return;
    }

    this.loading = true;
    this.cdr.detectChanges();

    this.http.post<any>('http://localhost:8000/auth/login', {
      cin: this.cin,
      password: this.password
    }).subscribe({
      next: (res) => {
        this.loading = false;

        if (res.user.first_login) {
          this.pendingUser     = res.user;
          this.pendingToken    = res.access_token;
          this.oldPassword     = this.password;
          this.showChangeModal = true;
          this.cdr.detectChanges();
          return;
        }

        this.finalizeLogin(res);
      },
      error: (err) => {
        this.loading = false;
        this.error   = err.error?.detail || 'Identifiants incorrects.';
        this.cdr.detectChanges();
      }
    });
  }

  // ── CHANGER MOT DE PASSE (première connexion) ──
  submitChangePassword() {
    this.changeError   = '';
    this.changeSuccess = '';

    if (!this.newPassword || !this.confirmPassword) {
      this.changeError = 'Tous les champs sont obligatoires.';
      return;
    }
    if (this.newPassword.length < 8) {
      this.changeError = 'Minimum 8 caractères.';
      return;
    }
    if (this.newPassword !== this.confirmPassword) {
      this.changeError = 'Les mots de passe ne correspondent pas.';
      return;
    }
    if (this.newPassword === this.oldPassword) {
      this.changeError = 'Le nouveau mot de passe doit être différent.';
      return;
    }

    this.changeLoading = true;
    this.cdr.detectChanges();

    this.http.post<any>('http://localhost:8000/auth/change-password', {
      cin:          this.cin,
      old_password: this.oldPassword,
      new_password: this.newPassword
    }).subscribe({
      next: () => {
        this.changeLoading = false;
        this.changeSuccess = '✅ Mot de passe changé ! Redirection...';
        this.cdr.detectChanges();
        setTimeout(() => {
          this.showChangeModal = false;
          localStorage.setItem('token', this.pendingToken);
          localStorage.setItem('user', JSON.stringify({
            ...this.pendingUser,
            first_login: false
          }));
          this.router.navigate(['/chat']);
        }, 1500);
      },
      error: (err) => {
        this.changeLoading = false;
        this.changeError   = err.error?.detail || 'Erreur lors du changement.';
        this.cdr.detectChanges();
      }
    });
  }

  // ── FORGOT PASSWORD ──
  openForgotModal() {
    this.showForgotModal = true;
    this.forgotStep      = 1;
    this.forgotCin       = '';
    this.forgotError     = '';
    this.forgotSuccess   = '';
    this.otpCode         = '';
    this.forgotNewPw     = '';
    this.forgotConfirmPw = '';
    this.forgotLoading   = false;
    this.cdr.detectChanges();
  }

  closeForgotModal() {
    this.showForgotModal = false;
    this.forgotLoading   = false;
    clearInterval(this.otpInterval);
    this.cdr.detectChanges();
  }

  // Étape 1 : envoyer OTP
  sendOtp() {
    this.forgotError   = '';
    this.forgotSuccess = '';

    if (!this.forgotCin.trim()) {
      this.forgotError = 'Veuillez entrer votre CIN.';
      return;
    }

    this.forgotLoading = true;
    this.cdr.detectChanges();

    this.http.post<any>('http://localhost:8000/auth/forgot-password', {
      cin: this.forgotCin
    }).subscribe({
      next: (res) => {
        console.log('✅ Réponse reçue:', res);
        this.forgotLoading   = false;
        this.forgotEmailHint = res.email_hint;
        this.forgotStep      = 2;
        this.startOtpTimer();
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('❌ Erreur:', err);
        this.forgotLoading = false;
        this.forgotError   = err.error?.detail || 'Erreur lors de l\'envoi.';
        this.cdr.detectChanges();
      }
    });
  }

  // Timer 10 minutes
  startOtpTimer() {
    this.otpTimer = 600;
    clearInterval(this.otpInterval);
    this.otpInterval = setInterval(() => {
      this.otpTimer--;
      this.cdr.detectChanges();
      if (this.otpTimer <= 0) clearInterval(this.otpInterval);
    }, 1000);
  }

  get otpTimerDisplay(): string {
    const m = Math.floor(this.otpTimer / 60);
    const s = this.otpTimer % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  }

  // Étape 2 : vérifier OTP
  verifyOtp() {
    this.forgotError = '';

    if (this.otpCode.length !== 6) {
      this.forgotError = 'Entrez le code à 6 chiffres.';
      return;
    }

    this.forgotLoading = true;
    this.cdr.detectChanges();

    this.http.post<any>('http://localhost:8000/auth/verify-otp', {
      cin:  this.forgotCin,
      code: this.otpCode
    }).subscribe({
      next: () => {
        this.forgotLoading = false;
        this.forgotStep    = 3;
        clearInterval(this.otpInterval);
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.forgotLoading = false;
        this.forgotError   = err.error?.detail || 'Code invalide ou expiré.';
        this.cdr.detectChanges();
      }
    });
  }

  // Étape 3 : reset mot de passe
  resetPassword() {
    this.forgotError   = '';
    this.forgotSuccess = '';

    if (!this.forgotNewPw || !this.forgotConfirmPw) {
      this.forgotError = 'Tous les champs sont obligatoires.';
      return;
    }
    if (this.forgotNewPw.length < 8) {
      this.forgotError = 'Minimum 8 caractères.';
      return;
    }
    if (this.forgotNewPw !== this.forgotConfirmPw) {
      this.forgotError = 'Les mots de passe ne correspondent pas.';
      return;
    }

    this.forgotLoading = true;
    this.cdr.detectChanges();

    this.http.post<any>('http://localhost:8000/auth/reset-password', {
      cin:          this.forgotCin,
      code:         this.otpCode,
      new_password: this.forgotNewPw
    }).subscribe({
      next: () => {
        this.forgotLoading = false;
        this.forgotSuccess = '✅ Mot de passe réinitialisé ! Redirection...';
        this.cdr.detectChanges();
        setTimeout(() => this.closeForgotModal(), 2000);
      },
      error: (err) => {
        this.forgotLoading = false;
        this.forgotError   = err.error?.detail || 'Erreur réinitialisation.';
        this.cdr.detectChanges();
      }
    });
  }

  // Renvoyer OTP
  resendOtp() {
    this.otpCode     = '';
    this.forgotError = '';
    this.forgotStep  = 1;
    this.cdr.detectChanges();
    this.sendOtp();
  }

  // ── Finaliser Login ──
  private finalizeLogin(res: any) {
    localStorage.setItem('token', res.access_token);
    localStorage.setItem('user', JSON.stringify(res.user));

    if (res.user.is_admin) {
      localStorage.setItem('admin_token', res.access_token);
      localStorage.setItem('admin_user', JSON.stringify(res.user));
      this.router.navigate(['/admin']);
    } else {
      this.router.navigate(['/chat']);
    }
  }

  // ── Password Strength ──
  get passwordStrength(): number {
    const p = this.newPassword;
    let score = 0;
    if (p.length >= 8)           score++;
    if (p.length >= 12)          score++;
    if (/[A-Z]/.test(p))        score++;
    if (/[0-9]/.test(p))        score++;
    if (/[^A-Za-z0-9]/.test(p)) score++;
    return score;
  }

  get strengthLabel(): string {
    const s = this.passwordStrength;
    if (s <= 1) return 'Faible';
    if (s <= 3) return 'Moyen';
    return 'Fort';
  }

  get strengthColor(): string {
    const s = this.passwordStrength;
    if (s <= 1) return '#ef4444';
    if (s <= 3) return '#f59e0b';
    return '#16a34a';
  }
}