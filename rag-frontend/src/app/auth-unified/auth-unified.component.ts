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

  isLogin = true;
  cinFocused: boolean = false;
  pwFocused: boolean = false;

  cin = '';
  password = '';
  showPassword = false;

  nom = '';
  prenom = '';
  email = '';
  regCin = '';
  termsAccepted = false;

  loading = false;
  error = '';
  success = '';

  constructor(
    private http: HttpClient,
    private router: Router,
    private cd: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.initParticles();
  }

  initParticles() {
    setTimeout(() => {
      const canvas = document.getElementById('particles') as HTMLCanvasElement;
      if (!canvas) return;

      const ctx = canvas.getContext('2d')!;
      let W = canvas.width = window.innerWidth;
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
            const d = Math.sqrt(dx * dx + dy * dy);

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
        W = canvas.width = window.innerWidth;
        H = canvas.height = window.innerHeight;
      });

    }, 100);
  }

  switchToRegister() {
    this.isLogin = false;
    this.error = '';
    this.success = '';
  }

  switchToLogin() {
    this.isLogin = true;
    this.error = '';
    this.success = '';
  }

  // 🔐 LOGIN
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

        if (res.user.is_admin) {
          localStorage.setItem('admin_token', res.access_token);
          localStorage.setItem('admin_user', JSON.stringify(res.user));
          this.router.navigate(['/admin']);
        } else {
          // ✅ Redirection par département
          this.router.navigate(['/chat']);

          // 🔓 (optionnel)
          // const dept = res.user.department?.toLowerCase();
          // if (dept === 'rh') this.router.navigate(['/chat']);
          // else if (dept === 'it') this.router.navigate(['/chat']);
          // else if (dept === 'marketing') this.router.navigate(['/chat']);
          // else this.router.navigate(['/chat']);
        }
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.detail || 'Identifiants incorrects.';
      }
    });
  }

  // 📝 REGISTER
  register() {
    this.error = '';
    this.success = '';

    if (!this.nom || !this.prenom || !this.regCin || !this.email) {
      this.error = 'Tous les champs sont obligatoires.';
      return;
    }

    if (!this.termsAccepted) {
      this.error = 'Veuillez accepter les conditions.';
      return;
    }

    this.loading = true;

    this.http.post<any>('http://localhost:8000/auth/register', {
      nom: this.nom,
      prenom: this.prenom,
      cin: this.regCin,
      email: this.email
    }).subscribe({
      next: () => {
        this.loading = false;

        this.success = '📩 Compte créé ! Vérifiez votre email.';

        this.nom = '';
        this.prenom = '';
        this.regCin = '';
        this.email = '';
        this.termsAccepted = false;

        setTimeout(() => {
          this.success = '🔐 Redirection vers login...';
          this.isLogin = true;
          this.cd.detectChanges();

          setTimeout(() => {
            this.switchToLogin();
          }, 100);

        }, 1500);
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.detail || "Erreur lors de l'inscription.";
      }
    });
  }
}