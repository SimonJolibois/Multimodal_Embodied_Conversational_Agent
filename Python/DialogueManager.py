import logging
import re
import random
import sentence_transformers

from Python.Agent import Agent
from Python.Artwork import Artwork
from Python.AUEmotionClassification import AUEmotionClassification
from Python.Azure import Azure
from Python.Emotion import Emotion
from Python.Exchange import Exchange
from Python.MessageMic import MessageMic
from Python.SentenceEmotionClassification import SentenceEmotionClassification
from Python.Socket import Socket
from Python.Webcam import Webcam

from typing import Dict, List, Tuple


class DialogueManager:
    def __init__(self, path: str):
        self.dialogue = []
        self.dict_qa, self.question_list = self.create_dictionary(path)
        self.embedding_model = sentence_transformers.SentenceTransformer('paraphrase-MiniLM-L3-v2')
        self.question_list_embedded = self.embedding_model.encode(self.question_list)
        self.agent = Agent()
        self.azure = Azure()
        self.webcam = Webcam()
        self.socket = Socket()
        self.sentence_model = SentenceEmotionClassification(
            ".\\models\\uncased_L-2_H-768_A-12_small_remove__noneutral_16b_2e_5e-05lr.model")
        #    ".\\models\\remove_small_noneutral_finetuned_BERT_4epoch.model")  #  choose another model
        self.au_model = AUEmotionClassification(".\\models\\au_classifier_v2.pth")
        self.artwork = None

    def set_artwork(self, name: str):
        """
        Modify the generic dictionary to fit the information of the selected artwork, and the list of questions
        """
        self.artwork = Artwork(name)
        self.dict_qa = self.adapt_to_artwork(self.dict_qa, self.artwork.data)
        self.question_list = [self.update_markers(question, self.artwork.data) for question in self.question_list]

    @staticmethod
    def create_dictionary(path: str) -> Tuple[Dict[str, List[str]], List[str]]:
        """
        Create a dictionary from a  CSV file.

        Parameters:
        path (str): Path to the file

        Returns:
        dict_qa (dict): Dictionary with Question keys (str) and Answer Values (str)
        questions_list (list): List of all question keys
        """
        dict_qa = {}
        questions_list = []

        with open(path, 'r') as file:
            lines = file.readlines()
        lines = [line.strip() for line in lines if line.strip()]

        # Each question can have multiple answers
        for i in range(0, len(lines), 3):
            question_line = lines[i]
            answer_line = lines[i + 1] if i + 1 < len(lines) else ""

            questions = [q.strip() for q in question_line.split(';') if q.strip()]
            answers = [a.strip() for a in answer_line.split(';') if a.strip()]

            for question in questions:
                if question not in dict_qa:
                    dict_qa[question] = answers
                    questions_list.append(question)

        return dict_qa, questions_list

    @staticmethod
    def update_markers(sentence: str, art_data: dict):
        """
        Remove markup elements in a sentence and replace it by data from a dictionary

        Parameters:
        sentence (str): Sentence to be processed
        art_data (dict): Dictionary with markup keys (str) and sentence values (str)

        Returns:
        up_sentence (str): Processed sentence
        """
        m_list = re.findall(r'<(.+?)>', sentence)
        m_list = [i for i in m_list if i.isupper()]
        up_sentence = sentence

        for m in m_list:
            if m in ['OTHER_ARTWORK_NAME', 'OTHER_ARTWORK_LINK', 'OTHER_ARTWORK_DATE']:
                if len(art_data['artwork_info']['related_works']) > 0:
                    selected_artwork = random.choice(art_data['artwork_info']['related_works'])
                    marker_spec = {
                        'OTHER_ARTWORK_NAME': selected_artwork['title'],
                        'OTHER_ARTWORK_DATE': selected_artwork['year_created'],
                        'OTHER_ARTWORK_LINK': selected_artwork['link'],
                    }
                    up_sentence = up_sentence.replace(f"<{m}>", str(marker_spec[m]))
                else:
                    up_sentence = "I don't know what other artworks the artist did."

            elif m in ['INSPIRATION_NAME', 'INSPIRATION_DESCRIPTION', 'INSPIRATION_LINK']:
                if len(art_data['artwork_info']['inspirations']) > 0:
                    selected_artwork = random.choice(art_data['artwork_info']['inspirations'])
                    marker_spec = {
                        'INSPIRATION_NAME': selected_artwork['inspiration_name'],
                        'INSPIRATION_DESCRIPTION': selected_artwork['description'],
                        'INSPIRATION_LINK': selected_artwork['inspiration_link'],
                    }
                    up_sentence = up_sentence.replace(f"<{m}>", str(marker_spec[m]))
                else:
                    up_sentence = "I don't know on which inspirations the artist based his or her craft."

            elif m == 'COLOR':
                color_string = ",".join(art_data['artwork_info']['color'])
                up_sentence = up_sentence.replace(f"<{m}>", color_string)

            elif m in ['BRUSH_NAME', 'BRUSH_DESCRIPTION', 'BRUSH_LINK']:
                if len(art_data['artwork_info']['brush']) > 0:
                    selected_artwork = random.choice(art_data['artwork_info']['brush'])
                    marker_spec = {
                        'BRUSH_NAME': selected_artwork['name'],
                        'BRUSH_DESCRIPTION': selected_artwork['description'],
                        'BRUSH_LINK': selected_artwork['link'],
                    }
                    up_sentence = up_sentence.replace(f"<{m}>", str(marker_spec[m]))
                else:
                    up_sentence = "I don't know of brush."

            elif m in ['EXHIBITION_NAME', 'EXHIBITION_LOCATION', 'EXHIBITION_DATE', 'EXHIBITION_LINK',
                       'EXHIBITION_DESCRIPTION']:
                if len(art_data['artwork_info']['exhibition']) > 0:
                    selected_artwork = random.choice(art_data['artwork_info']['exhibition'])
                    marker_spec = {
                        'EXHIBITION_NAME': selected_artwork['name'],
                        'EXHIBITION_LOCATION': selected_artwork['location'],
                        'EXHIBITION_DATE': selected_artwork['date'],
                        'EXHIBITION_LINK': selected_artwork['link'],
                        'EXHIBITION_DESCRIPTION': selected_artwork['description'],
                    }
                    up_sentence = up_sentence.replace(f"<{m}>", str(marker_spec[m]))
                else:
                    up_sentence = "I don't know of any exhibition displaying this artwork."

            elif m in ['OWNER_LINK', 'OWNER_NAME', 'OWNER_DATE']:
                if len(art_data['artwork_info']['ownership_history']) > 0:
                    selected_artwork = random.choice(art_data['artwork_info']['ownership_history'])
                    marker_spec = {
                        'OWNER_LINK': selected_artwork['source_link'],
                        'OWNER_NAME': selected_artwork['owner_name'],
                        'OWNER_DATE': selected_artwork['period_owned'],
                    }
                    up_sentence = up_sentence.replace(f"<{m}>", str(marker_spec[m]))
                else:
                    up_sentence = "I don't know about the previous owners of the artwork."

            elif m in ['SALE_DATE', 'SALE_PRICE', 'SALE_LINK']:
                if len(art_data['artwork_info']['sale_history']) > 0:
                    selected_artwork = random.choice(art_data['artwork_info']['sale_history'])
                    marker_spec = {
                        'SALE_PRICE': selected_artwork['selling_price'],
                        'SALE_LINK': selected_artwork['source_link'],
                        'SALE_DATE': selected_artwork['sale_date'],
                    }
                    up_sentence = up_sentence.replace(f"<{m}>", str(marker_spec[m]))
                else:
                    up_sentence = "I don't know about the sale history of the painting."

            elif m in ['ANALYSIS_TYPE', 'ANALYSIS_SUMMARY', 'ANALYSIS_DESCRIPTION', 'ANALYSIS_LINK']:
                if len(art_data['artwork_info']['technical_analysis']) > 0:
                    selected_artwork = random.choice(art_data['artwork_info']['technical_analysis'])
                    marker_spec = {
                        'ANALYSIS_TYPE': selected_artwork['analysis_type'],
                        'ANALYSIS_SUMMARY': selected_artwork['analysis_summary'],
                        'ANALYSIS_DESCRIPTION': selected_artwork['analysis_description'],
                        'ANALYSIS_LINK': selected_artwork['analysis_link'],
                    }
                    up_sentence = up_sentence.replace(f"<{m}>", str(marker_spec[m]))
                else:
                    up_sentence = "I don't know about the analysis done on the artwork."

            else:
                marker_map = {
                    'NAME': art_data['artwork_info']['title'],
                    'ORIGIN_NAME': art_data['artwork_info']['original_title'],
                    'TYPE': art_data['artwork_info']['type'],
                    'AUTHOR': art_data['artwork_info']['author']['name'],
                    'AUTHOR_DESCRIPTION': art_data['artwork_info']['author']['description'],
                    'AUTHOR_LINK': art_data['artwork_info']['author']['bio_link'],
                    'DATE': art_data['artwork_info']['year_created'],
                    'CREATION_LOCATION': art_data['artwork_info']['location_created'],
                    'DIMENSION': art_data['artwork_info']['dimensions'],
                    'STYLE': art_data['artwork_info']['style']['name'],
                    'STYLE_DEFINITION': art_data['artwork_info']['style']['description'],
                    'STYLE_LINK': art_data['artwork_info']['style']['link'],
                    'GENRE': art_data['artwork_info']['genre'],
                    'FORMAT': art_data['artwork_info']['format'],
                    'SUBJECT_MATTER': art_data['artwork_info']['subject_matter']['subject_type'],
                    'SUBJECT_MATTER_LINK': art_data['artwork_info']['subject_matter']['subject_link'],
                    'VISUAL_DESCRIPTION': art_data['artwork_info']['visual_description'],
                    'MATERIAL': art_data['artwork_info']['medium']['materials_used'],
                    'MEDIUM_LINK': art_data['artwork_info']['medium']['medium_link'],
                    'SUPPORT': art_data['artwork_info']['medium']['support'],
                    'CULTURAL_CONTEXT': art_data['artwork_info']['cultural_context']['context_summary'],
                    'CULTURAL_CONTEXT_LINK': art_data['artwork_info']['cultural_context']['context_link'],
                    'HISTORICAL_CONTEXT': art_data['artwork_info']['historical_context']['context_summary'],
                    'HISTORICAL_CONTEXT_LINK': art_data['artwork_info']['historical_context']['context_link'],
                    'ARTISTIC_MESSAGE': art_data['artwork_info']['artistic_message']['message'],
                    'ARTISTIC_MESSAGE_LINK': art_data['artwork_info']['artistic_message']['message_link'],
                    'CONSERVATION_LOCATION': art_data['artwork_info']['conservation']['location'],
                    'CONSERVATION_LOCATION_LINK': art_data['artwork_info']['conservation']['location_link'],
                    'CONSERVATION_METHOD': art_data['artwork_info']['conservation']['methods'],
                    'CONDITION': art_data['artwork_info']['conservation']['condition'],
                    'CONSERVATION_FRAME': art_data['artwork_info']['conservation']['frame'],
                    'COMPOSITION': art_data['artwork_info']['composition'],
                    'PROCESS_SUMMARY': art_data['artwork_info']['creation_process']['process_summary'],
                    'PROCESS_LINK': art_data['artwork_info']['creation_process']['process_link'],
                }
                up_sentence = up_sentence.replace(f"<{m}>", str(marker_map[m]))
        up_sentence = up_sentence.replace('__', "'")
        return up_sentence

    def adapt_to_artwork(self, dictionary: dict, art_data: dict):
        """
        Remove markup elements in dictionary items and replace them with data from another dictionary.

        Parameters:
        dictionary (dict): Dictionary to be processed (question-answer pairs)
        art_data (dict): Dictionary with markup keys (str) and corresponding values
        """
        updated_dict = {}
        for question, answers in dictionary.items():
            updated_question = self.update_markers(question, art_data)
            updated_answers = [self.update_markers(answer, art_data) for answer in answers]

            if updated_question in updated_dict:
                updated_dict[updated_question].extend(updated_answers)
            else:
                updated_dict[updated_question] = updated_answers

        return updated_dict

    def add_exchange(self, exchange: Exchange):
        """Add an exchange to the total dialogue"""
        self.dialogue.append(exchange)

    def mic_on(self):
        """Send a message to UE5 to display the 'mic on' button"""
        message_mic_on = MessageMic(status=True)
        self.socket.send(message_mic_on.format())

    def mic_off(self):
        """Send a message to UE5 to display the 'mic off' button"""
        message_mic_off = MessageMic(status=False)
        self.socket.send(message_mic_off.format())

    def get_answer(self, exchange: Exchange):
        """Select an answer based on a user input"""
        exchange.get_answer(self.embedding_model, self.question_list_embedded, self.dict_qa, self.question_list)

    def select_emotion(self, exchange: Exchange):
        """Select an emotion based on processed inputs and generated answer

        Parameters:
        agent (Agent): Agent whose emotion is to be changed
        exchange (Exchange): Exchange which we want to choose an emotion for
        webcam (Webcam): Webcam collecting user's Facial Action

        Returns:
        emotion_to_send (str): Selected emotion
        """

        # Set default to previous exchange's emotion
        previous_emotion = "curiosity" if len(self.dialogue) <= 1 else self.dialogue[-2]

        labels = ['anger', 'annoyance', 'confusion', 'curiosity', 'disgust', 'embarrassment', 'excitement', 'fear',
                  'grief', 'joy', 'nervousness', 'pride', 'sadness', 'surprise']

        expression_probabilities = self.webcam.au_probabilities.copy()
        expression_label = self.webcam.label.copy()

        # we add the probabilities of both inputs from input and facial expression
        for index, prob in enumerate(exchange.input.emotion_prob):
            if labels[index] in self.webcam.label:
                emotion = labels[index]
                expression_probabilities[expression_label.index(emotion)] += exchange.input.emotion_prob[index]
            else:
                if prob != 0:
                    expression_probabilities.append(prob)
                    expression_label.append(labels[index])

        # Normalization
        sum_prob = sum(expression_probabilities)
        expression_probabilities = [i/sum_prob for i in expression_probabilities]

        max_prob = max(expression_probabilities)
        max_prob_index = expression_probabilities.index(max_prob)
        expression_prediction_name = expression_label[max_prob_index]

        # If confidence is high, we select the new answer's emotion
        # Else, we keep the previous selected emotion
        # But in case it was neutral, we copy the user's facial expression
        if exchange.output.emotion_conf > 1/len(expression_label):
            logging.debug("Selecting current emotion")
            emotion_to_send = exchange.output.emotion
        elif previous_emotion != 'neutral':
            logging.debug("Selecting previous emotion")
            emotion_to_send = previous_emotion
        else:
            logging.debug("Selecting predicted user expression")
            emotion_to_send = expression_prediction_name

        self.agent.emotion = Emotion(emotion_to_send)
        return emotion_to_send
