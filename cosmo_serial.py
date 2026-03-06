import os
import sys
import json
import asyncio
import serial_asyncio
import typing
from pydantic import BaseModel


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
            # print(f"Received raw data: {msg}")  # Debug: print raw data received
            msg = msg.replace('\n', '')
            self.buffer.append(msg)
            
        loop = asyncio.get_running_loop()
        if self.timeout_handle:
            self.timeout_handle.cancel()
        self.timeout_handle = loop.call_later(1, self.on_timeout)


    def on_timeout(self):
        data = self.buffer.copy()
        data = [item.replace('\r', '&&') for item in data if item.strip() != '']
        data = ''.join(data).split('&&')
        data.pop()
        
        try:
            if self.callback:
                if (len(data) > 1) and (data[-1] == ''):
                    data.pop()
                # print(f"Received raw data: {data}")  # Debug: print raw data received
                
                message = data
                self.callback(message) #Callback returns data to handler
        except Exception as e:
            print(f"Error in callback: {e}", file= sys.stderr)
        finally:
            self.buffer.clear()


def handler_message(message):
    print(f"Received message: {message}")
    

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
            baudrate
        )
        print(f"Connected to {comPort} at {baudrate} baud.")
        
        await asyncio.Event().wait()
    except Exception as e:
        print(f"Failed to connect to {comPort} at {baudrate} baud: {e}", file= sys.stderr)

            
if __name__ == "__main__":
    comPort = input("Your Port: ")
    baudrate = get_valid_baudrate()
            
    asyncio.run(main(str(comPort).upper(), int(baudrate)))
