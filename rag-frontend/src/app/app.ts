import { Component, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

interface Message {
  role: 'user' | 'bot';
  content: string;
  timestamp: string;
}

interface Conversation {
  id: number;
  title: string;
  messages: Message[];
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class AppComponent {

  constructor(private http: HttpClient) {}

  @ViewChild('scrollContainer') scrollContainer!: ElementRef;

  conversations: Conversation[] = [];
  activeConversationId!: number;
  userMessage = '';
  isTyping = false;

  apiUrl = 'http://localhost:8000/chat';

  get currentConversation(): Conversation | undefined {
    return this.conversations.find(c => c.id === this.activeConversationId);
  }

  ngOnInit() {
    this.createNewConversation();
  }

  createNewConversation() {
    const newConv: Conversation = {
      id: Date.now(),
      title: 'Nouvelle conversation',
      messages: []
    };

    this.conversations.unshift(newConv);
    this.activeConversationId = newConv.id;
  }

  selectConversation(id: number) {
    this.activeConversationId = id;
  }

  sendMessage() {

    if (!this.userMessage.trim() || this.isTyping) return;

    const message: Message = {
      role: 'user',
      content: this.userMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    this.currentConversation?.messages.push(message);

    if (this.currentConversation?.messages.length === 1) {
      this.currentConversation.title = this.userMessage.slice(0, 25);
    }

    const userInput = this.userMessage;
    this.userMessage = '';
    this.isTyping = true;
    this.scrollToBottom();

  
    this.http.post<any>(this.apiUrl, {
      question: userInput
    }).subscribe({
      next: (response) => {

        const botMessage: Message = {
          role: 'bot',
          content: response.answer,
          timestamp: new Date().toLocaleTimeString()
        };

        this.currentConversation?.messages.push(botMessage);
        this.isTyping = false;
        this.scrollToBottom();
      },
      error: (err) => {

        const errorMessage: Message = {
          role: 'bot',
          content: 'Erreur de connexion au serveur.',
          timestamp: new Date().toLocaleTimeString()
        };

        this.currentConversation?.messages.push(errorMessage);
        this.isTyping = false;
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
}
