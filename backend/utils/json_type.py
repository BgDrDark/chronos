import strawberry
from typing import Any


@strawberry.scalar
class JSONScalar:
    """Custom scalar for JSON data"""
    def serialize(self, value: Any) -> Any:
        return value
    
    def parse_value(self, value: Any) -> Any:
        return value
