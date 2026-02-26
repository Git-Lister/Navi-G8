# backend/app/main.py
from fastapi import FastAPI

app = FastAPI(title="Navi-G8 API")

@app.get("/")
def root():
    return {"message": "Navi-G8 Backend"}
