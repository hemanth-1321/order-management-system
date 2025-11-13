from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from src.auth.routes import auth_router
from src.orders.routes import order_router
from src.config.logger import configure_logging
from src.config.ratelimiting import limiter

configure_logging("INFO")
load_dotenv()

app = FastAPI(
    title="Order Management API",
    version="1.0",
    description="Simple order management backend for testing auth & jobs."
)

# Attach limiter middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Rate limit exceeded handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Try again later."}
    )

@app.get("/")
def health():
    return {"msg": "Hello world, Health check"}

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["users"])
app.include_router(order_router, prefix="/orders", tags=["orders"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
