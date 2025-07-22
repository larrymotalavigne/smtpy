import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from starlette.middleware.sessions import SessionMiddleware

from config import SETTINGS
from database.models import User
from utils.db import get_session, init_db
from views import domain_view, alias_view, billing_view, user_view, main_view


def create_default_admin():
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    with get_session() as session:
        if not session.query(User).first():
            hashed = pwd_context.hash("password")
            user = User(
                username="admin",
                hashed_password=hashed,
                email=None,
                role="admin",
                is_active=True,
                email_verified=True
            )
            session.add(user)
            session.commit()
            print("\n\033[92mCreated default admin user: admin / password\033[0m\n")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    create_default_admin()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="SMTPy API",
        lifespan=lifespan
    )
    app.add_middleware(SessionMiddleware, secret_key=SETTINGS.SECRET_KEY)
    app.include_router(domain_view.router, prefix="/api")
    app.include_router(alias_view.router, prefix="/api")
    app.include_router(user_view.router, prefix="/api")
    app.include_router(domain_view.router, prefix="/api")
    app.include_router(billing_view.router, prefix="/api")
    app.include_router(main_view.router)

    app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "./static")), name="static")
    return app


if __name__ == "__main__":
    from uvicorn import run

    run("main:create_app", host="0.0.0.0", port=80, reload=True, factory=True)
