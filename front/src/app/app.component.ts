import { Component, OnInit } from '@angular/core';
import { Router, RouterOutlet, NavigationEnd } from '@angular/router';
import { CommonModule } from '@angular/common';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
  standalone: true,
  imports: [RouterOutlet, CommonModule]
})
export class AppComponent implements OnInit {
  title = 'SMTPy';
  currentRoute = '';
  showNavigation = false;
  showSidebar = false;

  constructor(private router: Router) {}

  ngOnInit() {
    // Listen to route changes
    this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event) => {
        this.updateLayoutVisibility((event as NavigationEnd).url);
      });

    // Set initial route
    this.updateLayoutVisibility(this.router.url);
  }

  private updateLayoutVisibility(url: string) {
    this.currentRoute = url.replace('/', '') || 'landing';
    
    // Show navigation bar only on landing page
    this.showNavigation = this.currentRoute === 'landing';
    
    // Show sidebar on dashboard pages
    this.showSidebar = ['dashboard', 'domains', 'messages', 'statistics', 'billing'].includes(this.currentRoute);
  }

  navigateTo(route: string) {
    this.router.navigate([route]);
  }
}