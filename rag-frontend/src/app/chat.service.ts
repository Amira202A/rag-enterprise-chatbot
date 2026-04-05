import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ChatService {

  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('token') || '';
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  createConversation(): Observable<any> {
    return this.http.post(`${this.apiUrl}/conversation/new`, {}, {
      headers: this.getHeaders()
    });
  }

  sendMessage(question: string, conversation_id: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/chat`, {
      question, conversation_id
    }, { headers: this.getHeaders() });
  }

  getConversations(): Observable<any> {
    return this.http.get(`${this.apiUrl}/conversation/full`, {
      headers: this.getHeaders()
    });
  }
}