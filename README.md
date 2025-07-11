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
   uvicorn web.app:app --reload
   ```
3. **Visit:**
   - [http://localhost:8000/presentation](http://localhost:8000/presentation) — Landing page
   - [http://localhost:8000/dashboard](http://localhost:8000/dashboard) — Dashboard
   - [http://localhost:8000/](http://localhost:8000/) — Admin panel

4. **SMTP server:**
   - The SMTP server runs as part of the app and handles incoming mail for configured domains/aliases.

## Documentation
See the [docs/](docs/) folder for detailed setup, configuration, and API usage. 