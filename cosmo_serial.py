import os
import sys
import json
import asyncio
import serial_asyncio
import typing
from pydantic import BaseModel


class CosmoModel_ExcessTh(BaseModel):
    date: str
    time: str
    item: int
    channel: typing.Optional[int] = 1
    filter: int
    log_number: int
    judge_result: str
    judge_number_type: int
    judge_type: int
    summary: str

class CosmoModel_NumberExcessTh(BaseModel):
    pass

class CosmoModel_DurationExcessTh(BaseModel):
    pass

class CosmoModel_Attenuation(BaseModel):
    pass

class CosmoModel_Inclanation(BaseModel):
    pass

class CosmoModel_Undulation(BaseModel):
    pass

class CosmoModel_Waveform(BaseModel):
    pass


class CosmoSerial(asyncio.Protocol):
    def __init__(self, callback= None):
        self.callback = callback
        self.buffer = []
        self.timeout_handle = None


    def connection_made(self, transport):
        """Called when serial connection is established"""
        self.transport = transport
        print(f"✓ Serial port opened successfully", file=sys.stderr)
        print(f"✓ Connected to: {transport.serial.port}", file=sys.stderr)
        print(f"✓ Baudrate: {transport.serial.baudrate}", file=sys.stderr)
        print(f"✓ Waiting for data...", file=sys.stderr)
    
    
    def connection_lost(self, exc):
        """Called when serial connection is lost"""
        if exc:
            print(f"✗ Serial connection lost with error: {exc}", file=sys.stderr)
        else:
            print(f"✗ Serial connection closed", file=sys.stderr)


    def data_received(self, data):
        msg = data.decode('utf-8')
        if msg:
            msg = msg.replace('\n', '')
            self.buffer.append(msg)
            
        loop = asyncio.get_running_loop()
        if self.timeout_handle:
            self.timeout_handle.cancel()
        self.timeout_handle = loop.call_later(1, self.on_timeout)


    def on_timeout(self):
        message = self.buffer.copy()
        message = ''.join(message)        
        
        try:
            if message != "" and message is not None:
                if self.callback:
                    # print(f"Received2: {data}")  # Debug: print raw data received
                    self.callback(message) #Callback returns data to handler
        except Exception as e:
            print(f"Error in callback: {e}", file= sys.stderr)
        finally:
            self.buffer.clear()

# ----------------------------------------------------------------------------------------------
# Untuk Trial 
# ----------------------------------------------------------------------------------------------

def handler_message(message):
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
        summary= msg[7][2:]
        )
    

def get_valid_baudrate() -> int:
    while True:
        try:
            baudrate = input("Enter baudrate (default 9600): ") or "9600"
            if baudrate.isdigit():
                return int(baudrate)
            else:
                print("Invalid input. Please enter a numeric baudrate.")
        except Exception as e:
            print(f"Error: {e}. Please try again.")


async def main(comPort: str, baudrate: int):
    loop = asyncio.get_running_loop()
    try:
        transport, protocol = await serial_asyncio.create_serial_connection(
            loop, 
            lambda: CosmoSerial(callback= handler_message), 
            comPort,
            baudrate,
            parity=serial_asyncio.serial.PARITY_EVEN,
            stopbits=serial_asyncio.serial.STOPBITS_ONE,
        )
        print(f"Connected to {comPort} at {baudrate} baud.")
        
        await asyncio.Event().wait()
    except Exception as e:
        print(f"Failed to connect to {comPort} at {baudrate} baud: {e}", file= sys.stderr)

            
if __name__ == "__main__":
    comPort = input("Your Port: ")
    baudrate = get_valid_baudrate()          
    asyncio.run(main(str(comPort).upper(), int(baudrate)))
