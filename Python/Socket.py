import logging
import socket


class Socket:
    """TCP socket for communication between Python and UE5"""

    def __init__(self):
        self.messages_sent = []
        self.messages_received = []
        self.received_queue = []

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("127.0.0.1", 5580))
        self.server.listen()
        print("Please launch the game")
        self.clientsocket, self.address = self.server.accept()
        logging.info(f"Connected to {self.clientsocket}")

    def close(self):
        try:
            self.clientsocket.close()
        except socket.error:
            logging.warning("Clientsocket couldn't be closed")
        try:
            self.server.close()
        except socket.error:
            logging.warning("Server couldn't be closed")
        logging.info("Socket was closed")

    def send(self, message: bytes):
        self.clientsocket.sendall(message)

    def receive(self):
        message = self.clientsocket.recv(4096).decode('utf-8')
        self.received_queue.append(message)
