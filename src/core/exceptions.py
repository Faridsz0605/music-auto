"""Custom exceptions for the application."""


class YMDError(Exception):
    """Base exception for all YMD errors."""


class AuthenticationError(YMDError):
    """Raised when authentication fails or is missing."""


class PlaylistNotFoundError(YMDError):
    """Raised when a playlist cannot be found."""


class DownloadError(YMDError):
    """Raised when a download fails."""


class MetadataError(YMDError):
    """Raised when metadata extraction or tagging fails."""


class ConfigError(YMDError):
    """Raised when configuration is invalid or missing."""


class SyncError(YMDError):
    """Raised when sync operations fail."""


class OrganizationError(YMDError):
    """Raised when file organization fails."""
