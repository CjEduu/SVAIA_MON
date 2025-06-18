from typing import Union

from pydantic import BaseModel, ValidationError


class SystemMetric(BaseModel):
    total_memory:int
    used_memory:int
    total_swap:int
    used_swap:int
    cpu_usage:float
    load_avg:tuple[float,float,float]
    uptime:int

class FileLog(BaseModel):
    attrs: dict
    kind: str
    mode: str
    paths: list[str]
    type: str

class ToLog(BaseModel):
    message_type:str
    host:str
    timestamp:str
    data: Union[SystemMetric,FileLog]
    


def validate_data(data:str)->Union[ToLog,None]:
    try:
        result:ToLog = ToLog.model_validate_json(data)
    except ValidationError as e:
        print(f"Failed to validate {data}: {e}")
        result = None
    
    return result
