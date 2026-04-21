import asyncio
import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func

from backend.database.database import AsyncSessionLocal
from backend.database.models import (
    Company, User, Role, Department, Position,
    StorageZone, Supplier, Ingredient, Batch,
    Shift, WorkSchedule, Payroll, Workstation,
    Invoice, InvoiceItem,
    Recipe, RecipeSection, RecipeIngredient, RecipeStep
)


async def get_unique_email(base_email: str, db) -> str:
    """Проверява дали имейлът съществува и връща уникален"""
    result = await db.execute(select(User.email).where(User.email == base_email))
    if not result.scalar_one_or_none():
        return base_email
    
    counter = 2
    while True:
        new_email = base_email.replace("@", f"{counter}@")
        result = await db.execute(select(User.email).where(User.email == new_email))
        if not result.scalar_one_or_none():
            return new_email
        counter += 1


async def get_unique_username(base_username: str, db) -> str:
    """Проверява дали потребителското име съществува и връща уникално"""
    result = await db.execute(select(User.username).where(User.username == base_username))
    if not result.scalar_one_or_none():
        return base_username
    
    counter = 2
    while True:
        new_username = f"{base_username}_{counter}"
        result = await db.execute(select(User.username).where(User.username == new_username))
        if not result.scalar_one_or_none():
            return new_username
        counter += 1


async def get_unique_barcode(base_barcode: str, db) -> str:
    """Проверява дали баркод съществува и връща уникален"""
    result = await db.execute(select(Ingredient.barcode).where(Ingredient.barcode == base_barcode))
    if not result.scalar_one_or_none():
        return base_barcode
    
    counter = 2
    while True:
        new_barcode = f"{base_barcode[:-3]}{int(base_barcode[-3:]) + counter:03d}"
        result = await db.execute(select(Ingredient.barcode).where(Ingredient.barcode == new_barcode))
        if not result.scalar_one_or_none():
            return new_barcode
        counter += 1


async def get_unique_invoice_number(base_number: str, db) -> str:
    """Проверява дали номер на фактура/разписка съществува и връща уникален"""
    result = await db.execute(select(Invoice.number).where(Invoice.number == base_number))
    if not result.scalar_one_or_none():
        return base_number
    
    counter = 2
    while True:
        parts = base_number.rsplit('-', 1)
        if len(parts) == 2:
            new_number = f"{parts[0]}-{counter:04d}"
        else:
            new_number = f"{base_number}-{counter:04d}"
        result = await db.execute(select(Invoice.number).where(Invoice.number == new_number))
        if not result.scalar_one_or_none():
            return new_number
        counter += 1


async def seed_all():
    print("=" * 60)
    print("ЗАРЕЖДАНЕ НА ТЕСТОВИ ДАННИ")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        try:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
            hashed_password = pwd_context.hash("password123")

            result = await db.execute(select(Role))
            all_roles = result.scalars().all()
            
            result = await db.execute(select(Company))
            all_companies = result.scalars().all()
            
            print(f"✓ Роли: {len(all_roles)}")
            print(f"✓ Фирми: {len(all_companies)}")

            result = await db.execute(select(Department).where(Department.company_id == all_companies[0].id))
            departments = result.scalars().all()
            if len(departments) < 3:
                for name in ["Производство", "Склад", "Продажби"]:
                    dept = Department(name=name, company_id=all_companies[0].id)
                    db.add(dept)
                await db.flush()
            result = await db.execute(select(Department).where(Department.company_id == all_companies[0].id))
            departments = result.scalars().all()
            print(f"✓ Отдели: {len(departments)}")

            # Създаваме длъжности за всеки отдел
            positions_by_dept = {
                "Производство": ["Готвач", "Помощник-готвач", "Технолог", "Началник производство", "Опаковчик"],
                "Склад": ["Складов работник", "Кладовник", "Началник склад", "Шофьор", "Комплектовчик"],
                "Продажби": ["Продавач", "Касиер", "Търговски представител", "Мениджър продажби", "Оперативен мениджър"],
            }
            
            for dept in departments:
                result = await db.execute(select(Position).where(Position.department_id == dept.id))
                existing_positions = result.scalars().all()
                if len(existing_positions) < 3:
                    for pos_title in positions_by_dept.get(dept.name, []):
                        pos = Position(title=pos_title, department_id=dept.id)
                        db.add(pos)
                    await db.flush()
            
            result = await db.execute(select(Position).where(Position.department_id.in_([d.id for d in departments])))
            all_positions = result.scalars().all()
            print(f"✓ Длъжности: {len(all_positions)}")

            result = await db.execute(select(StorageZone).where(StorageZone.company_id == all_companies[0].id))
            zones = result.scalars().all()
            if len(zones) < 4:
                zones_data = [
                    {"name": "Хладилна стая (+2°C до +6°C)", "temp_min": Decimal("2"), "temp_max": Decimal("6"), 
                     "description": "За бързоразвалящи се продукти", "zone_type": "food", "asset_type": "KMA"},
                    {"name": "Морозилна стая (-18°C)", "temp_min": Decimal("-20"), "temp_max": Decimal("-18"), 
                     "description": "За замразени продукти", "zone_type": "food", "asset_type": "KMA"},
                    {"name": "Сух склад (15-20°C)", "temp_min": Decimal("15"), "temp_max": Decimal("20"), 
                     "description": "За брашно, захар, консерви", "zone_type": "food", "asset_type": "KMA"},
                    {"name": "Зона за алергени", "temp_min": Decimal("15"), "temp_max": Decimal("25"), 
                     "description": "Отделна зона за продукти с алергени", "zone_type": "food", "asset_type": "KMA"},
                ]
                for data in zones_data:
                    zone = StorageZone(company_id=all_companies[0].id, **data)
                    db.add(zone)
                await db.flush()
            result = await db.execute(select(StorageZone).where(StorageZone.company_id == all_companies[0].id))
            zones = result.scalars().all()
            print(f"✓ Складови зони: {len(zones)}")

            result = await db.execute(select(Supplier))
            all_suppliers = result.scalars().all()
            existing_eiks = [s.eik for s in all_suppliers if s.eik]
            
            suppliers_data = [
                {"name": "Млечна компания АД", "eik": "111111111", "vat_number": "BG1111111111", 
                 "address": "Млечна ферма", "contact_person": "Драган Драганов", 
                 "phone": "+359321123456", "email": "office@mlekna.bg"},
                {"name": "Зърнопроизводител ООД", "eik": "222222222", "vat_number": "BG2222222222", 
                 "address": "Пшенична борса", "contact_person": "Кръстьо Кръстев", 
                 "phone": "+359321234567", "email": "grain@zarno.bg"},
                {"name": "Шоколадова къща ГмбХ", "eik": "DE999999999", "vat_number": "DE999999999", 
                 "address": "Lindt Strasse", "contact_person": "Hans Mueller", 
                 "phone": "+4989123456", "email": "sales@lindt.de"},
            ]
            for data in suppliers_data:
                if data["eik"] not in existing_eiks:
                    supplier = Supplier(company_id=all_companies[0].id, **data)
                    db.add(supplier)
            await db.flush()
            result = await db.execute(select(Supplier).where(Supplier.company_id == all_companies[0].id))
            suppliers = result.scalars().all()
            print(f"✓ Доставчици: {len(all_suppliers)}")

            ingredient_names_raw = [
                ("Брашно тип 500", "kg", "raw"), ("Захар кристална", "kg", "raw"), ("Яйца (клас А)", "br", "raw"),
                ("Прясно мляко 3.5%", "l", "raw"), ("Краве масло 82%", "kg", "raw"),
                ("Черпуков шоколад (млечен)", "kg", "raw"), ("Ванилия (екстракт)", "l", "raw"),
                ("Бакпулвер", "kg", "raw"), ("Сол", "kg", "raw"), ("Олио (слънчогледово)", "l", "raw"),
                ("Пудра захар", "kg", "raw"), ("Какао прах", "kg", "raw"),
                ("Заготовка - сметанов крем", "kg", "semi_finished"), ("Заготовка - шоколадов блат", "kg", "semi_finished"),
                ("Торта Шоколадова", "br", "finished"), ("Торта Плодова", "br", "finished"),
                # Нови артикули за рецептите
                ("Сметана течна 35%", "l", "raw"), ("Кокосови стърготини", "kg", "raw"),
                ("Лешници (смлени)", "kg", "raw"), ("Желатин", "kg", "raw"),
                ("Лимонов сок", "l", "raw"), ("Плодов микс (ягоди, малини)", "kg", "raw"),
                ("Готова блатова смес", "kg", "semi_finished"),
                ("Крема сирене", "kg", "raw"),
            ]
            
            all_allergens = [[], ["gluten"], ["milk"], ["eggs"], ["soy"], ["gluten", "milk"], ["milk", "soy"], ["gluten", "milk", "eggs"]]
            
            result = await db.execute(select(Ingredient))
            existing_ingredients = result.scalars().all()
            existing_barcodes = [i.barcode for i in existing_ingredients if i.barcode]
            
            ingredients_created = 0
            target_ingredients = 100
            current_count = len(existing_ingredients)
            
            print(f"  Има {current_count} артикула, добавям до {target_ingredients}...")
            
            for i in range(current_count, target_ingredients):
                name_idx = i % len(ingredient_names_raw)
                name, unit, ptype = ingredient_names_raw[name_idx]
                
                if i >= len(ingredient_names_raw):
                    name = f"{name} {i // len(ingredient_names_raw) + 1}"
                
                barcode = await get_unique_barcode(f"380001{1000 + i:04d}", db)
                
                allergen_idx = i % len(all_allergens)
                is_perishable = ptype in ["raw", "semi_finished", "finished"]
                
                ing = Ingredient(
                    name=name,
                    unit=unit,
                    barcode=barcode,
                    baseline_min_stock=Decimal("10"),
                    current_price=Decimal(str(1 + (i % 50))),
                    storage_zone_id=zones[i % len(zones)].id,
                    is_perishable=is_perishable,
                    expiry_warning_days=7 if is_perishable else 30,
                    product_type=ptype,
                    allergens=all_allergens[allergen_idx],
                    company_id=all_companies[0].id
                )
                db.add(ing)
                ingredients_created += 1
                
                if (i + 1) % 20 == 0:
                    await db.flush()
            
            await db.flush()
            result = await db.execute(select(Ingredient))
            all_ingredients = result.scalars().all()
            print(f"✓ Артикули: {len(all_ingredients)}")

            today = date.today()
            result = await db.execute(select(Batch))
            existing_batches = result.scalars().all()
            
            batch_ingredient_ids = {b.ingredient_id for b in existing_batches}
            
            batches_created = 0
            for i, ingredient in enumerate(all_ingredients):
                if ingredient.id in batch_ingredient_ids:
                    continue
                
                invoice_num = await get_unique_invoice_number(f"СР-2026-{1000+i:04d}", db)
                
                batch = Batch(
                    ingredient_id=ingredient.id,
                    batch_number=f"BATCH-2026-{1000+i:04d}",
                    quantity=Decimal(str(20 + (i % 80))),
                    unit_value=Decimal("1"),
                    production_date=today - timedelta(days=30 + i),
                    expiry_date=today + timedelta(days=365 - i * 3),
                    price_no_vat=Decimal(str(ingredient.current_price or 10)) * Decimal("20"),
                    vat_percent=Decimal("20"),
                    price_with_vat=Decimal(str(ingredient.current_price or 10)) * Decimal("20") * Decimal("1.2"),
                    supplier_id=suppliers[i % len(suppliers)].id if suppliers else None,
                    storage_zone_id=ingredient.storage_zone_id,
                    received_by=None,
                    is_stock_receipt=True,
                    invoice_number=invoice_num,
                    invoice_date=today - timedelta(days=30 + i),
                    status="active"
                )
                db.add(batch)
                batches_created += 1
                
                if batches_created % 20 == 0:
                    await db.flush()
            
            await db.flush()
            result = await db.execute(select(Batch))
            all_batches = result.scalars().all()
            print(f"✓ Партиди (стока): {batches_created} нови (общо {len(all_batches)})")

            print("  Създавам фактури за склада...")
            invoices_created = 0
            result = await db.execute(select(Invoice))
            existing_invoices = result.scalars().all()
            existing_invoice_numbers = {inv.number for inv in existing_invoices}
            
            for batch in all_batches:
                if batch.invoice_number and batch.invoice_number not in existing_invoice_numbers:
                    result = await db.execute(select(Ingredient).where(Ingredient.id == batch.ingredient_id))
                    ingredient = result.scalar_one_or_none()
                    
                    result = await db.execute(select(Supplier).where(Supplier.id == batch.supplier_id))
                    supplier = result.scalar_one_or_none()
                    
                    result = await db.execute(select(StorageZone).where(StorageZone.id == batch.storage_zone_id))
                    storage_zone = result.scalar_one_or_none()
                    
                    company_id = storage_zone.company_id if storage_zone else all_companies[0].id
                    
                    payment_methods = ["Банков превод", "В брой", "Карта"]
                    payment_method = payment_methods[i % len(payment_methods)]
                    
                    delivery_methods = ["Доставка до адрес", "Взимане от склад", "Куриер", "Еконт", "Спиди"]
                    delivery_method = delivery_methods[i % len(delivery_methods)]
                    
                    invoice = Invoice(
                        number=batch.invoice_number,
                        type="incoming",
                        document_type="ФАКТУРА",
                        griff="ОРИГИНАЛ",
                        description="Доставка на хранителни продукти",
                        date=batch.invoice_date or date.today(),
                        supplier_id=batch.supplier_id,
                        batch_id=batch.id,
                        subtotal=batch.price_no_vat or Decimal("0"),
                        vat_rate=batch.vat_percent or Decimal("20"),
                        vat_amount=(batch.price_no_vat or Decimal("0")) * (batch.vat_percent or Decimal("20")) / Decimal("100"),
                        total=batch.price_with_vat or Decimal("0"),
                        payment_method=payment_method,
                        delivery_method=delivery_method,
                        status="paid",
                        company_id=company_id,
                        created_by=None
                    )
                    db.add(invoice)
                    await db.flush()
                    invoices_created += 1
                    
                    if ingredient and invoice.id:
                        invoice_item = InvoiceItem(
                            invoice_id=invoice.id,
                            ingredient_id=ingredient.id,
                            batch_id=batch.id,
                            name=ingredient.name,
                            quantity=batch.quantity,
                            unit=ingredient.unit,
                            unit_price=ingredient.current_price or Decimal("1"),
                            total=batch.price_with_vat or Decimal("0")
                        )
                        db.add(invoice_item)
                    
                    existing_invoice_numbers.add(batch.invoice_number)
                    
                    if invoices_created % 20 == 0:
                        await db.flush()
            
            await db.flush()
            result = await db.execute(select(Invoice))
            all_invoices = result.scalars().all()
            print(f"✓ Фактури (счетоводство): {len(all_invoices)}")

            ws1 = await db.execute(select(Workstation).where(
                Workstation.name == "Пекарна", 
                Workstation.company_id == all_companies[0].id
            ))
            if not ws1.scalar_one_or_none():
                # Използваме станциите от init_db.py
                for ws_name, ws_desc in [
                    ("Пекарна", "Изпичане на блатове и основи"),
                    ("Кремове", "Приготвяне на кремове и пълнежи"),
                    ("Декорация", "Украса на готовите изделия"),
                ]:
                    ws = Workstation(name=ws_name, description=ws_desc, company_id=all_companies[0].id)
                    db.add(ws)
                await db.flush()
            
            # Взимаме станциите за рецептите
            result = await db.execute(select(Workstation).where(Workstation.company_id == all_companies[0].id))
            workstations = {ws.name: ws for ws in result.scalars().all()}
            print(f"✓ Работни станции: {len(workstations)}")

            # ============== СЪЗДАВАНЕ НА РЕЦЕПТИ ==============
            print("  Създавам рецепти за торти...")
            
            # Взимаме всички артикули за рецептите
            result = await db.execute(select(Ingredient))
            all_ingredients_db = result.scalars().all()
            ingredients_by_name = {ing.name: ing for ing in all_ingredients_db}
            
            recipes_data = [
                {
                    "name": "Торта Шоколадова",
                    "category": "Торти",
                    "description": " класическа шоколадова торта с крем от черен шоколад",
                    "yield_quantity": Decimal("2.5"),
                    "yield_unit": "kg",
                    "default_pieces": 12,
                    "shelf_life_days": 3,
                    "production_time_days": 1,
                    "selling_price": Decimal("45.00"),
                    "instructions": "1. Пригответе шоколадовия блат. 2. Пригответе шоколадовия крем. 3. Сглобете тортата. 4. Декорирайте с шоколад.",
                    "sections": [
                        {
                            "name": "Блат - Шоколадов",
                            "section_type": "dough",
                            "shelf_life_days": 2,
                            "waste_percentage": Decimal("5"),
                            "section_order": 1,
                            "ingredients": [
                                ("Брашно тип 500", 400), ("Захар кристална", 300), ("Яйца (клас А)", 200),
                                ("Какао прах", 60), ("Краве масло 82%", 150), ("Бакпулвер", 10),
                            ],
                            "steps": [
                                ("Претеглете всички съставки", 1, 10),
                                ("Разбийте яйцата със захарта до пухкавост", 2, 15),
                                ("Добавете разтопеното масло и какаото", 3, 5),
                                ("Добавете пресятото брашно с бакпулвер", 4, 5),
                                ("Изпечете при 180°C за 25-30 минути", 5, 30),
                            ]
                        },
                        {
                            "name": "Крем - Шоколадов",
                            "section_type": "cream",
                            "shelf_life_days": 2,
                            "waste_percentage": Decimal("0"),
                            "section_order": 2,
                            "ingredients": [
                                ("Черпуков шоколад (млечен)", 300), ("Сметана течна 35%", 300),
                                ("Краве масло 82%", 200), ("Захар кристална", 100),
                            ],
                            "steps": [
                                ("Загрейте сметаната до кипене", 1, 5),
                                ("Залейте шоколада със горещата сметана", 2, 3),
                                ("Разбъркайте до гладка смес", 3, 5),
                                ("Добавете маслото и захарта", 4, 5),
                                ("Охладете преди употреба", 5, 30),
                            ]
                        },
                        {
                            "name": "Декорация - Шоколадова",
                            "section_type": "decoration",
                            "shelf_life_days": 3,
                            "waste_percentage": Decimal("0"),
                            "section_order": 3,
                            "ingredients": [
                                ("Черпуков шоколад (млечен)", 150), ("Пудра захар", 30),
                            ],
                            "steps": [
                                ("Разтопете шоколада за декорация", 1, 5),
                                ("Полейте тортата с разтопен шоколад", 2, 5),
                                ("Поръсете с пудра захар", 3, 2),
                            ]
                        },
                    ]
                },
                {
                    "name": "Торта Ванилова",
                    "category": "Торти",
                    "description": " класическа ванилова торта с крем от крема сирене",
                    "yield_quantity": Decimal("2.5"),
                    "yield_unit": "kg",
                    "default_pieces": 12,
                    "shelf_life_days": 3,
                    "production_time_days": 1,
                    "selling_price": Decimal("42.00"),
                    "instructions": "1. Пригответе ваниловия блат. 2. Пригответе крема от крема сирене. 3. Сглобете тортата. 4. Декорирайте.",
                    "sections": [
                        {
                            "name": "Блат - Ванилов",
                            "section_type": "dough",
                            "shelf_life_days": 2,
                            "waste_percentage": Decimal("5"),
                            "section_order": 1,
                            "ingredients": [
                                ("Брашно тип 500", 380), ("Захар кристална", 320), ("Яйца (клас А)", 220),
                                ("Прясно мляко 3.5%", 150), ("Краве масло 82%", 120),
                                ("Ванилия (екстракт)", 20), ("Бакпулвер", 8),
                            ],
                            "steps": [
                                ("Претеглете всички съставки", 1, 10),
                                ("Разбийте яйцата със захарта и ванилията", 2, 15),
                                ("Добавете млякото и маслото", 3, 5),
                                ("Добавете пресятото брашно с бакпулвер", 4, 5),
                                ("Изпечете при 180°C за 25-30 минути", 5, 30),
                            ]
                        },
                        {
                            "name": "Крем - Ванилов",
                            "section_type": "cream",
                            "shelf_life_days": 2,
                            "waste_percentage": Decimal("0"),
                            "section_order": 2,
                            "ingredients": [
                                ("Крема сирене", 500), ("Захар кристална", 150),
                                ("Ванилия (екстракт)", 15), ("Сметана течна 35%", 200),
                            ],
                            "steps": [
                                ("Разбийте крема сирене със захарта", 1, 10),
                                ("Добавете ванилията", 2, 2),
                                ("Разбийте сметаната на пяна", 3, 10),
                                ("Смесете двете смеси внимателно", 4, 5),
                            ]
                        },
                        {
                            "name": "Декорация - Ванилова",
                            "section_type": "decoration",
                            "shelf_life_days": 3,
                            "waste_percentage": Decimal("0"),
                            "section_order": 3,
                            "ingredients": [
                                ("Пудра захар", 50),
                            ],
                            "steps": [
                                ("Поръсете обилно с пудра захар", 1, 3),
                            ]
                        },
                    ]
                },
                {
                    "name": "Торта Плодова",
                    "category": "Торти",
                    "description": " освежаваща плодова торта с крем и пресни плодове",
                    "yield_quantity": Decimal("2.5"),
                    "yield_unit": "kg",
                    "default_pieces": 12,
                    "shelf_life_days": 2,
                    "production_time_days": 1,
                    "selling_price": Decimal("48.00"),
                    "instructions": "1. Пригответе блатa. 2. Пригответе крема с желатин. 3. Добавете плодове. 4. Декорирайте.",
                    "sections": [
                        {
                            "name": "Блат - Плодов",
                            "section_type": "dough",
                            "shelf_life_days": 2,
                            "waste_percentage": Decimal("5"),
                            "section_order": 1,
                            "ingredients": [
                                ("Брашно тип 500", 350), ("Захар кристална", 280), ("Яйца (клас А)", 200),
                                ("Прясно мляко 3.5%", 120), ("Краве масло 82%", 100),
                            ],
                            "steps": [
                                ("Претеглете всички съставки", 1, 10),
                                ("Разбийте яйцата със захарта", 2, 15),
                                ("Добавете мляко и масло", 3, 5),
                                ("Добавете брашното", 4, 5),
                                ("Изпечете при 180°C за 25 минути", 5, 25),
                            ]
                        },
                        {
                            "name": "Крем - Плодов",
                            "section_type": "cream",
                            "shelf_life_days": 2,
                            "waste_percentage": Decimal("0"),
                            "section_order": 2,
                            "ingredients": [
                                ("Крема сирене", 400), ("Сметана течна 35%", 250),
                                ("Желатин", 30), ("Лимонов сок", 30),
                            ],
                            "steps": [
                                ("Накиснете желатина в студена вода", 1, 10),
                                ("Загрейте част от сметаната и разтворете желатина", 2, 5),
                                ("Смесете с крема сирене и останалата сметана", 3, 10),
                                ("Добавете лимоновия сок", 4, 2),
                                ("Охладете до сгъстяване", 5, 30),
                            ]
                        },
                        {
                            "name": "Плодове",
                            "section_type": "filling",
                            "shelf_life_days": 1,
                            "waste_percentage": Decimal("0"),
                            "section_order": 3,
                            "ingredients": [
                                ("Плодов микс (ягоди, малини)", 400),
                            ],
                            "steps": [
                                ("Измийте и подсушете плодовете", 1, 5),
                                ("Нарежете по-едрите плодове", 2, 5),
                            ]
                        },
                        {
                            "name": "Декорация - Плодова",
                            "section_type": "decoration",
                            "shelf_life_days": 2,
                            "waste_percentage": Decimal("0"),
                            "section_order": 4,
                            "ingredients": [
                                ("Плодов микс (ягоди, малини)", 150),
                            ],
                            "steps": [
                                ("Подредете пресни плодове отгоре", 1, 10),
                            ]
                        },
                    ]
                },
                {
                    "name": "Торта Млечна",
                    "category": "Торти",
                    "description": "кремообразна млечна торта с кокос и лешници",
                    "yield_quantity": Decimal("2.5"),
                    "yield_unit": "kg",
                    "default_pieces": 12,
                    "shelf_life_days": 3,
                    "production_time_days": 1,
                    "selling_price": Decimal("46.00"),
                    "instructions": "1. Пригответе кокосовия блат. 2. Пригответе млечния крем. 3. Декорирайте.",
                    "sections": [
                        {
                            "name": "Блат - Кокосов",
                            "section_type": "dough",
                            "shelf_life_days": 2,
                            "waste_percentage": Decimal("5"),
                            "section_order": 1,
                            "ingredients": [
                                ("Брашно тип 500", 360), ("Захар кристална", 300), ("Яйца (клас А)", 210),
                                ("Прясно мляко 3.5%", 180), ("Краве масло 82%", 130),
                                ("Кокосови стърготини", 50),
                            ],
                            "steps": [
                                ("Претеглете всички съставки", 1, 10),
                                ("Разбийте яйцата със захарта", 2, 15),
                                ("Добавете мляко, масло и кокос", 3, 5),
                                ("Добавете брашното", 4, 5),
                                ("Изпечете при 180°C за 25-30 минути", 5, 30),
                            ]
                        },
                        {
                            "name": "Млечен крем",
                            "section_type": "cream",
                            "shelf_life_days": 2,
                            "waste_percentage": Decimal("0"),
                            "section_order": 2,
                            "ingredients": [
                                ("Прясно мляко 3.5%", 400), ("Захар кристална", 180),
                                ("Крема сирене", 300), ("Желатин", 25),
                                ("Кокосови стърготини", 40),
                            ],
                            "steps": [
                                ("Загрейте млякото със захарта", 1, 10),
                                ("Добавете накиснатия желатин", 2, 5),
                                ("Охладете малко и добавете крема сирене", 3, 10),
                                ("Добавете кокосовите стърготини", 4, 3),
                                ("Охладете до сгъстяване", 5, 30),
                            ]
                        },
                        {
                            "name": "Декорация - Млечна",
                            "section_type": "decoration",
                            "shelf_life_days": 3,
                            "waste_percentage": Decimal("0"),
                            "section_order": 3,
                            "ingredients": [
                                ("Кокосови стърготини", 60), ("Лешници (смлени)", 40),
                            ],
                            "steps": [
                                ("Поръсете с кокосови стърготини", 1, 3),
                                ("Поръсете със смлени лешници", 2, 3),
                            ]
                        },
                    ]
                },
            ]

            recipes_created = 0
            for recipe_data in recipes_data:
                recipe = Recipe(
                    name=recipe_data["name"],
                    category=recipe_data["category"],
                    description=recipe_data["description"],
                    yield_quantity=recipe_data["yield_quantity"],
                    yield_unit=recipe_data["yield_unit"],
                    default_pieces=recipe_data["default_pieces"],
                    shelf_life_days=recipe_data["shelf_life_days"],
                    production_time_days=recipe_data["production_time_days"],
                    selling_price=recipe_data["selling_price"],
                    instructions=recipe_data["instructions"],
                    company_id=all_companies[0].id
                )
                db.add(recipe)
                await db.flush()
                
                for section_data in recipe_data["sections"]:
                    section = RecipeSection(
                        recipe_id=recipe.id,
                        section_type=section_data["section_type"],
                        name=section_data["name"],
                        shelf_life_days=section_data["shelf_life_days"],
                        waste_percentage=section_data["waste_percentage"],
                        section_order=section_data["section_order"]
                    )
                    db.add(section)
                    await db.flush()
                    
                    # Добавяне на съставки към секцията
                    for ing_name, qty in section_data["ingredients"]:
                        if ing_name in ingredients_by_name:
                            recipe_ing = RecipeIngredient(
                                section_id=section.id,
                                recipe_id=recipe.id,
                                ingredient_id=ingredients_by_name[ing_name].id,
                                quantity_gross=Decimal(str(qty))
                            )
                            db.add(recipe_ing)
                    
                    # Добавяне на стъпки към секцията
                    for step_name, step_order, step_duration in section_data["steps"]:
                        ws_name = "Пекарна" if section_data["section_type"] == "dough" else "Кремове" if section_data["section_type"] in ["cream", "filling"] else "Декорация"
                        if ws_name in workstations:
                            step = RecipeStep(
                                section_id=section.id,
                                recipe_id=recipe.id,
                                workstation_id=workstations[ws_name].id,
                                name=step_name,
                                step_order=step_order,
                                estimated_duration_minutes=step_duration
                            )
                            db.add(step)
                
                recipes_created += 1
                print(f"  ✓ Рецепта: {recipe.name}")
            
            await db.flush()
            print(f"✓ Рецепти: {recipes_created}")

            users_created = 0
            
            first_names_list = {
                "super_admin": ["Симеон", "Никола", "Георги", "Мартин", "Иван", "Петър", "Димитър"],
                "company_admin": ["Иван", "Петър", "Димитър", "Никола", "Георги", "Симеон", "Мартин"],
                "hr_manager": ["Мария", "Елена", "Гергана", "Даниела", "Силвия", "Таня", "Ирина"],
                "manager": ["Пламен", "Красимир", "Борис", "Александър", "Петър", "Георги", "Никола"],
                "employee": ["Гошо", "Тошо", "Пешо", "Дошо", "Мишо", "Любо", "Стоян"],
                "viewer": ["Наблюдател", "Монитор", "Одитор", "Контрольор", "Проверител", "Наблюдател2", "Наблюдател3"],
                "admin": ["Админ", "Сисадмин", "Мениджър", "Супервайзор", "Координатор", "Специалист", "Оперативен"]
            }
            lastnames = ["Иванов", "Петров", "Димитров", "Георгиев", "Стоянов", "Николов", "Колев", "Тодоров", "Дimitrov", "Симеонов"]
            
            for company_idx, company in enumerate(all_companies):
                for role_idx, role in enumerate(all_roles):
                    base_email = f"{role.name}@c{company_idx+1}.com"
                    email = await get_unique_email(base_email, db)
                    
                    base_username = f"{role.name}_c{company_idx+1}"
                    username = await get_unique_username(base_username, db)
                    
                    fn_idx = (company_idx + role_idx) % len(first_names_list.get(role.name, ["Потребител"]))
                    first_name = first_names_list.get(role.name, ["Потребител"])[fn_idx]
                    last_name = lastnames[(company_idx + role_idx) % len(lastnames)]
                    
                    user = User(
                        email=email,
                        username=username,
                        first_name=first_name,
                        last_name=last_name,
                        phone_number=f"+35988{company_idx:02d}{role_idx:02d}{users_created % 100:02d}",
                        egn=f"75550{company_idx:02d}{role_idx:02d}{users_created % 100:02d}",
                        iban=f"BG80BNBG96611020{company_idx:02d}{role_idx:02d}",
                        hashed_password=hashed_password,
                        company_id=company.id,
                        role_id=role.id,
                        is_active=True,
                    )
                    db.add(user)
                    users_created += 1
                    
                    await db.flush()
                    
                    payroll = Payroll(
                        user_id=user.id,
                        hourly_rate=Decimal("12.50"),
                        monthly_salary=Decimal("2000"),
                        overtime_multiplier=Decimal("1.5"),
                        standard_hours_per_day=8,
                        currency="EUR",
                        annual_leave_days=20,
                        tax_percent=Decimal("10"),
                        health_insurance_percent=Decimal("13.78"),
                        has_tax_deduction=True,
                        has_health_insurance=True,
                    )
                    db.add(payroll)
                    
                    for day_offset in range(22):
                        schedule_date = date.today() + timedelta(days=day_offset)
                        if schedule_date.weekday() < 5:
                            schedule = WorkSchedule(
                                user_id=user.id,
                                date=schedule_date,
                                shift_id=1
                            )
                            db.add(schedule)
                    
                    if users_created % 10 == 0:
                        await db.flush()
            
            await db.flush()
            print(f"✓ Потребители: {users_created} нови")
            
            result = await db.execute(select(User))
            all_users = result.scalars().all()
            print(f"  Общо потребители: {len(all_users)}")

            result = await db.execute(select(Payroll))
            all_payrolls = result.scalars().all()
            print(f"  Общо Payroll записи: {len(all_payrolls)}")

            result = await db.execute(select(WorkSchedule))
            all_schedules = result.scalars().all()
            print(f"  Общо Графици: {len(all_schedules)}")

            await db.commit()
            print("\n" + "=" * 60)
            print("✓ ВСИЧКИ ТЕСТОВИ ДАННИ СА ЗАПАЗЕНИ УСПЕШНО!")
            print("=" * 60)
            
            print("\n=== СЪЗДАДЕНИ ДАННИ ===")
            print(f"  - Фирми: {len(all_companies)}")
            print(f"  - Роли: {len(all_roles)}")
            print(f"  - Потребители: {len(all_users)}")
            print(f"  - Трудови договори: {len(all_users)}")
            print(f"  - Заплати (Payroll): {len(all_payrolls)}")
            print(f"  - Работни графици: {len(all_schedules)}")
            print(f"  - Складови зони: {len(zones)}")
            print(f"  - Доставчици: {len(all_suppliers)}")
            print(f"  - Артикули: {len(all_ingredients)}")
            print(f"  - Партиди: {len(all_batches)}")
            print(f"  - Фактури: {len(all_invoices)}")
            print(f"  - Рецепти: {recipes_created}")
            print(f"  - Отдели: {len(departments)}")
            print(f"  - Длъжности: {len(all_positions)}")
            
            print("\n=== ПОТРЕБИТЕЛСКИ АКАУНТИ ===")
            print("  Всички пароли: password123")
            print("  Всички потребители имат:")
            print("    - Трудов договор")
            print("    - Работен график (22 дни)")
            print("    - Заплата 2000 EUR")
            
        except Exception as e:
            print(f"\n❌ Грешка: {e}")
            await db.rollback()
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(seed_all())
