"""
Optimized database management with connection pooling and health checks.
Provides async database sessions with proper error handling and monitoring.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from urllib.parse import urlparse

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import get_settings
from app.core.exceptions import DatabaseError, handle_database_errors

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseManager:
    """Manages database connections with optimization and monitoring."""

    def __init__(self) -> None:
        self._async_engine: Optional[AsyncEngine] = None
        self._async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._is_connected = False

    @property
    def async_engine(self) -> AsyncEngine:
        """Get or create async database engine with optimized settings."""
        if self._async_engine is None:
            self._async_engine = self._create_async_engine()
        return self._async_engine

    @property
    def async_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create async session factory."""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )
        return self._async_session_factory

    def _create_async_engine(self) -> AsyncEngine:
        """Create optimized async database engine."""
        database_url = self._get_database_url()
        engine_kwargs = self._get_engine_kwargs(database_url)
        
        engine = create_async_engine(database_url, **engine_kwargs)
        
        # Add connection event listeners
        self._setup_event_listeners(engine.sync_engine)
        
        logger.info(f"Created async database engine for {self._mask_url(database_url)}")
        return engine

    def _get_database_url(self) -> str:
        """Get and validate database URL."""
        database_url = settings.DATABASE_URL
        
        if not database_url:
            raise DatabaseError("DATABASE_URL not configured")
        
        # Convert PostgreSQL URL to async version if needed
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        elif database_url.startswith("sqlite://"):
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
        
        return database_url

    def _get_engine_kwargs(self, database_url: str) -> dict:
        """Get engine configuration based on database type."""
        parsed = urlparse(database_url)
        is_sqlite = parsed.scheme.startswith("sqlite")
        
        if is_sqlite:
            return {
                "echo": settings.DATABASE_ECHO,
                "poolclass": NullPool,  # SQLite doesn't support connection pooling
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 30,
                },
            }
        else:
            return {
                "echo": settings.DATABASE_ECHO,
                "poolclass": QueuePool,
                "pool_size": settings.DATABASE_POOL_SIZE,
                "max_overflow": settings.DATABASE_MAX_OVERFLOW,
                "pool_pre_ping": True,
                "pool_recycle": settings.DATABASE_POOL_RECYCLE,
                "pool_timeout": 30,
                "connect_args": {
                    "command_timeout": 60,
                    "server_settings": {
                        "jit": "off",  # Disable JIT for faster startup
                    },
                },
            }

    def _setup_event_listeners(self, engine) -> None:
        """Setup database event listeners for monitoring and optimization."""
        
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Optimize SQLite connection settings."""
            if "sqlite" in str(dbapi_connection):
                cursor = dbapi_connection.cursor()
                # Performance optimizations for SQLite
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL") 
                cursor.execute("PRAGMA cache_size=1000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()
        
        @event.listens_for(engine, "connect")
        def set_postgresql_settings(dbapi_connection, connection_record):
            """Optimize PostgreSQL connection settings."""
            if hasattr(dbapi_connection, "set_session"):
                # Set timezone and encoding
                dbapi_connection.set_session(autocommit=False)

    def _mask_url(self, url: str) -> str:
        """Mask sensitive information in database URL for logging."""
        parsed = urlparse(url)
        if parsed.password:
            masked_url = url.replace(parsed.password, "***")
            return masked_url
        return url

    async def health_check(self) -> bool:
        """Check database connectivity and basic functionality."""
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
                self._is_connected = True
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            self._is_connected = False
            return False

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with proper error handling."""
        async with handle_database_errors("session_creation"):
            async with self.async_session_factory() as session:
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()

    async def create_tables(self) -> None:
        """Create database tables."""
        from app.models import Base  # Import here to avoid circular imports
        
        async with handle_database_errors("table_creation"):
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")

    async def drop_tables(self) -> None:
        """Drop all database tables (use with caution)."""
        from app.models import Base
        
        async with handle_database_errors("table_deletion"):
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.warning("All database tables dropped")

    async def close(self) -> None:
        """Close database connections."""
        if self._async_engine:
            await self._async_engine.dispose()
            self._async_engine = None
            self._async_session_factory = None
            self._is_connected = False
            logger.info("Database connections closed")

    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._is_connected

    async def get_connection_info(self) -> dict:
        """Get database connection information for monitoring."""
        if not self._async_engine:
            return {"status": "not_initialized"}
        
        pool = self._async_engine.pool
        return {
            "status": "connected" if self._is_connected else "disconnected",
            "pool_size": getattr(pool, "size", lambda: 0)(),
            "checked_in": getattr(pool, "checkedin", lambda: 0)(),
            "checked_out": getattr(pool, "checkedout", lambda: 0)(),
            "overflow": getattr(pool, "overflow", lambda: 0)(),
            "invalid": getattr(pool, "invalid", lambda: 0)(),
        }


# Global database manager instance
db_manager = DatabaseManager()


# Dependency for FastAPI
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get database session."""
    async with db_manager.get_session() as session:
        yield session


# Database initialization functions
async def init_database() -> None:
    """Initialize database on application startup."""
    try:
        await db_manager.create_tables()
        health_ok = await db_manager.health_check()
        if health_ok:
            logger.info("Database initialized successfully")
        else:
            logger.error("Database initialization failed health check")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def close_database() -> None:
    """Close database connections on application shutdown."""
    await db_manager.close()
    logger.info("Database connections closed")


# Transaction management utilities
@asynccontextmanager
async def transaction() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database transactions with automatic rollback."""
    async with db_manager.get_session() as session:
        try:
            async with session.begin():
                yield session
        except Exception:
            # Rollback is automatic with session.begin()
            raise


class DatabaseMetrics:
    """Collect database performance metrics."""
    
    def __init__(self) -> None:
        self.query_count = 0
        self.slow_query_count = 0
        self.error_count = 0
    
    def record_query(self, duration: float, threshold: float = 1.0) -> None:
        """Record query execution metrics."""
        self.query_count += 1
        if duration > threshold:
            self.slow_query_count += 1
            logger.warning(f"Slow query detected: {duration:.2f}s")
    
    def record_error(self) -> None:
        """Record database error."""
        self.error_count += 1
    
    def get_metrics(self) -> dict:
        """Get current metrics."""
        return {
            "total_queries": self.query_count,
            "slow_queries": self.slow_query_count,
            "errors": self.error_count,
            "slow_query_ratio": (
                self.slow_query_count / self.query_count 
                if self.query_count > 0 else 0
            ),
        }


# Global metrics instance
db_metrics = DatabaseMetrics()