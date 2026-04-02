"""Data processor with callback-based interface — needs async refactoring."""

import time
from dataclasses import dataclass, field


@dataclass
class ProcessResult:
    """Result of a processing operation."""
    input_size: int
    output_data: dict
    elapsed: float
    transformations: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.output_data is not None


class ProcessError(Exception):
    """Raised when processing fails."""
    pass


class Processor:
    """Processes downloaded data using callbacks.

    Current callback-hell interface:
        processor.process(data,
            on_process_start=lambda: ...,
            on_process_complete=lambda result: ...,
            on_error=lambda err: ...
        )
    """

    def __init__(self, delay: float = 0.01):
        self._delay = delay

    def process(self, data: str, on_process_start=None,
                on_process_complete=None, on_error=None) -> None:
        """Process data using callbacks."""
        try:
            if on_process_start:
                on_process_start()

            start = time.monotonic()
            time.sleep(self._delay)

            if not data:
                raise ProcessError("Cannot process empty data")

            lines = data.strip().split("\n")
            result_data = {
                "line_count": len(lines),
                "char_count": len(data),
                "lines": lines,
                "summary": f"Processed {len(lines)} lines, {len(data)} characters",
            }
            transformations = ["split_lines", "count_chars", "summarize"]

            elapsed = time.monotonic() - start
            result = ProcessResult(
                input_size=len(data),
                output_data=result_data,
                elapsed=elapsed,
                transformations=transformations,
            )

            if on_process_complete:
                on_process_complete(result)

        except Exception as e:
            if on_error:
                on_error(e)
            else:
                raise

    def process_sync(self, data: str) -> ProcessResult:
        """Synchronous process — basic functionality test helper."""
        if not data:
            raise ProcessError("Cannot process empty data")
        start = time.monotonic()
        time.sleep(self._delay)
        lines = data.strip().split("\n")
        result_data = {
            "line_count": len(lines),
            "char_count": len(data),
            "lines": lines,
            "summary": f"Processed {len(lines)} lines, {len(data)} characters",
        }
        elapsed = time.monotonic() - start
        return ProcessResult(
            input_size=len(data),
            output_data=result_data,
            elapsed=elapsed,
            transformations=["split_lines", "count_chars", "summarize"],
        )
