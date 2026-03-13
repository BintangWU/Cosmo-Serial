import rk_mcprotocol as mc
import asyncio
import logging

log = logging.getLogger('plc-control')
plc: mc = None
_heartbead_task: asyncio.Task
_data_reader_task: asyncio.Task


async def plc_init(host: str, port: int):
    global plc
    try:
        plc = mc.open_socket(host, port)
        log.info("PLC connected successfully.")
    except Exception as e:
        log.error(f"Error connecting to PLC: {e}")
        plc = None


async def plc_start_heartbeat():
    global _heartbead_task
    loop = asyncio.get_event_loop()
    
    async def heartbeat():
        while not _heartbead_task.cancelled():
            try:
                log.info("PLC heartbeat ON")
                # mc.write_sign_word(plc, headdevice= 'd0', data_list= [2], signed_type=True)
                await asyncio.sleep(0.5)
                
                log.info("PLC heartbeat OFF")
                # mc.write_sign_word(plc, headdevice= 'd0', data_list= [0], signed_type=True)
                await asyncio.sleep(0.5)
            except Exception as e:
                log.error(f"Error => {e}")
    
    _heartbead_task = loop.create_task(heartbeat())
    

async def plc_stop_heartbeat():
    global _heartbead_task
    _heartbead_task.cancel()
    await asyncio.gather(_heartbead_task, return_exceptions=True)

