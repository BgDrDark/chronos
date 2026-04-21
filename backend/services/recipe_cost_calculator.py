"""
Recipe Cost Calculator Service

Изчислява себестойността на рецепти на база използваните продукти.
"""
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from backend.database.models import Recipe, RecipeSection, RecipeIngredient


class RecipeCostCalculator:
    """Калкулатор за себестойност на рецепти"""
    
    @staticmethod
    async def get_latest_batch_price(db: "AsyncSession", ingredient_id: int) -> Optional[Decimal]:
        """Взема цената на най-новата активна партида за даден продукт.
        
        Приоритет:
        1. Цена от InvoiceItem (ако партидата е свързана с фактура)
        2. Цена на партидата (price_no_vat/price_with_vat)
        3. ingredient.current_price
        """
        from sqlalchemy import select, desc
        from backend.database.models import Batch, InvoiceItem
        
        # Първо провери партидата и InvoiceItem заедно
        stmt = (
            select(Batch, InvoiceItem)
            .outerjoin(InvoiceItem, InvoiceItem.batch_id == Batch.id)
            .where(
                Batch.ingredient_id == ingredient_id,
                Batch.status == "active",
                Batch.quantity > 0
            )
            .order_by(desc(Batch.received_at))
            .limit(1)
        )
        result = await db.execute(stmt)
        row = result.first()
        
        if row:
            batch, invoice_item = row
            
            # Приоритет 1: InvoiceItem.unit_price
            if invoice_item and invoice_item.unit_price:
                return Decimal(str(invoice_item.unit_price))
            
            # Приоритет 2: batch.price_no_vat
            if batch.price_no_vat:
                return Decimal(str(batch.price_no_vat))
            
            # Приоритет 3: batch.price_with_vat
            if batch.price_with_vat:
                return Decimal(str(batch.price_with_vat))
        
        return None
    
    @staticmethod
    async def calculate_recipe_cost(db: "AsyncSession", recipe_id: int) -> Decimal:
        """
        Изчислява себестойността на рецепта
        
        Формула:
            себестойност = Σ (количество_neto × единична цена от партида)
        
        За всяка съставка се взема цената от най-новата активна партида.
        Ако няма партида - използва се ingredient.current_price.
        
        Args:
            db: Database session (async)
            recipe_id: ID на рецептата
            
        Returns:
            Обща себестойност на рецептата
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from backend.database.models import Recipe, RecipeSection, RecipeIngredient
        
        stmt = (
            select(Recipe)
            .where(Recipe.id == recipe_id)
            .options(
                selectinload(Recipe.sections)
                .selectinload(RecipeSection.ingredients)
                .selectinload(RecipeIngredient.ingredient)
            )
        )
        result = await db.execute(stmt)
        recipe = result.scalar_one_or_none()
        
        if not recipe:
            raise ValueError("Рецептата не е намерена")
        
        total_cost = Decimal("0")
        
        for section in recipe.sections:
            section_cost = Decimal("0")
            
            for ri in section.ingredients:
                if not ri.ingredient_id:
                    continue
                
                # Вземи цена от най-новата партида
                price = await RecipeCostCalculator.get_latest_batch_price(db, ri.ingredient_id)
                
                # Ако няма партида с цена, използвай ingredient.current_price
                if price is None:
                    if ri.ingredient and ri.ingredient.current_price:
                        price = Decimal(str(ri.ingredient.current_price))
                    else:
                        continue  # Пропуска съставката ако няма цена
                
                gross_qty = Decimal(str(ri.quantity_gross or 0))
                
                # Рецептата винаги съхранява в грамове (g) или милилитри (ml)
                # Цените са на килограм (kg) или литър (l)
                # Винаги конвертираме: g→kg и ml→l
                unit = ri.ingredient.unit.lower() if ri.ingredient and ri.ingredient.unit else 'kg'
                if unit in ['g', 'gr', 'gram', 'grams', 'бр', 'брой', 'pcs', 'piece']:
                    # Бройки - не конвертираме
                    pass
                elif unit in ['ml', 'milliliter', 'milliliters', 'мл']:
                    gross_qty = gross_qty / Decimal("1000")  # ml → l
                else:
                    # kg, l и други - конвертираме от g/ml към kg/l
                    gross_qty = gross_qty / Decimal("1000")
                
                waste_pct = Decimal(str(ri.waste_percentage or section.waste_percentage or 0))
                net_qty = gross_qty * (1 - waste_pct / 100)
                
                cost = net_qty * price
                section_cost += cost
            
            total_cost += section_cost
        
        return total_cost
    
    @staticmethod
    def calculate_final_price(
        cost_price: Decimal,
        markup_percentage: Optional[Decimal] = None,
        premium_amount: Optional[Decimal] = None
    ) -> Decimal:
        """
        Изчислява крайната продажна цена
        
        Формула:
            продажна = себестойност + марж + надценка
            
        Ако markup_percentage е 0 или None:
            продажна = себестойност + надценка
            
        Args:
            cost_price: Себестойност
            markup_percentage: Марж % (по подразбиране 0)
            premium_amount: Надценка в лв (по подразбиране 0)
            
        Returns:
            Крайна продажна цена
        """
        markup = Decimal("0")
        if markup_percentage and markup_percentage > 0:
            markup = cost_price * markup_percentage / 100
        
        premium = premium_amount if premium_amount else Decimal("0")
        
        return cost_price + markup + premium
    
    @staticmethod
    def calculate_markup_amount(
        cost_price: Decimal,
        markup_percentage: Optional[Decimal] = None
    ) -> Decimal:
        """
        Изчислява стойността на маржа в лв
        
        Args:
            cost_price: Себестойност
            markup_percentage: Марж %
            
        Returns:
            Стойност на маржа в лв
        """
        if not markup_percentage or markup_percentage <= 0:
            return Decimal("0")
        
        return cost_price * markup_percentage / 100
