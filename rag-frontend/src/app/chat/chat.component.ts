import { Component, ViewChild, ElementRef, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { ChatService } from '../chat.service';

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
  isTyping = false;
  selectedLanguage = 'en-US';

  private recognition: any = null;
  isListening = false;
  private finalTranscript = '';
  private interimTranscript = '';
  private shouldRestart = false;
  private isRestarting = false;

  private silenceTimer: any = null;
  private readonly SILENCE_DELAY = 1800;

  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private mediaStream: MediaStream | null = null;
  private animationFrame: number | null = null;
  waveformBars: number[] = Array(20).fill(2);

  constructor(private chatService: ChatService, private cdr: ChangeDetectorRef) {}

  get currentConversation(): Conversation | undefined {
    return this.conversations.find(c => c.id === this.activeConversationId);
  }

  ngOnInit() {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
    }
    this.loadConversations();
  }

  loadConversations() {
    this.chatService.getConversations().subscribe({
      next: (convs: any[]) => {
        if (convs && convs.length > 0) {
          this.conversations = convs.map(conv => ({
            id: conv.id,
            title: conv.title,
            messages: conv.messages || []
          }));
          this.activeConversationId = '';
          this.cdr.detectChanges();
        } else {
          this.createNewConversation();
        }
      },
      error: () => {
        this.createNewConversation();
      }
    });
  }

  ngOnDestroy() {
    this.stopVoice();
    window.speechSynthesis?.cancel();
  }

  private playBip(type: 'start' | 'stop') {
    try {
      const ctx = new AudioContext();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = type === 'start' ? 880 : 440;
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.15);
      osc.onended = () => ctx.close();
    } catch (e) {
      console.warn('Bip non disponible:', e);
    }
  }

  private async startWaveform() {
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioContext = new AudioContext();
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 64;
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      source.connect(this.analyser);
      this.drawWaveform();
    } catch (e) {
      console.warn('Waveform non disponible:', e);
    }
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
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
      this.animationFrame = null;
    }
    this.mediaStream?.getTracks().forEach(t => t.stop());
    this.audioContext?.close();
    this.audioContext = null;
    this.analyser = null;
    this.mediaStream = null;
    this.waveformBars = Array(20).fill(2);
  }

  private resetSilenceTimer() {
    if (this.silenceTimer) clearTimeout(this.silenceTimer);
    this.silenceTimer = setTimeout(() => {
      const text = this.userMessage?.trim();
      if (text && this.isListening) {
        this.stopVoice();
        this.sendMessage();
      }
    }, this.SILENCE_DELAY);
  }

  private clearSilenceTimer() {
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
  }

  createNewConversation() {
    this.chatService.createConversation().subscribe({
      next: (res: any) => {
        if (!res?.conversation_id) return;
        const newConv: Conversation = {
          id: res.conversation_id,
          title: 'Nouvelle conversation',
          messages: []
        };
        this.conversations.unshift(newConv);
        this.activeConversationId = newConv.id;
      },
      error: (err: any) => console.error('Erreur createConversation:', err)
    });
  }

  selectConversation(id: string) {
    this.activeConversationId = id;
  }

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
            id: res.conversation_id,
            title: input.slice(0, 28),
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

    const message: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString()
    };

    this.currentConversation!.messages.push(message);
    this.userMessage = '';
    this.finalTranscript = '';
    this.interimTranscript = '';
    this.isTyping = true;
    this.cdr.detectChanges();
    this.scrollToBottom();

    this.chatService.sendMessage(input, this.activeConversationId).subscribe({
      next: (res: any) => {
        this.currentConversation?.messages.push({
          role: 'bot',
          content: res?.answer || res?.response || 'Pas de réponse',
          timestamp: new Date().toLocaleTimeString()
        });
        this.isTyping = false;
        this.cdr.detectChanges();
        this.scrollToBottom();
      },
      error: (err: any) => {
        this.currentConversation?.messages.push({
          role: 'bot',
          content: `Erreur serveur (${err?.status || '??'})`,
          timestamp: new Date().toLocaleTimeString()
        });
        this.isTyping = false;
        this.cdr.detectChanges();
        this.scrollToBottom();
      }
    });
  }

  toggleVoice() {
    this.isListening ? this.stopVoice() : this.startVoice();
  }

  async startVoice() {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Utilise Google Chrome pour le micro');
      return;
    }

    this.finalTranscript = '';
    this.interimTranscript = '';
    this.shouldRestart = true;
    this.isRestarting = false;

    this.playBip('start');
    await this.startWaveform();

    this.recognition = new SpeechRecognition();
    this.recognition.lang = this.selectedLanguage;
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.maxAlternatives = 1;

    this.recognition.onstart = () => {
      this.isListening = true;
      this.isRestarting = false;
      this.interimTranscript = '';
    };

    this.recognition.onresult = (event: any) => {
      this.interimTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const text = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          this.finalTranscript += text + ' ';
        } else {
          this.interimTranscript += text;
        }
      }
      this.userMessage = (this.finalTranscript + this.interimTranscript).trim();
      this.resetSilenceTimer();
    };

    this.recognition.onerror = (event: any) => {
      if (event.error === 'not-allowed') {
        alert('Permission micro refusée');
        this.shouldRestart = false;
        this.isListening = false;
        this.stopWaveform();
        return;
      }
      if (event.error !== 'no-speech') {
        console.error('Voice error:', event.error);
        this.shouldRestart = false;
        this.isListening = false;
        this.stopWaveform();
      }
    };

    this.recognition.onend = () => {
      if (this.shouldRestart && this.isListening && !this.isRestarting) {
        this.isRestarting = true;
        setTimeout(() => {
          if (this.shouldRestart && this.isListening) {
            try { this.recognition.start(); }
            catch (e) {
              console.warn('Restart failed:', e);
              this.isListening = false;
              this.stopWaveform();
            }
          }
          this.isRestarting = false;
        }, 300);
      } else {
        this.isListening = false;
        this.stopWaveform();
      }
    };

    this.recognition.start();
  }

  stopVoice() {
    this.shouldRestart = false;
    this.isListening = false;
    this.isRestarting = false;
    this.clearSilenceTimer();
    this.stopWaveform();
    if (this.recognition) {
      try { this.recognition.stop(); } catch {}
      this.recognition = null;
    }
    this.playBip('stop');
  }

  speak(text: string) {
    window.speechSynthesis?.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = this.selectedLanguage;
    const voices = window.speechSynthesis.getVoices();
    const langCode = this.selectedLanguage.split('-')[0];
    const voice = voices.find(v => v.lang.startsWith(langCode));
    if (voice) utterance.voice = voice;
    window.speechSynthesis.speak(utterance);
  }

  scrollToBottom() {
    setTimeout(() => {
      if (this.scrollContainer) {
        this.scrollContainer.nativeElement.scrollTop =
          this.scrollContainer.nativeElement.scrollHeight;
      }
    }, 100);
  }
}