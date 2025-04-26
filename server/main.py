from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from api import api
from auth import auth, SCHEME

from starsessions import InMemoryStore, SessionMiddleware


app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    store=InMemoryStore(),
    rolling=True,
    cookie_https_only=SCHEME == "https",
    lifetime=3600,
)

app.mount("/public", StaticFiles(directory="../client/public", html=True))


@app.get("/", include_in_schema=False)
async def public():
    return RedirectResponse("/public/", status_code=303)


app.include_router(auth)
app.include_router(api)
