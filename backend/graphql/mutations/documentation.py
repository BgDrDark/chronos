import strawberry
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import DocumentationCategory, DocumentationArticle, sofia_now
from backend.graphql.types.documentation import (
    DocumentationCategory as DocCategoryType,
    DocumentationArticle as DocArticleType,
    DocumentationCategoryInput,
    DocumentationArticleInput,
)


@strawberry.type
class DocumentationMutation:
    @strawberry.mutation
    async def create_documentation_category(
        self, info: strawberry.Info, input: DocumentationCategoryInput
    ) -> DocCategoryType:
        db: AsyncSession = info.context["db"]
        current_user = info.context["current_user"]
        
        if current_user.role.name != "super_admin":
            raise Exception("Само super_admin може да създава категории")
        
        category = DocumentationCategory(
            title=input.title,
            icon=input.icon,
            order=input.order,
            is_active=input.is_active,
            created_at=sofia_now(),
            updated_at=sofia_now(),
        )
        db.add(category)
        await db.commit()
        await db.refresh(category)
        
        return DocCategoryType(
            id=category.id,
            title=category.title,
            icon=category.icon,
            order=category.order,
            is_active=category.is_active,
            articles=None,
        )

    @strawberry.mutation
    async def update_documentation_category(
        self, info: strawberry.Info, id: int, input: DocumentationCategoryInput
    ) -> DocCategoryType:
        db: AsyncSession = info.context["db"]
        current_user = info.context["current_user"]
        
        if current_user.role.name != "super_admin":
            raise Exception("Само super_admin може да редактира категории")
        
        result = await db.execute(
            select(DocumentationCategory).where(DocumentationCategory.id == id)
        )
        category = result.scalar_one_or_none()
        
        if not category:
            raise Exception("Категорията не е намерена")
        
        category.title = input.title
        category.icon = input.icon
        category.order = input.order
        category.is_active = input.is_active
        category.updated_at = sofia_now()
        
        await db.commit()
        await db.refresh(category)
        
        return DocCategoryType(
            id=category.id,
            title=category.title,
            icon=category.icon,
            order=category.order,
            is_active=category.is_active,
            articles=None,
        )

    @strawberry.mutation
    async def delete_documentation_category(self, info: strawberry.Info, id: int) -> bool:
        db: AsyncSession = info.context["db"]
        current_user = info.context["current_user"]
        
        if current_user.role.name != "super_admin":
            raise Exception("Само super_admin може да изтрива категории")
        
        result = await db.execute(
            select(DocumentationCategory).where(DocumentationCategory.id == id)
        )
        category = result.scalar_one_or_none()
        
        if not category:
            raise Exception("Категорията не е намерена")
        
        await db.delete(category)
        await db.commit()
        
        return True

    @strawberry.mutation
    async def create_documentation_article(
        self, info: strawberry.Info, input: DocumentationArticleInput
    ) -> DocArticleType:
        db: AsyncSession = info.context["db"]
        current_user = info.context["current_user"]
        
        if current_user.role.name != "super_admin":
            raise Exception("Само super_admin може да създава статии")
        
        article = DocumentationArticle(
            category_id=input.category_id,
            title=input.title,
            content=input.content,
            order=input.order,
            is_active=input.is_active,
            created_by=current_user.id,
            created_at=sofia_now(),
            updated_at=sofia_now(),
        )
        db.add(article)
        await db.commit()
        await db.refresh(article)
        
        return DocArticleType(
            id=article.id,
            category_id=article.category_id,
            title=article.title,
            content=article.content,
            order=article.order,
            is_active=article.is_active,
            created_at=article.created_at.isoformat() if article.created_at else None,
            updated_at=article.updated_at.isoformat() if article.updated_at else None,
        )

    @strawberry.mutation
    async def update_documentation_article(
        self, info: strawberry.Info, id: int, input: DocumentationArticleInput
    ) -> DocArticleType:
        db: AsyncSession = info.context["db"]
        current_user = info.context["current_user"]
        
        if current_user.role.name != "super_admin":
            raise Exception("Само super_admin може да редактира статии")
        
        result = await db.execute(
            select(DocumentationArticle).where(DocumentationArticle.id == id)
        )
        article = result.scalar_one_or_none()
        
        if not article:
            raise Exception("Статията не е намерена")
        
        article.category_id = input.category_id
        article.title = input.title
        article.content = input.content
        article.order = input.order
        article.is_active = input.is_active
        article.updated_at = sofia_now()
        
        await db.commit()
        await db.refresh(article)
        
        return DocArticleType(
            id=article.id,
            category_id=article.category_id,
            title=article.title,
            content=article.content,
            order=article.order,
            is_active=article.is_active,
            created_at=article.created_at.isoformat() if article.created_at else None,
            updated_at=article.updated_at.isoformat() if article.updated_at else None,
        )

    @strawberry.mutation
    async def delete_documentation_article(self, info: strawberry.Info, id: int) -> bool:
        db: AsyncSession = info.context["db"]
        current_user = info.context["current_user"]
        
        if current_user.role.name != "super_admin":
            raise Exception("Само super_admin може да изтрива статии")
        
        result = await db.execute(
            select(DocumentationArticle).where(DocumentationArticle.id == id)
        )
        article = result.scalar_one_or_none()
        
        if not article:
            raise Exception("Статията не е намерена")
        
        await db.delete(article)
        await db.commit()
        
        return True
