"""
Database module with connection pool and repositories
"""
from .connection import db_pool, DatabaseConnectionPool
from .base_repository import BaseRepository
from .claim_repository import claim_repository, ClaimRepository
from .user_repository import user_repository, UserRepository
from .hitl_repository import hitl_repository, HitlRepository
from .history_repository import history_repository, HistoryRepository

__all__ = [
    'db_pool',
    'DatabaseConnectionPool',
    'BaseRepository',
    'claim_repository',
    'ClaimRepository',
    'user_repository',
    'UserRepository',
    'hitl_repository',
    'HitlRepository',
    'history_repository',
    'HistoryRepository',
]
