import {Component, OnDestroy, OnInit} from '@angular/core';

import {FormBuilder, FormGroup, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {Subject, takeUntil} from 'rxjs';
import {Router} from '@angular/router';

// PrimeNG Modules
import {CardModule} from 'primeng/card';
import {ButtonModule} from 'primeng/button';
import {MessageModule} from 'primeng/message';
import {ToastModule} from 'primeng/toast';
import {ConfirmationService, MessageService} from 'primeng/api';
import {DividerModule} from 'primeng/divider';
import {ConfirmDialogModule} from 'primeng/confirmdialog';
import {InputTextModule} from 'primeng/inputtext';
import {ToggleSwitchModule} from 'primeng/toggleswitch';
import {DialogModule} from 'primeng/dialog';
import {TableModule} from 'primeng/table';

// Services
import {AuthService, User} from '../service/auth.service';
import {UsersApiService} from '../service/users-api.service';

// Layout

interface ApiKey {
    id: string;
    name: string;
    key: string;
    created_at: string;
    last_used: string | null;
}

interface Session {
    id: string;
    device: string;
    location: string;
    ip_address: string;
    last_active: string;
    is_current: boolean;
}

@Component({
    selector: 'app-settings',
    templateUrl: './settings.component.html',
    styleUrls: ['./settings.component.scss'],
    standalone: true,
    imports: [
    ReactiveFormsModule,
    FormsModule,
    CardModule,
    ButtonModule,
    MessageModule,
    ToastModule,
    DividerModule,
    ConfirmDialogModule,
    InputTextModule,
    ToggleSwitchModule,
    DialogModule,
    TableModule
],
    providers: [MessageService, ConfirmationService]
})
export class SettingsComponent implements OnInit, OnDestroy {
    currentUser: User | null = null;
    notificationsForm: FormGroup;
    loading = false;
    // API Keys
    apiKeys: ApiKey[] = [
        {
            id: '1',
            name: 'Production API',
            key: 'sk_live_*********************abc123',
            created_at: '2025-01-15T10:30:00Z',
            last_used: '2025-10-19T14:22:00Z'
        },
        {
            id: '2',
            name: 'Development API',
            key: 'sk_test_*********************def456',
            created_at: '2025-02-01T09:15:00Z',
            last_used: null
        }
    ];
    showApiKeyDialog = false;
    newApiKeyName = '';
    generatedApiKey = '';
    // Sessions
    sessions: Session[] = [
        {
            id: '1',
            device: 'Chrome on macOS',
            location: 'Paris, France',
            ip_address: '192.168.1.100',
            last_active: '2025-10-20T16:45:00Z',
            is_current: true
        },
        {
            id: '2',
            device: 'Firefox on Windows',
            location: 'Lyon, France',
            ip_address: '192.168.1.101',
            last_active: '2025-10-18T09:30:00Z',
            is_current: false
        }
    ];
    private destroy$ = new Subject<void>();

    constructor(
        private fb: FormBuilder,
        private authService: AuthService,
        private usersApi: UsersApiService,
        private messageService: MessageService,
        private confirmationService: ConfirmationService,
        private router: Router
    ) {
        // Initialize form in constructor to prevent null reference errors
        this.notificationsForm = this.fb.group({
            emailOnNewMessage: [true],
            emailOnDomainVerified: [true],
            emailOnQuotaWarning: [true],
            emailWeeklySummary: [false]
        });
    }

    ngOnInit(): void {
        // Set up form value changes subscription
        this.notificationsForm.valueChanges
            .pipe(takeUntil(this.destroy$))
            .subscribe(() => {
                this.saveNotificationPreferences();
            });

        // Subscribe to current user
        this.authService.currentUser$
            .pipe(takeUntil(this.destroy$))
            .subscribe(user => {
                this.currentUser = user;
                if (user) {
                    this.updateFormWithUserPreferences();
                }
            });
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    saveNotificationPreferences(): void {
        if (!this.notificationsForm) return;

        const preferences = {
            email_on_new_message: this.notificationsForm.value.emailOnNewMessage,
            email_on_domain_verified: this.notificationsForm.value.emailOnDomainVerified,
            email_on_quota_warning: this.notificationsForm.value.emailOnQuotaWarning,
            email_weekly_summary: this.notificationsForm.value.emailWeeklySummary
        };

        this.usersApi.updatePreferences(preferences).subscribe({
            next: (response) => {
                if (response.success) {
                    this.messageService.add({
                        severity: 'success',
                        summary: 'Préférences enregistrées',
                        detail: 'Vos préférences de notification ont été mises à jour'
                    });
                }
            },
            error: (error) => {
                this.messageService.add({
                    severity: 'error',
                    summary: 'Erreur',
                    detail: 'Impossible d\'enregistrer les préférences'
                });
            }
        });
    }

    // API Keys Management
    generateApiKey(): void {
        if (!this.newApiKeyName.trim()) {
            this.messageService.add({
                severity: 'warn',
                summary: 'Nom requis',
                detail: 'Veuillez saisir un nom pour la clé API'
            });
            return;
        }

        this.usersApi.generateApiKey(this.newApiKeyName).subscribe({
            next: (response) => {
                if (response.success && response.data) {
                    this.generatedApiKey = response.data.key;
                    this.messageService.add({
                        severity: 'success',
                        summary: 'Clé API générée',
                        detail: 'Copiez cette clé maintenant, elle ne sera plus affichée'
                    });
                }
            },
            error: (error) => {
                this.messageService.add({
                    severity: 'error',
                    summary: 'Erreur',
                    detail: 'Impossible de générer la clé API'
                });
            }
        });
    }

    copyApiKey(key: string): void {
        navigator.clipboard.writeText(key);
        this.messageService.add({
            severity: 'success',
            summary: 'Copié',
            detail: 'La clé API a été copiée dans le presse-papiers'
        });
    }

    revokeApiKey(apiKey: ApiKey): void {
        this.confirmationService.confirm({
            message: `Êtes-vous sûr de vouloir révoquer la clé "${apiKey.name}" ?`,
            header: 'Confirmer la révocation',
            icon: 'pi pi-exclamation-triangle',
            acceptLabel: 'Oui, révoquer',
            rejectLabel: 'Annuler',
            acceptButtonStyleClass: 'p-button-danger',
            accept: () => {
                this.usersApi.revokeApiKey(apiKey.id).subscribe({
                    next: (response) => {
                        if (response.success) {
                            this.apiKeys = this.apiKeys.filter(k => k.id !== apiKey.id);
                            this.messageService.add({
                                severity: 'success',
                                summary: 'Clé révoquée',
                                detail: 'La clé API a été révoquée avec succès'
                            });
                        }
                    },
                    error: (error) => {
                        this.messageService.add({
                            severity: 'error',
                            summary: 'Erreur',
                            detail: 'Impossible de révoquer la clé API'
                        });
                    }
                });
            }
        });
    }

    closeApiKeyDialog(): void {
        this.showApiKeyDialog = false;
        this.newApiKeyName = '';
        this.generatedApiKey = '';
    }

    // Session Management
    revokeSession(session: Session): void {
        if (session.is_current) {
            this.messageService.add({
                severity: 'warn',
                summary: 'Session actuelle',
                detail: 'Vous ne pouvez pas révoquer votre session actuelle'
            });
            return;
        }

        this.confirmationService.confirm({
            message: `Révoquer la session "${session.device}" ?`,
            header: 'Confirmer la révocation',
            icon: 'pi pi-exclamation-triangle',
            acceptLabel: 'Oui, révoquer',
            rejectLabel: 'Annuler',
            acceptButtonStyleClass: 'p-button-danger',
            accept: () => {
                this.usersApi.revokeSession(session.id).subscribe({
                    next: (response) => {
                        if (response.success) {
                            this.sessions = this.sessions.filter(s => s.id !== session.id);
                            this.messageService.add({
                                severity: 'success',
                                summary: 'Session révoquée',
                                detail: 'La session a été révoquée avec succès'
                            });
                        }
                    },
                    error: (error) => {
                        this.messageService.add({
                            severity: 'error',
                            summary: 'Erreur',
                            detail: 'Impossible de révoquer la session'
                        });
                    }
                });
            }
        });
    }

    revokeAllSessions(): void {
        this.confirmationService.confirm({
            message: 'Toutes les autres sessions seront fermées. Vous devrez vous reconnecter sur ces appareils.',
            header: 'Révoquer toutes les sessions',
            icon: 'pi pi-exclamation-triangle',
            acceptLabel: 'Oui, révoquer tout',
            rejectLabel: 'Annuler',
            acceptButtonStyleClass: 'p-button-danger',
            accept: () => {
                this.usersApi.revokeAllSessions().subscribe({
                    next: (response) => {
                        if (response.success) {
                            this.sessions = this.sessions.filter(s => s.is_current);
                            this.messageService.add({
                                severity: 'success',
                                summary: 'Sessions révoquées',
                                detail: 'Toutes les autres sessions ont été révoquées'
                            });
                        }
                    },
                    error: (error) => {
                        this.messageService.add({
                            severity: 'error',
                            summary: 'Erreur',
                            detail: 'Impossible de révoquer les sessions'
                        });
                    }
                });
            }
        });
    }

    // Danger Zone
    deleteAccount(): void {
        this.confirmationService.confirm({
            message: 'Cette action est irréversible. Toutes vos données seront supprimées définitivement.',
            header: 'Supprimer le compte',
            icon: 'pi pi-exclamation-triangle',
            acceptLabel: 'Oui, supprimer mon compte',
            rejectLabel: 'Annuler',
            acceptButtonStyleClass: 'p-button-danger',
            accept: () => {
                this.usersApi.deleteAccount().subscribe({
                    next: (response) => {
                        if (response.success) {
                            this.messageService.add({
                                severity: 'info',
                                summary: 'Compte supprimé',
                                detail: 'Votre compte a été supprimé. Au revoir !'
                            });

                            // Logout and redirect
                            setTimeout(() => {
                                this.authService.logout().subscribe(() => {
                                    this.router.navigate(['/']);
                                });
                            }, 2000);
                        }
                    },
                    error: (error) => {
                        this.messageService.add({
                            severity: 'error',
                            summary: 'Erreur',
                            detail: 'Impossible de supprimer le compte'
                        });
                    }
                });
            }
        });
    }

    formatDate(dateString: string | null): string {
        if (!dateString) return 'Jamais';

        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    private updateFormWithUserPreferences(): void {
        // Update form values if user has specific preferences
        // For now, keeping default values
        // In the future, you could load user preferences from the backend
        // and update the form using patchValue
    }
}
