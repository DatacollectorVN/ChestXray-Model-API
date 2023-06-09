import os, uuid, sys
sys.path.append(os.getcwd())
from app.src.utils import logger
from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute, APIRouter 
import uvicorn
import time

# add router
from app.routers import call_endpoint_model

app = FastAPI(
    title= 'XRay Model Endpoint',
    description = 'Open Beta V.001',
    version = '0.0.1',
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

app.include_router(call_endpoint_model.router)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)