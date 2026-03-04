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
    Invoice, InvoiceItem
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
                ("Черупков шоколад (млечен)", "kg", "raw"), ("Ванилия (екстракт)", "l", "raw"),
                ("Бакпулвер", "kg", "raw"), ("Сол", "kg", "raw"), ("Олио (слънчогледово)", "l", "raw"),
                ("Пудра захар", "kg", "raw"), ("Какао прах", "kg", "raw"),
                ("Заготовка - сметанов крем", "kg", "semi_finished"), ("Заготовка - шоколадов блат", "kg", "semi_finished"),
                ("Торта Шоколадова", "br", "finished"), ("Торта Плодова", "br", "finished"),
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
                Workstation.name == "Замесване", 
                Workstation.company_id == all_companies[0].id
            ))
            if not ws1.scalar_one_or_none():
                for ws_name, ws_desc in [
                    ("Замесване", "Машина за замесване"),
                    ("Печене", "Пещ за изпичане"),
                    ("Охлаждане", "Хладилна витрина"),
                    ("Декорация", "Работилница за декорация"),
                    ("Опаковане", "Автоматична опаковъчна линия")
                ]:
                    ws = Workstation(name=ws_name, description=ws_desc, company_id=all_companies[0].id)
                    db.add(ws)
                await db.flush()
            print(f"✓ Работни станции: 5")

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
