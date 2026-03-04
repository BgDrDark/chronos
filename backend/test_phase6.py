import asyncio
from backend.database.database import AsyncSessionLocal
from backend.database.models import ProductionOrder, Recipe, sofia_now
from sqlalchemy.future import select
import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_label_generation():
    async with AsyncSessionLocal() as db:
        logger.info("--- СТАРТ НА ТЕСТ: ФАЗА 6 (ЕТИКЕТИРАНЕ) ---")
        
        # 1. Намиране на последната завършена поръчка
        stmt = select(ProductionOrder).where(ProductionOrder.status == "completed").order_by(ProductionOrder.id.desc())
        res = await db.execute(stmt)
        order = res.scalars().first()
        
        if not order:
            logger.error("❌ Не е намерена завършена поръчка! Първо изпълнете тест 4_5.")
            return

        # 2. Симулиране на логиката на GenerateLabel Query
        recipe = await db.get(Recipe, order.recipe_id)
        now = sofia_now()
        
        # Калкулация на срок на годност
        expiry_date = now.date() + datetime.timedelta(days=recipe.shelf_life_days)
        
        # Генериране на партиден номер
        batch_num = f"PRD-{order.id}-{now.strftime('%y%m%d')}"
        
        # Данни за етикета
        label_data = {
            "product_name": recipe.name,
            "batch_number": batch_num,
            "production_date": now,
            "expiry_date": expiry_date,
            "quantity": f"{order.quantity} {recipe.yield_unit}",
            "qr_content": f"BATCH:{batch_num}|PROD:{recipe.name}"
        }

        logger.info(f"📋 Генериран етикет за: {label_data['product_name']}")
        logger.info(f"🔢 Партиден номер: {label_data['batch_number']}")
        logger.info(f"📅 Произведено на: {label_data['production_date'].strftime('%d.%m.%Y %H:%M')}")
        logger.info(f"🛑 Годно до: {label_data['expiry_date'].strftime('%d.%m.%Y')}")
        logger.info(f"⚖️ Количество: {label_data['quantity']}")
        logger.info(f"📱 QR Код съдържание: {label_data['qr_content']}")

        # 3. Валидация
        errors = []
        if label_data['expiry_date'] != now.date() + datetime.timedelta(days=2):
            errors.append("Неправилно изчислен срок на годност!")
        
        if not label_data['batch_number'].startswith(f"PRD-{order.id}"):
            errors.append("Неправилен формат на партидния номер!")

        if not errors:
            logger.info("✅ Тестът на етикетирането е успешен!")
        else:
            for err in errors:
                logger.error(f"❌ {err}")

        logger.info("--- КРАЙ НА ТЕСТА (Фаза 6) ---")

if __name__ == "__main__":
    asyncio.run(test_label_generation())
