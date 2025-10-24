import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';
import { Chart, ChartConfiguration, registerables } from 'chart.js';

// PrimeNG Modules
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { SkeletonModule } from 'primeng/skeleton';
import { DatePicker } from 'primeng/datepicker';
import { Select } from 'primeng/select';
import { MenuModule } from 'primeng/menu';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';

// Services
import { StatisticsApiService } from '../service/statistics-api.service';

// Layout

// Interfaces
import {
  StatisticsResponse,
  OverallStats,
  DomainStats,
  AliasStats,
  StatisticsFilter
} from '../../core/interfaces/statistics.interface';

// Register Chart.js components
Chart.register(...registerables);

interface PeriodOption {
  label: string;
  value: string;
  days: number;
}

@Component({
  selector: 'app-statistics',
  templateUrl: './statistics.component.html',
  styleUrls: ['./statistics.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    TableModule,
    SkeletonModule,
    DatePicker,
    Select,
    MenuModule,
    ToastModule
  ],
  providers: [MessageService]
})
export class StatisticsComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  @ViewChild('timeSeriesCanvas') timeSeriesCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('domainBreakdownCanvas') domainBreakdownCanvas!: ElementRef<HTMLCanvasElement>;

  private timeSeriesChart?: Chart;
  private domainChart?: Chart;

  loading = false;
  overallStats: OverallStats | null = null;
  domainStats: DomainStats[] = [];
  topAliases: AliasStats[] = [];

  // Date range selection
  dateRange: Date[] = [];
  selectedPeriod: PeriodOption;

  periodOptions: PeriodOption[] = [
    { label: '7 derniers jours', value: '7days', days: 7 },
    { label: '30 derniers jours', value: '30days', days: 30 },
    { label: '3 derniers mois', value: '3months', days: 90 },
    { label: 'Personnalisé', value: 'custom', days: 0 }
  ];

  exportMenuItems = [
    {
      label: 'Exporter en CSV',
      icon: 'pi pi-file',
      command: () => this.exportData('csv')
    },
    {
      label: 'Exporter en JSON',
      icon: 'pi pi-code',
      command: () => this.exportData('json')
    },
    {
      label: 'Exporter en PDF',
      icon: 'pi pi-file-pdf',
      command: () => this.exportData('pdf')
    }
  ];

  constructor(
    private statisticsService: StatisticsApiService,
    private messageService: MessageService
  ) {
    this.selectedPeriod = this.periodOptions[1]; // Default to 30 days
  }

  ngOnInit(): void {
    this.initializeDateRange();
    this.loadStatistics();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();

    // Destroy charts
    if (this.timeSeriesChart) {
      this.timeSeriesChart.destroy();
    }
    if (this.domainChart) {
      this.domainChart.destroy();
    }
  }

  initializeDateRange(): void {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - this.selectedPeriod.days);
    this.dateRange = [startDate, endDate];
  }

  onPeriodChange(): void {
    if (this.selectedPeriod.value !== 'custom') {
      this.initializeDateRange();
      this.loadStatistics();
    }
  }

  onDateRangeChange(): void {
    if (this.dateRange && this.dateRange.length === 2 && this.dateRange[0] && this.dateRange[1]) {
      this.loadStatistics();
    }
  }

  loadStatistics(): void {
    this.loading = true;

    const filter: StatisticsFilter = {
      date_from: this.dateRange[0]?.toISOString().split('T')[0],
      date_to: this.dateRange[1]?.toISOString().split('T')[0],
      granularity: this.getGranularity()
    };

    this.statisticsService.getStatistics(filter)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          if (response.success && response.data) {
            this.overallStats = response.data.overall;
            this.domainStats = response.data.top_domains || [];
            this.topAliases = response.data.top_aliases || [];

            // Update charts
            setTimeout(() => {
              this.createTimeSeriesChart(response.data!.time_series || []);
              this.createDomainChart(response.data!.top_domains || []);
            }, 0);
          }
          this.loading = false;
        },
        error: (error) => {
          console.error('Error loading statistics:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Erreur',
            detail: 'Impossible de charger les statistiques'
          });
          this.loading = false;

          // Load mock data for development
          this.loadMockData();
        }
      });
  }

  private getGranularity(): 'day' | 'week' | 'month' {
    const daysDiff = Math.ceil(
      (this.dateRange[1].getTime() - this.dateRange[0].getTime()) / (1000 * 60 * 60 * 24)
    );

    if (daysDiff <= 31) return 'day';
    if (daysDiff <= 90) return 'week';
    return 'month';
  }

  private createTimeSeriesChart(data: any[]): void {
    if (!this.timeSeriesCanvas) return;

    // Destroy existing chart
    if (this.timeSeriesChart) {
      this.timeSeriesChart.destroy();
    }

    const ctx = this.timeSeriesCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    const config: ChartConfiguration = {
      type: 'line',
      data: {
        labels: data.map(d => new Date(d.date).toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' })),
        datasets: [
          {
            label: 'Emails envoyés',
            data: data.map(d => d.emails_sent),
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            fill: true,
            tension: 0.4
          },
          {
            label: 'Emails échoués',
            data: data.map(d => d.emails_failed),
            borderColor: '#f87171',
            backgroundColor: 'rgba(248, 113, 113, 0.1)',
            fill: true,
            tension: 0.4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              usePointStyle: true,
              padding: 15
            }
          },
          tooltip: {
            mode: 'index',
            intersect: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        }
      }
    };

    this.timeSeriesChart = new Chart(ctx, config);
  }

  private createDomainChart(data: DomainStats[]): void {
    if (!this.domainBreakdownCanvas || data.length === 0) return;

    // Destroy existing chart
    if (this.domainChart) {
      this.domainChart.destroy();
    }

    const ctx = this.domainBreakdownCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    const colors = [
      '#667eea',
      '#764ba2',
      '#f093fb',
      '#4facfe',
      '#43e97b',
      '#fa709a',
      '#fee140',
      '#30cfd0'
    ];

    const config: ChartConfiguration = {
      type: 'doughnut',
      data: {
        labels: data.map(d => d.domain_name),
        datasets: [{
          data: data.map(d => d.email_count),
          backgroundColor: colors.slice(0, data.length),
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'right',
            labels: {
              usePointStyle: true,
              padding: 15,
              generateLabels: (chart) => {
                const data = chart.data;
                if (data.labels?.length && data.datasets.length) {
                  return data.labels.map((label, i) => ({
                    text: `${label} (${data.datasets[0].data[i]})`,
                    fillStyle: colors[i],
                    hidden: false,
                    index: i
                  }));
                }
                return [];
              }
            }
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const label = context.label || '';
                const value = context.parsed || 0;
                const total = (context.dataset.data as number[]).reduce((a, b) => a + b, 0);
                const percentage = ((value / total) * 100).toFixed(1);
                return `${label}: ${value} (${percentage}%)`;
              }
            }
          }
        }
      }
    };

    this.domainChart = new Chart(ctx, config);
  }

  exportData(format: 'csv' | 'json' | 'pdf'): void {
    const filter: StatisticsFilter = {
      date_from: this.dateRange[0]?.toISOString().split('T')[0],
      date_to: this.dateRange[1]?.toISOString().split('T')[0]
    };

    this.statisticsService.exportStatistics(format, filter)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (blob) => {
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `statistics-${new Date().toISOString().split('T')[0]}.${format}`;
          link.click();
          window.URL.revokeObjectURL(url);

          this.messageService.add({
            severity: 'success',
            summary: 'Succès',
            detail: 'Statistiques exportées avec succès'
          });
        },
        error: (error) => {
          console.error('Error exporting data:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Erreur',
            detail: 'Impossible d\'exporter les statistiques'
          });
        }
      });
  }

  // Mock data for development
  private loadMockData(): void {
    this.overallStats = {
      total_emails: 1247,
      emails_sent: 1189,
      emails_failed: 58,
      active_domains: 5,
      active_aliases: 23,
      success_rate: 95.3,
      total_size_mb: 487.3
    };

    const mockTimeSeries: Array<{date: string, emails_sent: number, emails_failed: number, success_rate: number}> = [];
    const days = this.selectedPeriod.days;
    for (let i = days; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      mockTimeSeries.push({
        date: date.toISOString().split('T')[0],
        emails_sent: Math.floor(Math.random() * 50) + 30,
        emails_failed: Math.floor(Math.random() * 5),
        success_rate: 95 + Math.random() * 4
      });
    }

    this.domainStats = [
      { domain_id: 1, domain_name: 'example.com', email_count: 456, success_count: 445, failure_count: 11, success_rate: 97.6, percentage_of_total: 36.5 },
      { domain_id: 2, domain_name: 'mycompany.com', email_count: 312, success_count: 298, failure_count: 14, success_rate: 95.5, percentage_of_total: 25.0 },
      { domain_id: 3, domain_name: 'business.io', email_count: 234, success_count: 228, failure_count: 6, success_rate: 97.4, percentage_of_total: 18.8 },
      { domain_id: 4, domain_name: 'startup.xyz', email_count: 156, success_count: 145, failure_count: 11, success_rate: 92.9, percentage_of_total: 12.5 },
      { domain_id: 5, domain_name: 'tech.dev', email_count: 89, success_count: 73, failure_count: 16, success_rate: 82.0, percentage_of_total: 7.2 }
    ];

    this.topAliases = [
      { alias_id: 1, alias_email: 'contact@example.com', domain_name: 'example.com', email_count: 156, last_used: '2025-10-20T10:30:00Z' },
      { alias_id: 2, alias_email: 'support@mycompany.com', domain_name: 'mycompany.com', email_count: 89, last_used: '2025-10-20T09:15:00Z' },
      { alias_id: 3, alias_email: 'info@business.io', domain_name: 'business.io', email_count: 67, last_used: '2025-10-19T16:45:00Z' },
      { alias_id: 4, alias_email: 'hello@startup.xyz', domain_name: 'startup.xyz', email_count: 54, last_used: '2025-10-19T14:20:00Z' },
      { alias_id: 5, alias_email: 'team@tech.dev', domain_name: 'tech.dev', email_count: 43, last_used: '2025-10-19T11:30:00Z' }
    ];

    setTimeout(() => {
      this.createTimeSeriesChart(mockTimeSeries);
      this.createDomainChart(this.domainStats);
    }, 0);
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
}
