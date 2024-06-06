from Python.Emotion import Emotion
from Python.Message import Message
from Python.Target import Target


class MessageExpression(Message):
    """Message with expression for agent"""
    def __init__(self, emotion: Emotion):
        super().__init__(target=Target.EXPRESSION)
        self.emotion = emotion

    def format(self):
        return "    ".join((str(self.timestamp), self.target.name, str(self.emotion))).encode('utf-8')