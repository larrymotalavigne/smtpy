import {Component, OnInit} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators} from '@angular/forms';
import {ActivatedRoute, Router} from '@angular/router';


import {AliasCreate, AliasListItem, AliasResponse, AliasUpdate} from '../../core/interfaces/alias.interface';
import {DomainResponse} from '../../core/interfaces/domain.interface';
import {AliasesApiService} from '../service/aliases-api.service';
import {DomainsApiService} from '../service/domains-api.service';
import {Select} from 'primeng/select';
import {Button} from 'primeng/button';
import {Card} from 'primeng/card';
import {TableModule} from 'primeng/table';
import {Tag} from 'primeng/tag';
import {Dialog} from 'primeng/dialog';
import {ConfirmationService, MessageService} from 'primeng/api';
import {InputText} from 'primeng/inputtext';
import {Toast} from 'primeng/toast';
import {ConfirmDialog} from 'primeng/confirmdialog';
import {Chip} from 'primeng/chip';

interface AliasWithDomain extends AliasListItem {
    targetsArray?: string[];
}

@Component({
    selector: 'app-aliases',
    templateUrl: './aliases.component.html',
    styleUrls: ['./aliases.component.scss'],
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        Select,
        Button,
        Card,
        TableModule,
        Tag,
        Dialog,
        InputText,
        Toast,
        ConfirmDialog,
        Chip,
    ],
    providers: [MessageService, ConfirmationService]
})
export class AliasesComponent implements OnInit {
    aliases: AliasWithDomain[] = [];
    domains: DomainResponse[] = [];
    loading = false;
    domainsLoading = false;

    // Dialog states
    displayAddDialog = false;
    displayEditDialog = false;

    // Forms
    addAliasForm: FormGroup;
    editAliasForm: FormGroup;

    // Selected alias
    selectedAlias: AliasWithDomain | null = null;

    // Loading states
    savingAlias = false;

    // Filter
    selectedDomainFilter: DomainResponse | null = null;

    // Pagination
    totalRecords = 0;
    currentPage = 1;
    pageSize = 10;

    constructor(
        private fb: FormBuilder,
        private router: Router,
        private route: ActivatedRoute,
        private messageService: MessageService,
        private confirmationService: ConfirmationService,
        private aliasesApiService: AliasesApiService,
        private domainsApiService: DomainsApiService
    ) {
        this.addAliasForm = this.fb.group({
            domain_id: [null, [Validators.required]],
            local_part: ['', [Validators.required, Validators.pattern(/^[a-z0-9._-]+$/)]],
            targets: [[], [Validators.required, Validators.minLength(1)]]
        });

        this.editAliasForm = this.fb.group({
            targets: [[], [Validators.required, Validators.minLength(1)]]
        });
    }

    ngOnInit(): void {
        this.loadDomains();

        // Check for domain filter from query params
        this.route.queryParams.subscribe(params => {
            if (params['domain']) {
                // Will set filter after domains are loaded
                this.filterByDomainName(params['domain']);
            } else {
                this.loadAliases();
            }
        });
    }

    loadDomains(): void {
        this.domainsLoading = true;
        this.domainsApiService.getDomains().subscribe({
            next: (response) => {
                this.domains = (response.items || []) as DomainResponse[];
                this.domainsLoading = false;

                // Apply domain filter from query params if exists
                const domainParam = this.route.snapshot.queryParams['domain'];
                if (domainParam) {
                    this.filterByDomainName(domainParam);
                }
            },
            error: (error) => {
                console.error('Error loading domains:', error);
                this.messageService.add({
                    severity: 'error',
                    summary: 'Erreur',
                    detail: 'Impossible de charger les domaines.'
                });
                this.domainsLoading = false;
            }
        });
    }

    loadAliases(page?: number): void {
        this.loading = true;
        if (page !== undefined) {
            this.currentPage = page;
        }

        const domainId = this.selectedDomainFilter?.id;

        this.aliasesApiService.getAliases(this.currentPage, this.pageSize, domainId).subscribe({
            next: (response) => {
                this.aliases = (response.items || []) as AliasWithDomain[];
                this.totalRecords = response.total || 0;
                this.loading = false;
            },
            error: (error) => {
                console.error('Error loading aliases:', error);
                this.messageService.add({
                    severity: 'error',
                    summary: 'Erreur',
                    detail: 'Impossible de charger les alias.'
                });
                this.loading = false;
            }
        });
    }

    filterByDomainName(domainName: string): void {
        const domain = this.domains.find(d => d.name === domainName);
        if (domain) {
            this.selectedDomainFilter = domain;
            this.loadAliases();
        }
    }

    onDomainFilterChange(): void {
        this.loadAliases();
    }

    clearDomainFilter(): void {
        this.selectedDomainFilter = null;
        this.loadAliases();
    }

    onPageChange(event: any): void {
        this.currentPage = event.first / event.rows + 1;
        this.pageSize = event.rows;
        this.loadAliases();
    }

    openAddDialog(): void {
        this.addAliasForm.reset();

        // Pre-select domain if filter is active
        if (this.selectedDomainFilter) {
            this.addAliasForm.patchValue({
                domain_id: this.selectedDomainFilter.id
            });
        }

        this.displayAddDialog = true;
    }

    submitAddAlias(): void {
        if (this.addAliasForm.invalid) {
            Object.keys(this.addAliasForm.controls).forEach(key => {
                this.addAliasForm.get(key)?.markAsTouched();
            });
            return;
        }

        this.savingAlias = true;
        const formValue = this.addAliasForm.value;

        const aliasData: AliasCreate = {
            domain_id: formValue.domain_id,
            local_part: formValue.local_part,
            targets: formValue.targets
        };

        this.aliasesApiService.createAlias(aliasData).subscribe({
            next: (alias) => {
                const selectedDomain = this.domains.find(d => d.id === formValue.domain_id);
                this.messageService.add({
                    severity: 'success',
                    summary: 'Alias créé',
                    detail: `L'alias ${formValue.local_part}@${selectedDomain?.name} a été créé avec succès.`
                });

                this.displayAddDialog = false;
                this.addAliasForm.reset();
                this.savingAlias = false;
                this.loadAliases(this.currentPage);
            },
            error: (error) => {
                console.error('Error creating alias:', error);
                this.messageService.add({
                    severity: 'error',
                    summary: 'Erreur',
                    detail: error.error?.detail || 'Impossible de créer l\'alias. Veuillez réessayer.'
                });
                this.savingAlias = false;
            }
        });
    }

    openEditDialog(alias: AliasWithDomain): void {
        this.selectedAlias = alias;

        // Fetch full alias details to get target list
        this.aliasesApiService.getAlias(alias.id).subscribe({
            next: (fullAlias: AliasResponse) => {
                this.editAliasForm.patchValue({
                    targets: fullAlias.target_list || []
                });
                this.displayEditDialog = true;
            },
            error: (error) => {
                console.error('Error loading alias details:', error);
                this.messageService.add({
                    severity: 'error',
                    summary: 'Erreur',
                    detail: 'Impossible de charger les détails de l\'alias.'
                });
            }
        });
    }

    submitEditAlias(): void {
        if (this.editAliasForm.invalid || !this.selectedAlias) {
            return;
        }

        this.savingAlias = true;
        const formValue = this.editAliasForm.value;

        const aliasUpdate: AliasUpdate = {
            targets: formValue.targets
        };

        this.aliasesApiService.updateAlias(this.selectedAlias.id, aliasUpdate).subscribe({
            next: (updatedAlias) => {
                this.messageService.add({
                    severity: 'success',
                    summary: 'Alias modifié',
                    detail: `L'alias a été modifié avec succès.`
                });

                this.displayEditDialog = false;
                this.editAliasForm.reset();
                this.savingAlias = false;
                this.selectedAlias = null;
                this.loadAliases(this.currentPage);
            },
            error: (error) => {
                console.error('Error updating alias:', error);
                this.messageService.add({
                    severity: 'error',
                    summary: 'Erreur',
                    detail: error.error?.detail || 'Impossible de modifier l\'alias.'
                });
                this.savingAlias = false;
            }
        });
    }

    deleteAlias(alias: AliasWithDomain): void {
        this.confirmationService.confirm({
            message: `Êtes-vous sûr de vouloir supprimer l'alias ${alias.full_address} ? Cette action est irréversible.`,
            header: 'Confirmer la suppression',
            icon: 'pi pi-exclamation-triangle',
            acceptButtonStyleClass: 'p-button-danger',
            accept: () => {
                this.aliasesApiService.deleteAlias(alias.id, true).subscribe({
                    next: () => {
                        this.messageService.add({
                            severity: 'success',
                            summary: 'Alias supprimé',
                            detail: `L'alias ${alias.full_address} a été supprimé.`
                        });
                        this.loadAliases(this.currentPage);
                    },
                    error: (error) => {
                        console.error('Error deleting alias:', error);
                        this.messageService.add({
                            severity: 'error',
                            summary: 'Erreur',
                            detail: error.error?.detail || 'Impossible de supprimer l\'alias.'
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

    formatDate(dateString: string): string {
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    formatDateTime(dateString: string): string {
        const date = new Date(dateString);
        return date.toLocaleString('fr-FR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    getActiveDomainsForDropdown(): DomainResponse[] {
        return this.domains.filter(d => d.is_active && d.is_fully_verified);
    }

    isValidEmail(email: string): boolean {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
}
