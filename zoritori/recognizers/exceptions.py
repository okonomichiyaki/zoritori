class RecognizerException(Exception):
    """Thrown when encountering errors in external recognizers"""

    def __init__(self, message=None):
        self.message = message
