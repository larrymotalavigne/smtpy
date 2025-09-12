import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ReactiveFormsModule } from '@angular/forms';

// PrimeNG Modules
import { ButtonModule } from 'primeng/button';
import { MenuModule } from 'primeng/menu';
import { MenubarModule } from 'primeng/menubar';
import { SidebarModule } from 'primeng/sidebar';
import { AvatarModule } from 'primeng/avatar';
import { TooltipModule } from 'primeng/tooltip';
import { RippleModule } from 'primeng/ripple';
import { BadgeModule } from 'primeng/badge';
import { InputTextModule } from 'primeng/inputtext';
import { ToastModule } from 'primeng/toast';

// Components
import { MainLayoutComponent } from './components/layout/main-layout.component';

@NgModule({
  declarations: [
    MainLayoutComponent
  ],
  imports: [
    CommonModule,
    RouterModule,
    ReactiveFormsModule,
    
    // PrimeNG Modules
    ButtonModule,
    MenuModule,
    MenubarModule,
    SidebarModule,
    AvatarModule,
    TooltipModule,
    RippleModule,
    BadgeModule,
    InputTextModule,
    ToastModule
  ],
  exports: [
    MainLayoutComponent,
    
    // Re-export common modules for use in feature modules
    CommonModule,
    RouterModule,
    ReactiveFormsModule,
    
    // PrimeNG Modules
    ButtonModule,
    MenuModule,
    MenubarModule,
    SidebarModule,
    AvatarModule,
    TooltipModule,
    RippleModule,
    BadgeModule,
    InputTextModule,
    ToastModule
  ]
})
export class SharedModule { }