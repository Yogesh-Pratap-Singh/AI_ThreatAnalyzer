import os
import sys
import asyncio
import hashlib
import uuid
from datetime import datetime

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.config import settings
from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models.all_models import User, DataSource

def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

async def main():
    print("Connecting to database...")
    async with SessionLocal() as db:
        # 1. Seed Analyst User
        user_email = "analyst@yourorg.com"
        user_id = uuid.UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")
        
        from sqlalchemy.future import select
        query = select(User).where(User.email == user_email)
        result = await db.execute(query)
        existing_user = result.scalars().first()
        
        if existing_user:
            print(f"Analyst user {user_email} already exists.")
            user_id = existing_user.id
        else:
            print(f"Creating analyst user {user_email}...")
            hashed_pass = get_password_hash("Password123")
            new_user = User(
                id=user_id,
                email=user_email,
                password_hash=hashed_pass,
                full_name="Lead Analyst",
                role="analyst",
                is_active=True
            )
            db.add(new_user)
            await db.flush() # Ensure user_id is populated/flushed
            print(f"Analyst user created with ID: {user_id}")

        # 2. Seed Data Source
        ds_id = uuid.UUID("8b9b8b20-df5b-4395-8e31-862d66579b29")
        api_key = "dev-api-key-12345"
        api_key_hash = hash_key(api_key)
        
        query_ds = select(DataSource).where(DataSource.name == "Network Firewall Logs")
        result_ds = await db.execute(query_ds)
        existing_ds = result_ds.scalars().first()
        
        if existing_ds:
            print("Data source 'Network Firewall Logs' already exists.")
            print(f"ID: {existing_ds.id}")
            print(f"API Key: {api_key}")
        else:
            print("Creating data source 'Network Firewall Logs'...")
            new_ds = DataSource(
                id=ds_id,
                name="Network Firewall Logs",
                source_type="syslog",
                api_key_hash=api_key_hash,
                status="active",
                created_by=user_id
            )
            db.add(new_ds)
            print(f"Data source created with ID: {ds_id}")
            print(f"API Key: {api_key}")

        await db.commit()
    print("Database seeding of user and data source completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
