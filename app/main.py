from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routes.profiles import router as profiles_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database before yielding
    await init_db()
    yield
    # Shutdown: Add any cleanup code here if needed


app = FastAPI(lifespan=lifespan)

# Register the router
app.include_router(profiles_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"Hello": "World"}
