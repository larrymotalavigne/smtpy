import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router, RouterModule, ActivatedRoute } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';

// PrimeNG Modules
import { CardModule } from 'primeng/card';
import { PasswordModule } from 'primeng/password';
import { ButtonModule } from 'primeng/button';
import { MessageModule } from 'primeng/message';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';

// Services
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-reset-password',
  templateUrl: './reset-password.component.html',
  styleUrls: ['./reset-password.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterModule,
    CardModule,
    PasswordModule,
    ButtonModule,
    MessageModule,
    ToastModule
  ],
  providers: [MessageService]
})
export class ResetPasswordComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  resetPasswordForm!: FormGroup;
  loading = false;
  errorMessage = '';
  resetToken = '';
  resetSuccess = false;
  tokenInvalid = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    // Get token from query params
    this.route.queryParams
      .pipe(takeUntil(this.destroy$))
      .subscribe(params => {
        this.resetToken = params['token'];
        if (!this.resetToken) {
          this.tokenInvalid = true;
          this.errorMessage = 'Lien de réinitialisation invalide ou expiré';
        }
      });

    this.resetPasswordForm = this.fb.group({
      password: ['', [
        Validators.required,
        Validators.minLength(8),
        this.passwordStrengthValidator
      ]],
      confirmPassword: ['', [Validators.required]]
    }, {
      validators: this.passwordMatchValidator
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  passwordStrengthValidator(control: AbstractControl): ValidationErrors | null {
    const password = control.value;
    if (!password) return null;

    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumeric = /[0-9]/.test(password);
    const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);

    const passwordValid = hasUpperCase && hasLowerCase && (hasNumeric || hasSpecialChar);

    return passwordValid ? null : { passwordStrength: true };
  }

  passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
    const password = control.get('password');
    const confirmPassword = control.get('confirmPassword');

    if (!password || !confirmPassword) return null;

    return password.value === confirmPassword.value ? null : { passwordMismatch: true };
  }

  onSubmit(): void {
    if (this.resetPasswordForm.invalid || !this.resetToken) {
      this.markFormGroupTouched(this.resetPasswordForm);
      return;
    }

    this.loading = true;
    this.errorMessage = '';

    const { password } = this.resetPasswordForm.value;

    this.authService.resetPassword(this.resetToken, password)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.loading = false;
          if (response.success) {
            this.resetSuccess = true;

            this.messageService.add({
              severity: 'success',
              summary: 'Succès',
              detail: 'Votre mot de passe a été réinitialisé avec succès'
            });

            // Redirect to login after short delay
            setTimeout(() => {
              this.router.navigate(['/auth/login']);
            }, 3000);
          } else {
            this.errorMessage = response.message || 'Erreur lors de la réinitialisation du mot de passe';
          }
        },
        error: (error) => {
          this.loading = false;
          console.error('Password reset error:', error);

          if (error.status === 400 || error.status === 404) {
            this.tokenInvalid = true;
            this.errorMessage = 'Lien de réinitialisation invalide ou expiré';
          } else {
            this.errorMessage = error.error?.message || 'Une erreur est survenue lors de la réinitialisation';
          }

          this.messageService.add({
            severity: 'error',
            summary: 'Erreur',
            detail: this.errorMessage
          });
        }
      });
  }

  requestNewLink(): void {
    this.router.navigate(['/auth/forgot-password']);
  }

  private markFormGroupTouched(formGroup: FormGroup): void {
    Object.keys(formGroup.controls).forEach(key => {
      const control = formGroup.get(key);
      control?.markAsTouched();

      if (control instanceof FormGroup) {
        this.markFormGroupTouched(control);
      }
    });
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.resetPasswordForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  getFieldError(fieldName: string): string {
    const field = this.resetPasswordForm.get(fieldName);

    if (field?.hasError('required')) {
      return 'Ce champ est requis';
    }
    if (field?.hasError('minlength')) {
      const minLength = field.errors?.['minlength'].requiredLength;
      return `Minimum ${minLength} caractères requis`;
    }
    if (field?.hasError('passwordStrength')) {
      return 'Le mot de passe doit contenir au moins une majuscule, une minuscule et un chiffre ou caractère spécial';
    }

    return '';
  }

  getPasswordMatchError(): string {
    if (this.resetPasswordForm.hasError('passwordMismatch')) {
      const confirmPassword = this.resetPasswordForm.get('confirmPassword');
      if (confirmPassword?.touched || confirmPassword?.dirty) {
        return 'Les mots de passe ne correspondent pas';
      }
    }
    return '';
  }
}
