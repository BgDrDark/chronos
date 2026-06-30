import asyncio
import subprocess
import sys


async def main():
    from backend.database.database import engine

    async with engine.connect() as conn:
        from sqlalchemy import inspect
        tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())

    base = ["alembic", "-c", "backend/alembic.ini"]
    if "alembic_version" not in tables:
        cmd = base + ["stamp", "head"]
        print("alembic_version не съществува — stamp-ваме към head")
    else:
        cmd = base + ["upgrade", "head"]
        print("alembic_version съществува — upgrade до head")

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    asyncio.run(main())
