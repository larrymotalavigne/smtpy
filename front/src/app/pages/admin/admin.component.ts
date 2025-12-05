import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Card } from 'primeng/card';
import { Button } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { Tag } from 'primeng/tag';
import { UIChart } from 'primeng/chart';
import { MessageService, SharedModule } from 'primeng/api';
import { Toast } from 'primeng/toast';
import { AdminApiService } from '../../core/services/admin-api.service';
import { Skeleton } from 'primeng/skeleton';
import { InputText } from 'primeng/inputtext';
import { Accordion, AccordionPanel, AccordionHeader, AccordionContent } from 'primeng/accordion';

interface DatabaseStats {
  users: {
    total: number;
    active: number;
    admins: number;
    recent_signups: number;
  };
  organizations: {
    total: number;
    active: number;
    with_subscription: number;
  };
  domains: {
    total: number;
    verified: number;
    unverified: number;
    active: number;
  };
  aliases: {
    total: number;
    active: number;
    inactive: number;
  };
  messages: {
    total: number;
    today: number;
    this_week: number;
    this_month: number;
    failed: number;
  };
}

interface RecentActivity {
  id: number;
  type: string;
  description: string;
  timestamp: string;
  user?: string;
}

interface SystemHealth {
  database: {
    status: string;
    connections: number;
    size: string;
  };
  redis?: {
    status: string;
    memory_used: string;
  };
}

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    Card,
    Button,
    TableModule,
    Tag,
    UIChart,
    Toast,
    Skeleton,
    InputText,
    Accordion,
    AccordionPanel,
    AccordionHeader,
    AccordionContent,
    SharedModule
  ],
  providers: [MessageService]
})
export class AdminComponent implements OnInit {
  loading = true;
  stats: DatabaseStats | null | undefined = null;
  recentActivity: RecentActivity[] = [];
  systemHealth: SystemHealth | null | undefined = null;

  // Chart data
  userGrowthData: any;
  messageVolumeData: any;
  domainStatusData: any;
  subscriptionData: any;

  // Chart options
  chartOptions: any;

  constructor(
    private adminApiService: AdminApiService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.loadAdminData();
    this.initializeChartOptions();
  }

  loadAdminData(): void {
    this.loading = true;

    // Load all admin data
    Promise.all([
      this.adminApiService.getDatabaseStats().toPromise(),
      this.adminApiService.getRecentActivity().toPromise(),
      this.adminApiService.getSystemHealth().toPromise()
    ])
      .then(([statsResponse, activityResponse, healthResponse]) => {
        if (statsResponse?.success) {
          this.stats = statsResponse.data;
          this.updateCharts();
        }
        if (activityResponse?.success) {
          this.recentActivity = activityResponse.data || [];
        }
        if (healthResponse?.success) {
          this.systemHealth = healthResponse.data;
        }
        this.loading = false;
      })
      .catch(error => {
        console.error('Error loading admin data:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Impossible de charger les données admin'
        });
        this.loading = false;
      });
  }

  initializeChartOptions(): void {
    const documentStyle = getComputedStyle(document.documentElement);
    const textColor = documentStyle.getPropertyValue('--text-color');
    const textColorSecondary = documentStyle.getPropertyValue('--text-color-secondary');
    const surfaceBorder = documentStyle.getPropertyValue('--surface-border');

    this.chartOptions = {
      maintainAspectRatio: false,
      aspectRatio: 0.6,
      plugins: {
        legend: {
          labels: {
            color: textColor
          }
        }
      },
      scales: {
        x: {
          ticks: {
            color: textColorSecondary
          },
          grid: {
            color: surfaceBorder
          }
        },
        y: {
          ticks: {
            color: textColorSecondary
          },
          grid: {
            color: surfaceBorder
          }
        }
      }
    };
  }

  updateCharts(): void {
    if (!this.stats) return;

    // Domain Status Pie Chart
    const documentStyle = getComputedStyle(document.documentElement);
    this.domainStatusData = {
      labels: ['Vérifiés', 'Non vérifiés', 'Inactifs'],
      datasets: [{
        data: [
          this.stats.domains.verified,
          this.stats.domains.unverified,
          this.stats.domains.total - this.stats.domains.active
        ],
        backgroundColor: [
          documentStyle.getPropertyValue('--green-500'),
          documentStyle.getPropertyValue('--yellow-500'),
          documentStyle.getPropertyValue('--red-500')
        ]
      }]
    };

    // Subscription Pie Chart
    this.subscriptionData = {
      labels: ['Avec abonnement', 'Gratuit'],
      datasets: [{
        data: [
          this.stats.organizations.with_subscription,
          this.stats.organizations.total - this.stats.organizations.with_subscription
        ],
        backgroundColor: [
          documentStyle.getPropertyValue('--blue-500'),
          documentStyle.getPropertyValue('--gray-500')
        ]
      }]
    };

    // Message Volume Bar Chart
    this.messageVolumeData = {
      labels: ['Aujourd\'hui', 'Cette semaine', 'Ce mois'],
      datasets: [{
        label: 'Messages envoyés',
        data: [
          this.stats.messages.today,
          this.stats.messages.this_week,
          this.stats.messages.this_month
        ],
        backgroundColor: documentStyle.getPropertyValue('--blue-500')
      }]
    };

    // User Growth Line Chart
    this.userGrowthData = {
      labels: ['Total', 'Actifs', 'Admins', 'Nouveaux'],
      datasets: [{
        label: 'Utilisateurs',
        data: [
          this.stats.users.total,
          this.stats.users.active,
          this.stats.users.admins,
          this.stats.users.recent_signups
        ],
        borderColor: documentStyle.getPropertyValue('--primary-color'),
        backgroundColor: documentStyle.getPropertyValue('--primary-color'),
        tension: 0.4
      }]
    };
  }

  getActivityIcon(type: string): string {
    switch (type) {
      case 'user_signup': return 'pi-user-plus';
      case 'domain_added': return 'pi-globe';
      case 'alias_created': return 'pi-at';
      case 'message_sent': return 'pi-envelope';
      case 'subscription': return 'pi-credit-card';
      default: return 'pi-info-circle';
    }
  }

  getActivitySeverity(type: string): string {
    switch (type) {
      case 'user_signup': return 'success';
      case 'domain_added': return 'info';
      case 'alias_created': return 'primary';
      case 'message_sent': return 'secondary';
      case 'subscription': return 'warn';
      default: return 'info';
    }
  }

  getHealthStatusSeverity(status: string): string {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'connected':
      case 'ok': return 'success';
      case 'warning': return 'warn';
      case 'error':
      case 'disconnected': return 'danger';
      default: return 'info';
    }
  }

  refreshData(): void {
    this.loadAdminData();
  }

  getStatusSeverity(status: string): string {
    if (!status) return 'info';
    switch (status.toLowerCase()) {
      case 'success': return 'success';
      case 'error': return 'danger';
      case 'warning': return 'warn';
      case 'skipped': return 'secondary';
      default: return 'info';
    }
  }
}
