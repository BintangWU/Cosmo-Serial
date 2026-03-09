from pydantic import BaseModel
from typing import Optional, List



class MeasurementRow(BaseModel):
    step: int
    no: int
    limit_index: str
    meas_no: int
    item: str
    low: float
    high: float
    unit: str
    initial_value: str
    initial_judge: str
    final_value: str
    final_judge: str


class TestDataReport(BaseModel):
    line_name: str
    stand_no: str
    engine_type: str
    engine_number: str
    test_pattern_id: int
    test_pattern_name: str
    limit_table_id: int
    limit_table_name: str
    var_table_id: int
    var_table_name: str
    initial_result: str
    final_result: str
    retry_count: int
    date: str
    time: str
    measurements: List[MeasurementRow] = []


class ConfigParams(BaseModel):
    l: float
    h: float
    

class SerialConfig(BaseModel):
    com_port: str
    baudrate: int

