import asyncio
import logging
import queue
import threading
import time
import torch
import re

from Python.DialogueManager import DialogueManager
from Python.Exchange import Exchange
from Python.MessageExchange import MessageExchange
from Python.MessageURL import MessageURL
from Python.MessagebEmotion import MessagebEmotion
from Python.Webcam import Webcam
from Python.Experiment import experiment_table, painting_table, delay_table


def measure_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        logging.info(f"{func.__name__} execution time: {execution_time} seconds")
        return result

    return wrapper


@measure_time
def task1_mic(queue_sentence_user: queue.Queue, manager: DialogueManager, event: threading.Event):
    """ Function to continuously listen for speech input and put recognized text into a queue.

    Parameters:
    queue_sentence_user (Queue): Queue to store recognized sentences.
    manager: Manager object to control microphone and listener.
    event (threading.Event): Event to signal when to stop listening.
    """
    while not event.is_set():
        print("Say something")
        manager.mic_on()
        output = manager.azure.listener.recognize_once_async().get().text.strip()
        manager.mic_off()

        if output:
            print(output)
            logging.debug(f"\nTranscript - '{output}'")
            queue_sentence_user.put(output)
            time.sleep(0.002)


def task1_mic_continuous(queue_sentence_user: queue.Queue, manager: DialogueManager, event: threading.Event):
    """ Listen continuously to the user speech through the microphone.

    Parameters:
    queue_sentence_user (Queue): Queue to store recognized sentences.
    manager (DialogueManager): Manager object to control microphone and listener.
    event: (threading.Event): Event to signal when to stop listening.
    """
    def stop_callback(evt):
        print(f'CLOSING ON {evt}')
        manager.azure.listener.stop_continuous_recognition()
        manager.mic_off()
        nonlocal done
        done = True

    def to_queue(evt):
        output = evt.result.text.strip()
        if output and output != "Hey, Cortana.":
            print(output)
            logging.debug(f"Transcript - {output}")
            queue_sentence_user.put(output)

    while not event.is_set():
        done = False

        manager.azure.listener.recognized.connect(to_queue)
        manager.azure.listener.session_started.connect(lambda evt: print(f'Listening: {evt}'))
        manager.azure.listener.session_stopped.connect(lambda evt: print(f'SESSION STOPPED {evt}'))
        manager.azure.listener.canceled.connect(lambda evt: print(f'CANCELED {evt}'))
        manager.azure.listener.session_stopped.connect(stop_callback)
        manager.azure.listener.canceled.connect(stop_callback)

        manager.mic_on()
        manager.azure.listener.start_continuous_recognition()

        while not done:
            if event.is_set():
                manager.azure.listener.stop_continuous_recognition()
                manager.mic_off()
                break
            time.sleep(.01)


@measure_time
def task2_webcam(queue_reaction_user: queue.Queue, webcam: Webcam, model, event: threading.Event):
    """ Function to continuously update webcam data and predict the user's emotion based on this data

    Parameters:
    queue_reaction_user (Queue): Queue to store reaction predictions.
    webcam: Webcam object to update and predict.
    model: Model used for predictions.
    event (threading.Event): Event to signal when to stop updating.
    """
    # TODO: reactions should be not only emotions, but also other things
    while not event.is_set():
        logging.debug("Updating webcam data")
        webcam.update()
        webcam.predict(model)
        queue_reaction_user.put(webcam.au_prediction_name)
        time.sleep(1)


@measure_time
def nested_input(manager: DialogueManager, exchange: Exchange):
    manager.sentence_model.predict_input(exchange)
    logging.debug(f"Input predicted emotion - {exchange.input.emotion}")


@measure_time
def nested_t2s(manager: DialogueManager, exchange: Exchange):
    exchange.viseme_timestamp, exchange.viseme_id = asyncio.run(manager.azure.t2s_split_async(exchange))
    logging.debug("Speech synthesized")


@measure_time
def nested_select_emotion(manager: DialogueManager, exchange: Exchange):
    manager.select_emotion(exchange)
    logging.debug(f"Selecting the emotion {manager.agent.emotion}")


@measure_time
def nested_output_prediction(manager: DialogueManager, exchange: Exchange):
    manager.sentence_model.predict_output(exchange)
    logging.debug(f"Output predicted emotion - {exchange.output.emotion}")


@measure_time
def task4_emitter(queue_action_agent: queue.Queue, manager: DialogueManager, event: threading.Event):
    """ Send messages in the queue to the animation software

    Parameters:
    queue_action_agent (Queue): Queue to store action of the agent to send to UE5
    manager (DialogueManager): Manager object to control microphone and listener.
    event: (threading.Event): Event to signal when to stop listening.
    """
    while not event.is_set():
        if not queue_action_agent.empty():
            message = queue_action_agent.get()
            manager.socket.send(message)
            logging.debug(f"Emitted message - {message}")
        time.sleep(.001)


async def catch_experiment_params(manager: DialogueManager):
    """ Receive experiment parameters from the animation software that drive the agent response time and choose the artwork

    Parameters:
    manager (DialogueManager): Manager object to control microphone and listener.
    """
    while True:
        data = manager.socket.clientsocket.recv(4096).decode('utf-8')
        if not data:
            print("No parameters")
            continue

        participant, turn = data.split('  ')
        PARTICIPANT, ROUND = int(participant[:-2]), int(round[:-2])
        CONTROLTIME = delay_table[experiment_table[f"Participant_{PARTICIPANT}"][f"Round {ROUND}"]["Delay"]]
        ARTWORK = painting_table[experiment_table[f"Participant_{PARTICIPANT}"][f"Round {ROUND}"]["Painting"]]
        EMOTION = experiment_table[f"Participant_{PARTICIPANT}"][f"Round {ROUND}"]["Emotion"]
        message_bemotion = MessagebEmotion(EMOTION, ARTWORK).format()
        manager.socket.send(message_bemotion)
        logging.debug(f"Emitted Emotion message - {message_bemotion}")
        logging.debug(f"\n EXPERIMENT PARAMETERS\n"
                      f"\nParticipant = {PARTICIPANT}"
                      f"\nROUND = {ROUND}"
                      f"\nARTWORK = {ARTWORK}"
                      f"\nEMOTION = {EMOTION}"
                      f"\nCONTROL TIME: {CONTROLTIME}")
        return PARTICIPANT, ROUND, CONTROLTIME, ARTWORK, EMOTION


async def catch_artwork(manager: DialogueManager):
    """ Receive data from the animation software to choose the artwork

    Parameters:
    manager (DialogueManager): Manager object to control microphone and listener.
    """
    while True:
        artwork = manager.socket.clientsocket.recv(4096).decode('utf-8')
        if not artwork:
            logging.debug("No artwork selection")
            break
        else:
            logging.debug(f"Artwork: {artwork}")
            return artwork


async def main():
    # Definition of the variables
    current_time = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    filename = f"logs/logfile_{current_time}.log"
    logging.basicConfig(filename=filename,
                        encoding='utf-8',
                        level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s',
                        datefmt="%Y-%m%d %H:%M:%S",
                        filemode='w')

    torch.cuda.empty_cache()
    dm = DialogueManager('.\\dialogue generation\\dialogue_database_v2.csv')
    ARTWORK = await catch_artwork(dm)
    dm.set_artwork(ARTWORK)

    #
    print("\n===== BEGINNING CONVERSATION =====\n")
    logging.debug("\n\n===== BEGINNING CONVERSATION =====\n")

    queue_sentence_user, queue_reaction_user, queue_action_agent = queue.Queue(), queue.Queue(), queue.Queue()
    task_queue, task_queue_nested = queue.Queue(), queue.Queue()
    event = threading.Event()
    logging.debug("Creating tasks")

    def worker(task_q: queue.Queue):
        while True:
            task, args = task_q.get()
            if task is None:
                break
            task(*args)
            task_q.task_done()

    def start_threads(task_q: queue.Queue, num_threads: int) -> list:
        thread = []
        for _ in range(num_threads):
            td = threading.Thread(target=worker, args=(task_q,), daemon=True)
            td.start()
            thread.append(td)
        return thread

    threads = start_threads(task_queue, 2)                  # Handle Mic and Webcam
    threads_nested = start_threads(task_queue_nested, 3)    # Handle emotions and dialogue

    task_queue.put((task1_mic_continuous, (queue_sentence_user, dm, event)))
    task_queue.put((task2_webcam, (queue_reaction_user, dm.webcam, dm.au_model, event)))

    try:
        while not event.is_set():
            if queue_sentence_user.empty():
                continue

            if queue_sentence_user.empty():
                continue

            input_mic = queue_sentence_user.get()
            initial_exchange = Exchange(input_mic)
            dm.add_exchange(initial_exchange)
            dm.get_answer(initial_exchange)
            logging.debug(f"Finding an answer - {initial_exchange.output.sentence}")

            # Split by sentences (character .) and remove empties
            sentence_split = (re.split('(?<=[.?])', initial_exchange.output.sentence))
            sentence_split = [s for s in sentence_split if s]

            # Each sentence is processed individually to get faster reaction
            for sentence in sentence_split:
                if sentence.startswith("http"):
                    message_url = MessageURL(sentence).format()
                    dm.socket.send(message_url)
                    logging.debug(f"Emitted URL message - {message_url}")
                    continue

                exchange = initial_exchange.copy()
                exchange.set_answer(sentence)

                # We do Text-to-Speech, input and output emotion predictions all at once
                task_queue_nested.put((nested_output_prediction, (dm, exchange)))
                task_queue_nested.put((nested_t2s, (dm, exchange)))
                task_queue_nested.put((nested_input, (dm, exchange)))
                task_queue_nested.join()
                nested_select_emotion(dm, exchange)

                message = MessageExchange(exchange.timingbegin, exchange.output.sentence, dm.agent.emotion,
                                          exchange.viseme_id, exchange.viseme_timestamp, exchange.output_wav).format()

                # Only used for experiment
                """
                process_time = time.time() - exchange.timingbegin
                logging.debug(f"Total time for processing: {process_time}")
                if process_time < CONTROLTIME:
                    logging.debug(f"Time lower than {CONTROLTIME}, waiting for {CONTROLTIME - process_time}.")
                    time.sleep(CONTROLTIME - process_time)
                else:
                    logging.debug(f"Time higher than {CONTROLTIME}, directly continuing")
                """
                dm.socket.send(message)
                logging.debug(f"Emitted full message - {message}")
                time.sleep(0.01)

    except (KeyboardInterrupt or ConnectionAbortedError or TypeError) as e:
        # TODO: stop script when stopping UE5
        logging.debug(f"Caught an exception: {e}")
        logging.debug(f"Closing the socket")
        print(f"Caught an exception: {e}")
        event.set()

        for _ in range(2):
            task_queue.put(None)
        for _ in range(3):
            task_queue_nested.put(None)
        for t in threads:
            t.join()
        for t in threads_nested:
            t.join()
        dm.socket.close()

        logging.debug("Socket closed")


if __name__ == '__main__':
    asyncio.run(main())
