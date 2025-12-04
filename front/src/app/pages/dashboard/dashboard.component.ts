import {Component, OnInit} from '@angular/core';
import {CommonModule} from '@angular/common';
import {Router} from '@angular/router';

// PrimeNG Modules
import {CardModule} from 'primeng/card';
import {ButtonModule} from 'primeng/button';
import {ChartModule} from 'primeng/chart';
import {TableModule} from 'primeng/table';
import {TagModule} from 'primeng/tag';
import {AvatarModule} from 'primeng/avatar';
import {ToastModule} from 'primeng/toast';
import {MessageService} from 'primeng/api';
import {SkeletonModule} from 'primeng/skeleton';

import {StatisticsApiService} from '../../core/services/statistics-api.service';
import {DomainsApiService} from '../../core/services/domains-api.service';
import {DomainList, DomainStatus} from '../../core/interfaces/domain.interface';

interface DomainSummary {
    id: number;
    name: string;
    status: 'active' | 'pending' | 'error';
    aliasCount: number;
    lastActivity: string;
    emailsToday: number;
}

interface StatCard {
    title: string;
    value: string;
    icon: string;
    iconColor: string;
    change: number;
    changeLabel: string;
}

@Component({
    selector: 'app-dashboard',
    templateUrl: './dashboard.component.html',
    styleUrls: ['./dashboard.component.scss'],
    standalone: true,
    imports: [
        CommonModule,
        CardModule,
        ButtonModule,
        ChartModule,
        TableModule,
        TagModule,
        AvatarModule,
        ToastModule,
        SkeletonModule
    ],
    providers: [MessageService]
})
export class DashboardComponent implements OnInit {
    stats: StatCard[] = [];
    recentDomains: DomainSummary[] = [];

    chartData: any;
    chartOptions: any;

    // Loading states
    loadingStats = false;
    loadingChart = false;
    loadingDomains = false;

    // Data availability flags
    hasChartData = false;

    constructor(
        private router: Router,
        private messageService: MessageService,
        private statisticsApiService: StatisticsApiService,
        private domainsApiService: DomainsApiService
    ) {
    }

    ngOnInit() {
        this.initChart();
        this.loadOverallStats();
        this.loadTimeSeriesData();
        this.loadRecentDomains();
    }

    initChart() {
        this.chartData = {
            labels: [],
            datasets: [
                {
                    label: 'Emails transférés',
                    data: [],
                    fill: true,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                }
            ]
        };

        this.chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#6c757d'
                    },
                    grid: {
                        color: '#e9ecef'
                    }
                },
                x: {
                    ticks: {
                        color: '#6c757d'
                    },
                    grid: {
                        color: '#e9ecef'
                    }
                }
            }
        };
    }

    getStatusSeverity(status: string): 'success' | 'warning' | 'danger' | 'secondary' {
        switch (status) {
            case 'active':
                return 'success';
            case 'pending':
                return 'warning';
            case 'error':
                return 'danger';
            default:
                return 'secondary';
        }
    }

    getStatusLabel(status: string): string {
        switch (status) {
            case 'active':
                return 'Actif';
            case 'pending':
                return 'En attente';
            case 'error':
                return 'Erreur';
            default:
                return status;
        }
    }

    navigateTo(path: string) {
        this.router.navigate([path]);
    }

    private loadOverallStats(): void {
        this.loadingStats = true;

        // Get stats for last 7 days for comparison
        const dateFrom = new Date();
        dateFrom.setDate(dateFrom.getDate() - 7);

        this.statisticsApiService.getOverallStats({
            date_from: dateFrom.toISOString(),
            date_to: new Date().toISOString()
        }).subscribe({
            next: (response) => {
                if (response.success && response.data) {
                    const data = response.data;

                    this.stats = [
                        {
                            title: 'Domaines actifs',
                            value: data.active_domains.toString(),
                            icon: 'pi pi-globe',
                            iconColor: 'text-blue-600',
                            change: 0,
                            changeLabel: `${data.active_domains} domaines`
                        },
                        {
                            title: 'Alias créés',
                            value: data.active_aliases.toString(),
                            icon: 'pi pi-at',
                            iconColor: 'text-green-600',
                            change: 0,
                            changeLabel: `${data.active_aliases} alias`
                        },
                        {
                            title: 'Emails transférés',
                            value: this.formatNumber(data.total_emails),
                            icon: 'pi pi-send',
                            iconColor: 'text-purple-600',
                            change: 0,
                            changeLabel: `${this.formatNumber(data.emails_sent)} envoyés`
                        },
                        {
                            title: 'Taux de livraison',
                            value: `${data.success_rate.toFixed(1)}%`,
                            icon: 'pi pi-check-circle',
                            iconColor: 'text-emerald-600',
                            change: 0,
                            changeLabel: `${data.emails_failed} échecs`
                        }
                    ];
                }
                this.loadingStats = false;
            },
            error: (error) => {
                console.error('Error loading overall stats:', error);
                this.messageService.add({
                    severity: 'error',
                    summary: 'Erreur',
                    detail: 'Impossible de charger les statistiques.'
                });
                this.loadingStats = false;
            }
        });
    }

    private loadTimeSeriesData(): void {
        this.loadingChart = true;

        // Get last 7 days of data
        const dateFrom = new Date();
        dateFrom.setDate(dateFrom.getDate() - 7);

        this.statisticsApiService.getTimeSeries({
            date_from: dateFrom.toISOString(),
            date_to: new Date().toISOString(),
            granularity: 'day'
        }).subscribe({
            next: (response) => {
                if (response.success && response.data) {
                    const timeSeries = response.data;

                    // Extract labels and data from time series
                    const labels = timeSeries.map(point => {
                        const date = new Date(point.date);
                        return this.formatDayLabel(date);
                    });

                    const emailData = timeSeries.map(point => point.emails_sent);

                    this.chartData = {
                        labels: labels,
                        datasets: [
                            {
                                label: 'Emails transférés',
                                data: emailData,
                                fill: true,
                                borderColor: '#667eea',
                                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                                tension: 0.4
                            }
                        ]
                    };

                    // Check if we have data
                    this.hasChartData = emailData.length > 0 && emailData.some(val => val > 0);
                }
                this.loadingChart = false;
            },
            error: (error) => {
                console.error('Error loading time series data:', error);
                this.messageService.add({
                    severity: 'error',
                    summary: 'Erreur',
                    detail: 'Impossible de charger les données du graphique.'
                });
                this.loadingChart = false;
            }
        });
    }

    private loadRecentDomains(): void {
        this.loadingDomains = true;

        this.domainsApiService.getDomains({page: 1, size: 5, sort: 'created_at', order: 'desc'}).subscribe({
            next: (response) => {
                this.recentDomains = response.items.map(domain => this.mapDomainToSummary(domain));
                this.loadingDomains = false;
            },
            error: (error) => {
                console.error('Error loading recent domains:', error);
                this.messageService.add({
                    severity: 'error',
                    summary: 'Erreur',
                    detail: 'Impossible de charger les domaines récents.'
                });
                this.loadingDomains = false;
            }
        });
    }

    private mapDomainToSummary(domain: DomainList): DomainSummary {
        let status: 'active' | 'pending' | 'error' = 'pending';

        if (domain.status === DomainStatus.VERIFIED && domain.is_active) {
            status = 'active';
        } else if (domain.status === DomainStatus.FAILED) {
            status = 'error';
        }

        return {
            id: domain.id,
            name: domain.name,
            status: status,
            aliasCount: 0, // Will be populated from domain stats if available
            lastActivity: this.formatTimeAgo(domain.created_at),
            emailsToday: 0 // Will be populated from domain stats if available
        };
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
        return `Il y a ${diffDays}j`;
    }

    private formatDayLabel(date: Date): string {
        const days = ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'];
        return days[date.getDay()];
    }

    private formatNumber(num: number): string {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
}
