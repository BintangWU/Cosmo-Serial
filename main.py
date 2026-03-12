import asyncio
from email.mime import message
import serial_asyncio
import sys
import os
import typing
import json
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
import socketio
import uvicorn


sys.path.insert(0, os.path.dirname(__file__))
import model
import pyPlc
from csv_log import TestDataReport, MeasurementRow, generate_csv
from ws_manager import init_websocket, get_websocket
from cosmo_serial import CosmoSerial, CosmoModel_ExcessTh

load_dotenv()
async_lock: asyncio.Lock
cosmo_data: typing.Any = None

COM_PORT= os.getenv("COM_PORT")
BAUDRATE= os.getenv("BAUDRATE")
PLC_HOST= os.getenv("PLC_HOST")
PLC_PORT= os.getenv("PLC_PORT")
LOG_DIR = "Log-Cosmo"


class Response(BaseModel):
    status: bool = False
    message: str = None
    data: typing.Any = None
    

class FastAPP(FastAPI):
    sio: socketio.AsyncServer
    serial_transport: typing.Any
    serial_protocol: CosmoSerial
    plc_heartbeat_task: typing.Any = None
    

@asynccontextmanager
async def lifespan(app: FastAPP):
    global async_lock
    async_lock = asyncio.Lock()
    os.makedirs(LOG_DIR, exist_ok=True)    
    
    # Initialize PLC connection and start heartbeat
    try:
        await pyPlc.plc_init(PLC_HOST, int(PLC_PORT))
        app.plc_heartbeat_task = asyncio.create_task(pyPlc.plc_heartbeat())
        print("PLC heartbeat task started")
    except Exception as e:
        print(f"Error initializing PLC: {e}")
        app.plc_heartbeat_task = None
    
    try:
        loop = asyncio.get_running_loop()
        current_log = {
            "file": None,
            "session": None
        }
        
        def serial_callback(message):
            global cosmo_data
        
            session_key = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            msg = message.replace('\x02', '').replace('\x03', '').replace('\n', '').replace('\r', '')
            msg = msg.split(',')
            # print(f"Received message: {msg}")
            
            cosmo_data = CosmoModel_ExcessTh(
                date = msg[0][:6],
                time = msg[0][6:],
                item= msg[1],
                channel= msg[2],
                judge_result= msg[3],
                log_number= msg[4],
                filter= msg[5],
                judge_number_type= msg[6],
                judge_type= msg[7][:2],
                summary= msg[7][2:],
            )
            
            # if current_log["file"] is None:
            #     current_log["session"] = session_key
            #     current_log["file"] = os.path.join(LOG_DIR, f"cosmo_log_{session_key}.txt")
            
            # with open(current_log["file"], "a") as file:
            #     file.write(f"{datetime.now().isoformat()} - {message}\n")
            
            # current_log["file"] = None
            asyncio.create_task(get_websocket().emit("cosmo", {"data": cosmo_data.model_dump()}))
        
        trasport, protocol = await serial_asyncio.create_serial_connection(
            loop,
            lambda: CosmoSerial(callback= serial_callback),
            str(COM_PORT).upper(),
            baudrate= int(BAUDRATE),
            parity= serial_asyncio.serial.PARITY_EVEN,
            stopbits= serial_asyncio.serial.STOPBITS_ONE,
        )
        
        app.serial_transport = trasport
        app.serial_protocol = protocol
        
    except Exception as e:
        print(f"Error initializing serial connection: {e}")
        app.serial_transport = None
        app.serial_protocol = None
    
    yield
    
    # Cleanup: Stop PLC heartbeat task
    if app.plc_heartbeat_task:
        app.plc_heartbeat_task.cancel()
        try:
            await app.plc_heartbeat_task
        except asyncio.CancelledError:
            print("PLC heartbeat task cancelled")
    
    # Cleanup: Close serial connection
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


@app.get("/health", summary="Health Check for Docker")
async def health_check():
    """Simple health check endpoint for Docker container monitoring."""
    return {"status": "healthy", "service": "cosmo-serial"}


@app.get("/status", response_model=Response, summary="Get Serial Port Status")
async def serial_status():
    global async_lock
    serial_status =  True if app.serial_transport and app.serial_protocol else False
    
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


@app.post("./Config/serial-config", response_model=Response, summary="Update Serial Port Configuration")
async def serial_config(body: model.SerialConfig = Body(...)):
    global async_lock
    
    async with async_lock:
        config_data = body.model_dump_json(indent= 4)
        with open("serial_cfg.json", "w") as file:
            file.write(config_data)
        
        return Response(
            status= True, 
            message= f"Serial configuration updated to {body.com_port} at {body.baudrate} baud.",
            data= None
            )
        
@app.post("/plc-config", response_model=Response, summary="Update PLC Configuration")
async def plc_config(body: model.PlcConfig = Body(...)):
    global async_lock
    
    async with async_lock:
        config_data = body.model_dump_json(indent= 4)
        with open("./Config/plc_cfg.json", "w") as file:
            file.write(config_data)
        
        return Response(
            status= True, 
            message= f"PLC configuration updated to {body.ip_address}:{body.port}.",
            data= None
            )

# async def server_async():    
#     server_config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
#     server_run = uvicorn.Server(server_config)
#     return await server_run.serve()


# async def main():
#     await pyPlc.plc_init(PLC_HOST, int(PLC_PORT))
#     asyncio.create_task(pyPlc.plc_heartbeat())
    
# if __name__ == "__main__":
#     asyncio.run(server_async())