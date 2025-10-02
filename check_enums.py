"""Check database ENUM types"""
import asyncio
from sqlalchemy import text
from app.database import engine

async def check_enums():
    async with engine.begin() as conn:
        result = await conn.execute(text(
            "SELECT typname FROM pg_type WHERE typtype = 'e' ORDER BY typname"
        ))
        enums = [row[0] for row in result]
        print("Existing ENUM types in database:")
        for enum_type in enums:
            print(f"  - {enum_type}")
        return enums

if __name__ == "__main__":
    asyncio.run(check_enums())
