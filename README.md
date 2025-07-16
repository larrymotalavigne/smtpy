# smtpy

A modern, open-source addy.io alternative for custom email aliasing and forwarding.

## Features
- Custom domain support
- Alias management with catch-all
- Secure SMTP receiving and forwarding
- REST API and beautiful admin panel (Tabler.io)
- DKIM/SPF/DMARC ready
- Activity logging and dashboard

## Quickstart

1. **Install dependencies:**
   ```bash
   uv pip install -r requirements.txt
   ```
2. **Run the app:**
   ```bash
   uvicorn views.web:app --reload
   ```
3. **Visit:**
   - [http://localhost:8000/presentation](http://localhost:8000/presentation) — Landing page
   - [http://localhost:8000/dashboard](http://localhost:8000/dashboard) — Dashboard
   - [http://localhost:8000/](http://localhost:8000/) — Admin panel

4. **SMTP server:**
   - The SMTP server runs as part of the app and handles incoming mail for configured domains/aliases.

## CI/CD Pipeline

This project includes a comprehensive GitHub Actions workflow for automated testing, building, and deployment to Scaleway.

### Workflow Features:
- **Testing**: Runs pytest, linting (flake8, black, isort)
- **Building**: Multi-platform Docker image (AMD64, ARM64)
- **Security**: Trivy vulnerability scanning
- **Deployment**: Automatic deployment to Scaleway Container Instances

### Required Secrets:
Set these in your GitHub repository settings:
- `SCALEWAY_ACCESS_KEY`: Your Scaleway access key
- `SCALEWAY_SECRET_KEY`: Your Scaleway secret key
- `SCALEWAY_ORG_ID`: Your Scaleway organization ID
- `SCALEWAY_PROJECT_ID`: Your Scaleway project ID

### Deployment:
The workflow automatically:
1. Builds and pushes Docker images to Scaleway Container Registry
2. Deploys to Scaleway Container Instances
3. Exposes ports 80 (HTTP) and 8025 (SMTP)

## Documentation
See the [docs/](docs/) folder for detailed setup, configuration, and API usage. 