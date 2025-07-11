# Configuration

## Domains & Aliases
- Add, edit, and delete domains and aliases via the admin panel or API.
- Each domain can have a catch-all address and multiple aliases.

## Forwarding Rules
- (Planned) Advanced routing with wildcards/regex.

## Database
- Uses SQLite by default (see `SMTPY_DB_PATH` env variable).

## Environment Variables
- `SMTPY_DB_PATH`: Path to the SQLite database file. 