class BorealisError(RuntimeError):
    """Base exception for the toolkit."""


class BorealisNotFoundError(BorealisError):
    pass


class BorealisAccessError(BorealisError):
    pass


class BorealisFileTooLargeError(BorealisError):
    pass


class BorealisUnsupportedFileError(BorealisError):
    pass
