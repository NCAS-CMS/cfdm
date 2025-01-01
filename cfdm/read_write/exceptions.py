"""Custom exceptions for read/write errors."""


class FileTypeError(Exception):
    """Raised when an input dataset is of an inknown type."""


class ReadError(Exception):
    """A general dataset read error."""


class Writerror(Exception):
    """A general dataset write error."""
