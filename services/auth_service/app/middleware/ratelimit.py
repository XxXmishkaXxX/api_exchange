from fastapi import Request
from app.db.database import redis_client
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        if response.status_code == 422:
            ip = request.client.host  
            error_count_key = f"error_count:{ip}"
            error_count = redis_client.get(error_count_key)
            
            if error_count and int(error_count) > 10:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many errors, rate limited."},
                )

            redis_client.incr(error_count_key)
            redis_client.expire(error_count_key, 600)  

        return response