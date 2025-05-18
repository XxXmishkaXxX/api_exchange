from app.core.logger import logger
from app.deps.services import get_assets_service
from app.schemas.asset import AssetSchema
from app.db.database import get_db


stable_coins = {
    "RUB": "Крипто-рубль",
    "USDT": "Tether",
    "USDC": "USD Coin",
}

async def create_stable_coins_on_start():
    async with get_db() as session:
        service = get_assets_service(session)
        try:
            for ticker, name in stable_coins.items():
                existing = await service.get_asset_by_ticker(ticker)
                if existing:
                    logger.info(f"Asset {ticker} уже существует")
                    continue
                asset = AssetSchema(ticker=ticker, name=name)
                await service.create_asset(asset)
                logger.info(f"Asset {ticker} создан")
            logger.info("Стейблкоины инициализированы")
        except Exception as e:
            logger.exception("Ошибка при создании стейблкоинов")
