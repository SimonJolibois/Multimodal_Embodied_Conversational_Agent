import time

from Python.Target import Target


class Message:
    """Generic class for data to be sent to UE5"""
    def __init__(self, target=Target.BASIC, timestamp=time.time()):
        self.timestamp = timestamp
        self.target = target

    def format(self):
        return "    ".join((str(self.timestamp), self.target.name)).encode('utf-8')
