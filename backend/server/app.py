#!/usr/bin/env python3
from fastapi import FastAPI

from .config import Routes

app = FastAPI()


@app.get(Routes.healthcheck)
def healthcheck():
    return {"running": True}
