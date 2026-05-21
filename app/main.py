from __future__ import annotations

from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.database import init_main_db
from app.core.middleware import SecurityHeadersMiddleware
from app.routers import auth, grades, publish, students
from app.tasks import cleanup_expired_tokens_and_notifications

scheduler = BackgroundScheduler(timezone="Asia/Baghdad")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_main_db()

    if not scheduler.running:
        scheduler.add_job(cleanup_expired_tokens_and_notifications, "interval", hours=12, id="cleanup_job", replace_existing=True)
        scheduler.start()

    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, lifespan=lifespan)

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.default_rate_limit])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(grades.router)
app.include_router(publish.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def auth_exception_handler(request: Request, exc: HTTPException):
    # If the request accepts HTML, redirect to login page (like powerful sites)
    if "text/html" in request.headers.get("accept", ""):
        return RedirectResponse(url="/login")
    return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_error(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": f"Unexpected server error: {type(exc).__name__}"})
