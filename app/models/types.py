"""Custom SQLAlchemy column types for Postgres geo/vector columns.

``PointType`` maps a Python ``(lat, lng)`` tuple onto the native Postgres
``point`` (x = lng, y = lat by Postgres convention) so the API stays in
(lat, lng) everywhere. ``VectorType`` maps a ``list[float]`` onto a
pgvector ``vector`` column.
"""
from typing import Any, Optional

# pyrefly: ignore [missing-import]
from sqlalchemy.types import UserDefinedType


class PointType(UserDefinedType):
    """Postgres ``point`` as a ``(lat, lng)`` tuple."""

    cache_ok = True

    def get_col_spec(self, **kw: Any) -> str:
        return "POINT"

    def bind_processor(self, dialect):
        def process(value: Optional[tuple]) -> Optional[str]:
            if value is None:
                return None
            lat, lng = value
            return f"({lng},{lat})"

        return process

    def result_processor(self, dialect, coltype):
        def process(value: Any) -> Optional[tuple]:
            if value is None:
                return None
            if isinstance(value, (tuple, list)):
                x, y = value
                return (float(y), float(x))
            if isinstance(value, str):
                inner = value.strip("()")
                x, y = inner.split(",")
                return (float(y), float(x))
            return value

        return process


class VectorType(UserDefinedType):
    """pgvector ``vector`` column of fixed dimension."""

    cache_ok = True

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def get_col_spec(self, **kw: Any) -> str:
        return f"VECTOR({self.dim})"

    def bind_processor(self, dialect):
        def process(value: Optional[list]) -> Optional[str]:
            if value is None:
                return None
            return "[" + ",".join(repr(float(v)) for v in value) + "]"

        return process

    def result_processor(self, dialect, coltype):
        def process(value: Any) -> Optional[list]:
            if value is None:
                return None
            if isinstance(value, (list, tuple)):
                return [float(v) for v in value]
            if isinstance(value, str):
                inner = value.strip("[]")
                if not inner:
                    return []
                return [float(v) for v in inner.split(",")]
            return value

        return process
