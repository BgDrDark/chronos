import asyncio
from backend.database.database import AsyncSessionLocal
from backend.database.models import Ingredient, Recipe, RecipeIngredient, RecipeStep, Workstation
from sqlalchemy.future import select
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_recipe_logic():
    async with AsyncSessionLocal() as db:
        logger.info("--- СТАРТ НА ТЕСТ: ФАЗА 3 (РЕЦЕПТУРНИК) ---")
        
        # 1. Намиране на съставка (от предния тест)
        result = await db.execute(select(Ingredient).filter(Ingredient.name == "Сметана 35%"))
        ingredient = result.scalars().first()
        if not ingredient:
            logger.info("Създаване на съставка за теста...")
            ingredient = Ingredient(name="Сметана 35%", unit="l", company_id=1)
            db.add(ingredient)
            await db.flush()

        # 2. Създаване на Работна станция
        logger.info("2. Създаване на работна станция 'Декорация'...")
        workstation = Workstation(name="Декорация", description="Място за сглобяване и украса", company_id=1)
        db.add(workstation)
        await db.flush()
        logger.info(f"✅ Станция създадена (ID: {workstation.id})")

        # 3. Създаване на Рецепта
        logger.info("3. Създаване на рецепта 'Торта Павлова'...")
        recipe = Recipe(
            name="Торта Павлова",
            yield_quantity=Decimal("1.0"),
            yield_unit="br",
            shelf_life_days=2,
            instructions="1. Разбийте сметаната. 2. Гарнирайте целувчения блат.",
            company_id=1
        )
        db.add(recipe)
        await db.flush()

        # 4. Добавяне на съставка към рецептата (с фира)
        logger.info("4. Добавяне на сметана към рецептата (Бруто vs Нето)...")
        recipe_ing = RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ingredient.id,
            quantity_gross=Decimal("0.500"), # вземаме 500 мл
            quantity_net=Decimal("0.450"),   # остават 450 мл след обработка
            waste_percentage=Decimal("10.0") # 10% фира
        )
        db.add(recipe_ing)

        # 5. Добавяне на производствена стъпка
        logger.info("5. Добавяне на производствена стъпка...")
        recipe_step = RecipeStep(
            recipe_id=recipe.id,
            workstation_id=workstation.id,
            name="Разбиване на сметана и декориране",
            step_order=1,
            estimated_duration_minutes=20
        )
        db.add(recipe_step)
        
        await db.commit()
        
        # Финална проверка
        logger.info(f"✅ Рецепта '{recipe.name}' е успешно създадена!")
        logger.info(f"📊 Анализ: Вложена съставка: {ingredient.name}, Фира: {recipe_ing.waste_percentage}%")
        
        logger.info("--- КРАЙ НА ТЕСТА (Фаза 3) ---")

if __name__ == "__main__":
    asyncio.run(test_recipe_logic())
