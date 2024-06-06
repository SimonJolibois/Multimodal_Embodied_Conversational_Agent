import numpy as np
import torch
import transformers
import logging

from Python.Exchange import Exchange


class SentenceEmotionClassification:
    """Model for emotion classification of sentence (string)"""

    def __init__(self, path):
        self.model_path = path
        self.label_dict, self.label_dict_inverse = self.choose_label_dict()
        self.model, self.tokenizer = self.load_model()

    @staticmethod
    def choose_label_dict(selected_label_list='no_neutral'):
        """ Choose between multiple label lists which corresponds to the model

        Returns:
        label_dict (dict): Dictionary of emotion keys (str) and index values (int)
        label_dict_inverse (dict): Dictionary of index keys (int) and emotion values (str)
        """
        label_lists = {
            'base': ['admiration', 'amusement', 'anger', 'annoyance', 'approval', 'caring', 'confusion', 'curiosity',
                     'desire', 'disapproval', 'disgust', 'embarrassment', 'excitement', 'fear', 'gratitude', 'grief',
                     'joy', 'love', 'nervousness', 'neutral', 'optimism', 'pride', 'realization', 'relief', 'remorse',
                     'sadness', 'surprise'],
            'small_noneutral': ['anger', 'annoyance', 'confusion', 'curiosity', 'disgust', 'embarrassment',
                                'excitement', 'fear', 'grief', 'joy', 'nervousness', 'pride', 'sadness', 'surprise'],
            'small': ['anger', 'annoyance', 'confusion', 'curiosity', 'disgust', 'embarrassment', 'excitement', 'fear',
                      'grief', 'joy', 'nervousness', 'neutral', 'pride', 'sadness', 'surprise'],
            'reduced2': ['anger', 'disgust', 'excitement', 'fear', 'joy', 'love', 'neutral', 'sadness', 'surprise'],
            'reduced': ['anger', 'confusion', 'curiosity', 'disgust', 'excitement', 'fear', 'joy', 'love',
                        'nervousness', 'neutral', 'sadness', 'surprise'],
            'AU': ['neutral', 'anger', 'pride', 'disgust', 'fear', 'joy', 'sadness', 'surprise'],
            # The original contempt and happy labels are replaced 1 to 1 by respectively pride and joy
        }

        labels = label_lists.get(selected_label_list, label_lists['small_noneutral'])
        label_dict = {emotion: index for index, emotion in enumerate(labels)}
        label_dict_inverse = {index: emotion for emotion, index in label_dict.items()}

        return label_dict, label_dict_inverse

    def load_model(self):
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logging.debug(f"device for sentence model - {device}")
        transformers.logging.set_verbosity_error()
        model = transformers.BertForSequenceClassification.from_pretrained(f".\\models\\uncased_L-2_H-768_A-12",
                                                                           #  'bert-base-uncased',
                                                                           num_labels=len(self.label_dict),
                                                                           output_attentions=False,
                                                                           output_hidden_states=False)
        model.load_state_dict(torch.load(self.model_path, map_location=device))
        model.to(device)
        model.eval()
        tokenizer = transformers.BertTokenizer.from_pretrained('bert-base-uncased', do_lower_case=True)
        return model, tokenizer

    @staticmethod
    def predict(answer: str, model, tokenizer):
        """
        Predict emotion of a sentence using a BERT model and tokenizer.

        Parameters:
        answer (str): The text to be analyzed.
        model (BertForSequenceClassification): Pre-trained BERT model for sequence classification.
        tokenizer (BertTokenizer): Tokenizer corresponding to the BERT model.

        Returns:
        list: Probabilities of each class.
        """
        model.eval()
        encoded_data = tokenizer.batch_encode_plus(
            np.array([answer], dtype=object),
            add_special_tokens=True,
            return_attention_mask=True,
            padding='max_length',
            max_length=128,
            return_tensors='pt')

        input_ids = encoded_data['input_ids']
        attention_masks = encoded_data['attention_mask']

        device = next(model.parameters()).device
        input_ids = input_ids.to(device)
        attention_masks = attention_masks.to(device)

        with torch.no_grad():
            outputs = model(**{'input_ids': input_ids.to(device),
                               'attention_mask': attention_masks.to(device)})

        softmax = torch.nn.Softmax(dim=1)
        probabilities = softmax(outputs.logits).squeeze().tolist()

        return probabilities

    def predict_input(self, exchange: Exchange):
        """Emotion classification of the user input"""
        exchange.input.emotion_prob = self.predict(exchange.input.sentence, self.model, self.tokenizer)
        exchange.input.emotion_index = np.argmax(exchange.input.emotion_prob)
        exchange.input.emotion_confidence = exchange.input.emotion_prob[exchange.input.emotion_index]
        exchange.input.emotion = self.label_dict_inverse[exchange.input.emotion_index]

    def predict_output(self, exchange: Exchange):
        """Emotion classification of the generated answer"""
        exchange.output.emotion_prob = self.predict(exchange.output.sentence, self.model, self.tokenizer)
        exchange.output.emotion_index = np.argmax(exchange.output.emotion_prob)
        exchange.output.emotion_conf = exchange.output.emotion_prob[exchange.output.emotion_index]
        exchange.output.emotion = self.label_dict_inverse[exchange.output.emotion_index]
