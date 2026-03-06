import asyncio
from email.mime import message
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
from cosmo_serial import CosmoSerial

load_dotenv()
async_lock: asyncio.Lock

COM_PORT= os.getenv("COM_PORT")
BAUDRATE= os.getenv("BAUDRATE")
PLC_HOST= os.getenv("PLC_HOST")
PLC_PORT= os.getenv("PLC_PORT")


class Response(BaseModel):
    status: bool = False
    message: str = None
    data: typing.Any = None
    

class FastAPP(FastAPI):
    sio: socketio.AsyncServer
    serial_transport: typing.Any
    serial_protocol: CosmoSerial


@asynccontextmanager
async def lifespan(app: FastAPP):
    global async_lock
    async_lock = asyncio.Lock()
    
    try:
        loop = asyncio.get_running_loop()
        
        def serial_callback(message):
            asyncio.create_task(get_websocket().emit("cosmo", {"data": message}))
        
        trasport, protocol = await serial_asyncio.create_serial_connection(
            loop,
            lambda: CosmoSerial(callback= serial_callback),
            str(COM_PORT).upper(),
            baudrate= int(BAUDRATE),
        )
        
        app.serial_transport = trasport
        app.serial_protocol = protocol
    except Exception as e:
        print(f"Error initializing serial connection: {e}")
        app.serial_transport = None
        app.serial_protocol = None
    yield
    
    if app.serial_transport:
        app.serial_transport.close()    


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


@app.get("/read-plc-data", response_model=Response, summary="Read data from PLC")
async def read_config():
    # Baca data dari PLC
    return Response(
        status= True, 
        message= "success",
        data= None)


@app.post("/save-plc-data", response_model=Response, summary="Save data to PLC")
async def save_config(config: model.ConfigParams = Body(...)):
    # Save ke PLC
    pass   


@app.get("/serial-status", response_model=Response, summary="Get Serial Port Status")
async def serial_status():
    global async_lock
    
    async with async_lock:
        if app.serial_transport and app.serial_protocol:
            return Response(
                status= True, 
                message= f"Connected to {app.serial_protocol} at {app.serial_protocol} baud.",
                data= None
            )
        else:
            return Response(
                status= False, 
                message= "Serial port not connected.",
                data= None
            )

@app.post("/serial-config", response_model=Response, summary="Update Serial Port Configuration")
async def serial_config(body: model.SerialConfig = Body(...)):
    global async_lock
    
    async with async_lock:
        config_data = body.model_dump_json(indent= 4)
        with open("serial_cfg.json", "w") as file:
            file.write(config_data)
        
        return Response(
            status= True, 
            message= f"Serial configuration updated to {body.com_port} at {body.baudrate} baud.",
            data= None)


