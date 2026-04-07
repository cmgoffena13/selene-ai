class CustomException(Exception):
    """
    Custom exception class for the application.
    """

    pass


class DuplicateIndexError(CustomException):
    """
    Exception raised when a duplicate LEANN index is found.
    """

    pass


class AgentDoesNotExistError(CustomException):
    """
    Exception raised when an agent does not exist.
    """

    pass
