from abc import ABC
from enum import Enum
from dataclasses import dataclass


class BookletTypes(Enum):
    OKT = "OKT"
    DDK = "DDK"
    AK = "AK"

class StampType(Enum):
    Digital = "digistamp"
    Kezi = "register"


@dataclass
class JSONBH(ABC):
    mtsz_id: str
    stampType:StampType
    timestamp:int