# Phase 1: Foundation - Research

## Standard Stack (2025)
- **Orchestration**: `pnpm` workspaces (v9+) for root task management and frontend dependencies.
- **Python Management**: `uv` (v0.4+) for high-performance Python environment and backend dependency management.
- **Frontend**: SvelteKit 2 (TypeScript, Standard library).
- **Backend**: FastAPI 0.110+ (Python 3.12).
- **Automation**: `concurrently` for unified local development logs.

## Architecture Patterns
- **Shared Workspace**: Root `package.json` manages cross-domain scripts.
- **Domain Isolation**: Backend uses `pyproject.toml` (uv); Frontend uses `package.json` (pnpm). 
- **Environment**: Single `.env` at root, symlinked or referenced by both domains.

## Don't Hand-Roll
- **Env Loading**: Use `pydantic-settings` for FastAPI and `$env/static/private` / `$env/dynamic/private` for SvelteKit.
- **Concurrent Execution**: Don't use custom shell scripts; use `concurrently` or `pnpm -r dev`.

## Common Pitfalls
- **Python Path**: Ensure `uv` virtual environment is correctly recognized by VS Code (typically in `backend/.venv` or root `.venv`).
- **Pnpm Filters**: In mono-repos, always use `--filter ./frontend` to avoid ambiguity.
- **SvelteKit Origin**: Ensure `ORIGIN` and `PUBLIC_API_BASE_URL` are correctly set for dev to avoid CORS issues.

## References
- [pnpm workspaces](https://pnpm.io/workspaces)
- [uv workspaces](https://docs.astral.sh/uv/concepts/workspaces/)
- [SvelteKit + FastAPI boilerplate patterns](https://testdriven.io/blog/svelte-fastapi/)

---
*Status: Complete*
