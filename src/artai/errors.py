"""Errors that artai reports to the user as one line, without a traceback."""


class ArtaiError(Exception):
    """Base class: the CLI prints ``artai: <message>`` and exits 1."""


class ManifestError(ArtaiError):
    """The manifest or its data file cannot be used."""


class ConfigError(ArtaiError):
    """An option, environment variable or backend setting is invalid."""
