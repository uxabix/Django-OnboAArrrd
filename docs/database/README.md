# Database schema diagrams

Entity-relationship diagrams are generated from Django models with [django-extensions](https://django-extensions.readthedocs.io/en/latest/graph_models.html) `graph_models` and [Graphviz](https://graphviz.org/).

## Output

| File | Description |
|------|-------------|
| `DB Diagram/erd.png` | Raster diagram (README, slides) |
| `DB Diagram/erd.svg` | Vector diagram (scales cleanly) |
| `DB Diagram/erd.dot` | Graphviz source (regenerated each run) |

Only project apps are included: `accounts`, `chat`, `onboarding`. Django contrib models such as `Session`, `ContentType`, `Group`, and `Permission` are excluded. Model boxes show field names and types (django2018 theme).

## Prerequisites

- Python dependencies: `pip install -r requirements.txt` (includes `django-extensions`).
- **Graphviz** system install with `dot` on `PATH`:
  - **Docker**: included in the project `Dockerfile`.
  - **Windows**: [Graphviz download](https://graphviz.org/download/) or `winget install Graphviz.Graphviz`.
  - **Linux**: `sudo apt install graphviz` (Debian/Ubuntu).

`graph_models` does not require a running database; minimal Postgres env vars are still needed for Django settings (see below).

## Generate

From the project root (next to `manage.py`):

```bash
# Minimal env if .env is missing (values are not used for diagram generation)
export POSTGRES_DB=onboard POSTGRES_USER=user POSTGRES_PASSWORD=pass POSTGRES_HOST=localhost POSTGRES_PORT=5432

python manage.py db_diagram
```

Options:

```bash
python manage.py db_diagram --output-dir "DB Diagram"
python manage.py db_diagram --dot-only   # DOT only, no PNG/SVG
```

Equivalent low-level command:

```bash
python manage.py graph_models accounts chat onboarding \
  -X Session,ContentType,LogEntry,Group,Permission,AdminLogEntry \
  -t django2018 -o "DB Diagram/erd.png"
```

## Docker

```bash
docker compose run --rm \
  -e POSTGRES_DB=onboard -e POSTGRES_USER=user -e POSTGRES_PASSWORD=pass \
  -e POSTGRES_HOST=db -e POSTGRES_PORT=5432 \
  web python manage.py db_diagram
```

Diagrams are written to `DB Diagram/` on the mounted volume.
