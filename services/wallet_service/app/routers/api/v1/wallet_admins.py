from fastapi import APIRouter, Depends, Response, Request

from app.services.wallet import get_wallet_service, WalletService
from app.deps.security import admin_required
from app.schemas.wallet import DepositAssetsSchema, WithdrawAssetsSchema
from app.services.producers import ChangeBalanceKafkaProducerService, get_change_balance_producer_service

router = APIRouter()


@router.post("/deposit")
async def deposit_assets(data: DepositAssetsSchema,
                        check_role = Depends(admin_required), 
                        service: WalletService = Depends(get_wallet_service),
                        prod: ChangeBalanceKafkaProducerService = Depends(
                            get_change_balance_producer_service)):
    return await service.deposit_assets_user(data, prod)

@router.post("/withdraw")
async def withdraw_assets(data: WithdrawAssetsSchema,
                          check_role = Depends(admin_required),
                          service: WalletService = Depends(get_wallet_service),
                          prod: ChangeBalanceKafkaProducerService = Depends(
                            get_change_balance_producer_service)):
    return await service.withdraw_assets_user(data, prod)
