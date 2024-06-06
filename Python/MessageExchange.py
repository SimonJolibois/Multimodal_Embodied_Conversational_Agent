import time

from Python.Emotion import Emotion
from Python.Message import Message
from Python.Target import Target


class MessageExchange(Message):
    """Message with sentence to be said by the agent"""

    def __init__(self, timestamp: float, text: str, emotion: Emotion, viseme_id: list, viseme_ts: list, audio_name: str):
        super().__init__(target=Target.FULL_MESSAGE)
        self.text = text
        self.emotion = emotion
        self.viseme_id = viseme_id
        self.viseme_ts = viseme_ts
        self.audio_name = audio_name
        self.timestamp_processed = 0
        self.timestamp = timestamp

    def processed(self):
        self.timestamp_processed = time.time()

    def get_processing_time(self):
        return self.timestamp_processed - self.timestamp

    @staticmethod
    def preprocess_viseme_id(viseme):
        processed_viseme_id = str(viseme)[1:-1].replace("'", '')
        return processed_viseme_id

    @staticmethod
    def preprocess_viseme_ts(viseme):
        processed_viseme_ts = str(viseme)[1:-1].replace("'", '')
        return processed_viseme_ts

    def format(self):
        message = "    ".join((str(self.timestamp), self.target.name, self.text, str(self.emotion),
                               self.preprocess_viseme_id(self.viseme_id), self.preprocess_viseme_ts(self.viseme_ts), self.audio_name)).encode('utf-8')
        return message
