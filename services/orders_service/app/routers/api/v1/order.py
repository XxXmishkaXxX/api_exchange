from fastapi import APIRouter, Depends, Response, Request
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from app.schemas.order import Order, OrderResponse, OrderListResponse
from app.core.config import settings

router = APIRouter()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_token(token: str = Security(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITM_JWT])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/", response_model=OrderListResponse)
async def get_orders_list(user_data: dict = Depends(verify_token)):
    return {"message": "Authorized", "user": user_data}


@router.post("/", response_model=OrderResponse)
async def create_order(order: Order,):
    # try:
        # order_id = await order_service.create_order(order)
        # return OrderResponse(order_id=order_id, **order.dict())
    # except Exception as e:
        # raise HTTPException(status_code=400, detail=str(e))
        pass

@router.get("/", response_model=OrderListResponse)
async def get_orders_list():
     pass

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str,):
    # order = await order_service.get_order(order_id)
    # if not order:
        # raise HTTPException(status_code=404, detail="Order not found")
    # return OrderResponse(**order)
    pass

@router.delete("/{order_id}")
async def cancel_order(order_id: str,):
    # try:
        # await order_service.cancel_order(order_id)
        # return {"message": "Order cancelled successfully"}
    # except Exception as e:
        # raise HTTPException(status_code=400, detail=str(e))
    pass
