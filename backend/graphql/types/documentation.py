import strawberry
from strawberry.experimental import pydantic as sp
from backend import schemas


@strawberry.type
class DocumentationArticle:
    id: int
    category_id: int
    title: str
    content: str
    order: int
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None


@strawberry.type
class DocumentationCategory:
    id: int
    title: str
    icon: str
    order: int
    is_active: bool
    articles: list[DocumentationArticle] | None = None


@strawberry.input
class DocumentationCategoryInput:
    title: str
    icon: str = "folder"
    order: int = 0
    is_active: bool = True


@strawberry.input
class DocumentationArticleInput:
    category_id: int
    title: str
    content: str = ""
    order: int = 0
    is_active: bool = True
