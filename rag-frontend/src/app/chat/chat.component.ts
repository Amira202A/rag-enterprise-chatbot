import { Component, ViewChild, ElementRef, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { ChatService } from '../chat.service';
import { Router } from '@angular/router';

interface Message {
  role: 'user' | 'bot';
  content: string;
  timestamp: string;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit, OnDestroy {

  @ViewChild('scrollContainer') scrollContainer!: ElementRef;

  conversations: Conversation[] = [];
  activeConversationId!: string;
  userMessage = '';
  isTyping    = false;
  selectedLanguage = 'fr-FR';
  currentUser: any = {};

  // Search + FAQ
  searchHistory = '';
  openFaq: number | null = null;

  // Voice
  private recognition: any = null;
  isListening = false;
  private finalTranscript    = '';
  private interimTranscript  = '';
  private shouldRestart      = false;
  private isRestarting       = false;
  private silenceTimer: any  = null;
  private readonly SILENCE_DELAY = 1800;
  private audioContext: AudioContext | null  = null;
  private analyser: AnalyserNode | null      = null;
  private mediaStream: MediaStream | null    = null;
  private animationFrame: number | null      = null;
  waveformBars: number[] = Array(20).fill(2);

  constructor(
    private chatService: ChatService,
    private cdr: ChangeDetectorRef,
    private router: Router
  ) {}

  // ─────────────── GETTERS ───────────────

  get currentConversation(): Conversation | undefined {
    return this.conversations.find(c => c.id === this.activeConversationId);
  }

  get filteredConversations(): Conversation[] {
    if (!this.searchHistory.trim()) return this.conversations;
    const q = this.searchHistory.toLowerCase();
    return this.conversations.filter(c =>
      c.title.toLowerCase().includes(q)
    );
  }

  // ─────────────── LIFECYCLE ───────────────

  ngOnInit() {
    const userStr = localStorage.getItem('user');
    if (userStr) this.currentUser = JSON.parse(userStr);

    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
    }
    this.loadConversations();
  }

  ngOnDestroy() {
    this.stopVoice();
    window.speechSynthesis?.cancel();
  }

  // ─────────────── LANGUE AUTO ───────────────

  private autoDetectLanguage(text: string): string {
    const arabicChars = (text.match(/[\u0600-\u06FF]/g) || []).length;
    const totalChars  = text.replace(/\s/g, '').length;

    // Arabe standard
    if (totalChars > 0 && arabicChars / totalChars > 0.3) return 'ar-SA';

    // Anglais
    const englishWords = [
      'what', 'who', 'where', 'when', 'how', 'why',
      'is', 'are', 'the', 'give', 'tell', 'define',
      'explain', 'can', 'do', 'does', 'did', 'a', 'an'
    ];
    const words = text.toLowerCase().split(/\s+/);
    const englishScore = words.filter(w => englishWords.includes(w)).length;
    if (englishScore >= 1) return 'en-US';

    // Français par défaut
    return 'fr-FR';
  }

  // ─────────────── FAQ ───────────────

  toggleFaq(index: number) {
    this.openFaq = this.openFaq === index ? null : index;
  }

  // ─────────────── CONVERSATIONS ───────────────

  loadConversations() {
    this.chatService.getConversations().subscribe({
      next: (convs: any[]) => {
        if (convs && convs.length > 0) {
          this.conversations = convs.map(conv => ({
            id:       conv.id,
            title:    conv.title,
            messages: conv.messages || []
          }));
          this.activeConversationId = '';
          this.cdr.detectChanges();
        } else {
          this.createNewConversation();
        }
      },
      error: () => this.createNewConversation()
    });
  }

  createNewConversation() {
    this.chatService.createConversation().subscribe({
      next: (res: any) => {
        if (!res?.conversation_id) return;
        const newConv: Conversation = {
          id:       res.conversation_id,
          title:    'Nouvelle conversation',
          messages: []
        };
        this.conversations.unshift(newConv);
        this.activeConversationId = newConv.id;
        this.cdr.detectChanges();
      },
      error: (err: any) => console.error('Erreur createConversation:', err)
    });
  }

  selectConversation(id: string) {
    this.activeConversationId = id;
    this.cdr.detectChanges();
    setTimeout(() => this.scrollToBottom(), 100);
  }

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    this.router.navigate(['/login']);
  }

  // ─────────────── MESSAGES ───────────────

  onEnterKey() {
    if (this.isListening) this.stopVoice();
    this.sendMessage();
  }

  sendMessage() {
    const input = this.userMessage?.trim();
    if (!input || this.isTyping) return;

    if (!this.activeConversationId) {
      this.chatService.createConversation().subscribe({
        next: (res: any) => {
          if (!res?.conversation_id) return;
          const newConv: Conversation = {
            id:       res.conversation_id,
            title:    input.slice(0, 28),
            messages: []
          };
          this.conversations.unshift(newConv);
          this.activeConversationId = newConv.id;
          this.cdr.detectChanges();
          this._sendMessageNow(input);
        }
      });
      return;
    }
    this._sendMessageNow(input);
  }

  _sendMessageNow(input: string) {
    if (this.isListening) this.stopVoice();
    window.speechSynthesis?.cancel();

    // ✅ Auto-détection de langue
    this.selectedLanguage = this.autoDetectLanguage(input);

    const message: Message = {
      role:      'user',
      content:   input,
      timestamp: new Date().toLocaleTimeString('fr-FR', {
        hour: '2-digit', minute: '2-digit'
      })
    };

    this.currentConversation!.messages.push(message);
    this.userMessage      = '';
    this.finalTranscript  = '';
    this.interimTranscript = '';
    this.isTyping = true;
    this.cdr.detectChanges();
    this.scrollToBottom();

    this.chatService.sendMessage(input, this.activeConversationId).subscribe({
      next: (res: any) => {
        this.currentConversation?.messages.push({
          role:      'bot',
          content:   res?.answer || res?.response || 'Pas de réponse',
          timestamp: new Date().toLocaleTimeString('fr-FR', {
            hour: '2-digit', minute: '2-digit'
          })
        });
        this.isTyping = false;
        this.cdr.detectChanges();
        this.scrollToBottom();
      },
      error: (err: any) => {
        this.currentConversation?.messages.push({
          role:      'bot',
          content:   `Erreur serveur (${err?.status || '??'})`,
          timestamp: new Date().toLocaleTimeString('fr-FR', {
            hour: '2-digit', minute: '2-digit'
          })
        });
        this.isTyping = false;
        this.cdr.detectChanges();
        this.scrollToBottom();
      }
    });
  }

  scrollToBottom() {
    setTimeout(() => {
      if (this.scrollContainer) {
        this.scrollContainer.nativeElement.scrollTop =
          this.scrollContainer.nativeElement.scrollHeight;
      }
    }, 100);
  }

  // ─────────────── VOICE ───────────────

  toggleVoice() {
    this.isListening ? this.stopVoice() : this.startVoice();
  }

  private playBip(type: 'start' | 'stop') {
    try {
      const ctx  = new AudioContext();
      const osc  = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = type === 'start' ? 880 : 440;
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.15);
      osc.onended = () => ctx.close();
    } catch (e) {}
  }

  private async startWaveform() {
    try {
      this.mediaStream  = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioContext = new AudioContext();
      this.analyser     = this.audioContext.createAnalyser();
      this.analyser.fftSize = 64;
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      source.connect(this.analyser);
      this.drawWaveform();
    } catch (e) {}
  }

  private drawWaveform() {
    if (!this.analyser || !this.isListening) return;
    const data = new Uint8Array(this.analyser.frequencyBinCount);
    this.analyser.getByteFrequencyData(data);
    const step = Math.floor(data.length / 20);
    this.waveformBars = Array.from({ length: 20 }, (_, i) => {
      const val = data[i * step] / 255;
      return Math.max(2, Math.round(val * 40));
    });
    this.animationFrame = requestAnimationFrame(() => this.drawWaveform());
  }

  private stopWaveform() {
    if (this.animationFrame) cancelAnimationFrame(this.animationFrame);
    this.animationFrame = null;
    this.mediaStream?.getTracks().forEach(t => t.stop());
    this.audioContext?.close();
    this.audioContext = null;
    this.analyser     = null;
    this.mediaStream  = null;
    this.waveformBars = Array(20).fill(2);
  }

  private resetSilenceTimer() {
    if (this.silenceTimer) clearTimeout(this.silenceTimer);
    this.silenceTimer = setTimeout(() => {
      if (this.userMessage?.trim() && this.isListening) {
        this.stopVoice();
        this.sendMessage();
      }
    }, this.SILENCE_DELAY);
  }

  private clearSilenceTimer() {
    if (this.silenceTimer) clearTimeout(this.silenceTimer);
    this.silenceTimer = null;
  }

  async startVoice() {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Utilise Google Chrome pour le micro');
      return;
    }

    this.finalTranscript   = '';
    this.interimTranscript = '';
    this.shouldRestart     = true;
    this.isRestarting      = false;

    this.playBip('start');
    await this.startWaveform();

    this.recognition = new SpeechRecognition();
    this.recognition.lang           = this.selectedLanguage;
    this.recognition.continuous     = true;
    this.recognition.interimResults = true;
    this.recognition.maxAlternatives = 1;

    this.recognition.onstart = () => {
      this.isListening      = true;
      this.isRestarting     = false;
      this.interimTranscript = '';
      this.cdr.detectChanges();
    };

    this.recognition.onresult = (event: any) => {
      this.interimTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const text = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          this.finalTranscript += text + ' ';
          // ✅ Auto-détecter la langue pendant la dictée
          this.selectedLanguage = this.autoDetectLanguage(this.finalTranscript);
        } else {
          this.interimTranscript += text;
        }
      }
      this.userMessage = (this.finalTranscript + this.interimTranscript).trim();
      this.resetSilenceTimer();
      this.cdr.detectChanges();
    };

    this.recognition.onerror = (event: any) => {
      if (event.error === 'not-allowed') {
        alert('Permission micro refusée');
        this.shouldRestart = false;
        this.isListening   = false;
        this.stopWaveform();
        this.cdr.detectChanges();
        return;
      }
      if (event.error !== 'no-speech') {
        this.shouldRestart = false;
        this.isListening   = false;
        this.stopWaveform();
        this.cdr.detectChanges();
      }
    };

    this.recognition.onend = () => {
      if (this.shouldRestart && this.isListening && !this.isRestarting) {
        this.isRestarting = true;
        setTimeout(() => {
          if (this.shouldRestart && this.isListening) {
            try { this.recognition.start(); }
            catch (e) {
              this.isListening = false;
              this.stopWaveform();
              this.cdr.detectChanges();
            }
          }
          this.isRestarting = false;
        }, 300);
      } else {
        this.isListening = false;
        this.stopWaveform();
        this.cdr.detectChanges();
      }
    };

    this.recognition.start();
  }

  stopVoice() {
    this.shouldRestart = false;
    this.isListening   = false;
    this.isRestarting  = false;
    this.clearSilenceTimer();
    this.stopWaveform();
    if (this.recognition) {
      try { this.recognition.stop(); } catch {}
      this.recognition = null;
    }
    this.playBip('stop');
    this.cdr.detectChanges();
  }

  speak(text: string) {
    window.speechSynthesis?.cancel();
    const utterance  = new SpeechSynthesisUtterance(text);
    // ✅ Utilise la langue auto-détectée
    utterance.lang   = this.autoDetectLanguage(text);
    const voices     = window.speechSynthesis.getVoices();
    const langCode   = utterance.lang.split('-')[0];
    const voice      = voices.find(v => v.lang.startsWith(langCode));
    if (voice) utterance.voice = voice;
    window.speechSynthesis.speak(utterance);
  }
  
}
