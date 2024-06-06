import copy
import logging

import numpy as np
import sklearn.metrics.pairwise as sk
import random
import time

from Python.Line import Line


class Exchange:
    """
    Gather variables for a conversation round, from user input to Text-to-Speech
    Both the input question and the output sentences are considered as Line components
    """

    def __init__(self, input_sentence: str):
        self.input = Line(input_sentence)
        self.timingbegin = time.time()
        self.output = Line()
        self.viseme_timestamp = []
        self.viseme_id = []
        self.output_wav = None
        self.output_wav_duration = None
        self.output_wav_split = []

    def get_answer(self, model, question_list_embedded: list, dict_qa: dict, question_list: list):
        """
        Predict answer from input by calculating the cosine similarity between encoded questions and input

        Inputs:
        model: Embedding model
        question_list_embedded (list): List of vectors corresponding to embedded questions
        dict_qa (dict): dictionary of questions and answers
        question_list (list): List of questions
        """
        self.input.embedded = model.encode(self.input.sentence)
        cos = sk.cosine_similarity([self.input.embedded], question_list_embedded)
        self.input.closest = question_list[np.argmax(cos)]
        logging.debug(f"Best match in database - {self.input.closest}")
        self.output.sentence = random.choice(dict_qa[self.input.closest])

    def set_answer(self, answer):
        self.output.sentence = answer

    def copy(self):
        return copy.deepcopy(self)
