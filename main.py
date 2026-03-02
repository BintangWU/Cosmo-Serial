import asyncio
import serial_asyncio
import sys
import os
import typing
import json
from dotenv import load_dotenv  
from fastapi import FastAPI, File, UploadFile, Query, applications, Body
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import fastapi_offline_swagger_ui
import socketio


sys.path.insert(0, os.path.dirname(__file__))
import model
from ws_manager import init_websocket, get_websocket


async_lock: asyncio.Lock

class Response(BaseModel):
    status: bool = False
    message: str = None
    data: typing.Any = None
    

class FastAPP(FastAPI):
    sio: socketio.AsyncServer


@asynccontextmanager
async def lifespan(app: FastAPP):
    global async_lock
    async_lock = asyncio.Lock()
    yield


app = FastAPP(
    title= "MMKI Noise Sensor Tracebility",
    version= "1.0.0",
    description= "MMKI Noise Sensor Tracebility",
    lifespan= lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


assets_path = fastapi_offline_swagger_ui.__path__[0]
if os.path.exists(assets_path + "/swagger-ui.css") and os.path.exists(assets_path + "/swagger-ui-bundle.js"):
    app.mount("/assets", StaticFiles(directory=assets_path), name="static")

    def swagger_monkey_patch(*args, **kwargs):
        return get_swagger_ui_html(
            *args,
            **kwargs,
            swagger_favicon_url="",
            swagger_css_url="/assets/swagger-ui.css",
            swagger_js_url="/assets/swagger-ui-bundle.js",
        )
    applications.get_swagger_ui_html = swagger_monkey_patch
    
init_websocket(app, ['*'])


@app.get("/status", response_model=Response, summary="Get Server Status")
async def get_status():
    global async_lock
    
    async with async_lock:
        await get_websocket().emit("status", {"status": "Server is running"})
        return Response(
            status= True, 
            message= "Server is running")


@app.get("/read-config", response_model=Response, summary="Read Configuration")
async def read_config():
    # Read dari PLC
    # config = model.ConfigParams(l= 0.0, h= 0.0)
    return Response(
        status= True, 
        message= "success",
        data= None)


@app.post("/save-config", response_model=Response, summary="Save Configuration")
async def save_config(config: model.ConfigParams = Body(...)):
    # Save ke PLC
    pass    


