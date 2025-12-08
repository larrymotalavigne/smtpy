import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
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
import { CommonModule } from '@angular/common';

interface MessageWithDetails extends MessageResponse {
  senderInitials?: string;
  timeAgo?: string;
  direction?: 'sent' | 'received';
}

@Component({
  selector: 'app-mail-history',
  templateUrl: './mail-history.component.html',
  styleUrls: ['./mail-history.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
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
export class MailHistoryComponent implements OnInit {
  email: string = '';
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

  directionOptions = [
    { label: 'Tous', value: null },
    { label: 'Envoyés', value: 'sent' },
    { label: 'Reçus', value: 'received' }
  ];

  // Loading states
  loadingDetail = false;
  deleting = false;

  // Pagination
  totalRecords = 0;
  currentPage = 1;
  pageSize = 10;

  // Stats
  sentCount = 0;
  receivedCount = 0;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private fb: FormBuilder,
    private messageService: MessageService,
    private messagesApiService: MessagesApiService
  ) {
    this.filterForm = this.fb.group({
      status: [null],
      direction: [null],
      dateRange: [[]]
    });
  }

  ngOnInit(): void {
    // Get email from route parameter
    this.route.params.subscribe(params => {
      this.email = params['email'];
      if (this.email) {
        this.loadMessages();
      } else {
        // Redirect back to aliases if no email is provided
        this.router.navigate(['/aliases']);
      }
    });
  }

  private loadMessages(): void {
    this.loading = true;

    // Build filter from form
    const filter: MessageFilter = {};
    const formValues = this.filterForm.value;

    if (formValues.status) {
      filter.status = formValues.status;
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

    this.messagesApiService.getMessagesByEmail(this.email, paginationParams, filter).subscribe({
      next: (response) => {
        if (response.success && response.data) {
          this.messages = response.data.items.map(msg => this.enhanceMessageList(msg));
          this.totalRecords = response.data.total;
          this.calculateStats();
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
    const direction = msg.sender_email.toLowerCase() === this.email.toLowerCase() ? 'sent' : 'received';
    return {
      ...msg,
      senderInitials: this.getInitials(msg.sender_email),
      timeAgo: this.formatTimeAgo(msg.created_at),
      direction: direction
    };
  }

  private enhanceMessageList(msg: any): MessageWithDetails {
    const direction = msg.sender_email.toLowerCase() === this.email.toLowerCase() ? 'sent' : 'received';
    return {
      ...msg,
      senderInitials: this.getInitials(msg.sender_email),
      timeAgo: this.formatTimeAgo(msg.created_at),
      direction: direction
    };
  }

  private calculateStats(): void {
    this.sentCount = this.messages.filter(m => m.direction === 'sent').length;
    this.receivedCount = this.messages.filter(m => m.direction === 'received').length;
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

  getFilteredMessages(): MessageWithDetails[] {
    const directionFilter = this.filterForm.value.direction;
    if (!directionFilter) {
      return this.messages;
    }
    return this.messages.filter(m => m.direction === directionFilter);
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
      direction: null,
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

  getAvatarColor(message: MessageWithDetails): string {
    // Color based on direction
    if (message.direction === 'sent') {
      return '#667eea'; // Purple for sent
    }
    return '#10b981'; // Green for received
  }

  getDirectionIcon(message: MessageWithDetails): string {
    return message.direction === 'sent' ? 'pi-send' : 'pi-inbox';
  }

  getDirectionLabel(message: MessageWithDetails): string {
    return message.direction === 'sent' ? 'Envoyé' : 'Reçu';
  }

  goBack(): void {
    this.router.navigate(['/aliases']);
  }
}
