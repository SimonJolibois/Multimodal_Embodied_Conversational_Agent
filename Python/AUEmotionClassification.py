import torch

from Python.Net7 import Net7
from Python.Net8 import Net8


class AUEmotionClassification:
    """
    Model for emotion classification of Action Units (based on FACS)
    It can either be with 7 or 8 outputs (if you add or remove "neutral" emotion)
    """

    def __init__(self, path: str):
        self.model_path = path
        self.model = Net7()
        self.model.load_state_dict(torch.load(path))
        self.model.eval()
        self.list_columns = ["frame", " AU01_r", " AU02_r", " AU04_r", " AU05_r", " AU06_r", " AU07_r", " AU09_r",
                             " AU10_r", " AU12_r", " AU14_r", " AU15_r", " AU17_r", " AU20_r", " AU23_r", " AU25_r",
                             " AU26_r", " AU45_r"]
        self.list_emotions = ['anger', 'pride', 'disgust', 'fear', 'joy', 'sadness',
                              'surprise']
        # The original values of OpenFace are ['anger', 'contempt', 'disgust', 'fear', 'happy', 'sadness', 'surprise']
        # They are replaced to match the sentence model emotions
