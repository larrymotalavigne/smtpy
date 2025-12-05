import { Component, OnInit } from '@angular/core';

import { ReactiveFormsModule, FormBuilder, FormGroup } from '@angular/forms';
import { MessageResponse, MessageStatus, MessageFilter } from '@/core/interfaces/message.interface';
import { MessagesApiService } from '@/core/services/messages-api.service';

// PrimeNG Modules
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { Select } from 'primeng/select';
import { DatePicker } from 'primeng/datepicker';
import { TagModule } from 'primeng/tag';
import { DialogModule } from 'primeng/dialog';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService } from 'primeng/api';
import { BadgeModule } from 'primeng/badge';
import { AvatarModule } from 'primeng/avatar';

interface MessageWithDetails extends MessageResponse {
  senderInitials?: string;
  timeAgo?: string;
}

@Component({
  selector: 'app-messages',
  templateUrl: './messages.component.html',
  styleUrls: ['./messages.component.scss'],
  standalone: true,
  imports: [
    ReactiveFormsModule,
    CardModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    Select,
    DatePicker,
    TagModule,
    DialogModule,
    ToastModule,
    TooltipModule,
    BadgeModule,
    AvatarModule
],
  providers: [MessageService]
})
export class MessagesComponent implements OnInit {
  messages: MessageWithDetails[] = [];
  loading = false;

  // Filter form
  filterForm: FormGroup;

  // Dialog states
  displayDetailDialog = false;
  selectedMessage: MessageWithDetails | null = null;

  // Filter options
  statusOptions = [
    { label: 'Tous les statuts', value: null },
    { label: 'Délivré', value: MessageStatus.DELIVERED },
    { label: 'En attente', value: MessageStatus.PENDING },
    { label: 'Échec', value: MessageStatus.FAILED },
    { label: 'Rejeté', value: MessageStatus.BOUNCED }
  ];

  domainOptions = [
    { label: 'Tous les domaines', value: null }
  ];

  // Loading states
  loadingDetail = false;
  deleting = false;

  // Pagination
  totalRecords = 0;
  currentPage = 1;
  pageSize = 10;

  constructor(
    private fb: FormBuilder,
    private messageService: MessageService,
    private messagesApiService: MessagesApiService
  ) {
    this.filterForm = this.fb.group({
      status: [null],
      domain: [null],
      search: [''],
      dateRange: [[]]
    });
  }

  ngOnInit(): void {
    this.loadMessages();
  }

  private loadMessages(): void {
    this.loading = true;

    // Build filter from form
    const filter: MessageFilter = {};
    const formValues = this.filterForm.value;

    if (formValues.status) {
      filter.status = formValues.status;
    }
    if (formValues.domain) {
      filter.domain_id = formValues.domain;
    }
    if (formValues.dateRange && formValues.dateRange.length === 2) {
      filter.date_from = formValues.dateRange[0].toISOString();
      filter.date_to = formValues.dateRange[1].toISOString();
    }

    // Pagination params
    const paginationParams = {
      page: this.currentPage,
      size: this.pageSize,
      sort: 'created_at',
      order: 'desc' as const
    };

    // Use search if query exists
    const searchQuery = formValues.search?.trim();
    const apiCall = searchQuery
      ? this.messagesApiService.searchMessages(searchQuery, paginationParams, filter)
      : this.messagesApiService.getMessages(paginationParams, filter);

    apiCall.subscribe({
      next: (response) => {
        if (response.success && response.data) {
          this.messages = response.data.items.map(msg => this.enhanceMessageList(msg));
          this.totalRecords = response.data.total;
        }
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading messages:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Impossible de charger les messages. Veuillez réessayer.'
        });
        this.loading = false;
      }
    });
  }

  private enhanceMessage(msg: MessageResponse): MessageWithDetails {
    return {
      ...msg,
      senderInitials: this.getInitials(msg.sender_email),
      timeAgo: this.formatTimeAgo(msg.created_at)
    };
  }

  private enhanceMessageList(msg: any): MessageWithDetails {
    return {
      ...msg,
      senderInitials: this.getInitials(msg.sender_email),
      timeAgo: this.formatTimeAgo(msg.created_at)
    };
  }

  private getInitials(email: string): string {
    const name = email.split('@')[0];
    const parts = name.split(/[._-]/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  }

  private formatTimeAgo(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'À l\'instant';
    if (diffMins < 60) return `Il y a ${diffMins}min`;
    if (diffHours < 24) return `Il y a ${diffHours}h`;
    if (diffDays === 1) return 'Hier';
    if (diffDays < 7) return `Il y a ${diffDays}j`;
    return date.toLocaleDateString('fr-FR');
  }

  getStatusSeverity(status: MessageStatus): 'success' | 'info' | 'warn' | 'danger' | 'secondary' {
    switch (status) {
      case MessageStatus.DELIVERED:
        return 'success';
      case MessageStatus.PENDING:
        return 'info';
      case MessageStatus.BOUNCED:
        return 'warn';
      case MessageStatus.FAILED:
        return 'danger';
      default:
        return 'secondary';
    }
  }

  getStatusLabel(status: MessageStatus): string {
    switch (status) {
      case MessageStatus.DELIVERED:
        return 'Délivré';
      case MessageStatus.PENDING:
        return 'En attente';
      case MessageStatus.BOUNCED:
        return 'Rejeté';
      case MessageStatus.FAILED:
        return 'Échec';
      default:
        return status;
    }
  }

  formatSize(sizeBytes?: number): string {
    if (!sizeBytes) return '0 B';

    const units = ['B', 'KB', 'MB', 'GB'];
    let size = sizeBytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  viewMessageDetails(message: MessageWithDetails): void {
    this.loadingDetail = true;
    this.displayDetailDialog = true;

    // Load full message details
    this.messagesApiService.getMessage(message.id).subscribe({
      next: (response) => {
        if (response.success && response.data) {
          this.selectedMessage = this.enhanceMessage(response.data);
        }
        this.loadingDetail = false;
      },
      error: (error) => {
        console.error('Error loading message details:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Impossible de charger les détails du message.'
        });
        this.loadingDetail = false;
        this.displayDetailDialog = false;
      }
    });
  }

  retryMessage(message: MessageWithDetails): void {
    this.messageService.add({
      severity: 'info',
      summary: 'Nouvelle tentative',
      detail: `Nouvelle tentative d'envoi pour le message "${message.subject}"...`
    });
  }

  deleteMessage(message: MessageWithDetails): void {
    this.deleting = true;

    this.messagesApiService.deleteMessage(message.id).subscribe({
      next: (response) => {
        if (response.success) {
          this.messageService.add({
            severity: 'success',
            summary: 'Message supprimé',
            detail: `Le message "${message.subject}" a été supprimé.`
          });
          this.loadMessages();
        }
        this.deleting = false;
      },
      error: (error) => {
        console.error('Error deleting message:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Erreur',
          detail: error.error?.message || 'Impossible de supprimer le message.'
        });
        this.deleting = false;
      }
    });
  }

  applyFilters(): void {
    this.currentPage = 1; // Reset to first page when applying filters
    this.loadMessages();
  }

  clearFilters(): void {
    this.filterForm.reset({
      status: null,
      domain: null,
      search: '',
      dateRange: []
    });
    this.currentPage = 1;
    this.loadMessages();
  }

  onPageChange(event: any): void {
    this.currentPage = event.page + 1; // PrimeNG uses 0-based page index
    this.pageSize = event.rows;
    this.loadMessages();
  }

  truncateText(text: string | undefined, maxLength: number): string {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  }

  getAvatarColor(status: MessageStatus): string {
    switch (status) {
      case MessageStatus.DELIVERED:
        return '#10b981';
      case MessageStatus.PENDING:
        return '#3b82f6';
      case MessageStatus.BOUNCED:
        return '#f59e0b';
      case MessageStatus.FAILED:
        return '#ef4444';
      default:
        return '#667eea';
    }
  }
}
