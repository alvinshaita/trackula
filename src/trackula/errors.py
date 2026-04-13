class ID3Error(Exception):
    """Base exception for ID3-related errors."""


class InvalidHeaderError(ID3Error):
    """Raised when an ID3 header cannot be parsed."""
