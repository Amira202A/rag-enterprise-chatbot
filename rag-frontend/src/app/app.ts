import { Component, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { LucideAngularModule, Mic } from 'lucide-angular';
import { ChatService } from './chat.service';

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
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule, LucideAngularModule],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class AppComponent {

  @ViewChild('scrollContainer') scrollContainer!: ElementRef;

  conversations: Conversation[] = [];
  activeConversationId!: string;

  userMessage = '';
  isTyping = false;

  selectedLanguage = 'en-US';

  isListening = false;
  recognition: any;
  readonly Mic = Mic;

  voiceType: 'text' | 'voice' = 'text';

  constructor(private chatService: ChatService) {}

  get currentConversation(): Conversation | undefined {
    return this.conversations.find(c => c.id === this.activeConversationId);
  }

  ngOnInit() {
    this.createNewConversation();

    window.speechSynthesis.onvoiceschanged = () => {
      window.speechSynthesis.getVoices();
    };
  }

  createNewConversation() {
    this.chatService.createConversation().subscribe((res: any) => {

      const id = res.conversation_id;

      const newConv: Conversation = {
        id: id,
        title: 'Nouvelle conversation',
        messages: []
      };

      this.conversations.unshift(newConv);
      this.activeConversationId = id;
    });
  }

  selectConversation(id: string) {
    this.activeConversationId = id;
  }

  sendMessage() {
    console.log("CLICK");
    console.log("userMessage =", this.userMessage);
    console.log("isTyping =", this.isTyping);

    if (!this.userMessage.trim() || this.isTyping) return;
    if (!this.currentConversation) return;

    window.speechSynthesis.cancel();

    const input = this.userMessage.trim();

    const message: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString()
    };

    this.currentConversation.messages.push(message);

    if (this.currentConversation.messages.length === 1) {
      this.currentConversation.title = input.slice(0, 25);
    }

    this.userMessage = '';
    this.isTyping = true;

    this.scrollToBottom();

    this.chatService.sendMessage(input, this.activeConversationId)
      .subscribe({
        next: (res: any) => {

          const botMessage: Message = {
            role: 'bot',
            content: res.answer || res.response || "Pas de réponse",
            timestamp: new Date().toLocaleTimeString()
          };

          this.currentConversation?.messages.push(botMessage);

          if (this.voiceType === 'voice') {
            this.speak(botMessage.content);
          }

          this.isTyping = false;
          this.scrollToBottom();
        },

        error: () => {
          this.currentConversation?.messages.push({
            role: 'bot',
            content: 'Erreur serveur.',
            timestamp: new Date().toLocaleTimeString()
          });

          this.isTyping = false;
          this.scrollToBottom();
        }
      });
  }

  speak(text: string) {

    if (this.recognition) {
      this.recognition.stop();
    }

    const utterance = new SpeechSynthesisUtterance(text);

    utterance.lang = this.selectedLanguage;
    utterance.rate = 0.95;

    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find(v => v.lang === this.selectedLanguage);

    if (voice) {
      utterance.voice = voice;
    }

    window.speechSynthesis.cancel();
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

  startVoiceRecognition(type: 'text' | 'voice') {

    this.voiceType = type;

    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Speech recognition not supported');
      return;
    }

    this.recognition = new SpeechRecognition();

    this.recognition.lang = this.selectedLanguage;
    this.recognition.continuous = false;
    this.recognition.interimResults = false;

    this.isListening = true;

    this.recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;

      this.userMessage = transcript;

      if (transcript.trim()) {
        this.sendMessage();
      }
    };

    this.recognition.onerror = () => {
      this.isListening = false;
    };

    this.recognition.onend = () => {
      this.isListening = false;
    };

    this.recognition.start();
  }
}