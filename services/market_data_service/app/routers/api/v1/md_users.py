from fastapi import APIRouter, Depends, Path, Query
from typing import List, Annotated
from uuid import UUID

from app.services.assets import AssetsService
from app.services.market_data import MarketDataService
from app.deps.services import get_assets_service_for_deps, get_market_data_service
from app.schemas.orderbook import OrderBookRequest, OrderBookResponse, OrderBookErrorResponse
from app.schemas.transactions import Transaction

router = APIRouter()

def get_offset(page: int, limit: int) -> int:
    return (page - 1) * limit

@router.get("/instrument", response_model=List[dict])
async def get_assets_list(
    service: Annotated[AssetsService, Depends(get_assets_service_for_deps)]
):
    return await service.get_list_assets()

@router.get("/orderbook/{ticker}", response_model=OrderBookResponse | OrderBookErrorResponse)
async def get_orderbook(
    ticker: Annotated[str, Path(description="Тикер актива (например BTC)")],
    service: Annotated[MarketDataService, Depends(get_market_data_service)],
    pair: Annotated[str, Query(description="Пара актива, например USDT")] = "RUB",
    limit: Annotated[int, Query(ge=1, le=1000, description="Лимит заявок для отображения")] = 10
):
    data = OrderBookRequest(ticker=ticker, pair=pair, limit=limit)
    return await service.get_orderbook(data)

@router.get("/transactions/{ticker}", response_model=List[Transaction])
async def get_all_transactions_by_pair(
    asset_service: Annotated[AssetsService, Depends(get_assets_service_for_deps)],
    market_data_service: Annotated[MarketDataService, Depends(get_market_data_service)],
    ticker: Annotated[str, Path(description="Тикер актива (например BTC)")],
    pair: Annotated[str, Query(description="Пара актива, например USDT")] = "RUB",
    limit: Annotated[int, Query(ge=1, le=1000)] = 10,
    page: Annotated[int, Query(ge=1)] = 1
):
    asset1_id, asset2_id = await asset_service.get_assets_ids_pair(ticker, pair)
    return await market_data_service.get_transactions(
        asset1_id, asset2_id, limit, get_offset(page, limit)
    )

@router.get("/transactions/user/{user_id}/{ticker}", response_model=List[Transaction])
async def get_user_transactions_by_pair(
    user_id: Annotated[UUID, Path(description="ID пользователя")],
    ticker: Annotated[str, Path(description="Тикер актива (например BTC)")],
    asset_service: Annotated[AssetsService, Depends(get_assets_service_for_deps)],
    market_data_service: Annotated[MarketDataService, Depends(get_market_data_service)],
    pair: Annotated[str, Query(description="Пара актива, например USDT")] = "RUB",
    limit: Annotated[int, Query(ge=1, le=1000)] = 10,
    page: Annotated[int, Query(ge=1)] = 1
):
    asset1_id, asset2_id = await asset_service.get_assets_ids_pair(ticker, pair)
    return await market_data_service.get_user_transactions_by_pair(
        asset1_id, asset2_id, user_id, limit, get_offset(page, limit)
    )

@router.get("/transactions/user/{user_id}", response_model=List[Transaction])
async def get_all_user_transactions(
    user_id: Annotated[UUID, Path(description="ID пользователя")],
    market_data_service: Annotated[MarketDataService, Depends(get_market_data_service)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 10,
    page: Annotated[int, Query(ge=1)] = 1,
):
    return await market_data_service.get_all_user_transactions(
        user_id, limit, get_offset(page, limit)
    )
