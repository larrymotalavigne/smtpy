import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-statistics',
  templateUrl: './statistics.component.html',
  styleUrls: ['./statistics.component.scss'],
  standalone: true,
  imports: [CommonModule]
})
export class StatisticsComponent {
  selectedPeriod = '7days';

  selectPeriod(period: string) {
    this.selectedPeriod = period;
  }
}