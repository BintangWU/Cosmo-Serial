from pydantic import BaseModel
from typing import Optional


class MeasurementInfo(BaseModel):
    line_name: str
    engine_type: str
    engine_number: str


class MeasurementJudge(BaseModel):
    value: int
    judge: str


class MeasurementValue(BaseModel):
    step: int
    no: int
    limit_index: str
    no_item: int
    measurement_item: str
    measurement_l: float
    measurement_h: float
    measurement_unit: str
    iniial: MeasurementJudge | None
    final: MeasurementJudge | None


class ConfigParams(BaseModel):
    l: float
    h: float

