import asyncio
from typing import Dict
from datetime import datetime, timedelta
from sqlalchemy.future import select
from fastapi_mail import FastMail, MessageSchema

from app.tasks.worker_config import app
from app.models.user import User
from app.db.database import get_db
from app.core.config import email_conf


mail = FastMail(email_conf)


@app.task
def delete_inactive_users() -> None:
    """
    Задача для удаления неактивных пользователей из базы данных.

    Пользователи считаются неактивными, если они не были подтверждены
    и созданы более чем 1 день назад.
    """
    asyncio.run(run_delete_inactive_users())


async def run_delete_inactive_users() -> None:
    """
    Асинхронная функция для удаления неактивных пользователей из базы данных.

    :return: None
    """
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
        break


@app.task
def send_email_task(message: Dict[str, str]) -> None:
    """
    Задача для отправки email сообщения.

    :param message: Словарь, содержащий данные сообщения (subject, recipients, body, subtype).
    :return: None
    """
    asyncio.run(send_email(message))


async def send_email(message: Dict[str, str]) -> None:
    """
    Асинхронная функция для отправки email сообщения.

    :param message: Словарь, содержащий данные сообщения (subject, recipients, body, subtype).
    :return: None
    """
    email_message = MessageSchema(
        subject=message["subject"],
        recipients=message["recipients"],
        body=message["body"],
        subtype=message["subtype"]
    )
    await mail.send_message(email_message)
