"""
Custom exception hierarchy for TaskFlow.

Usage in services:
    from app.utils.exceptions import NotFoundError, DuplicateNameError
    raise NotFoundError("Task", task_id)

Usage in views (catching):
    from app.utils.exceptions import TaskFlowError
    except TaskFlowError as e:
        show_snack(page, str(e), error=True)
"""


class TaskFlowError(Exception):
    """Base exception for all TaskFlow domain errors."""


class NotFoundError(TaskFlowError):
    """Raised when a requested entity does not exist in the database."""
    def __init__(self, entity: str, entity_id: int):
        super().__init__(f"ไม่พบ {entity} (id={entity_id})")
        self.entity = entity
        self.entity_id = entity_id


class DuplicateNameError(TaskFlowError):
    """Raised when a unique name constraint would be violated."""
    def __init__(self, entity: str, name: str):
        super().__init__(f"{entity} ชื่อ '{name}' มีอยู่แล้ว")
        self.entity = entity
        self.name = name


class CircularDependencyError(TaskFlowError):
    """Raised when a task dependency would create a cycle."""
    def __init__(self, task_id: int, depends_on_id: int):
        super().__init__(
            f"การอ้างอิง Task #{depends_on_id} จาก Task #{task_id} "
            f"จะทำให้เกิด circular dependency"
        )
        self.task_id = task_id
        self.depends_on_id = depends_on_id


class SelfDependencyError(TaskFlowError):
    """Raised when a task tries to depend on itself."""
    def __init__(self, task_id: int):
        super().__init__(f"Task #{task_id} ไม่สามารถอ้างอิงตัวเองได้")
        self.task_id = task_id


class ValidationError(TaskFlowError):
    """Raised when input data fails business-rule validation."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
