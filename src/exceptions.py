class CustomException(Exception):
    """
    Custom exception class for the application.
    """

    pass


class DuplicateIndexError(CustomException):
    """
    Exception raised when a duplicate index is found.
    """

    pass
