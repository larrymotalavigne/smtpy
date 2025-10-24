import { Component } from '@angular/core';
import { ButtonModule } from 'primeng/button';
import { DividerModule } from 'primeng/divider';
import { RippleModule } from 'primeng/ripple';

@Component({
    selector: 'pricing-widget',
    imports: [DividerModule, ButtonModule, RippleModule],
    template: `
        <div id="pricing" class="py-6 px-6 lg:px-20 my-2 md:my-6">
            <div class="text-center mb-6">
                <div class="text-surface-900 dark:text-surface-0 font-normal mb-2 text-4xl">Tarifs transparents</div>
                <span class="text-muted-color text-2xl">Choisissez le plan qui correspond à vos besoins</span>
            </div>

            <div class="grid grid-cols-12 gap-4 justify-between mt-20 md:mt-0">
                <div class="col-span-12 lg:col-span-4 p-0 md:p-4">
                    <div class="p-4 flex flex-col border-surface-200 dark:border-surface-600 pricing-card cursor-pointer border-2 hover:border-primary duration-300 transition-all" style="border-radius: 10px">
                        <div class="text-surface-900 dark:text-surface-0 text-center my-8 text-3xl">Gratuit</div>
                        <div class="flex items-center justify-center my-8">
                            <i class="pi pi-fw pi-star" style="font-size: 6rem; color: var(--primary-color);"></i>
                        </div>
                        <div class="my-8 flex flex-col items-center gap-4">
                            <div class="flex items-center">
                                <span class="text-5xl font-bold mr-2 text-surface-900 dark:text-surface-0">0€</span>
                                <span class="text-surface-600 dark:text-surface-200">par mois</span>
                            </div>
                            <button pButton pRipple label="Commencer" class="p-button-rounded border-0 ml-4 font-light leading-tight" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;"></button>
                        </div>
                        <p-divider class="w-full bg-surface-200"></p-divider>
                        <ul class="my-8 list-none p-0 flex text-surface-900 dark:text-surface-0 flex-col px-8">
                            <li class="py-2">
                                <i class="pi pi-fw pi-check text-xl text-purple-500 mr-2"></i>
                                <span class="text-xl leading-normal">1 domaine</span>
                            </li>
                            <li class="py-2">
                                <i class="pi pi-fw pi-check text-xl text-purple-500 mr-2"></i>
                                <span class="text-xl leading-normal">5 alias email</span>
                            </li>
                            <li class="py-2">
                                <i class="pi pi-fw pi-check text-xl text-purple-500 mr-2"></i>
                                <span class="text-xl leading-normal">100 emails/mois</span>
                            </li>
                            <li class="py-2">
                                <i class="pi pi-fw pi-check text-xl text-purple-500 mr-2"></i>
                                <span class="text-xl leading-normal">Support email</span>
                            </li>
                        </ul>
                    </div>
                </div>

                <div class="col-span-12 lg:col-span-4 p-0 md:p-4 mt-6 md:mt-0">
                    <div class="p-4 flex flex-col border-surface-200 dark:border-surface-600 pricing-card cursor-pointer border-2 hover:border-primary duration-300 transition-all" style="border-radius: 10px; border-color: var(--primary-color) !important; box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);">
                        <div class="text-surface-900 dark:text-surface-0 text-center my-8 text-3xl">Pro</div>
                        <div class="flex items-center justify-center my-8">
                            <i class="pi pi-fw pi-bolt" style="font-size: 6rem; color: var(--primary-color);"></i>
                        </div>
                        <div class="my-8 flex flex-col items-center gap-4">
                            <div class="flex items-center">
                                <span class="text-5xl font-bold mr-2 text-surface-900 dark:text-surface-0">9€</span>
                                <span class="text-surface-600 dark:text-surface-200">par mois</span>
                            </div>
                            <button pButton pRipple label="Essayer gratuitement" class="p-button-rounded border-0 ml-4 font-light leading-tight" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;"></button>
                        </div>
                        <p-divider class="w-full bg-surface-200"></p-divider>
                        <ul class="my-8 list-none p-0 flex text-surface-900 dark:text-surface-0 flex-col px-8">
                            <li class="py-2">
                                <i class="pi pi-fw pi-check text-xl text-purple-500 mr-2"></i>
                                <span class="text-xl leading-normal">5 domaines</span>
                            </li>
                            <li class="py-2">
                                <i class="pi pi-fw pi-check text-xl text-purple-500 mr-2"></i>
                                <span class="text-xl leading-normal">Alias illimités</span>
                            </li>
                            <li class="py-2">
                                <i class="pi pi-fw pi-check text-xl text-purple-500 mr-2"></i>
                                <span class="text-xl leading-normal">10 000 emails/mois</span>
                            </li>
                            <li class="py-2">
                                <i class="pi pi-fw pi-check text-xl text-purple-500 mr-2"></i>
                                <span class="text-xl leading-normal">Support prioritaire</span>
                            </li>
                        </ul>
                    </div>
                </div>

                <div class="col-span-12 lg:col-span-4 p-0 md:p-4 mt-6 md:mt-0">
                    <div class="p-4 flex flex-col border-surface-200 dark:border-surface-600 pricing-card cursor-pointer border-2 hover:border-primary duration-300 transition-all" style="border-radius: 10px">
                        <div class="text-surface-900 dark:text-surface-0 text-center my-8 text-3xl">Entreprise</div>
                        <div class="flex items-center justify-center my-8">
                            <i class="pi pi-fw pi-building" style="font-size: 6rem; color: var(--primary-color);"></i>
                        </div>
                        <div class="my-8 flex flex-col items-center gap-4">
                            <div class="flex items-center">
                                <span class="text-5xl font-bold mr-2 text-surface-900 dark:text-surface-0">Sur mesure</span>
                            </div>
                            <button pButton pRipple label="Nous contacter" class="p-button-rounded border-0 ml-4 font-light leading-tight" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;"></button>
                        </div>
                        <p-divider class="w-full bg-surface-200"></p-divider>
                        <ul class="my-8 list-none p-0 flex text-surface-900 dark:text-surface-0 flex-col px-8">
                            <li class="py-2">
                                <i class="pi pi-fw pi-check text-xl text-purple-500 mr-2"></i>
                                <span class="text-xl leading-normal">Domaines illimités</span>
                            </li>
                            <li class="py-2">
                                <i class="pi pi-fw pi-check text-xl text-purple-500 mr-2"></i>
                                <span class="text-xl leading-normal">Alias illimités</span>
                            </li>
                            <li class="py-2">
                                <i class="pi pi-fw pi-check text-xl text-purple-500 mr-2"></i>
                                <span class="text-xl leading-normal">Volume personnalisé</span>
                            </li>
                            <li class="py-2">
                                <i class="pi pi-fw pi-check text-xl text-purple-500 mr-2"></i>
                                <span class="text-xl leading-normal">Support dédié 24/7</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    `
})
export class PricingWidget {}
