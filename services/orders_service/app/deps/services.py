from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.order import OrderService
from app.repositories.asset_repo import AssetRepository
from app.repositories.order_repo import OrderRepository

def get_order_service(session: AsyncSession = Depends(get_db)) -> OrderService:
    asset_repo = AssetRepository(session)
    order_repo = OrderRepository(session)
    return OrderService(order_repo=order_repo, asset_repo=asset_repo)
