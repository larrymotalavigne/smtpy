import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MenuItem } from 'primeng/api';
import { AppMenuitem } from './app.menuitem';

@Component({
    selector: 'app-menu',
    standalone: true,
    imports: [CommonModule, AppMenuitem, RouterModule],
    template: `<ul class="layout-menu">
        <ng-container *ngFor="let item of model; let i = index">
            <li app-menuitem *ngIf="!item.separator" [item]="item" [index]="i" [root]="true"></li>
            <li *ngIf="item.separator" class="menu-separator"></li>
        </ng-container>
    </ul> `
})
export class AppMenu {
    model: MenuItem[] = [];

    ngOnInit() {
        this.model = [
            {
                label: 'Principal',
                items: [
                    { label: 'Tableau de bord', icon: 'pi pi-fw pi-home', routerLink: ['/dashboard'] }
                ]
            },
            {
                label: 'Gestion',
                items: [
                    { label: 'Domaines', icon: 'pi pi-fw pi-globe', routerLink: ['/domains'] },
                    { label: 'Messages', icon: 'pi pi-fw pi-envelope', routerLink: ['/messages'] },
                    { label: 'Statistiques', icon: 'pi pi-fw pi-chart-bar', routerLink: ['/statistics'] }
                ]
            },
            {
                label: 'Compte',
                items: [
                    { label: 'Facturation', icon: 'pi pi-fw pi-credit-card', routerLink: ['/billing'] },
                    { label: 'Profil', icon: 'pi pi-fw pi-user', routerLink: ['/profile'] },
                    { label: 'Paramètres', icon: 'pi pi-fw pi-cog', routerLink: ['/settings'] }
                ]
            }
        ];
    }
}
