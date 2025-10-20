import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup } from '@angular/forms';
import { MessageResponse, MessageStatus } from '../../core/interfaces/message.interface';

// PrimeNG Modules
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { CalendarModule } from 'primeng/calendar';
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
    CommonModule,
    ReactiveFormsModule,
    CardModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    DropdownModule,
    CalendarModule,
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
    { label: 'Tous les domaines', value: null },
    { label: 'monentreprise.com', value: 1 },
    { label: 'nouveausite.fr', value: 2 },
    { label: 'startup.io', value: 3 }
  ];

  constructor(
    private fb: FormBuilder,
    private messageService: MessageService
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

    // Mock data for UI demonstration
    setTimeout(() => {
      this.messages = [
        {
          id: 1,
          message_id: 'msg_abc123',
          domain_id: 1,
          sender_email: 'john.doe@external.com',
          recipient_email: 'contact@monentreprise.com',
          forwarded_to: 'jean@gmail.com',
          subject: 'Demande de renseignements produit',
          body_preview: 'Bonjour, je souhaiterais obtenir plus d\'informations sur vos produits...',
          status: MessageStatus.DELIVERED,
          has_attachments: true,
          size_bytes: 45678,
          created_at: '2025-10-19T10:30:00Z',
          updated_at: '2025-10-19T10:30:15Z',
          senderInitials: 'JD',
          timeAgo: 'Il y a 2h'
        },
        {
          id: 2,
          message_id: 'msg_def456',
          domain_id: 1,
          sender_email: 'support@service.com',
          recipient_email: 'support@monentreprise.com',
          forwarded_to: 'support@gmail.com, marie@gmail.com',
          subject: 'Ticket #1234 - Problème technique',
          body_preview: 'Nous avons rencontré un problème technique avec votre service...',
          status: MessageStatus.DELIVERED,
          has_attachments: false,
          size_bytes: 12345,
          created_at: '2025-10-19T09:15:00Z',
          updated_at: '2025-10-19T09:15:10Z',
          senderInitials: 'SU',
          timeAgo: 'Il y a 4h'
        },
        {
          id: 3,
          message_id: 'msg_ghi789',
          domain_id: 2,
          sender_email: 'newsletter@marketing.com',
          recipient_email: 'info@nouveausite.fr',
          forwarded_to: 'admin@gmail.com',
          subject: 'Votre newsletter mensuelle',
          body_preview: 'Découvrez les dernières actualités de notre entreprise...',
          status: MessageStatus.PENDING,
          has_attachments: false,
          size_bytes: 8901,
          created_at: '2025-10-19T08:45:00Z',
          updated_at: '2025-10-19T08:45:00Z',
          senderInitials: 'NE',
          timeAgo: 'Il y a 5h'
        },
        {
          id: 4,
          message_id: 'msg_jkl012',
          domain_id: 3,
          sender_email: 'noreply@platform.io',
          recipient_email: 'admin@startup.io',
          forwarded_to: 'ceo@gmail.com',
          subject: 'Alerte sécurité - Connexion détectée',
          body_preview: 'Une nouvelle connexion à votre compte a été détectée depuis...',
          status: MessageStatus.FAILED,
          error_message: 'Connection timeout',
          has_attachments: false,
          size_bytes: 5432,
          created_at: '2025-10-18T22:30:00Z',
          updated_at: '2025-10-18T22:30:30Z',
          senderInitials: 'NO',
          timeAgo: 'Hier'
        },
        {
          id: 5,
          message_id: 'msg_mno345',
          domain_id: 1,
          sender_email: 'sales@bigcompany.com',
          recipient_email: 'contact@monentreprise.com',
          forwarded_to: 'jean@gmail.com',
          subject: 'Proposition commerciale',
          body_preview: 'Nous aimerions vous présenter notre nouvelle offre...',
          status: MessageStatus.BOUNCED,
          error_message: 'Recipient mailbox full',
          has_attachments: true,
          size_bytes: 234567,
          created_at: '2025-10-18T16:20:00Z',
          updated_at: '2025-10-18T16:20:45Z',
          senderInitials: 'SA',
          timeAgo: 'Hier'
        }
      ];
      this.loading = false;
    }, 500);
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
    this.selectedMessage = message;
    this.displayDetailDialog = true;
  }

  retryMessage(message: MessageWithDetails): void {
    this.messageService.add({
      severity: 'info',
      summary: 'Nouvelle tentative',
      detail: `Nouvelle tentative d'envoi pour le message "${message.subject}"...`
    });

    // Mock retry
    setTimeout(() => {
      this.messageService.add({
        severity: 'success',
        summary: 'Message envoyé',
        detail: 'Le message a été renvoyé avec succès.'
      });
      this.loadMessages();
    }, 1500);
  }

  deleteMessage(message: MessageWithDetails): void {
    this.messageService.add({
      severity: 'success',
      summary: 'Message supprimé',
      detail: `Le message "${message.subject}" a été supprimé.`
    });
    this.loadMessages();
  }

  applyFilters(): void {
    this.loadMessages();
  }

  clearFilters(): void {
    this.filterForm.reset({
      status: null,
      domain: null,
      search: '',
      dateRange: []
    });
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
