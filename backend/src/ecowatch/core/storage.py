"""Swappable object storage boundary and local filesystem adapter."""

from pathlib import Path
from typing import Protocol

from fastapi import status

from ecowatch.core.errors import DomainError, ErrorCode


class StorageProvider(Protocol):
    """Object storage protocol preserving originals separately from derivatives."""

    def put_bytes(self, storageKey: str, data: bytes) -> None: ...
    def get_bytes(self, storageKey: str) -> bytes: ...
    def exists(self, storageKey: str) -> bool: ...


class LocalFilesystemStorage:
    """Stores objects under an app-managed root outside public web directories."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, storageKey: str) -> Path:
        if not storageKey or storageKey.startswith("/") or ".." in Path(storageKey).parts:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "Invalid storage key",
                statusCode=status.HTTP_400_BAD_REQUEST,
            )
        candidate = (self._root / storageKey).resolve()
        if self._root not in candidate.parents:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "Storage key escapes storage root",
                statusCode=status.HTTP_400_BAD_REQUEST,
            )
        return candidate

    def put_bytes(self, storageKey: str, data: bytes) -> None:
        target = self._resolve_safe_path(storageKey)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def get_bytes(self, storageKey: str) -> bytes:
        target = self._resolve_safe_path(storageKey)
        if not target.is_file():
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Stored evidence object not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        return target.read_bytes()

    def exists(self, storageKey: str) -> bool:
        target = self._resolve_safe_path(storageKey)
        return target.is_file()
