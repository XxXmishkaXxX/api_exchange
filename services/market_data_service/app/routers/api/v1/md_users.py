from fastapi import APIRouter, Depends


from app.services.market_data import MarketDataService, get_market_data_service



router = APIRouter()


@router.get("/instrument")
async def get_assets_list(service: MarketDataService = Depends(get_market_data_service)):
    return await service.get_list_assets()

<<<<<<< Updated upstream
=======

@router.get("/orderbook/{ticker}", response_model=OrderBookResponse | OrderBookErrorResponse)
async def get_orderbook(
    ticker: str = Path(..., description="Тикер актива (например BTC)"),
    pair: str = Query("RUB", description="Пара актива, например USDT"),
    limit: int = Query(10, ge=1, le=1000, description="Лимит заявок для отображения"),
    service: MarketDataService = Depends(get_market_data_service)
):
    data = OrderBookRequest(ticker=ticker, pair=pair, limit=limit)
    return await service.get_orderbook(data)


@router.get("/transactions/{ticker}", response_model=List[Transaction])
async def get_all_transactions_by_pair(
    ticker: str = Path(..., description="Тикер актива (например BTC)"),
    pair: str = Query("RUB", description="Пара актива, например USDT"),
    limit: int = Query(10, ge=1, le=1000),
    page: int = Query(1, ge=1),
    asset_service: AssetsService = Depends(get_assets_service),
    market_data_service: MarketDataService = Depends(get_market_data_service)
):
    asset1_id, asset2_id = await asset_service.get_assets_ids_pair(ticker, pair)
    return await market_data_service.get_transactions(asset1_id, asset2_id, limit, get_offset(page, limit))


@router.get("/transactions/user/{user_id}/{ticker}", response_model=List[Transaction])
async def get_user_transactions_by_pair(
    user_id: int = Path(..., description="ID пользователя"),
    ticker: str = Path(..., description="Тикер актива (например BTC)"),
    pair: str = Query("RUB", description="Пара актива, например USDT"),
    limit: int = Query(10, ge=1, le=1000),
    page: int = Query(1, ge=1),
    asset_service: AssetsService = Depends(get_assets_service),
    market_data_service: MarketDataService = Depends(get_market_data_service)
):
    asset1_id, asset2_id = await asset_service.get_assets_ids_pair(ticker, pair)
    return await market_data_service.get_user_transactions_by_pair(
        asset1_id, asset2_id, user_id, limit, get_offset(page, limit)
    )


@router.get("/transactions/user/{user_id}", response_model=List[Transaction])
async def get_all_user_transactions(
    user_id: int = Path(..., description="ID пользователя"),
    limit: int = Query(10, ge=1, le=1000),
    page: int = Query(1, ge=1),
    market_data_service: MarketDataService = Depends(get_market_data_service)
):
    return await market_data_service.get_all_user_transactions(user_id, limit, get_offset(page, limit))
>>>>>>> Stashed changes
