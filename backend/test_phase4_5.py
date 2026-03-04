import asyncio
from backend.database.database import AsyncSessionLocal
from backend.database.models import Ingredient, Recipe, ProductionOrder, ProductionTask, Batch, sofia_now
from sqlalchemy.future import select
from decimal import Decimal
import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_production_cycle():
    async with AsyncSessionLocal() as db:
        logger.info("--- СТАРТ НА ТЕСТ: ФАЗА 4 & 5 (ПРОИЗВОДСТВО) ---")
        
        # 1. Намиране на Рецепта и Съставка
        res_recipe = await db.execute(select(Recipe).filter(Recipe.name == "Торта Павлова"))
        recipe = res_recipe.scalars().first()
        res_ing = await db.execute(select(Ingredient).filter(Ingredient.name == "Сметана 35%"))
        ingredient = res_ing.scalars().first()

        # Проверка на начална наличност
        res_batch = await db.execute(select(Batch).where(Batch.ingredient_id == ingredient.id, Batch.status == "active"))
        initial_stock = sum((b.quantity for b in res_batch.scalars().all()), Decimal("0"))
        logger.info(f"Начална наличност на {ingredient.name}: {initial_stock} l")

        # 2. Създаване на Поръчка (за 2 торти)
        logger.info("2. Създаване на поръчка за 2 торти...")
        order = ProductionOrder(
            recipe_id=recipe.id,
            quantity=Decimal("2.0"),
            due_date=sofia_now() + datetime.timedelta(hours=5),
            company_id=1,
            status="awaiting_stock"
        )
        db.add(order)
        await db.flush()

        # Симулираме логиката от мутацията за проверка на наличност
        needed = Decimal("0.500") * order.quantity # 1.0 l
        if initial_stock >= needed:
            order.status = "ready"
            logger.info("✅ Складът е наличен. Статус на поръчката: READY")
        
        # Създаваме задача към поръчката
        task = ProductionTask(
            order_id=order.id,
            workstation_id=1, # Декорация
            name="Декориране на Павлова",
            status="pending"
        )
        db.add(task)
        await db.flush()

        # 3. Симулираме работа по задачата
        logger.info("3. Започване и завършване на задачата...")
        task.status = "in_progress"
        task.started_at = sofia_now()
        
        # Завършване и автоматично изписване на стока (Симулация на логиката в мутацията)
        task.status = "completed"
        task.completed_at = sofia_now()
        order.status = "completed"

        # FEFO изписване на стока
        needed_to_deduct = needed
        res_batches = await db.execute(
            select(Batch).where(Batch.ingredient_id == ingredient.id, Batch.status == "active").order_by(Batch.expiry_date.asc())
        )
        batches = res_batches.scalars().all()
        
        for b in batches:
            if needed_to_deduct <= 0: break
            if b.quantity >= needed_to_deduct:
                b.quantity -= needed_to_deduct
                needed_to_deduct = 0
            else:
                needed_to_deduct -= b.quantity
                b.quantity = 0
                b.status = "depleted"

        await db.commit()
        logger.info("✅ Поръчката е завършена и стоката е изписана.")

        # 4. Финална проверка на склада
        res_final_stock = await db.execute(select(Batch).where(Batch.ingredient_id == ingredient.id, Batch.status == "active"))
        final_stock = sum((b.quantity for b in res_final_stock.scalars().all()), Decimal("0"))
        
        expected_stock = initial_stock - needed
        if final_stock == expected_stock:
            logger.info(f"✅ УСПЕХ! Финална наличност: {final_stock} l (Изписани точно {needed} l)")
        else:
            logger.error(f"❌ ГРЕШКА! Очаквана наличност: {expected_stock}, Намерена: {final_stock}")

        logger.info("--- КРАЙ НА ТЕСТА (Фаза 4 & 5) ---")

if __name__ == "__main__":
    asyncio.run(test_production_cycle())
