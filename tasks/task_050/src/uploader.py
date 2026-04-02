"""Data uploader with callback-based interface — needs async refactoring."""

import time
from dataclasses import dataclass


@dataclass
class UploadResult:
    """Result of an upload operation."""
    destination: str
    size: int
    elapsed: float

    @property
    def success(self) -> bool:
        return self.size > 0


class UploadError(Exception):
    """Raised when upload fails."""
    pass


# Simulated upload destinations
_UPLOAD_STORE: dict[str, dict] = {}


class Uploader:
    """Uploads processed data using callbacks.

    Current callback-hell interface:
        uploader.upload(data, destination,
            on_upload_start=lambda: ...,
            on_upload_complete=lambda result: ...,
            on_error=lambda err: ...
        )
    """

    def __init__(self, delay: float = 0.01):
        self._delay = delay

    def upload(self, data: dict, destination: str, on_upload_start=None,
               on_upload_complete=None, on_error=None) -> None:
        """Upload data to a destination using callbacks."""
        try:
            if on_upload_start:
                on_upload_start()

            start = time.monotonic()
            time.sleep(self._delay)

            if not data:
                raise UploadError("Cannot upload empty data")

            if destination.startswith("error://"):
                raise UploadError(f"Upload failed to {destination}")

            import json
            serialized = json.dumps(data)
            _UPLOAD_STORE[destination] = data

            elapsed = time.monotonic() - start
            result = UploadResult(
                destination=destination,
                size=len(serialized),
                elapsed=elapsed,
            )

            if on_upload_complete:
                on_upload_complete(result)

        except Exception as e:
            if on_error:
                on_error(e)
            else:
                raise

    def upload_sync(self, data: dict, destination: str) -> UploadResult:
        """Synchronous upload — basic functionality test helper."""
        if not data:
            raise UploadError("Cannot upload empty data")
        start = time.monotonic()
        time.sleep(self._delay)
        import json
        serialized = json.dumps(data)
        _UPLOAD_STORE[destination] = data
        elapsed = time.monotonic() - start
        return UploadResult(
            destination=destination,
            size=len(serialized),
            elapsed=elapsed,
        )

    @classmethod
    def get_uploaded(cls, destination: str) -> dict | None:
        """Retrieve uploaded data (for testing)."""
        return _UPLOAD_STORE.get(destination)

    @classmethod
    def clear_store(cls):
        """Clear the upload store."""
        _UPLOAD_STORE.clear()
