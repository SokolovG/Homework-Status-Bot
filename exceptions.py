class HttpStatusNotOkError(Exception):
    pass

class NotDictTypeDataError(TypeError):
    """Class responsible for handling errors when the data type is not a dictionary."""

class NotListTypeDataError(TypeError):
    """Class responsible for handling errors when the data type is not a list."""

class KeyNotFoundError(KeyError):
    """Class responsible for handling errors when the key is not found."""

class ApiConnectionError(Exception):
    """Class responsible for handling errors related to API issues."""

class JsonTypeError(Exception):
    """Class responsible for handling errors when the data is not in JSON format."""

class UnknownHomeworkError(ValueError):
    """Class responsible for handling errors when the homework status is unknown."""

class UnknownTelegramError(Exception):
    """Class responsible for unknown Telegram Error."""