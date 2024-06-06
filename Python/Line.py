from Python.Emotion import Emotion


class Line:
    def __init__(self, sentence: str = ""):
        self.sentence = sentence
        self.embedded = []
        self.closest: str = ""
        self.emotion = Emotion.NEUTRAL
        self.emotion_prob = []
        self.emotion_index: int = 0
        self.emotion_conf: float = 0
