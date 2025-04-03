from fastapi import APIRouter, Depends, Response, Request

from app.services.wallet import get_wallet_service, WalletService
from app.deps.security import admin_required
from  app.schemas.wallet import DepositAssetsSchema, WithdrawAssetsSchema

router = APIRouter()


@router.post("/deposit")
async def deposit_assets(data: DepositAssetsSchema,
                        check_role = Depends(admin_required), 
                        service: WalletService = Depends(get_wallet_service)):
    return await service.deposit_assets_user(data)

@router.post("/withdraw")
async def withdraw_assets(data: WithdrawAssetsSchema,
                          check_role = Depends(admin_required),
                          service: WalletService = Depends(get_wallet_service)):
    return await service.withdraw_assets_user(data)
