# Research: Standard Stack

## Overview
PolicySim requires a hybrid architecture: a high-performance Python backend for multi-agent simulation and a reactive SvelteKit frontend for data visualization.

## Primary Frameworks
- **Backend**: FastAPI (Python 3.11+)
    - Rationale: High performance, native async support for simulation loops and SSE.
- **Frontend**: SvelteKit 2 + TypeScript
    - Rationale: Superior reactivity for real-time dashboard updates and institutional aesthetic.

## Data Persistence & Modeling
- **ORM/Modeling**: SQLModel
    - Rationale: Bridges Pydantic and SQLAlchemy, allowing shared type definitions between the API and database.
- **Database**: SQLite (WAL Mode)
    - Rationale: Zero-config, single-file distribution. WAL (Write-Ahead Logging) enables concurrent read/write during active simulations.

## Communication & Real-time
- **Protocol**: Server-Sent Events (SSE)
    - Rationale: Lightweight unidirectional push from backend to frontend. Ideal for simulation "pulse" updates.
- **Client Side**: Native browser `EventSource` API integrated into Svelte stores.

## Visualization
- **Graph Core**: D3.js (`d3-force`)
    - Rationale: Gold standard for network physics calculations.
- **Rendering**: Svelte SVG
    - Rationale: Declarative rendering of nodes/links with full component-level control.

## Documentation & Export
- **PDF Generation**: WeasyPrint
    - Rationale: Best-in-class CSS Paged Media support for professional policy briefs.
- **Template Engine**: Jinja2 (Backend side) for report layout.

## Tooling
- **Python**: `uv` (Fastest dependency management and virtual environment handling).
- **Node**: `pnpm` (Fast, disk-efficient package management).

---
*Confidence: High*
