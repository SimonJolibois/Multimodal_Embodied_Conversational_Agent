from enum import Enum, auto


class Target(Enum):
    """Purpose of the message in UE5"""
    BASIC = auto()
    MICROPHONE = auto()
    EXPRESSION = auto()
    FULL_MESSAGE = auto()
    URL = auto()
    EMOTION = auto()