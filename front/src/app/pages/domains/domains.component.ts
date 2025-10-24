import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';

// PrimeNG Modules
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { ToastModule } from 'primeng/toast';
import { TagModule } from 'primeng/tag';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService, ConfirmationService } from 'primeng/api';
import { Tabs, TabPanel } from 'primeng/tabs';
import { AvatarModule } from 'primeng/avatar';
import { ProgressBarModule } from 'primeng/progressbar';

import { DomainResponse, DomainStatus, DNSRecords } from '../../core/interfaces/domain.interface';
import { DomainsApiService } from '../service/domains-api.service';

interface DomainWithStats extends DomainResponse {
  aliasCount?: number;
  messagesCount?: number;
  lastActivity?: string;
}

@Component({
  selector: 'app-domains',
  templateUrl: './domains.component.html',
  styleUrls: ['./domains.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    CardModule,
    TableModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    ToastModule,
    TagModule,
    ConfirmDialogModule,
    TooltipModule,
    Tabs,
    TabPanel,
    AvatarModule,
    ProgressBarModule
  ],
  providers: [MessageService, ConfirmationService]
})
export class DomainsComponent implements OnInit {
  domains: DomainWithStats[] = [];
  loading = false;

  // Dialog states
  displayAddDialog = false;
  displayDNSDialog = false;
  displayDetailDialog = false;

  // Forms
  addDomainForm: FormGroup;

  // Selected domain
  selectedDomain: DomainWithStats | null = null;

  // DNS records for display
  dnsRecords: DNSRecords | null = null;

  // Loading states
  verifying = false;
  savingDomain = false;

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private domainsApiService: DomainsApiService
  ) {
    this.addDomainForm = this.fb.group({
      name: ['', [Validators.required, Validators.pattern(/^[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,}$/)]]
    });
  }

  ngOnInit(): void {
    this.loadDomains();
  }

  private loadDomains(): void {
    this.loading = true;

    this.domainsApiService.getDomains().subscribe({
      next: (response) => {
        if (response.success && response.data) {
          // Map pagination response to domains array
          this.domains = response.data.items as DomainWithStats[];

          // Load stats for each domain
          this.domains.forEach(domain => {
            this.loadDomainStats(domain);
          });
        }
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading domains:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Impossible de charger les domaines. Veuillez réessayer.'
        });
        this.loading = false;
      }
    });
  }

  private loadDomainStats(domain: DomainWithStats): void {
    this.domainsApiService.getDomainStats(domain.id).subscribe({
      next: (response) => {
        if (response.success && response.data) {
          domain.aliasCount = response.data.active_aliases;
          domain.messagesCount = response.data.messages_received;
          domain.lastActivity = response.data.last_message_at
            ? this.formatTimeAgo(response.data.last_message_at)
            : 'Jamais';
        }
      },
      error: (error) => {
        console.error(`Error loading stats for domain ${domain.id}:`, error);
      }
    });
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

  getStatusSeverity(status: DomainStatus): 'success' | 'warning' | 'danger' | 'secondary' {
    switch (status) {
      case DomainStatus.VERIFIED:
        return 'success';
      case DomainStatus.PENDING:
        return 'warning';
      case DomainStatus.FAILED:
        return 'danger';
      default:
        return 'secondary';
    }
  }

  getStatusLabel(status: DomainStatus): string {
    switch (status) {
      case DomainStatus.VERIFIED:
        return 'Vérifié';
      case DomainStatus.PENDING:
        return 'En attente';
      case DomainStatus.FAILED:
        return 'Échec';
      default:
        return status;
    }
  }

  getDNSVerificationProgress(domain: DomainWithStats): number {
    const checks = [
      domain.mx_record_verified,
      domain.spf_record_verified,
      domain.dkim_record_verified,
      domain.dmarc_record_verified
    ];
    const verified = checks.filter(check => check).length;
    return (verified / checks.length) * 100;
  }

  openAddDialog(): void {
    this.addDomainForm.reset();
    this.displayAddDialog = true;
  }

  submitAddDomain(): void {
    if (this.addDomainForm.invalid) {
      return;
    }

    this.savingDomain = true;
    const domainData = { name: this.addDomainForm.value.name };

    this.domainsApiService.createDomain(domainData).subscribe({
      next: (response) => {
        if (response.success) {
          this.messageService.add({
            severity: 'success',
            summary: 'Domaine ajouté',
            detail: `Le domaine ${domainData.name} a été ajouté avec succès. Configurez maintenant vos DNS.`
          });

          this.displayAddDialog = false;
          this.addDomainForm.reset();
          this.loadDomains();
        }
        this.savingDomain = false;
      },
      error: (error) => {
        console.error('Error creating domain:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Erreur',
          detail: error.error?.message || 'Impossible d\'ajouter le domaine. Veuillez réessayer.'
        });
        this.savingDomain = false;
      }
    });
  }

  viewDNSRecords(domain: DomainWithStats): void {
    this.selectedDomain = domain;
    this.displayDNSDialog = true;

    // Load DNS records for the domain
    this.domainsApiService.getDNSRecords(domain.id).subscribe({
      next: (response) => {
        if (response.success && response.data) {
          this.dnsRecords = response.data;
        }
      },
      error: (error) => {
        console.error('Error loading DNS records:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Impossible de charger les enregistrements DNS.'
        });
      }
    });
  }

  viewDomainDetails(domain: DomainWithStats): void {
    this.selectedDomain = domain;
    this.displayDetailDialog = true;
  }

  verifyDNS(domain: DomainWithStats): void {
    this.verifying = true;
    this.messageService.add({
      severity: 'info',
      summary: 'Vérification en cours',
      detail: `Vérification DNS pour ${domain.name}...`
    });

    this.domainsApiService.verifyDomain(domain.id).subscribe({
      next: (response) => {
        if (response.success && response.data) {
          const verifiedCount = [
            response.data.dns_status.mx_record_verified,
            response.data.dns_status.spf_record_verified,
            response.data.dns_status.dkim_record_verified,
            response.data.dns_status.dmarc_record_verified
          ].filter(Boolean).length;

          this.messageService.add({
            severity: response.data.dns_status.is_fully_verified ? 'success' : 'warn',
            summary: response.data.dns_status.is_fully_verified ? 'DNS vérifié' : 'Vérification partielle',
            detail: `${verifiedCount}/4 enregistrements DNS vérifiés.`
          });

          this.loadDomains();
        }
        this.verifying = false;
      },
      error: (error) => {
        console.error('Error verifying domain:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Erreur de vérification',
          detail: 'Impossible de vérifier les enregistrements DNS. Veuillez réessayer.'
        });
        this.verifying = false;
      }
    });
  }

  toggleDomainStatus(domain: DomainWithStats): void {
    const action = domain.is_active ? 'désactiver' : 'activer';
    const newStatus = !domain.is_active;

    this.confirmationService.confirm({
      message: `Voulez-vous vraiment ${action} le domaine ${domain.name} ?`,
      header: 'Confirmation',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.domainsApiService.updateDomain(domain.id, { is_active: newStatus }).subscribe({
          next: (response) => {
            if (response.success) {
              domain.is_active = newStatus;
              this.messageService.add({
                severity: 'success',
                summary: 'Statut modifié',
                detail: `Le domaine a été ${newStatus ? 'activé' : 'désactivé'}.`
              });
            }
          },
          error: (error) => {
            console.error('Error updating domain:', error);
            this.messageService.add({
              severity: 'error',
              summary: 'Erreur',
              detail: 'Impossible de modifier le statut du domaine.'
            });
          }
        });
      }
    });
  }

  deleteDomain(domain: DomainWithStats): void {
    this.confirmationService.confirm({
      message: `Êtes-vous sûr de vouloir supprimer le domaine ${domain.name} ? Cette action est irréversible.`,
      header: 'Confirmer la suppression',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.domainsApiService.deleteDomain(domain.id).subscribe({
          next: (response) => {
            if (response.success) {
              this.messageService.add({
                severity: 'success',
                summary: 'Domaine supprimé',
                detail: `Le domaine ${domain.name} a été supprimé.`
              });
              this.loadDomains();
            }
          },
          error: (error) => {
            console.error('Error deleting domain:', error);
            this.messageService.add({
              severity: 'error',
              summary: 'Erreur',
              detail: error.error?.message || 'Impossible de supprimer le domaine.'
            });
          }
        });
      }
    });
  }

  copyToClipboard(text: string, label: string): void {
    navigator.clipboard.writeText(text).then(() => {
      this.messageService.add({
        severity: 'success',
        summary: 'Copié',
        detail: `${label} copié dans le presse-papiers`
      });
    });
  }

  manageAliases(domain: DomainWithStats): void {
    this.router.navigate(['/aliases'], { queryParams: { domain: domain.name } });
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }
}