import asyncio
from typing import Dict

# Словарь для хранения correlation_id -> asyncio.Future
lock_futures: Dict[str, asyncio.Future] = {}