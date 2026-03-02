import socketio
from fastapi import FastAPI

socket_manager: socketio.AsyncServer

def init_websocket(app: FastAPI, allowed_origins: list[str] = ['*']):
    global socket_manager
    
    sio = socketio.AsyncServer(async_mode= 'asgi', cors_allowed_origins= [])
    sio_app = socketio.ASGIApp(sio, socketio_path= '')
    app.mount('/socket.io', sio_app)
    socket_manager = sio
    app.sio = sio
    

def get_websocket()->socketio.AsyncServer:
    global socket_manager
    return socket_manager
