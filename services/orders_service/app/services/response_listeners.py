import asyncio
from typing import Dict

lock_futures: Dict[str, asyncio.Future] = {}

market_quote_futures: Dict[str, asyncio.Future] = {}
