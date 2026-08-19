from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar, cast

from sqlalchemy.orm import Session


P = ParamSpec("P")
R = TypeVar("R")


def transactional(method: Callable[P, R]) -> Callable[P, R]:
    """Commit or roll back the Session owned by a state-changing Usecase."""

    @wraps(method)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        if not args:
            raise TypeError("transactional Usecase methods require self")
        db = cast(Session, getattr(args[0], "db"))
        try:
            result = method(*args, **kwargs)
            db.commit()
        except Exception:
            db.rollback()
            raise
        return result

    return wrapped
