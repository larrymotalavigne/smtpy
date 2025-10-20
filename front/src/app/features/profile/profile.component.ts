import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';

// PrimeNG Modules
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { ButtonModule } from 'primeng/button';
import { AvatarModule } from 'primeng/avatar';
import { MessageModule } from 'primeng/message';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { DividerModule } from 'primeng/divider';
import { TagModule } from 'primeng/tag';
import { SkeletonModule } from 'primeng/skeleton';

// Services
import { AuthService, User } from '../../core/services/auth.service';

// Layout
import { MainLayoutComponent } from '../../shared/components/layout/main-layout.component';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MainLayoutComponent,
    CardModule,
    InputTextModule,
    ButtonModule,
    AvatarModule,
    MessageModule,
    ToastModule,
    DividerModule,
    TagModule,
    SkeletonModule
  ],
  providers: [MessageService]
})
export class ProfileComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  currentUser: User | null = null;
  profileForm!: FormGroup;
  passwordForm!: FormGroup;
  loading = false;
  savingProfile = false;
  changingPassword = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    // Subscribe to current user
    this.authService.currentUser$
      .pipe(takeUntil(this.destroy$))
      .subscribe(user => {
        this.currentUser = user;
        if (user) {
          this.initializeForms(user);
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initializeForms(user: User): void {
    // Profile information form
    this.profileForm = this.fb.group({
      username: [{ value: user.username, disabled: true }],  // Username cannot be changed
      email: [user.email, [Validators.required, Validators.email]]
    });

    // Password change form
    this.passwordForm = this.fb.group({
      currentPassword: ['', [Validators.required, Validators.minLength(8)]],
      newPassword: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', [Validators.required]]
    }, {
      validators: this.passwordMatchValidator
    });
  }

  passwordMatchValidator(group: FormGroup): { [key: string]: boolean } | null {
    const newPassword = group.get('newPassword');
    const confirmPassword = group.get('confirmPassword');

    if (newPassword && confirmPassword && newPassword.value !== confirmPassword.value) {
      confirmPassword.setErrors({ passwordMismatch: true });
      return { passwordMismatch: true };
    }

    return null;
  }

  onSaveProfile(): void {
    if (this.profileForm.invalid) {
      this.markFormGroupTouched(this.profileForm);
      return;
    }

    this.savingProfile = true;

    // TODO: Implement API call to update profile
    // For now, just show success message
    setTimeout(() => {
      this.savingProfile = false;
      this.messageService.add({
        severity: 'success',
        summary: 'Profil mis à jour',
        detail: 'Vos informations ont été enregistrées avec succès'
      });
    }, 1000);
  }

  onChangePassword(): void {
    if (this.passwordForm.invalid) {
      this.markFormGroupTouched(this.passwordForm);
      return;
    }

    this.changingPassword = true;

    const { currentPassword, newPassword } = this.passwordForm.value;

    // TODO: Implement API call to change password
    // For now, just show success message and reset form
    setTimeout(() => {
      this.changingPassword = false;
      this.passwordForm.reset();
      this.messageService.add({
        severity: 'success',
        summary: 'Mot de passe modifié',
        detail: 'Votre mot de passe a été changé avec succès'
      });
    }, 1000);
  }

  getUserInitials(): string {
    if (!this.currentUser) return '';
    return this.currentUser.username.substring(0, 2).toUpperCase();
  }

  getRoleSeverity(): 'success' | 'info' | 'warn' | 'danger' {
    if (!this.currentUser) return 'info';
    return this.currentUser.role === 'admin' ? 'success' : 'info';
  }

  getRoleLabel(): string {
    if (!this.currentUser) return '';
    return this.currentUser.role === 'admin' ? 'Administrateur' : 'Utilisateur';
  }

  getStatusSeverity(): 'success' | 'warn' {
    return this.currentUser?.is_active ? 'success' : 'warn';
  }

  getStatusLabel(): string {
    return this.currentUser?.is_active ? 'Actif' : 'Inactif';
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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

  isFieldInvalid(formGroup: FormGroup, fieldName: string): boolean {
    const field = formGroup.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  getFieldError(formGroup: FormGroup, fieldName: string): string {
    const field = formGroup.get(fieldName);

    if (field?.hasError('required')) {
      return 'Ce champ est requis';
    }
    if (field?.hasError('email')) {
      return 'Adresse email invalide';
    }
    if (field?.hasError('minlength')) {
      const minLength = field.errors?.['minlength'].requiredLength;
      return `Minimum ${minLength} caractères requis`;
    }
    if (field?.hasError('passwordMismatch')) {
      return 'Les mots de passe ne correspondent pas';
    }

    return '';
  }
}
