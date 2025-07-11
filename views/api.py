from fastapi import FastAPI
from controllers.domain_controller import router as domain_router
from controllers.alias_controller import router as alias_router
from database.db import init_db

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(domain_router)
app.include_router(alias_router) 