from Python.Message import Message
from Python.Target import Target


class MessageMic(Message):
    """Message for the mic to be turned on (True) or off (False)"""
    def __init__(self, status: bool):
        super().__init__(target=Target.MICROPHONE)
        self.mic_status = status

    def format(self):
        return "    ".join((str(self.timestamp), self.target.name, str(self.mic_status))).encode('utf-8')
