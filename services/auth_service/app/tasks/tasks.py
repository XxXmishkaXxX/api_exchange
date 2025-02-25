# tasks.py
import asyncio
from app.tasks.worker_config import app
from sqlalchemy.future import select
from app.models.user import User
from app.db.database import get_db
from datetime import datetime, timedelta

@app.task
def delete_inactive_users():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_delete_inactive_users())

async def run_delete_inactive_users():
    async for session in get_db():
        now = datetime.utcnow()
        inactive_threshold = now - timedelta(days=1)

        result = await session.execute(
            select(User).filter(
                User.is_verified == False,
                User.created_at < inactive_threshold
            )
        )
        users_to_delete = result.scalars().all()

        for user in users_to_delete:
            await session.delete(user)

        await session.commit()
        print(f"Deleted {len(users_to_delete)} inactive users.")
