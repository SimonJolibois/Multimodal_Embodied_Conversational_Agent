from Python.Message import Message
from Python.Target import Target


class MessageURL(Message):
    """Message with a URL to be displayed as QR code in UE5. Currently not used"""
    def __init__(self, url: str):
        super().__init__(target=Target.URL)
        self.url = url

    def format(self):
        return "    ".join((str(self.timestamp), self.target.name, self.url)).encode('utf-8')
