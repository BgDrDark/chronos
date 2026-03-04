import asyncio
from backend.database.database import AsyncSessionLocal
from backend.database.models import Supplier, StorageZone, Ingredient, Batch
from sqlalchemy.future import select
from decimal import Decimal
import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_warehouse_operations():
    async with AsyncSessionLocal() as db:
        logger.info("--- СТАРТ НА ТЕСТ: ФАЗА 2 (СКЛАД) ---")
        
        # 1. Създаване на Доставчик
        logger.info("1. Създаване на тестов доставчик...")
        supplier = Supplier(name="Млечна Дирекция ООД", eik="123456789", company_id=1)
        db.add(supplier)
        await db.flush()
        logger.info(f"✅ Доставчик създаден (ID: {supplier.id})")

        # 2. Създаване на Зона
        logger.info("2. Създаване на зона 'Хладилник'...")
        zone = StorageZone(name="Хладилник 1", temp_min=Decimal("2.0"), temp_max=Decimal("6.0"), company_id=1)
        db.add(zone)
        await db.flush()
        logger.info(f"✅ Зона създадена (ID: {zone.id})")

        # 3. Създаване на Съставка
        logger.info("3. Създаване на съставка 'Сметана 35%'...")
        ingredient = Ingredient(
            name="Сметана 35%", 
            unit="l", 
            barcode="3800012345678", 
            baseline_min_stock=Decimal("5.0"),
            storage_zone_id=zone.id,
            company_id=1
        )
        db.add(ingredient)
        await db.flush()
        logger.info(f"✅ Съставка създадена (ID: {ingredient.id})")

        # 4. Зачисляване на Партида (10 литра)
        logger.info("4. Зачисляване на 10 литра сметана...")
        expiry = datetime.date.today() + datetime.timedelta(days=7)
        batch = Batch(
            ingredient_id=ingredient.id,
            batch_number="LOT-2026-001",
            quantity=Decimal("10.0"),
            expiry_date=expiry,
            supplier_id=supplier.id,
            status="active"
        )
        db.add(batch)
        await db.flush()
        logger.info(f"✅ Партида зачислена (Expiry: {expiry})")

        # 5. Проверка на наличността
        logger.info("5. Проверка на текущата наличност чрез заявка...")
        stmt = select(Batch).where(Batch.ingredient_id == ingredient.id, Batch.status == "active")
        res = await db.execute(stmt)
        active_batches = res.scalars().all()
        total_stock = sum((b.quantity for b in active_batches), Decimal("0"))
        
        if total_stock == Decimal("10.0"):
            logger.info(f"✅ Тестът е успешен! Наличност: {total_stock} l")
        else:
            logger.error(f"❌ Грешка в наличността! Очаквано: 10.0, Намерено: {total_stock}")

        await db.commit()
        logger.info("--- КРАЙ НА ТЕСТА (Данните са записани) ---")

if __name__ == "__main__":
    asyncio.run(test_warehouse_operations())
