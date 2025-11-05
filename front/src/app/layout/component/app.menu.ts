import { Component } from '@angular/core';

import { RouterModule } from '@angular/router';
import { MenuItem } from 'primeng/api';
import { AppMenuitem } from './app.menuitem';

@Component({
    selector: 'app-menu',
    standalone: true,
    imports: [AppMenuitem, RouterModule],
    template: `<ul class="layout-menu">
          @for (item of model; track item; let i = $index) {
            @if (!item.separator) {
              <li app-menuitem [item]="item" [index]="i" [root]="true"></li>
            }
            @if (item.separator) {
              <li class="menu-separator"></li>
            }
          }
        </ul>`
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
                    { label: 'Alias', icon: 'pi pi-fw pi-at', routerLink: ['/aliases'] },
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
