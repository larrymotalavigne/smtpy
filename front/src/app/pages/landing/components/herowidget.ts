import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { RippleModule } from 'primeng/ripple';
import { AuthService } from '../../../core/services/auth.service';
import { AsyncPipe } from '@angular/common';

@Component({
    selector: 'hero-widget',
    imports: [RouterModule, ButtonModule, RippleModule, AsyncPipe],
    template: `
        <div
            id="hero"
            class="flex flex-col pt-6 px-6 lg:px-20 overflow-hidden"
            style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); clip-path: ellipse(150% 87% at 93% 13%)"
        >
            <div class="mx-6 md:mx-20 mt-0 md:mt-6">
                <h1 class="text-6xl font-bold text-white leading-tight"><span class="font-light block">Gestion d'emails professionnels</span>Simple, sécurisée et performante</h1>
                <p class="font-normal text-2xl leading-normal md:mt-4 text-white opacity-90">Créez des alias email illimités et redirigez-les vers votre boîte existante. Configuration simple en quelques clics avec vérification DNS automatique.</p>
                @if (!(authService.currentUser$ | async)) {
                    <button pButton pRipple [rounded]="true" type="button" label="Commencer gratuitement" routerLink="/auth/register" class="text-xl! mt-8 px-4! bg-white! text-primary!"></button>
                } @else {
                    <button pButton pRipple [rounded]="true" type="button" label="Aller au tableau de bord" routerLink="/dashboard" class="text-xl! mt-8 px-4! bg-white! text-primary!"></button>
                }
            </div>
            <div class="flex justify-center md:justify-end mt-8">
                <div class="text-white text-center p-8">
                    <div class="flex gap-12 justify-center">
                        <div>
                            <div class="text-5xl font-bold">10k+</div>
                            <div class="text-xl opacity-90 mt-2">Utilisateurs actifs</div>
                        </div>
                        <div>
                            <div class="text-5xl font-bold">99.9%</div>
                            <div class="text-xl opacity-90 mt-2">Uptime garanti</div>
                        </div>
                        <div>
                            <div class="text-5xl font-bold">1M+</div>
                            <div class="text-xl opacity-90 mt-2">Emails traités</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
})
export class HeroWidget {
    constructor(public authService: AuthService) {}
}
