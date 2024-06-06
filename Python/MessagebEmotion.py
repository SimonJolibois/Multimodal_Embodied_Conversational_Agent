import time

from Python.Message import Message
from Python.Target import Target


class MessagebEmotion(Message):
    """Message telling whether we use emotion or not"""

    def __init__(self, bEmotion: bool, artwork):
        super().__init__(target=Target.EMOTION)
        self.bEmotion = bEmotion
        self.artwork = artwork

    def format(self):
        message = "    ".join((str(self.timestamp), self.target.name, str(self.bEmotion), self.artwork)).encode('utf-8')
        return message
