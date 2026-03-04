import asyncio
from backend.database.database import AsyncSessionLocal
from backend import crud, schemas
from backend.database.models import Base

async def seed():
    async with AsyncSessionLocal() as db:
        # 1. Добавяне на роли (Фаза 7) - Идемпотентно (само ако ги няма)
        print("Checking and adding roles...")
        new_roles = [
            ("super_admin", "Super Administrator with full system control"),
            ("trz", "Human Resources and Payroll Specialist"),
            ("accountant", "Company Accountant"),
            ("head_accountant", "Chief Accountant with access to all companies")
        ]
        
        for role_name, description in new_roles:
            role = await crud.get_role_by_name(db, role_name)
            if not role:
                await crud.create_role(db, schemas.RoleCreate(name=role_name, description=description))
                print(f"Added new role: {role_name}")
            else:
                print(f"Role {role_name} already exists.")

        # 2. Осигуряване на Super Admin (Критично за Фаза 7)
        super_admin_email = "superadmin@oblak24.org"
        db_user = await crud.get_user_by_email(db, super_admin_email)
        if not db_user:
            print(f"Creating super admin: {super_admin_email}...")
            admin_in = schemas.UserCreate(
                email=super_admin_email,
                password="superpassword123"
            )
            await crud.create_user(db, admin_in, role_name="super_admin")
            print("Super Admin created successfully.")

        await db.commit()

    print("Seed update complete!")

if __name__ == "__main__":
    asyncio.run(seed())
