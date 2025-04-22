import contextlib

from fastapi import FastAPI

from app.database import init_db

app = FastAPI()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


@app.get("/")
def read_root() -> dict[str, str]:
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None) -> dict[str, int | str | None]:
    return {"item_id": item_id, "q": q}
