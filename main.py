from dotenv import load_dotenv
from fastapi import FastAPI
from src.auth.routes import auth_router
from src.config.logger import configure_logging

configure_logging("INFO")

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Order Management API",
    version="1.0",
    description="Simple order management backend for testing auth & jobs."
)

@app.get("/")
def health():
    return {"msg": "Hello world, Health check"}

app.include_router(auth_router, prefix="/auth", tags=["users"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
