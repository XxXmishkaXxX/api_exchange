from fastapi import APIRouter, Depends, Response, Request

from app.services.wallet import WalletService
from app.deps.fabric import get_wallet_service
from app.deps.security import admin_required, verify_internal_token
from app.schemas.wallet import DepositAssetsSchema, WithdrawAssetsSchema

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


@router.get("/user")
async def get_user_asset_balance(user_id: int, 
                                 asset: str,
                                 verify_internal_token = Depends(verify_internal_token),
                                 service: WalletService = Depends(get_wallet_service),
                                 ):
    return await service.get_user_asset_balance(user_id, asset)
