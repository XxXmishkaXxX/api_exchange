from fastapi import APIRouter, Depends
from typing import Annotated

from app.services.wallet import WalletService
from app.deps.fabric import get_wallet_service
from app.deps.security import admin_required
from app.schemas.wallet import DepositAssetsSchema, WithdrawAssetsSchema

router = APIRouter()


@router.post("/deposit")
async def deposit_assets(data: DepositAssetsSchema,
                        check_role: Annotated[None, Depends(admin_required)], 
                        service: Annotated[WalletService, Depends(get_wallet_service)]):
    return await service.deposit_assets_user(data)

@router.post("/withdraw")
async def withdraw_assets(data: WithdrawAssetsSchema,
                          check_role: Annotated[None, Depends(admin_required)],
                          service: Annotated[WalletService, Depends(get_wallet_service)]):
    return await service.withdraw_assets_user(data)
