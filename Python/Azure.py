import azure.cognitiveservices.speech as speechsdk
import logging
import os
import wave
import asyncio
import re
import string

from gtts import gTTS
from pydub import AudioSegment
from g2p_en import G2p

from Python.Exchange import Exchange


def get_next_audio_name(folder_path: string):
    """ Return the name of the next audio file created by Text-to-Speech

    Parameters:
    folder_path (string): path of the audio folder
    """
    wav_files = [file for file in os.listdir(folder_path) if file.endswith('.wav')]

    # Find the maximum X value from the existing files
    max_x = 0
    for wav_file in wav_files:
        try:
            x = int(wav_file.split('_')[1][:-4])
            max_x = max(max_x, x)
        except (ValueError, IndexError):
            continue

    next_filename = f"audio_{max_x + 1}"

    return next_filename


def adjust(vis_timestamp: list):
    new_timestamp = [(vis_timestamp[i]-vis_timestamp[i-1])/1000 for i in range(1,len(vis_timestamp))]
    return [vis_timestamp[0]/1000] + new_timestamp


class Azure:
    """ Speech-to-Text and Text-to-Speech of Azure services"""

    def __init__(self):
        self.synthesizer = self.create_synthesizer()
        self.listener = self.create_listener()
        self.speech_emo_dict = {'anger': 'angry',
                                'annoyance': 'unfriendly',
                                'confusion': 'general',
                                'curiosity': 'cheerful',
                                'disgust': 'unfriendly',
                                'embarrassment': 'terrified',
                                'excitement': 'excited',
                                'fear': 'terrified',
                                'grief': 'sad',
                                'joy': 'excited',
                                'nervousness': 'hopeful',
                                'neutral': 'neutral',
                                'pride': 'friendly',
                                'sadness': 'sad',
                                'surprise': 'friendly',
                                }

    @staticmethod
    def create_synthesizer():
        SPEECH_KEY = ""
        SPEECH_REGION = ""

        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        speech_config.speech_synthesis_voice_name = 'en-US-JaneNeural'
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        return speech_synthesizer

    @staticmethod
    def speech_synthesizer_viseme_received_cb(evt, viseme_timestamps, viseme_ids):
        viseme_timestamps.append((evt.audio_offset + 5000) / 10000)
        viseme_ids.append(evt.viseme_id)

    @staticmethod
    def create_listener():
        SPEECH_KEY = ""
        SPEECH_REGION = ""

        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        speech_config.speech_recognition_language = "en-US"
        speech_config.set_property(speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "100")
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        return speech_recognizer


    @staticmethod
    def merge_wavs(filenames: list, output_filename: str):
        """ Merges multiple WAV files into a single WAV file.

         Parameters:
         filenames (list): List of filenames to be merged.
         output_filename (str): The filename for the merged output.
         """

        if len(filenames) <= 0:
            logging.warning("No temp audio files")
            return

        data = []
        for filename in filenames:
            try:
                with wave.open(filename, 'rb') as w:
                    data.append([w.getparams(), w.readframes(w.getnframes())])
            except wave.Error as e:
                logging.warning(f"Error processing {filename}: {e}")
                continue
            except EOFError:
                logging.warning(f"Error reading file (it might be empty or corrupt)")
                continue

        if not data:
            logging.warning("No valid audio data to merge.")
            return

        with wave.open(output_filename, 'wb') as output:
            output.setparams(data[0][0])
            for _, frames in data:
                output.writeframes(frames)

    @staticmethod
    def tts_google_translate(sentence: str, name: str):
        """ Voice a sentence using Google Translate free Text-to-Speech

        Parameters:
        sentence (string): Sentence to be voiced by the Text-to-Speech
        name (string): Name of the wavfile
        """

        tts = gTTS(sentence)
        tts.save(f".\\Audio files\\{name}.wav")

        # TODO: load beforehand to gain speed
        g2p = G2p()
        phoneme_list = g2p(sentence)
        phoneme_list = [re.sub(r'\d+', '', p) for p in phoneme_list]
        phoneme_list = [re.sub('[' + re.escape(string.punctuation) + ']', ' ', p) for p in phoneme_list]

        # The G2P uses the ARPAbet, while the Azure TTS uses a custom SSML dictionary
        arpabet_to_ssml_mapping = {
            # Silence
            " ": 0,
            ".": 0,

            # Vowels
            "AA": 2,
            "AE": 1,
            "AH": 1,
            "AO": 3,
            "AW": 9,
            "AX": 1,
            "AXR": 1,
            "AY": 11,
            "EH": 4,
            "ER": 5,
            "EY": 1,
            "IH": 6,
            "IX": 6,
            "IY": 6,
            "OW": 8,
            "OY": 10,
            "UH": 4,
            "UW": 7,
            "UX": 7,

            # Consonants
            "B": 21,
            "CH": 16,
            "D": 19,
            "DH": 17,
            "DX": 19,
            "EL": 14,
            "EM": 21,
            "EN": 19,
            "F": 18,
            "G": 20,
            "HH": 12,
            "JH": 16,
            "K": 20,
            "L": 14,
            "M": 21,
            "N": 19,
            "NG": 20,
            "NX": 19,
            "P": 21,
            "Q": 12,
            "R": 13,
            "S": 15,
            "SH": 16,
            "T": 19,
            "TH": 19,
            "V": 18,
            "W": 7,
            "WH": 7,
            "Y": 6,
            "Z": 15,
            "ZH": 16
        }

        # We assign a custom time for each viseme
        ssml_id_to_time = {
            0: 0.0505,
            1: 0.075,
            2: 0.075,
            3: 0.075,
            4: 0.062,
            5: 0.038,
            6: 0.087,
            7: 0.062,
            8: 0.075,
            9: 0.112,
            10: 0.088,
            11: 0.075,
            12: 0.05,
            13: 0.075,
            14: 0.2,
            15: 0.05,
            16: 0.038,
            17: 0.05,
            18: 0.05,
            19: 0.044,
            20: 0.075,
            21: 0.062
        }

        viseme_id = [arpabet_to_ssml_mapping[e] for e in phoneme_list]
        viseme_timestamp = [ssml_id_to_time[e] for e in viseme_id]
        return viseme_id, viseme_timestamp


    async def t2s_split_async(self, exchange: Exchange):
        """ Voice a sentence using  Text-to-Speech, without specifying voice emotion
        Return viseme ID and timestamps

        Parameters:
        exchange (Exchange): Gather variables for a conversation round, from user input to Text-to-Speech
        """
        sentence_split = re.split('(?<=[.?])', exchange.output.sentence)
        if '' in sentence_split:
            sentence_split.remove('')

        # We can specify the Text-to-Speech using SSML, and audio are merged together
        ssml_list = ["""<speak version='1.0' xml:lang='en-US' 
                    xmlns="http://www.w3.org/2001/10/synthesis" 
                    xmlns:mstts='http://www.w3.org/2001/mstts' 
                    xmlns:emo="http://www.w3.org/2009/10/emotionml">
                        <voice name="en-US-JennyNeural">
                            <mstts:viseme type="redlips_front"/>
                            <mstts:express-as style="assistant" >
                                    <prosody rate="0%" pitch="0%">
                                        '{}'
                                    </prosody>
                            </mstts:express-as>
                        </voice></speak>
                    """.format(e) for e in sentence_split]

        # Text-to-Speech is done for each sentence separately
        for sentence in sentence_split:
            # we use Google Translate Text-to-Speech
            if len(sentence) > 10000:
                gtts_logger = logging.getLogger("gtts")
                gtts_logger.setLevel(logging.CRITICAL)

                name_wavfile = get_next_audio_name(".\\Audio files\\")
                viseme_id, viseme_timestamp = self.tts_google_translate(sentence, name_wavfile)
                return viseme_id, viseme_timestamp
            # Else we use Microsoft Azure Text-to-Speech
            else:
                viseme_timestamp, viseme_id = [], []  # the lists are filled through the viseme_cb() event
                self.synthesizer.viseme_received.connect(lambda evt:
                                                         self.speech_synthesizer_viseme_received_cb(evt,
                                                                                                    viseme_timestamp,
                                                                                                    viseme_id))
                name_wavfile = get_next_audio_name(".\\Audio files\\")
                name_wavfile_true = f".\\Audio files\\{name_wavfile}.wav"
                wavfile_list = []

                async def process_ssml(index, ssml):
                    speech_synthesis = self.synthesizer.speak_ssml_async(ssml).get()

                    if speech_synthesis.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                        logging.debug("Speech synthesized")
                    elif speech_synthesis.reason == speechsdk.ResultReason.Canceled:
                        cancellation_details = speech_synthesis.cancellation_details
                        logging.warning(f"Speech synthesis canceled: {cancellation_details.reason}")
                        if cancellation_details.reason == speechsdk.CancellationReason.Error and cancellation_details.error_details:
                            logging.warning(f"Error details: {cancellation_details.error_details}")

                    stream = speechsdk.AudioDataStream(speech_synthesis)
                    wavfile_temp = f".\\Audio files\\temp_{name_wavfile}_{index}.wav"
                    stream.save_to_wav_file(wavfile_temp)
                    wavfile_list.append(wavfile_temp)
                    return index, wavfile_temp

                results = await asyncio.gather(*(process_ssml(i, ssml) for i, ssml in enumerate(ssml_list)))
                sorted_results = sorted(results, key=lambda x: x[0])
                wavfile_list = [result[1] for result in sorted_results]

                self.merge_wavs(wavfile_list, name_wavfile_true)
                # Removing the temporary wav. files
                for file in os.listdir(".\\Audio files\\"):
                    if file.startswith('temp'):
                        os.remove(f".\\Audio files\\{file}")

                exchange.output_wav = name_wavfile_true
                with wave.open(name_wavfile_true, 'rb') as f:
                    exchange.output_wav_duration = f.getnframes() / float(f.getframerate())

                exchange.output_wav = "." + name_wavfile_true  # remove the . for the correct path in UE5
                viseme_timestamp = adjust(viseme_timestamp)
                # TODO: check if it works with gTTS
                return viseme_timestamp, viseme_id


    @staticmethod
    def get_temp_wav(index):
        file_list = [f".\\Audio files\\{file}" for file in os.listdir("./Audio files\\") if
                     file.startswith(f'temp_{index}')]

        # Custom sorting function to extract Y value
        def sort_key(filename):
            match = re.search(r'temp_\d+_(\d+).wav', filename)
            return int(match.group(1)) if match else 0

        return sorted(file_list, key=sort_key)


    async def t2s_async(self, exchange: Exchange):
        """ Voice a sentence using  Text-to-Speech, without specifying voice emotion
        Return viseme ID and timestamps

        Parameters:
        exchange (Exchange): Gather variables for a conversation round, from user input to Text-to-Speech
        """
        sentence_split = exchange.output.sentence

        if not sentence_split:
            logging.warning("No sentences to process.")
            return [], []

        name_wavfile = get_next_audio_name(".\\Audio files\\")
        name_wavfile_true = f"\\Audio files\\{name_wavfile}"

        async def process_tts(sentence):
            viseme_id_list = []
            viseme_ts_list = []
            if len(sentence) > 1:
                viseme_id_temp, viseme_timestamp_temp = self.tts_google_translate(sentence, name_wavfile_true)

                viseme_ts_list.append(viseme_timestamp_temp)
                viseme_id_list.append(viseme_id_temp)

                # Converting MP3 to WAV
                sound = AudioSegment.from_mp3(f"{name_wavfile_true}.mp3")
                sound.export(f"{name_wavfile_true}.wav", format="wav")  # Convert and save as WAV
                os.remove(f"{name_wavfile_true}.mp3")

            else:
                ssml = (f"<speak version='1.0' xml:lang='en-US' "
                        "xmlns='http://www.w3.org/2001/10/synthesis' "
                        "xmlns:mstts='http://www.w3.org/2001/mstts' "
                        "xmlns:emo='http://www.w3.org/2009/10/emotionml'>"
                        "<voice name='en-US-JennyNeural'>"
                        "<mstts:viseme type='redlips_front'/>"
                        "<mstts:express-as style='assistant'>"
                        "<prosody rate='0%' pitch='0%'>"
                        f"{sentence}"
                        "</prosody>"
                        "</mstts:express-as>"
                        "</voice></speak>")

                try:
                    self.synthesizer.viseme_received.connect(lambda evt: self.speech_synthesizer_viseme_received_cb(evt, viseme_ts_list, viseme_id_list))
                    speech_synthesis = self.synthesizer.speak_ssml_async(ssml).get()
                    if speech_synthesis.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:

                        stream = speechsdk.AudioDataStream(speech_synthesis)
                        stream.save_to_wav_file(f"{name_wavfile_true}.wav")

                    else:
                        raise RuntimeError(f"Speech synthesis failed: {speech_synthesis.reason}")
                except Exception as e:
                    logging.error(f"Error during speech synthesis: {e}")
                    return None, None

            return viseme_ts_list[0], viseme_id_list[0]

        viseme_ts, viseme_id = await process_tts(sentence_split)
        viseme_ts = adjust(viseme_ts)
        # TODO: check if it works with gTTS

        with wave.open(f"{name_wavfile_true}.wav", 'rb') as f:
            exchange.output_wav_duration = f.getnframes() / float(f.getframerate())

        exchange.output_wav = name_wavfile
        return viseme_ts, viseme_id
