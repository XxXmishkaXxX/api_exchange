import aiohttp
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class WalletClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
    async def get_balance(self, user_id: str, asset: str):
        url = f"{self.base_url}/balance?user_id={user_id}&asset={asset}"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    logger.warning(f"Wallet service returned status {resp.status} for user={user_id}, asset={asset}")
        except Exception as e:
            logger.exception(f"Failed to fetch balance from wallet service: {e}")
        return None

wallet_client = WalletClient("http://localhost:8002/", settings.INTERNAL_API_TOKEN)  