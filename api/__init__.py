from fastapi import FastAPI
from api.endpoints import router
from config.db import init_db

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(router) 