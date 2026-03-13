import os
import sys
import asyncio
from dotenv import load_dotenv

os.chdir(os.path.dirname(os.path.abspath(__file__)))
env_loaded = load_dotenv(dotenv_path=os.path.join(os.getcwd(), '.env'), override=True, )
import pyPlc
import http_api

async def main():
    await pyPlc.plc_start_heartbeat()
    await http_api.server_async()
    
    #HTTP API Stopped, shutdown all services  
    await pyPlc.plc_stop_heartbeat()
    
    
if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())