"""
BaseRepository — Abstract contract for all repositories in TaskFlow.

All concrete repositories inherit from this class.
Provides a standard interface that makes it easy to:
  - Swap storage backends (SQLite → PostgreSQL)
  - Mock repositories in tests
  - Enforce consistent method naming
"""

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository defining the minimum CRUD interface.

    Type parameter T is the SQLAlchemy model class.

    Concrete example:
        class TaskRepository(BaseRepository[Task]):
            def get_by_id(self, id: int) -> Optional[Task]: ...
    """

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """Retrieve a single entity by primary key. Returns None if not found."""
        ...

    @abstractmethod
    def get_all(self) -> List[T]:
        """Retrieve all entities, typically ordered by created_at DESC."""
        ...

    @abstractmethod
    def delete(self, id: int) -> bool:
        """
        Delete entity by primary key.
        Returns True if deleted, False if not found.
        """
        ...
