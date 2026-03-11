import rk_mcprotocol as mc
import time
import asyncio

plc: mc = None

async def plc_init(host: str, port: int):
    global plc
    try:
        plc = mc.open_socket(host, port)
    except Exception as e:
        print(f"Error connecting to PLC: {e}")
        plc = None


async def plc_heartbeat():
    global plc
    
    while True:
        if plc:
            try:
                # mc.write_bit(plc, headdevice= 'm0', data_list= [1])
                mc.write_sign_word(plc, headdevice= 'd0', data_list= [2], signed_type=True)
                await asyncio.sleep(0.5)
                
                # mc.write_bit(plc, headdevice= 'm0', data_list= [0])
                mc.write_sign_word(plc, headdevice= 'd0', data_list= [0], signed_type=True)
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"PLC heartbeat failed: {e}")
                plc = None