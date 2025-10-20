import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';

@Component({
  selector: 'app-landing',
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.scss'],
  standalone: true,
  imports: [CommonModule, ButtonModule, CardModule]
})
export class LandingComponent {

  features = [
    {
      icon: 'pi pi-cog',
      title: 'Configuration simple',
      description: 'Configurez vos MX records en quelques minutes',
      color: 'text-blue-600'
    },
    {
      icon: 'pi pi-infinity',
      title: 'Alias illimités',
      description: 'Créez autant d\'alias que nécessaire',
      color: 'text-green-600'
    },
    {
      icon: 'pi pi-desktop',
      title: 'Interface intuitive',
      description: 'Gérez vos emails facilement',
      color: 'text-purple-600'
    },
    {
      icon: 'pi pi-shield',
      title: 'Sécurité renforcée',
      description: 'Protection DKIM et SPF incluses',
      color: 'text-red-600'
    },
    {
      icon: 'pi pi-chart-line',
      title: 'Statistiques détaillées',
      description: 'Suivez vos emails en temps réel',
      color: 'text-orange-600'
    },
    {
      icon: 'pi pi-bolt',
      title: 'Performance maximale',
      description: 'Livraison rapide et fiable',
      color: 'text-indigo-600'
    }
  ];

  constructor(private router: Router) {}

  navigateToDashboard() {
    this.router.navigate(['/dashboard']);
  }
}