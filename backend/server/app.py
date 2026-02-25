#!/usr/bin/env python3
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, field_validator

from .config import Routes

app = FastAPI()


class AuditRequest(BaseModel):
    githubUrl: HttpUrl

    @field_validator("githubUrl")
    @classmethod
    def github_repo_must_be_valid(cls, value: HttpUrl):
        if not str(value).startswith("https://github.com/"):
            raise ValueError("URL must be a GitHub Repository")

        parts = str(value).rstrip("/").split("/")
        if len(parts) < 5:
            raise ValueError("GitHub URL must include both owner and repository")
        return value


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    errors = [
        {
            "path": ".".join(str(loc) for loc in err["loc"] if loc != "body"),
            "message": err["msg"],
        }
        for err in exc.errors()
    ]
    return JSONResponse(status_code=422, content=errors)


@app.get(Routes.healthcheck)
def healthcheck():
    return {"running": True}


@app.post(Routes.audit, status_code=status.HTTP_201_CREATED)
def post_audit(payload: AuditRequest):
    return {"githubURL": payload.githubUrl}
