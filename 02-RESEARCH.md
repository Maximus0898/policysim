# Phase 2: Database & Modeling - Research

## Data Persistence Strategy (2025)
- **Framework**: **SQLModel** (v0.0.16+) for modern ORM based on Pydantic v2.
- **Backend**: **SQLite** for high performance and low operational complexity in an agentic simulation context.
- **Concurrency**: **Write-Ahead Logging (WAL)** mode is MANDATORY to support concurrent agent-stance updates and UI reads.

## Implementation Details
- **Driver**: `sqlite+aiosqlite` for asynchronous I/O.
- **Schema Management**:
  - `Simulation`: Core entity managing round state and project context.
  - `Agent`: Individual units with archetype, persona, and newly requested `age_group` and `income` fields.
  - `Round`: Step-by-step history snapshots.
  - `AgentRoundResult`: Stance and sentiment tracking (Time-series like).

## Async Integration Patterns
- **Engine**: `create_async_engine` from `sqlalchemy.ext.asyncio`.
- **Session**: `AsyncSession` provided via FastAPI dependency injection.
- **Table Creation**: `conn.run_sync(SQLModel.metadata.create_all)` inside a FastAPI `lifespan` hook.

## Don't Hand-Roll
- **Migrations**: While `create_all` works for MVP, if the project scales, Alembic should be introduced. For Phase 2, we will stick to `create_all` for fast iteration.
- **Manual PRAGMAs**: Use SQLAlchemy events to set `PRAGMA journal_mode=WAL` consistently.

## Common Pitfalls
- **Blocking I/O**: Ensure no `session.commit()` or `session.exec()` is called synchronously.
- **Relationship Lazy Loading**: Use `selectinload` or `joinedload` to avoid "N+1" query issues in async mode.

## References
- [SQLModel Async Documentation](https://sqlmodel.tiangolo.com/advanced/async/)
- [SQLAlchemy Async SQLite Guide](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#asyncio-support)

---
*Status: Complete*
