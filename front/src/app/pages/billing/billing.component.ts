import {Component, OnDestroy, OnInit} from '@angular/core';
import {CommonModule} from '@angular/common';
import {ReactiveFormsModule} from '@angular/forms';
import {Subject, takeUntil} from 'rxjs';
import {MessageService} from 'primeng/api';
import {BillingApiService} from '../../core/services/billing-api.service';
import {OrganizationBilling, PlanInfo, SubscriptionResponse} from '../../core/interfaces/billing.interface';

// PrimeNG Modules
import {CardModule} from 'primeng/card';
import {ButtonModule} from 'primeng/button';
import {TableModule} from 'primeng/table';
import {TagModule} from 'primeng/tag';
import {ProgressBarModule} from 'primeng/progressbar';
import {DialogModule} from 'primeng/dialog';
import {InputTextModule} from 'primeng/inputtext';
import {MessageModule} from 'primeng/message';
import {ConfirmDialogModule} from 'primeng/confirmdialog';
import {TooltipModule} from 'primeng/tooltip';
import {SkeletonModule} from 'primeng/skeleton';

@Component({
    selector: 'app-billing',
    templateUrl: './billing.component.html',
    styleUrls: ['./billing.component.scss'],
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        CardModule,
        ButtonModule,
        TableModule,
        TagModule,
        ProgressBarModule,
        DialogModule,
        InputTextModule,
        MessageModule,
        ConfirmDialogModule,
        TooltipModule,
        SkeletonModule
    ],
    providers: [MessageService]
})
export class BillingComponent implements OnInit, OnDestroy {
    loading = false;
    subscription: SubscriptionResponse | null = null;
    plans: PlanInfo[] = [];
    organizationBilling: OrganizationBilling | null = null;
    usageLimits: any = null;
    private destroy$ = new Subject<void>();

    constructor(
        private billingApiService: BillingApiService,
        private messageService: MessageService
    ) {
    }

    ngOnInit(): void {
        this.loadBillingData();
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    onUpgradePlan(priceId: string): void {
        this.loading = true;

        this.billingApiService.createCheckoutSession({
            price_id: priceId,
            success_url: `${window.location.origin}/billing?success=true`,
            cancel_url: `${window.location.origin}/billing?canceled=true`
        })
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response) => {
                    if (response.success && response.data?.url) {
                        // Redirect to Stripe checkout
                        window.location.href = response.data.url;
                    }
                },
                error: (error) => {
                    console.error('Error creating checkout session:', error);
                    this.loading = false;
                }
            });
    }

    onManageBilling(): void {
        this.loading = true;

        this.billingApiService.createCustomerPortal(`${window.location.origin}/billing`)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response) => {
                    if (response.success && response.data?.url) {
                        // Redirect to Stripe customer portal
                        window.location.href = response.data.url;
                    }
                },
                error: (error) => {
                    console.error('Error creating customer portal:', error);
                    this.loading = false;
                }
            });
    }

    onCancelSubscription(): void {
        if (!confirm('Are you sure you want to cancel your subscription? It will remain active until the end of the current billing period.')) {
            return;
        }

        this.loading = true;

        this.billingApiService.cancelSubscription()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response) => {
                    if (response.success) {
                        this.subscription = response.data || null;
                        this.messageService.add({
                            severity: 'success',
                            summary: 'Subscription Canceled',
                            detail: 'Your subscription has been canceled and will remain active until the end of the current billing period.'
                        });
                    }
                    this.loading = false;
                },
                error: (error) => {
                    console.error('Error canceling subscription:', error);
                    this.loading = false;
                }
            });
    }

    onReactivateSubscription(): void {
        this.loading = true;

        this.billingApiService.reactivateSubscription()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response) => {
                    if (response.success) {
                        this.subscription = response.data || null;
                        this.messageService.add({
                            severity: 'success',
                            summary: 'Subscription Reactivated',
                            detail: 'Your subscription has been reactivated and will continue automatically.'
                        });
                    }
                    this.loading = false;
                },
                error: (error) => {
                    console.error('Error reactivating subscription:', error);
                    this.loading = false;
                }
            });
    }

    formatCurrency(amount: number, currency: string = 'eur'): string {
        if (amount === 0) {
            return '0€';
        }
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: currency.toUpperCase()
        }).format(amount / 100);
    }

    getUsagePercentage(current: number, limit?: number): number {
        if (!limit) return 0;
        return Math.min((current / limit) * 100, 100);
    }

    isUsageHigh(current: number, limit?: number): boolean {
        if (!limit) return false;
        return (current / limit) > 0.8;
    }

    private loadBillingData(): void {
        this.loading = true;

        // Load subscription information
        this.billingApiService.getSubscription()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response) => {
                    if (response.success) {
                        this.subscription = response.data || null;
                    }
                },
                error: (error) => {
                    console.error('Error loading subscription:', error);
                }
            });

        // Load available plans
        this.billingApiService.getPlans()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response) => {
                    if (response.success) {
                        this.plans = response.data || [];
                    }
                },
                error: (error) => {
                    console.error('Error loading plans:', error);
                }
            });

        // Load organization billing info
        this.billingApiService.getOrganizationBilling()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response) => {
                    if (response.success) {
                        this.organizationBilling = response.data || null;
                    }
                },
                error: (error) => {
                    console.error('Error loading organization billing:', error);
                }
            });

        // Load usage limits
        this.billingApiService.checkUsageLimits()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response) => {
                    if (response.success) {
                        this.usageLimits = response.data;
                    }
                    this.loading = false;
                },
                error: (error) => {
                    console.error('Error loading usage limits:', error);
                    this.loading = false;
                }
            });
    }
}
