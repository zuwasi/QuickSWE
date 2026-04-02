"""Downloader with callback-based interface — needs async refactoring."""

import time
from dataclasses import dataclass


@dataclass
class DownloadResult:
    """Result of a download operation."""
    url: str
    data: str
    size: int
    elapsed: float

    @property
    def success(self) -> bool:
        return self.data is not None


# Simulated URL content database
_MOCK_CONTENT = {
    "http://example.com/data.csv": "id,name,value\n1,alpha,100\n2,beta,200\n3,gamma,300",
    "http://example.com/users.json": '{"users": [{"name": "Alice"}, {"name": "Bob"}]}',
    "http://example.com/config.yaml": "key: value\nmode: production\nretries: 3",
    "http://example.com/empty": "",
}


class DownloadError(Exception):
    """Raised when a download fails."""
    pass


class Downloader:
    """Downloads URL content using callbacks.

    Current callback-hell interface — all callbacks are nested:
        downloader.download(url,
            on_start=lambda: ...,
            on_progress=lambda pct: ...,
            on_complete=lambda data: ...,
            on_error=lambda err: ...,
            on_save=lambda path: ...
        )
    """

    def __init__(self, delay: float = 0.01):
        """Initialize downloader.

        Args:
            delay: Simulated download delay in seconds.
        """
        self._delay = delay

    def download(self, url: str, on_start=None, on_progress=None,
                 on_complete=None, on_error=None, on_save=None) -> None:
        """Download a URL using callbacks.

        This is the callback-based interface that should be converted to async.
        """
        try:
            if on_start:
                on_start()

            start = time.monotonic()
            time.sleep(self._delay)

            if on_progress:
                on_progress(0.5)

            if url not in _MOCK_CONTENT:
                raise DownloadError(f"URL not found: {url}")

            content = _MOCK_CONTENT[url]
            time.sleep(self._delay)

            if on_progress:
                on_progress(1.0)

            elapsed = time.monotonic() - start
            result = DownloadResult(
                url=url, data=content,
                size=len(content), elapsed=elapsed,
            )

            if on_complete:
                on_complete(result)

            if on_save:
                on_save(result)

        except Exception as e:
            if on_error:
                on_error(e)
            else:
                raise

    def download_sync(self, url: str) -> DownloadResult:
        """Synchronous download — basic functionality test helper."""
        if url not in _MOCK_CONTENT:
            raise DownloadError(f"URL not found: {url}")
        start = time.monotonic()
        time.sleep(self._delay)
        content = _MOCK_CONTENT[url]
        elapsed = time.monotonic() - start
        return DownloadResult(url=url, data=content,
                              size=len(content), elapsed=elapsed)
