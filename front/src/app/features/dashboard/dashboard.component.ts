import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

// PrimeNG Modules
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { ChartModule } from 'primeng/chart';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { AvatarModule } from 'primeng/avatar';

interface DomainSummary {
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
  imports: [CommonModule, CardModule, ButtonModule, ChartModule, TableModule, TagModule, AvatarModule]
})
export class DashboardComponent implements OnInit {
  stats: StatCard[] = [
    {
      title: 'Domaines actifs',
      value: '3',
      icon: 'pi pi-globe',
      iconColor: 'text-blue-600',
      change: 20,
      changeLabel: '+1 ce mois'
    },
    {
      title: 'Alias créés',
      value: '47',
      icon: 'pi pi-at',
      iconColor: 'text-green-600',
      change: 12,
      changeLabel: '+5 cette semaine'
    },
    {
      title: 'Emails transférés',
      value: '1,234',
      icon: 'pi pi-send',
      iconColor: 'text-purple-600',
      change: 8,
      changeLabel: '+94 aujourd\'hui'
    },
    {
      title: 'Taux de livraison',
      value: '99.8%',
      icon: 'pi pi-check-circle',
      iconColor: 'text-emerald-600',
      change: 0.2,
      changeLabel: '+0.1% ce mois'
    }
  ];

  recentDomains: DomainSummary[] = [
    {
      name: 'monentreprise.com',
      status: 'active',
      aliasCount: 12,
      lastActivity: 'Il y a 2h',
      emailsToday: 45
    },
    {
      name: 'nouveausite.fr',
      status: 'pending',
      aliasCount: 0,
      lastActivity: 'Créé il y a 1j',
      emailsToday: 0
    },
    {
      name: 'startup.io',
      status: 'active',
      aliasCount: 35,
      lastActivity: 'Il y a 5min',
      emailsToday: 123
    }
  ];

  chartData: any;
  chartOptions: any;

  constructor(private router: Router) {}

  ngOnInit() {
    this.initChart();
  }

  initChart() {
    this.chartData = {
      labels: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
      datasets: [
        {
          label: 'Emails transférés',
          data: [120, 150, 180, 170, 200, 140, 160],
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
}