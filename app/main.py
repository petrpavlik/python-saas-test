from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi_pagination import add_pagination

from app.database import init_db
from app.models.firebase_auth_user import FirebaseAuthUser
from app.routes.organizations import router as profiles_router
from app.routes.profiles import router as organization_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database before yielding
    await init_db()
    yield
    # Shutdown: Add any cleanup code here if needed


app = FastAPI(lifespan=lifespan)
add_pagination(app)  # important! add pagination to your app


@app.middleware("http")
async def jwt_auth_middleware(request: Request, call_next) -> Response:
    if request.url.path == "/":
        return await call_next(request)
    if request.url.path.startswith("/docs"):
        return await call_next(request)
    if request.url.path.startswith("/openapi.json"):
        return await call_next(request)

    # Looks like I cannot throw an exception in the middleware (ends up with internal server error), so I have to return a JSONResponse, this sucks
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Missing token"})

    token = auth_header.split(" ")[1]

    # This micks JWT token verification process, we'd greab a user id and email from the token.
    if token == "petr_token":
        # TODO: check if there's a user with this email in the database
        # TODO: check if the user is banned
        request.state.firebase_user = FirebaseAuthUser(
            email="petr@indiepitcher.com",
            user_id="1234567890",  # This would be the Firebase user ID
        )
        return await call_next(request)
    else:
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})


# Configure CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
#     allow_headers=["*"],  # Allow all headers
# )

# Register the router
app.include_router(profiles_router)
app.include_router(organization_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"Hello": "World"}
