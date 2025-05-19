"""Custom exceptions for read/write errors."""


class DatasetTypeError(Exception):
    """Raised when an input dataset is of an unknown type."""


class ReadError(Exception):
    """A general dataset read error."""


class WriteTypeError(Exception):
    """A general dataset write error."""
