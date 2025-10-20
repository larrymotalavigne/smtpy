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
import { TabViewModule } from 'primeng/tabview';
import { AvatarModule } from 'primeng/avatar';
import { ProgressBarModule } from 'primeng/progressbar';

import { DomainResponse, DomainStatus } from '../../core/interfaces/domain.interface';

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
    TabViewModule,
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
  dnsRecords = {
    mx: 'MX 10 mx1.smtpy.com\nMX 20 mx2.smtpy.com',
    spf: 'v=spf1 include:smtpy.com ~all',
    dkim: 'v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3...',
    dmarc: 'v=DMARC1; p=quarantine; rua=mailto:dmarc@smtpy.com'
  };

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private messageService: MessageService,
    private confirmationService: ConfirmationService
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

    // Mock data for UI demonstration
    setTimeout(() => {
      this.domains = [
        {
          id: 1,
          name: 'monentreprise.com',
          organization_id: 1,
          status: DomainStatus.VERIFIED,
          is_active: true,
          mx_record_verified: true,
          spf_record_verified: true,
          dkim_record_verified: true,
          dmarc_record_verified: true,
          is_fully_verified: true,
          created_at: '2025-09-15T10:00:00Z',
          updated_at: '2025-10-15T14:30:00Z',
          aliasCount: 12,
          messagesCount: 456,
          lastActivity: 'Il y a 2h'
        },
        {
          id: 2,
          name: 'nouveausite.fr',
          organization_id: 1,
          status: DomainStatus.PENDING,
          is_active: true,
          mx_record_verified: false,
          spf_record_verified: false,
          dkim_record_verified: false,
          dmarc_record_verified: false,
          is_fully_verified: false,
          dkim_public_key: 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC...',
          verification_token: 'smtpy-verify-abc123def456',
          created_at: '2025-10-18T08:00:00Z',
          updated_at: '2025-10-18T08:00:00Z',
          aliasCount: 0,
          messagesCount: 0,
          lastActivity: 'Jamais'
        },
        {
          id: 3,
          name: 'startup.io',
          organization_id: 1,
          status: DomainStatus.VERIFIED,
          is_active: true,
          mx_record_verified: true,
          spf_record_verified: true,
          dkim_record_verified: false,
          dmarc_record_verified: true,
          is_fully_verified: false,
          created_at: '2025-08-10T12:00:00Z',
          updated_at: '2025-10-19T09:15:00Z',
          aliasCount: 35,
          messagesCount: 2341,
          lastActivity: 'Il y a 5min'
        }
      ];
      this.loading = false;
    }, 500);
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
    if (this.addDomainForm.valid) {
      const domainName = this.addDomainForm.value.name;

      // Mock API call
      this.messageService.add({
        severity: 'success',
        summary: 'Domaine ajouté',
        detail: `Le domaine ${domainName} a été ajouté avec succès. Configurez maintenant vos DNS.`
      });

      this.displayAddDialog = false;
      this.loadDomains();
    }
  }

  viewDNSRecords(domain: DomainWithStats): void {
    this.selectedDomain = domain;
    this.displayDNSDialog = true;
  }

  viewDomainDetails(domain: DomainWithStats): void {
    this.selectedDomain = domain;
    this.displayDetailDialog = true;
  }

  verifyDNS(domain: DomainWithStats): void {
    this.messageService.add({
      severity: 'info',
      summary: 'Vérification en cours',
      detail: `Vérification DNS pour ${domain.name}...`
    });

    // Mock verification
    setTimeout(() => {
      this.messageService.add({
        severity: 'success',
        summary: 'DNS vérifié',
        detail: 'Les enregistrements DNS ont été vérifiés avec succès.'
      });
      this.loadDomains();
    }, 1500);
  }

  toggleDomainStatus(domain: DomainWithStats): void {
    const action = domain.is_active ? 'désactiver' : 'activer';

    this.confirmationService.confirm({
      message: `Voulez-vous vraiment ${action} le domaine ${domain.name} ?`,
      header: 'Confirmation',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        domain.is_active = !domain.is_active;
        this.messageService.add({
          severity: 'success',
          summary: 'Statut modifié',
          detail: `Le domaine a été ${domain.is_active ? 'activé' : 'désactivé'}.`
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
        this.messageService.add({
          severity: 'success',
          summary: 'Domaine supprimé',
          detail: `Le domaine ${domain.name} a été supprimé.`
        });
        this.loadDomains();
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