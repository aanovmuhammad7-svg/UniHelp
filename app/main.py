from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.events import create_start_app_handler, create_stop_app_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_start_app_handler(app, settings)()
    try:
        yield
    finally:
        await create_stop_app_handler(app)()

def get_application() -> FastAPI:
    settings.configure_logging()

    application = FastAPI(
        lifespan=lifespan,
        **settings.fastapi_kwargs
    )

    return application


app = get_application()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
