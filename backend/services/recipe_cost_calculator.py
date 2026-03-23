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
    def calculate_recipe_cost(db: "AsyncSession", recipe_id: int) -> Decimal:
        """
        Изчислява себестойността на рецепта
        
        Формула:
            себестойност = Σ (количество_neto × единична цена)
        
        Args:
            db: Database session
            recipe_id: ID на рецептата
            
        Returns:
            Обща себестойност на рецептата
        """
        from sqlalchemy import select
        from backend.database.models import Recipe, RecipeSection, RecipeIngredient
        
        recipe = db.get(Recipe, recipe_id)
        if not recipe:
            raise ValueError("Рецептата не е намерена")
        
        total_cost = Decimal("0")
        
        for section in recipe.sections:
            section_cost = Decimal("0")
            
            for ri in section.ingredients:
                ingredient = ri.ingredient
                if not ingredient or not ingredient.current_price:
                    continue
                
                # Бруто количество
                gross_qty = Decimal(str(ri.quantity_gross or 0))
                
                # Нето количество (след фира)
                waste_pct = Decimal(str(section.waste_percentage or 0))
                net_qty = gross_qty * (1 - waste_pct / 100)
                
                # Цена за това количество
                cost = net_qty * Decimal(str(ingredient.current_price))
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
