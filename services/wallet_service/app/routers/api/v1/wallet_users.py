from typing import Annotated
from fastapi import APIRouter, Depends

from app.deps.security import get_user_from_token
from app.services.wallet import WalletService
from app.deps.fabric import get_wallet_service

router = APIRouter()


@router.get("")
async def get_balance(user_info: Annotated[dict, Depends(get_user_from_token)],
                      service: Annotated[WalletService, Depends(get_wallet_service)]):
    return await service.get_all_assets_balance(user_info["user_id"])
