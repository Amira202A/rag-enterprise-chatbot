import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM, MAIL_SERVER, MAIL_PORT


def generate_password(length: int = 10) -> str:
    """Génère un mot de passe aléatoire sécurisé."""
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choices(chars, k=length))


def send_password_email(to_email: str, nom: str, password: str) -> bool:
    """Envoie le mot de passe par email via Gmail SMTP."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "PGH Brain — Votre mot de passe"
        msg["From"]    = MAIL_FROM
        msg["To"]      = to_email

        html = f"""
        <html><body style="font-family: Arial, sans-serif; background: #f8fafc; padding: 30px;">
          <div style="max-width: 500px; margin: auto; background: white;
                      border-radius: 12px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
            <div style="background: #2563eb; color: white; padding: 20px;
                        border-radius: 8px; text-align: center; margin-bottom: 24px;">
              <h2 style="margin:0">PGH Brain</h2>
            </div>
            <p>Bonjour <strong>{nom}</strong>,</p>
            <p>Votre compte a été créé avec succès.</p>
            <p>Voici votre mot de passe confidentiel :</p>
            <div style="background: #f1f5f9; border: 2px dashed #2563eb;
                        border-radius: 8px; padding: 16px; text-align: center; margin: 20px 0;">
              <span style="font-size: 22px; font-weight: bold;
                           letter-spacing: 3px; color: #2563eb;">{password}</span>
            </div>
            <p style="color: #ef4444; font-size: 13px;">
              ⚠️ Ne partagez jamais ce mot de passe. Connectez-vous avec votre CIN.
            </p>
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
            <p style="color: #94a3b8; font-size: 12px; text-align: center;">
              PGH Enterprise — Système de chatbot IA
            </p>
          </div>
        </body></html>
        """

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_FROM, to_email, msg.as_string())

        print(f"✅ Email envoyé à {to_email}")
        return True

    except Exception as e:
        print(f"❌ Erreur envoi email: {e}")
        return False


def send_otp_email(to_email: str, nom: str, otp_code: str) -> bool:
    """Envoie le code OTP de réinitialisation par email."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "PGH Brain — Code de réinitialisation"
        msg["From"]    = MAIL_FROM
        msg["To"]      = to_email

        html = f"""
        <html><body style="font-family: Arial, sans-serif;
                           background: #f8fafc; padding: 30px;">
          <div style="max-width: 500px; margin: auto; background: white;
                      border-radius: 12px; padding: 30px;
                      box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
            <div style="background: linear-gradient(135deg,#0f2a4e,#2563eb);
                        color: white; padding: 24px; border-radius: 10px;
                        text-align: center; margin-bottom: 28px;">
              <h2 style="margin:0; font-size:22px;">PGH Brain</h2>
              <p style="margin:6px 0 0; opacity:0.8; font-size:13px;">
                Réinitialisation de mot de passe
              </p>
            </div>

            <p>Bonjour <strong>{nom}</strong>,</p>
            <p style="margin:12px 0;">
              Voici votre code de réinitialisation :<br/>
              <strong style="color:#64748b; font-size:13px;">
                Valable 10 minutes uniquement.
              </strong>
            </p>

            <div style="background: #f1f5f9;
                        border: 2px dashed #2563eb;
                        border-radius: 12px; padding: 20px;
                        text-align: center; margin: 24px 0;">
              <span style="font-size: 38px; font-weight: 900;
                           letter-spacing: 10px; color: #1d4ed8;
                           font-family: monospace;">
                {otp_code}
              </span>
            </div>

            <p style="color:#ef4444; font-size:13px;">
              ⚠️ Ne partagez jamais ce code. S'il expire, faites une nouvelle demande.
            </p>

            <hr style="border:none; border-top:1px solid #e5e7eb; margin:20px 0;">
            <p style="color:#94a3b8; font-size:12px; text-align:center;">
              PGH Enterprise — Système de chatbot IA
            </p>
          </div>
        </body></html>
        """

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_FROM, to_email, msg.as_string())

        print(f"✅ OTP envoyé à {to_email}")
        return True

    except Exception as e:
        print(f"❌ Erreur envoi OTP: {e}")
        return False