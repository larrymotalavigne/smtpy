# SMTPy Frontend

Angular frontend for SMTPy email aliasing and forwarding service.

## Technologies

- **Angular 18**: Modern web framework
- **PrimeNG 20**: UI component library
- **TailwindCSS 3**: Utility-first CSS framework
- **TypeScript**: Type-safe JavaScript

## Project Structure

```
src/
├── app/
│   ├── core/
│   │   ├── interfaces/          # TypeScript interfaces
│   │   │   ├── domain.interface.ts
│   │   │   ├── message.interface.ts
│   │   │   ├── billing.interface.ts
│   │   │   └── common.interface.ts
│   │   └── services/            # HTTP services (to be implemented)
│   ├── features/                # Feature modules (to be implemented)
│   │   ├── dashboard/
│   │   ├── domains/
│   │   ├── messages/
│   │   └── billing/
│   ├── app-routing.module.ts    # Main routing configuration
│   ├── app.module.ts           # Main app module
│   └── app.component.*         # Root component
├── environments/               # Environment configurations
├── assets/                    # Static assets
└── styles.scss               # Global styles
```

## Features Implemented

### ✅ Core Framework
- Angular 18 project structure
- PrimeNG 20 integration with animations
- TailwindCSS configuration
- TypeScript strict mode enabled

### ✅ TypeScript Interfaces
Based on backend API schemas:
- **Domain interfaces**: DomainCreate, DomainResponse, DNSVerificationStatus, etc.
- **Message interfaces**: MessageResponse, MessageList, MessageStats, MessageFilter
- **Billing interfaces**: SubscriptionResponse, CheckoutSessionRequest, OrganizationBilling
- **Common interfaces**: PaginatedResponse, ErrorResponse, ApiResponse

### ✅ Routing Setup
- Lazy-loaded feature modules
- Routes for dashboard, domains, messages, billing
- Wildcard route handling

### ✅ Configuration
- Development and production environments
- API URL configuration
- Build and serve configurations

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
# Navigate to frontend directory
cd front

# Install dependencies
npm install

# Start development server
npm start
```

The application will be available at `http://localhost:4200`

### Available Scripts

```bash
npm start          # Start development server
npm run build      # Build for production
npm run build:dev  # Build for development
npm test           # Run tests
npm run lint       # Run linting
```

## Next Steps

The framework is ready for feature implementation:

1. **Services**: Implement HTTP services extending BaseService
2. **Components**: Create feature components for domains, messages, billing
3. **Guards**: Add authentication and authorization guards  
4. **Interceptors**: Add HTTP interceptors for auth tokens and error handling
5. **State Management**: Consider NgRx for complex state management
6. **Testing**: Add unit and integration tests

## Backend Integration

The frontend is designed to work with the SMTPy backend API:
- **API Base URL**: Configured in environment files
- **Authentication**: Session-based (matches backend)
- **Data Models**: TypeScript interfaces mirror backend Pydantic schemas

## Development Notes

- Uses function-based patterns (following project guidelines)
- No import aliases used (following project guidelines)
- Strict TypeScript configuration enabled
- PrimeNG theming with Lara Light Blue theme
- TailwindCSS with preflight disabled to avoid conflicts with PrimeNG