import os
import sys
import asyncio
from dotenv import load_dotenv

os.chdir(os.path.dirname(os.path.abspath(__file__)))
env_loaded = load_dotenv(dotenv_path=os.path.join(os.getcwd(), '.env'), override=True, )

import csv_log


async def main():
    csv_log.log_init()
    csv_log.log_mkdir(csv_log.LOG_DIR_NAME)
    
    


if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())