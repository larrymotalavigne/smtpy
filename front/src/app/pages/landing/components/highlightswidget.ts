import { Component } from '@angular/core';

@Component({
    selector: 'highlights-widget',
    template: `
        <div id="highlights" class="py-6 px-6 lg:px-20 mx-0 my-12 lg:mx-20">
            <div class="text-center">
                <div class="text-surface-900 dark:text-surface-0 font-normal mb-2 text-4xl">Pourquoi choisir SMTPy ?</div>
                <span class="text-muted-color text-2xl">Des avantages qui font la différence</span>
            </div>

            <div class="grid grid-cols-12 gap-4 mt-20 pb-2 md:pb-20">
                <div class="flex justify-center col-span-12 lg:col-span-6 p-12 order-1 lg:order-0" style="border-radius: 8px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
                    <div class="flex items-center justify-center text-white">
                        <i class="pi pi-fw pi-mobile" style="font-size: 12rem;"></i>
                    </div>
                </div>

                <div class="col-span-12 lg:col-span-6 my-auto flex flex-col lg:items-end text-center lg:text-right gap-4">
                    <div class="flex items-center justify-center bg-purple-200 self-center lg:self-end" style="width: 4.2rem; height: 4.2rem; border-radius: 10px">
                        <i class="pi pi-fw pi-mobile text-4xl! text-purple-700"></i>
                    </div>
                    <div class="leading-none text-surface-900 dark:text-surface-0 text-3xl font-normal">Interface intuitive</div>
                    <span class="text-surface-700 dark:text-surface-100 text-2xl leading-normal ml-0 md:ml-2" style="max-width: 650px"
                        >Gérez vos domaines et alias depuis n'importe quel appareil. Notre interface responsive s'adapte parfaitement à votre écran, mobile ou desktop.</span
                    >
                </div>
            </div>

            <div class="grid grid-cols-12 gap-4 my-20 pt-2 md:pt-20">
                <div class="col-span-12 lg:col-span-6 my-auto flex flex-col text-center lg:text-left lg:items-start gap-4">
                    <div class="flex items-center justify-center bg-indigo-200 self-center lg:self-start" style="width: 4.2rem; height: 4.2rem; border-radius: 10px">
                        <i class="pi pi-fw pi-clock text-3xl! text-indigo-700"></i>
                    </div>
                    <div class="leading-none text-surface-900 dark:text-surface-0 text-3xl font-normal">Configuration en 5 minutes</div>
                    <span class="text-surface-700 dark:text-surface-100 text-2xl leading-normal mr-0 md:mr-2" style="max-width: 650px"
                        >Plus besoin d'être un expert DNS. Notre assistant de configuration vous guide pas à pas pour configurer votre domaine en quelques minutes seulement.</span
                    >
                </div>

                <div class="flex justify-end order-1 sm:order-2 col-span-12 lg:col-span-6 p-12" style="border-radius: 8px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
                    <div class="flex items-center justify-center text-white">
                        <i class="pi pi-fw pi-clock" style="font-size: 12rem;"></i>
                    </div>
                </div>
            </div>
        </div>
    `
})
export class HighlightsWidget {}
