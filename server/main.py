from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
# from fastapi.middleware.cors import CORSMiddleware
from api import api
from auth import auth

app = FastAPI()

# origins = ["*"]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.mount("/public", StaticFiles(directory="../client/public", html=True))

@app.get("/", include_in_schema=False)
async def public():
    return RedirectResponse("/public/", status_code=303)


app.include_router(auth)
app.include_router(api)
