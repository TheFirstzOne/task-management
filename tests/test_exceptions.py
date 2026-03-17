"""
Tests for custom exception hierarchy.
"""

from app.utils.exceptions import (
    TaskFlowError, NotFoundError, DuplicateNameError,
    CircularDependencyError, SelfDependencyError, ValidationError,
)


def test_not_found_error_message():
    e = NotFoundError("Task", 42)
    assert "Task" in str(e)
    assert "42" in str(e)
    assert e.entity == "Task"
    assert e.id == 42


def test_duplicate_name_error_message():
    e = DuplicateNameError("ทีม", "Dev Team")
    assert "Dev Team" in str(e)
    assert e.name == "Dev Team"


def test_circular_dependency_error():
    e = CircularDependencyError(1, 2)
    assert e.task_id == 1
    assert e.depends_on_id == 2


def test_self_dependency_error():
    e = SelfDependencyError(5)
    assert e.task_id == 5
    assert "5" in str(e)


def test_all_inherit_from_taskflow_error():
    for exc_cls in [NotFoundError, DuplicateNameError,
                    CircularDependencyError, SelfDependencyError, ValidationError]:
        if exc_cls in (NotFoundError,):
            e = NotFoundError("X", 1)
        elif exc_cls in (DuplicateNameError,):
            e = DuplicateNameError("X", "y")
        elif exc_cls in (CircularDependencyError,):
            e = CircularDependencyError(1, 2)
        elif exc_cls in (SelfDependencyError,):
            e = SelfDependencyError(1)
        else:
            e = exc_cls("test")
        assert isinstance(e, TaskFlowError), f"{exc_cls} should inherit TaskFlowError"
