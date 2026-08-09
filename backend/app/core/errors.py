class ScribeCastError(Exception):
    """Base class for domain errors mapped to HTTP responses in main.py."""


class FolderNotFoundError(ScribeCastError):
    pass


class InvalidPathError(ScribeCastError):
    pass


class AudioExtractionError(ScribeCastError):
    pass


class ModelLoadError(ScribeCastError):
    pass


class VideoDownloadError(ScribeCastError):
    pass
