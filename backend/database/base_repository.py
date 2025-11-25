"""
Base Repository with common CRUD operations
All other repositories inherit from this
"""
import logging
from typing import Optional, List, Dict, Any, Type, TypeVar
from sqlmodel import SQLModel
from sqlalchemy import text
from .connection import db_pool

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=SQLModel)


class BaseRepository:
    """Base repository with generic CRUD operations"""
    
    def __init__(self, model: Type[T]):
        """
        Initialize repository with a SQLModel class
        
        Args:
            model: SQLModel class (e.g., ProposedClaim, User)
        """
        self.model = model
        self.table_name = model.__tablename__
        logger.info(f"[BaseRepository] Initialized for table: {self.table_name}")
    
    def create(self, obj: T | Dict[str, Any]) -> T:
        """Create a new record from a model instance or dictionary"""
        try:
            with db_pool.get_connection_safe() as conn:
                # Convert to dict if it's a model instance, otherwise use dict as-is
                if isinstance(obj, dict):
                    data = obj
                else:
                    data = obj.model_dump(exclude_unset=True)
                    # Ensure timestamp fields are set if required by the model
                    from datetime import datetime
                    current_time = datetime.utcnow()
                    
                    if 'created_at' in self.model.__fields__ and ('created_at' not in data or data['created_at'] is None):
                        data['created_at'] = current_time
                    
                    if 'updated_at' in self.model.__fields__ and ('updated_at' not in data or data['updated_at'] is None):
                        data['updated_at'] = current_time
                
                columns = ', '.join(data.keys())
                placeholders = ', '.join([f":{key}" for key in data.keys()])
                
                query = text(f"""
                    INSERT INTO "{self.table_name}" ({columns})
                    VALUES ({placeholders})
                    RETURNING *
                """)
                
                result = conn.execute(query, data)
                conn.commit()
                row = result.fetchone()
                
                logger.info(f"[{self.table_name}] Created record")
                return self.model.model_validate(dict(row._mapping))
                
        except Exception as e:
            logger.error(f"[{self.table_name}] Create error: {e}", exc_info=True)
            raise
    
    def get_by_id(self, id_value: Any, id_column: str = None) -> Optional[T]:
        """Get record by primary key"""
        try:
            if not id_column:
                # Get primary key column name from model
                id_column = list(self.model.__table__.primary_key.columns.keys())[0]
            
            with db_pool.get_connection_safe() as conn:
                query = text(f'SELECT * FROM "{self.table_name}" WHERE {id_column} = :id')
                result = conn.execute(query, {"id": id_value})
                row = result.fetchone()
                
                if row:
                    return self.model.model_validate(dict(row._mapping))
                return None
                
        except Exception as e:
            logger.error(f"[{self.table_name}] Get by ID error: {e}", exc_info=True)
            raise
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all records with pagination"""
        try:
            with db_pool.get_connection_safe() as conn:
                query = text(f"""
                    SELECT * FROM "{self.table_name}"
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """)
                result = conn.execute(query, {"limit": limit, "offset": offset})
                
                return [self.model.model_validate(dict(row._mapping)) for row in result]
                
        except Exception as e:
            logger.error(f"[{self.table_name}] Get all error: {e}", exc_info=True)
            raise
    
    def update(self, id_value: Any, updates: Dict[str, Any], id_column: str = None) -> Optional[T]:
        """Update a record"""
        try:
            if not id_column:
                id_column = list(self.model.__table__.primary_key.columns.keys())[0]
            
            if not updates:
                return self.get_by_id(id_value, id_column)
            
            # Auto-set updated_at if the model has it and it's not explicitly provided
            if 'updated_at' in self.model.__fields__ and 'updated_at' not in updates:
                from datetime import datetime
                updates['updated_at'] = datetime.utcnow()
            
            with db_pool.get_connection_safe() as conn:
                set_clause = ', '.join([f"{key} = :{key}" for key in updates.keys()])
                query = text(f"""
                    UPDATE "{self.table_name}"
                    SET {set_clause}
                    WHERE {id_column} = :id
                    RETURNING *
                """)
                
                params = {**updates, "id": id_value}
                result = conn.execute(query, params)
                conn.commit()
                row = result.fetchone()
                
                if row:
                    logger.info(f"[{self.table_name}] Updated record {id_value}")
                    return self.model.model_validate(dict(row._mapping))
                return None
                
        except Exception as e:
            logger.error(f"[{self.table_name}] Update error: {e}", exc_info=True)
            raise
    
    def delete(self, id_value: Any, id_column: str = None) -> bool:
        """Delete a record"""
        try:
            if not id_column:
                id_column = list(self.model.__table__.primary_key.columns.keys())[0]
            
            with db_pool.get_connection_safe() as conn:
                query = text(f'DELETE FROM "{self.table_name}" WHERE {id_column} = :id')
                result = conn.execute(query, {"id": id_value})
                conn.commit()
                
                deleted = result.rowcount > 0
                if deleted:
                    logger.info(f"[{self.table_name}] Deleted record {id_value}")
                return deleted
                
        except Exception as e:
            logger.error(f"[{self.table_name}] Delete error: {e}", exc_info=True)
            raise
    
    def count(self) -> int:
        """Count total records"""
        try:
            with db_pool.get_connection_safe() as conn:
                query = text(f'SELECT COUNT(*) FROM "{self.table_name}"')
                result = conn.execute(query)
                return result.scalar()
                
        except Exception as e:
            logger.error(f"[{self.table_name}] Count error: {e}", exc_info=True)
            raise
