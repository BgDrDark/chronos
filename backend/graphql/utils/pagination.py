import base64
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

import strawberry
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: str | None
    end_cursor: str | None


@strawberry.type
class Edge(Generic[T]):
    node: T
    cursor: str


@strawberry.type
class Connection(Generic[T]):
    edges: list[Edge[T]]
    page_info: PageInfo
    total_count: int


def encode_cursor(id: int) -> str:
    return base64.b64encode(f"cursor:{id}".encode()).decode()


def decode_cursor(cursor: str) -> int:
    decoded = base64.b64decode(cursor.encode()).decode()
    if not decoded.startswith("cursor:"):
        raise ValueError("Invalid cursor format")
    return int(decoded.split(":")[1])


async def paginate_cursor(
    query: Select,
    db: AsyncSession,
    model_class: Any,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
) -> tuple[list[Any], PageInfo, int]:
    limit = first or last or 20
    limit = min(limit, 100)

    count_query = select(func.count()).select_from(query.subquery())
    total_count = (await db.execute(count_query)).scalar() or 0

    if after:
        after_id = decode_cursor(after)
        query = query.where(model_class.id > after_id)

    if before:
        before_id = decode_cursor(before)
        query = query.where(model_class.id < before_id)

    query = query.order_by(model_class.id.asc())
    query = query.limit(limit + 1)

    result = await db.execute(query)
    items = list(result.scalars().all())

    has_next_page = len(items) > limit
    if has_next_page:
        items = items[:limit]

    has_previous_page = after is not None

    page_info = PageInfo(
        has_next_page=has_next_page,
        has_previous_page=has_previous_page,
        start_cursor=encode_cursor(items[0].id) if items else None,
        end_cursor=encode_cursor(items[-1].id) if items else None,
    )

    return items, page_info, total_count


_count_cache: dict[str, tuple[int, float]] = {}
COUNT_CACHE_TTL = 30


async def cached_count(
    db: AsyncSession,
    query: Select,
    cache_key: str,
    ttl: int = COUNT_CACHE_TTL,
) -> int:
    import time

    now = time.time()
    if cache_key in _count_cache:
        cached_value, cached_time = _count_cache[cache_key]
        if now - cached_time < ttl:
            return cached_value

    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    count = result.scalar() or 0

    _count_cache[cache_key] = (count, now)
    return count


def invalidate_count_cache(cache_key: str | None = None) -> None:
    global _count_cache
    if cache_key is None:
        _count_cache = {}
    elif cache_key in _count_cache:
        del _count_cache[cache_key]
