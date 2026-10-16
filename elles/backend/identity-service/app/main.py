from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.infrastructure.config import settings
from app.presentation.api import auth, admin
from app.domain.exceptions import (
DomainException, InactiveAccountError, InvalidCredentialsError, EmailAlreadyExistsError
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO)
    print("Starting identity-service | DB postgres")
    yield
    print("Shutting down identity-service | DB postgres")

app = FastAPI(
    title="Identity Service",  version="1.0.0", lifespan=lifespan
)
@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_exception_handler(request: Request, exc: InvalidCredentialsError):
    return JSONResponse(status_code=401, content={"detail":str(exc)})
@app.exception_handler(InactiveAccountError)
async def inactive_account_exception_handler(request: Request, exc: InactiveAccountError):
    return JSONResponse(status_code=403, content={"detail":str(exc)})
@app.exception_handler(EmailAlreadyExistsError)
async def email_exists_handler(request: Request, exc: EmailAlreadyExistsError):
    return JSONResponse(status_code=409, content={"detail":str(exc)})
@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(status_code=422, content={"detail":str(exc)})

app.include_router(auth.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status":"healthy", "service":"identity-service"}