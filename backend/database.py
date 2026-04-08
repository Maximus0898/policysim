from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event
from sqlmodel import SQLModel
from backend.config import settings

# Database URL for async SQLite
sqlite_url = settings.database_url

# Create the async engine
# check_same_thread=False is required for SQLite with async
engine = create_async_engine(
    sqlite_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False}
)

# Enable WAL mode via listener
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

# Create a sessionmaker specifically for AsyncSession
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        # Create all tables defined in models.py
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
