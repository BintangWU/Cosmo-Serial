import os
import sys
import smbclient
import csv
from pydantic import BaseModel
from typing import List
# from dotenv import load_dotenv  
# load_dotenv()

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
    

NAS_IP = os.getenv("NAS_IP")
NAS_SHARE_FOLDER = os.getenv("NAS_SHARE_FOLDER")
NAS_USERNAME = os.getenv("NAS_USERNAME", default="infinitigroup")
NAS_PASSWORD = os.getenv("NAS_PASSWORD", default="Changeyourpwd36689")
LOG_DIR_NAME = os.getenv("LOG_DIR_NAME", default="Log_Cosmo_Infiniti")

_nas_initialized: bool = False


def log_init() -> bool:
    global _nas_initialized
    
    if not _nas_initialized:
        try:
            smbclient.register_session(
                server=NAS_IP,
                username=NAS_USERNAME,
                password=NAS_PASSWORD,
            )
            _nas_initialized = True
            return True
            
        except Exception as e:
            _nas_initialized = False
            return False


def log_get_path(custom_path: str = "") -> str:
    if custom_path:
        return rf"\\{NAS_IP}\{NAS_SHARE_FOLDER}\{custom_path.lstrip('\\/')}" 
    return rf"\\{NAS_IP}\{NAS_SHARE_FOLDER}"


def log_dir_exist(dir_name: str) -> bool:
    # log_init()
    full_path = dir_name if dir_name.startswith("\\\\") else log_get_path(dir_name)
    return smbclient.path.exists(full_path)


def log_mkdir(dir_name: str) -> bool:
    # log_init()
    full_path = dir_name if dir_name.startswith("\\\\") else log_get_path(dir_name)
    if not log_dir_exist(dir_name):
        smbclient.mkdir(full_path)
        return True
    return False


def log_write_csv(report: TestDataReport, output_path: str):
    # log_init()
    full_path = output_path if output_path.startswith("\\\\") else log_get_path(output_path)
    
    with smbclient.open_file(full_path, "w") as file:    
    # with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)

        # ── Title row ─────────────────────────────────────
        writer.writerow(["Display test data report"])
        writer.writerow([])  # blank line

        # ── Header Block (rows 0–4) ────────────────────────
        # Row 0: Line name, Stand No.
        writer.writerow([
            "Line name", report.line_name, "",
            "Stand No.", f" {report.stand_no}"
        ])

        # Row 1: Engine Type, Test Pattern
        writer.writerow([
            "Engine Type", report.engine_type, "", "", "", "",
            "Test Pattern", report.test_pattern_id, report.test_pattern_name
        ])

        # Row 2: Engine Number, Limit Table
        writer.writerow([
            "Engine Number", report.engine_number, "", "", "", "",
            "Limit Table", report.limit_table_id, report.limit_table_name
        ])

        # Row 3: Var Table
        writer.writerow([
            "", "", "", "", "", "",
            "Var Table", report.var_table_id, report.var_table_name
        ])

        # Row 4: Initial, Final, Retry, Date time
        writer.writerow([
            "Initial", report.initial_result,
            "Final",   report.final_result,
            "Retry",   report.retry_count,
            "Date time", report.date, report.time, ""
        ])

        # ── Blank separator ───────────────────────────────
        writer.writerow([])

        # ── Measurement table sub-header ──────────────────
        writer.writerow([
            "", "", "", "", "", "", "", "",
            "Initial", "", "Final", "", ""
        ])

        # ── Measurement column headers ────────────────────
        writer.writerow([
            "STEP", "No", "Limit index", "No", "Measurement item",
            "L", "H", "Unit",
            "Value", "Judge",   # Initial
            "Value", "Judge",   # Final
            ""
        ])

        # ── Measurement data rows ─────────────────────────
        for m in report.measurements:
            writer.writerow([
                m.step,
                m.no,
                m.limit_index,
                m.meas_no,
                m.item,
                m.low,
                m.high,
                m.unit,
                f"{float(m.initial_value):>8.1f}" if m.initial_value.replace('.','').replace('-','').strip().isdigit() else m.initial_value,
                m.initial_judge,
                f"{float(m.final_value):>8.1f}"   if m.final_value.replace('.','').replace('-','').strip().isdigit()   else m.final_value,
                m.final_judge,
                ""
            ])
    

if __name__ == "__main__":  
    log_init()  
    report = TestDataReport(
        line_name         = "4A9",
        stand_no          = "1",
        engine_type       = "4A91473",
        engine_number     = "K DC7133",
        test_pattern_id   = 6,
        test_pattern_name = "AUTO TEST & SENSORY TEST  rev2",
        limit_table_id    = 1,
        limit_table_name  = "4A91 RN",
        var_table_id      = 1,
        var_table_name    = "4A9",
        initial_result    = "OK",
        final_result      = "OK",
        retry_count       = 0,
        date              = "2025/05/21",
        time              = "16:13:49",
    )
    
    report.measurements = [
        MeasurementRow(step=1, no=1, limit_index="Starting Torque(LOW)", meas_no=902, item="Eng Speed at Max Tq", low=0.0, high=100.0, unit="min-1", initial_value="     93", initial_judge="OK", final_value="     93", final_judge="OK"),
        MeasurementRow(step=1, no=1, limit_index="Starting Torque(LOW)", meas_no=11, item="Engine TEMP", low=0.0, high=50.0, unit="degC", initial_value="   31.2", initial_judge="OK", final_value="   31.2", final_judge="OK"),
        MeasurementRow(step=2, no=4, limit_index="Starting Torque(HI)", meas_no=901, item="Max Torque at Start", low=85.0, high=102.0, unit="N-m", initial_value="   91.3", initial_judge="OK", final_value="   91.3", final_judge="OK"),
        MeasurementRow(step=2, no=4, limit_index="Starting Torque(HI)", meas_no=902, item="Eng Speed at Max Tq", low=25.0, high=300.0, unit="min-1", initial_value="    222", initial_judge="OK", final_value="    222", final_judge="OK"),
        MeasurementRow(step=2, no=4, limit_index="Starting Torque(HI)", meas_no=11, item="Engine TEMP", low=0.0, high=50.0, unit="degC", initial_value="   31.2", initial_judge="OK", final_value="   31.2", final_judge="OK"),
        MeasurementRow(step=5, no=3, limit_index="OCV Mesurement OFF", meas_no=905, item="OCV-OFF Pressure", low=-79.0, high=-75.0, unit="kPa", initial_value="  -76.4", initial_judge="OK", final_value="  -76.4", final_judge="OK"),
        MeasurementRow(step=5, no=3, limit_index="OCV Mesurement OFF", meas_no=906, item="OCV-ON Pressure", low=-36.0, high=-28.0, unit="kPa", initial_value="  -33.3", initial_judge="OK", final_value="  -33.3", final_judge="OK"),
        MeasurementRow(step=5, no=3, limit_index="OCV Mesurement OFF", meas_no=907, item="OCV P-P Pressure", low=44.0, high=50.0, unit="kPa", initial_value="   45.0", initial_judge="OK", final_value="   45.0", final_judge="OK"),
        MeasurementRow(step=5, no=3, limit_index="OCV Mesurement OFF", meas_no=11, item="Engine TEMP", low=0.0, high=50.0, unit="degC", initial_value="   31.2", initial_judge="OK", final_value="   31.2", final_judge="OK"),
        MeasurementRow(step=12, no=10, limit_index="Manual Judge", meas_no=910, item="Manual Judge", low=1.0, high=1.0, unit="      ", initial_value="      1", initial_judge="OK", final_value="      1", final_judge="OK"),
        MeasurementRow(step=12, no=10, limit_index="Manual Judge", meas_no=11, item="Engine TEMP", low=0.0, high=50.0, unit="degC", initial_value="   31.3", initial_judge="OK", final_value="   31.3", final_judge="OK"),
    ]
    
    filename = f"/{LOG_DIR_NAME}/{report.engine_type}_{report.engine_number}_{report.date.replace('/', '')}_{report.time.replace(':', '')}.csv"
    log_write_csv(report, filename)