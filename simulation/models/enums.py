# simulation/models/enums.py

from enum import Enum


class Role(Enum):
    LEADER = "leader"
    VALIDATOR = "validator"
    APPEALANT = "appealant"


class LeaderResult(Enum):
    RECEIPT = "R"
    TIMEOUT = "T"
    IDLE = "I"


class Vote(Enum):
    AGREE = "A"
    DISAGREE = "D"
    TIMEOUT = "T"
    IDLE = "I"
    DET_VIOLATION = "V"


class AppealType(Enum):
    TRIBUNAL = "T"
    LEADER = "L"
    VALIDATOR = "V"
