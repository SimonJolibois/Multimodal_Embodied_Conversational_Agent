from Python.Emotion import Emotion


class Agent:
    """
    Correspond to the conversational agent. This class is unused for now.
    """
    def __init__(self):
        self.emotion: Emotion = Emotion.NEUTRAL
        self.expression: str