from pydantic import BaseModel
from typing import List

# Output structure
class Risk(BaseModel):
    risk: str
    severity_level: str
    therapeutic_goal: str
    doctor_advise: str
    patient_advise: str
    observations: str

class RisksResponse(BaseModel):
    risks: List[Risk]