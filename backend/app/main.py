from fastapi import FastAPI
from .routers import auth
from .database import engine
from .models import user

app = FastAPI(title="Navi-G8 API")

@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(user.Base.metadata.create_all)

@app.get("/")
def root():
    return {"message": "Navi-G8 Backend"}

app.include_router(auth.router, prefix="/api/v1")