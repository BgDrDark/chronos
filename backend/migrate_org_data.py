import asyncio
from sqlalchemy import select
from backend.database.database import AsyncSessionLocal
from backend.database.models import User, Company, Department, Position

async def migrate_data():
    async with AsyncSessionLocal() as session:
        print("Starting organization data migration...")
        
        # 1. Fetch all users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        companies_cache = {}
        departments_cache = {} # Key: (name, company_id)
        positions_cache = {}   # Key: (title, department_id)
        
        # Pre-fill caches to minimize queries (optional, but good for larger datasets)
        # For simplicity, we will check/create on the fly in this script as strict uniqueness isn't enforced globally yet
        
        migrated_count = 0
        
        for user in users:
            should_commit = False
            
            # --- Company ---
            if user.company and not user.company_id:
                comp_name = user.company.strip()
                if comp_name:
                    # Check cache or DB
                    if comp_name not in companies_cache:
                        res = await session.execute(select(Company).where(Company.name == comp_name))
                        existing_comp = res.scalar_one_or_none()
                        if not existing_comp:
                            print(f"Creating new company: {comp_name}")
                            existing_comp = Company(name=comp_name)
                            session.add(existing_comp)
                            await session.flush() # Get ID
                        companies_cache[comp_name] = existing_comp
                    
                    user.company_id = companies_cache[comp_name].id
                    should_commit = True

            # --- Department ---
            if user.department and not user.department_id:
                dept_name = user.department.strip()
                if dept_name:
                    # Department uniqueness is tricky without company, but we assume it belongs to the user's company (if any)
                    comp_id = user.company_id
                    cache_key = (dept_name, comp_id)
                    
                    if cache_key not in departments_cache:
                        query = select(Department).where(Department.name == dept_name)
                        if comp_id:
                            query = query.where(Department.company_id == comp_id)
                        
                        res = await session.execute(query)
                        existing_dept = res.first() # Take first match if multiple
                        existing_dept = existing_dept[0] if existing_dept else None

                        if not existing_dept:
                            print(f"Creating new department: {dept_name} (Company ID: {comp_id})")
                            existing_dept = Department(name=dept_name, company_id=comp_id)
                            session.add(existing_dept)
                            await session.flush()
                        departments_cache[cache_key] = existing_dept
                    
                    user.department_id = departments_cache[cache_key].id
                    should_commit = True

            # --- Position (Job Title) ---
            if user.job_title and not user.position_id:
                title_name = user.job_title.strip()
                if title_name:
                    dept_id = user.department_id
                    cache_key = (title_name, dept_id)
                    
                    if cache_key not in positions_cache:
                        query = select(Position).where(Position.title == title_name)
                        if dept_id:
                            query = query.where(Position.department_id == dept_id)
                            
                        res = await session.execute(query)
                        existing_pos = res.first()
                        existing_pos = existing_pos[0] if existing_pos else None
                        
                        if not existing_pos:
                            print(f"Creating new position: {title_name} (Dept ID: {dept_id})")
                            existing_pos = Position(title=title_name, department_id=dept_id)
                            session.add(existing_pos)
                            await session.flush()
                        positions_cache[cache_key] = existing_pos
                    
                    user.position_id = positions_cache[cache_key].id
                    should_commit = True
            
            if should_commit:
                migrated_count += 1
        
        await session.commit()
        print(f"Migration finished. Updated {migrated_count} users.")

if __name__ == "__main__":
    asyncio.run(migrate_data())
