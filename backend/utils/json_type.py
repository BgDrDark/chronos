import warnings

warnings.filterwarnings("ignore", message=".*strawberry.scalar.*")

from typing import Any

import strawberry


@strawberry.scalar
class JSONScalar:
    """Custom scalar for JSON data"""

    def serialize(self, value: Any) -> Any:
        return value

    def parse_value(self, value: Any) -> Any:
        return value


__all__ = ["JSONScalar"]
