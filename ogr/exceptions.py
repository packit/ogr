class OgrException(Exception):
    """ Something went wrong during our execution """


class PersistenStorageException(OgrException):
    """ Mocking Exceptions for persistent storage of objects """


class OurPagureRawRequest(OgrException):
    """ Mocking Exceptions for pagure raw request """
