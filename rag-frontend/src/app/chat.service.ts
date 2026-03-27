import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatService {

  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  // ✅ Créer une nouvelle conversation
  createConversation(): Observable<any> {
    return this.http.post(`${this.apiUrl}/conversation/new`, {});
  }

  // ✅ Envoyer un message
  sendMessage(question: string, conversation_id: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/chat`, {
      question: question,
      conversation_id: conversation_id
    });
  }

  // ✅ Récupérer toutes les conversations
  getConversations(): Observable<any> {
    return this.http.get(`${this.apiUrl}/conversation/full`);
  }
}