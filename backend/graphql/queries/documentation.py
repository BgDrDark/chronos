import strawberry
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import DocumentationCategory, DocumentationArticle
from backend.graphql.types.documentation import DocumentationCategory as DocCategoryType, DocumentationArticle as DocArticleType


@strawberry.type
class DocumentationQuery:
    @strawberry.field
    async def documentation_categories(self, info: strawberry.Info) -> list[DocCategoryType]:
        db: AsyncSession = info.context["db"]
        result = await db.execute(
            select(DocumentationCategory).order_by(DocumentationCategory.order)
        )
        categories = result.scalars().all()
        
        output = []
        for cat in categories:
            articles_result = await db.execute(
                select(DocumentationArticle)
                .where(DocumentationArticle.category_id == cat.id)
                .order_by(DocumentationArticle.order)
            )
            articles = articles_result.scalars().all()
            
            output.append(DocCategoryType(
                id=cat.id,
                title=cat.title,
                icon=cat.icon,
                order=cat.order,
                is_active=cat.is_active,
                articles=[
                    DocArticleType(
                        id=art.id,
                        category_id=art.category_id,
                        title=art.title,
                        content=art.content,
                        order=art.order,
                        is_active=art.is_active,
                        created_at=art.created_at.isoformat() if art.created_at else None,
                        updated_at=art.updated_at.isoformat() if art.updated_at else None,
                    )
                    for art in articles
                ]
            ))
        
        return output

    @strawberry.field
    async def documentation_articles(self, info: strawberry.Info, category_id: int) -> list[DocArticleType]:
        db: AsyncSession = info.context["db"]
        result = await db.execute(
            select(DocumentationArticle)
            .where(DocumentationArticle.category_id == category_id)
            .order_by(DocumentationArticle.order)
        )
        articles = result.scalars().all()
        
        return [
            DocArticleType(
                id=art.id,
                category_id=art.category_id,
                title=art.title,
                content=art.content,
                order=art.order,
                is_active=art.is_active,
                created_at=art.created_at.isoformat() if art.created_at else None,
                updated_at=art.updated_at.isoformat() if art.updated_at else None,
            )
            for art in articles
        ]
