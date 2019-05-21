class OgrException(Exception):
    """ Something went wrong during our execution """


class PagureAPIException(OgrException):
    """ Exception related to Pagure API """

    def __init__(self, *args: object, pagure_error: str = None) -> None:
        super().__init__(*args)
        self.pagure_error = pagure_error


class PersistenStorageException(OgrException):
    """ Mocking Exceptions for persistent storage of objects """


class OurPagureRawRequest(OgrException):
    """ Mocking Exceptions for pagure raw request """


class OperationNotSupported(OgrException):
    """ Raise when the operation is not supported by the backend. """
