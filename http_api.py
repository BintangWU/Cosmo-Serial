import asyncio
import serial_asyncio
import sys
import os
import typing
import uvicorn
from datetime import datetime
from dotenv import load_dotenv  
from fastapi import FastAPI, File, UploadFile, Query, applications, Body
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import fastapi_offline_swagger_ui
import uvicorn
import socketio
import logging


sys.path.insert(0, os.path.dirname(__file__))
import model
import pyPlc
import cosmo_serial


COM_PORT= os.getenv("COM_PORT")
BAUDRATE= os.getenv("BAUDRATE")
PLC_HOST= os.getenv("PLC_HOST")
PLC_PORT= os.getenv("PLC_PORT")
LOG_DIR = "Log-Cosmo"


log = logging.getLogger('http-api')
_serial_transport: typing.Any
_serial_protocol: cosmo_serial.CosmoSerial

_async_lock: asyncio.Lock
_cosmo_data: cosmo_serial.CosmoModel_ExcessTh
_cosmo_data_list: typing.List[cosmo_serial.CosmoModel_ExcessTh] = []


class Response(BaseModel):
    status: bool = False
    message: str = None
    data: typing.Any = None
    

class FastAPP(FastAPI):
    sio: socketio.AsyncServer


@asynccontextmanager
async def lifespan(app: FastAPP):
    global _async_lock
    _async_lock = asyncio.Lock()
    
    try:
        loop = asyncio.get_running_loop()
        
        def serial_callback(message):
            session_key = datetime.now().strftime("%Y%m%d%H%M%S")
            msg = message.replace('\x02', '').replace('\x03', '').replace('\n', '').replace('\r', '')
            msg = msg.split(',')
            
            _cosmo_data = cosmo_serial.CosmoModel_ExcessTh(
                date = msg[0][:6],
                time = msg[0][6:],
                item= msg[1],
                channel= msg[2],
                judge_result= msg[3],
                log_number= msg[4],
                filter= msg[5],
                judge_number_type= msg[6],
                judge_type= msg[7][:2],
                summary= msg[7][2:]
            )
            
        _serial_transport, _serial_protocol = await serial_asyncio.create_serial_connection(
            loop,
            lambda: cosmo_serial.CosmoSerial(callback= serial_callback),
            str(COM_PORT).upper(),
            baudrate= int(BAUDRATE),
            parity= serial_asyncio.serial.PARITY_EVEN,
            stopbits= serial_asyncio.serial.STOPBITS_ONE
        )
        log.info(f"Serial connection established on port {COM_PORT} at baudrate {BAUDRATE}")
            
    except Exception as e:
        _serial_transport = None
        _serial_protocol = None
        log.error(f"Error establishing serial connection: {e}")
    yield
    
    # Cleanup: Close serial connection
    if _serial_transport:
        _serial_transport.close()
    

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
    

@app.get("/health", summary="Health Check for Docker")
async def health_check():
    """Simple health check endpoint for Docker container monitoring."""
    return {"status": "healthy", "service": "cosmo-serial"}


async def server_async():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, headers=[("server", "cosmo-serial"), ("INFINITI", "SID-DEPT")], log_level="info")
    server = uvicorn.Server(config)
    return await server.serve()
