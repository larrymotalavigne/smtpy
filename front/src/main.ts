import { bootstrapApplication } from '@angular/platform-browser';
import { registerLocaleData } from '@angular/common';
import localeFr from '@angular/common/locales/fr';
import { appConfig } from './app.config';
import { AppComponent } from './app.component';

// Register French locale for DatePipe and other locale-aware pipes
registerLocaleData(localeFr, 'fr');

bootstrapApplication(AppComponent, appConfig).catch((err) => console.error(err));
