import operator
import pandas as pd
import torch

from Python.Emotion import Emotion


class Webcam:
    def __init__(self):
        self.au_list = []
        self.au_prediction: int = 0
        self.au_prediction_name = Emotion.NEUTRAL
        self.au_probabilities = []
        self.label = ['anger', 'pride', 'disgust', 'fear', 'joy', 'sadness', 'surprise']

    def update(self):
        window = 10
        address = ".\\webcam\\user_face.csv"
        list_columns = ["frame", " AU01_r", " AU02_r", " AU04_r", " AU05_r", " AU06_r", " AU07_r", " AU09_r",
                        " AU10_r", " AU12_r", " AU14_r", " AU15_r", " AU17_r", " AU20_r", " AU23_r", " AU25_r",
                        " AU26_r", " AU45_r"]
        df = pd.read_csv(address, header=0, sep=',', usecols=list_columns, encoding='utf-8')
        self.au_list = df.iloc[-window:, 1:].mean().tolist()

    def predict(self, model):
        au_softmax = torch.nn.Softmax(dim=0)
        au_outputs = model.model(torch.tensor(self.au_list))
        self.au_probabilities = au_softmax(torch.FloatTensor(au_outputs)).tolist()
        self.au_prediction = self.au_probabilities.index(max(self.au_probabilities))
        self.au_prediction_name = self.label[self.au_prediction]
