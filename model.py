from pydantic import BaseModel
from typing import Optional, List


class ConfigParams(BaseModel):
    l: float
    h: float
    

class SerialConfig(BaseModel):
    com_port: str
    baudrate: int
    
    
class PlcConfig(BaseModel):
    ip_address: str
    port: int

