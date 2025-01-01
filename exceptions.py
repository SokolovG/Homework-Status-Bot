class HttpStatusNotOkError(Exception):
    pass

class TokenNoFound(Exception):
    """Class to describe the absence of necessary tokens."""

class NotDictTypeData(TypeError):
    """Class responsible for handling errors when the data type is not a dictionary."""

class NotListTypeData(TypeError):
    """Class responsible for handling errors when the data type is not a list."""

class KeyNotFound(KeyError):
    """Class responsible for handling errors when the key is not found."""

class ApiError(Exception):
    """Class responsible for handling errors related to API issues."""

class JsonError(Exception):
    """Class responsible for handling errors when the data is not in JSON format."""

class UnknownHomework(ValueError):
    """Class responsible for handling errors when the homework status is unknown."""