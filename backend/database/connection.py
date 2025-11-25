import sqlalchemy
from google.cloud.sql.connector import Connector, IPTypes
import logging
from typing import Optional
from utils.config import get_gcp_credentials
from google.oauth2 import service_account
from contextlib import contextmanager 
from utils.config import (
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
    DB_HOST,
    DB_PORT,
    CLOUD_SQL_CONNECTION_NAME,
    USE_PRIVATE_IP,
    DB_POOL_MIN,
    DB_POOL_MAX,
)

logger = logging.getLogger(__name__)

class DatabaseConnectionPool:
    _instance: Optional['DatabaseConnectionPool'] = None
    _pool = None
    _engine = None
    _connector: Optional[Connector] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnectionPool, cls).__new__(cls)
        return cls._instance

    def initialize_pool(self, minconn=DB_POOL_MIN, maxconn=DB_POOL_MAX):
        if self._pool is not None or self._engine is not None:
            return
        try:
            if CLOUD_SQL_CONNECTION_NAME:
                self._initialize_cloud_sql_pool(minconn, maxconn)
            else:
                self._initialize_local_pool(minconn, maxconn)
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    def _initialize_cloud_sql_pool(self, minconn, maxconn):

        # Load service account credentials from config utility
        credentials_dict = get_gcp_credentials()
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)

        self._connector = Connector(credentials=credentials)
        ip_type = IPTypes.PRIVATE if USE_PRIVATE_IP else IPTypes.PUBLIC

        def getconn():
            return self._connector.connect(
                CLOUD_SQL_CONNECTION_NAME,
                "pg8000",
                user=DB_USER,
                password=DB_PASSWORD,
                db=DB_NAME,
                ip_type=ip_type,
            )
        self._engine = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            pool_size=minconn,
            max_overflow=maxconn - minconn,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
        )
        # Test connection
        with self._engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        logger.info(f"Cloud SQL pool initialized successfully: size={minconn}, max={maxconn}")

    def _initialize_local_pool(self, minconn, maxconn):
        """Initialize local PostgreSQL connection using SQLAlchemy (unified with Cloud SQL approach)"""
        database_url = sqlalchemy.URL.create(
            drivername="postgresql+pg8000",
            username=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=int(DB_PORT),
            database=DB_NAME,
        )

        # Create SQLAlchemy engine with same configuration as Cloud SQL
        self._engine = sqlalchemy.create_engine(
            database_url,
            pool_size=minconn,
            max_overflow=maxconn - minconn,
            pool_timeout=30,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=1800,  # Recycle connections after 30 minutes
        )


        # Test connection
        with self._engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        logger.info(f"Local PostgreSQL pool initialized successfully: size={minconn}, max={maxconn}")

    def get_connection(self):
        """
        Get a database connection from the pool.
        
        DEPRECATED: Use get_connection_safe() context manager instead for automatic cleanup.
        This method is kept for backward compatibility during migration.
        
        Returns:
            Connection object
        """
        conn = self._engine.connect()
        return conn

    @contextmanager
    def get_connection_safe(self):
        """
        Context manager that ensures connections are always returned to the pool.
        This is the recommended way to handle database connections.
        
        Usage:
            with db_pool.get_connection_safe() as conn:
                result = conn.execute(sqlalchemy.text("SELECT * FROM users"))
                conn.commit()  # If needed
        
        The connection is automatically returned to the pool when:
        - The context exits normally
        - An exception occurs
        - The code returns early
        
        Yields:
            Connection object from the pool
        """
        conn = None
        try:
            conn = self._engine.connect()
            logger.debug(
                f"Connection checked out - Pool: size={self._engine.pool.size()}, "
                f"checked_out={self._engine.pool.checkedout()}"
            )
            yield conn
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception as rollback_error:
                    logger.error(f"Error during rollback: {rollback_error}")
            logger.error(f"Error in connection context: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                    logger.debug(
                        f"Connection returned - Pool: size={self._engine.pool.size()}, "
                        f"checked_out={self._engine.pool.checkedout()}"
                    )
                except Exception as close_error:
                    logger.error(f"Error closing connection: {close_error}")


    def get_pool_status(self) -> dict:
        """
        Get current pool statistics for monitoring and debugging.
        
        Returns:
            dict: Pool status including size, checked_out connections, overflow, etc.
                 Returns {"status": "not_initialized"} if pool not ready.
        
        Example:
            status = db_pool.get_pool_status()
            if status['checked_out'] >= status['pool_size']:
                logger.warning("Pool exhausted!")
        """
        if not self._engine:
            return {"status": "not_initialized"}
        
        try:
            pool = self._engine.pool
            return {
                "status": "healthy",
                "pool_size": pool.size(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "max_overflow": pool._max_overflow,
                "timeout": pool._timeout,
            }
        except Exception as e:
            logger.error(f"Error getting pool status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


    def return_connection(self, conn):
        """
        Return a connection to the pool.
        
        DEPRECATED: Not needed when using get_connection_safe() context manager.
        This method is kept for backward compatibility during migration.
        
        Args:
            conn: Connection to return to pool
        """
        try:
            conn.close()
        except Exception as e:
            logger.error(f"Error returning connection: {e}")

    def close_all_connections(self):
        """
        Close all connections and clean up resources.
        Should be called during application shutdown.
        """
        try:
            if self._pool:
                self._pool.closeall()
                logger.info("psycopg2 pool closed")
            if self._engine:
                self._engine.dispose()
                logger.info("SQLAlchemy engine disposed")
            if self._connector:
                self._connector.close()
                logger.info("Cloud SQL connector closed")
            logger.info("All connections closed successfully")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")
        finally:
            self._pool = None
            self._engine = None
            self._connector = None

db_pool = DatabaseConnectionPool()