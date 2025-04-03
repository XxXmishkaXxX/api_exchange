from fastapi import APIRouter, Depends, Response, Request

from app.deps.security import get_user_from_token
from app.services.wallet import WalletService, get_wallet_service

router = APIRouter()


@router.get("")
async def get_balance(user_info=Depends(get_user_from_token),
                      service: WalletService = Depends(get_wallet_service)):
    return await service.get_all_assets_balance(user_info["user_id"])
