from fastapi import APIRouter, Depends, Response, Request
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from app.schemas.order import OrderSchema, OrderCreateResponse, OrderListResponse, OrderResponse, OrderCancelResponse
from app.core.config import settings
from app.services.order import OrderService, get_order_servcice

router = APIRouter()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_token(token: str = Security(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITM_JWT])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/", response_model=OrderListResponse)
async def get_orders_list(user_data: dict = Depends(verify_token),
                          service: OrderService = Depends(get_order_servcice)):
    return await service.get_list_order(user_data)


@router.post("/", response_model=OrderCreateResponse)
async def create_order(order: OrderSchema, 
                       user_data: dict = Depends(verify_token),  
                       service: OrderService = Depends(get_order_servcice)):
    return await service.create_order(user_data, order)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int,
                    user_data: dict = Depends(verify_token),  
                    service: OrderService = Depends(get_order_servcice)):
    return await service.get_order(user_data, order_id)

@router.delete("/{order_id}", response_model=OrderCancelResponse)
async def cancel_order(order_id: int, 
                       user_data: dict = Depends(verify_token),
                       service: OrderService = Depends(get_order_servcice)):
    return await service.cancel_order(user_data, order_id) 
