"""Pipeline with callback hell — needs async/await refactoring.

This module chains Downloader -> Processor -> Uploader using deeply
nested callbacks. The refactored version should use async/await.
"""

from dataclasses import dataclass, field
from typing import Optional

from .downloader import Downloader, DownloadResult
from .processor import Processor, ProcessResult
from .uploader import Uploader, UploadResult
from .logger import Logger


@dataclass
class PipelineResult:
    """Result of a full pipeline run."""
    success: bool
    download_result: Optional[DownloadResult] = None
    process_result: Optional[ProcessResult] = None
    upload_result: Optional[UploadResult] = None
    error: Optional[Exception] = None
    log_entries: list = field(default_factory=list)


class Pipeline:
    """Data processing pipeline: download -> process -> upload.

    CURRENT STATE: Classic callback hell with deeply nested callbacks.
    The run() method should be refactored to async/await.
    """

    def __init__(self, downloader: Downloader = None,
                 processor: Processor = None,
                 uploader: Uploader = None,
                 logger: Logger = None):
        self._downloader = downloader or Downloader()
        self._processor = processor or Processor()
        self._uploader = uploader or Uploader()
        self._logger = logger or Logger()

    def run(self, url: str, destination: str) -> PipelineResult:
        """Run the full pipeline with deeply nested callbacks.

        This is the callback-hell version. Should be refactored to:
            async def run(self, url, destination) -> PipelineResult

        with flat async/await calls.
        """
        result = PipelineResult(success=False)
        self._logger.log("pipeline_start", f"Starting pipeline: {url} -> {destination}")

        # ---- CALLBACK HELL STARTS HERE ----
        def on_download_error(err):
            self._logger.log("download_error", str(err), level="ERROR")
            result.error = err

        def on_download_complete(download_res):
            result.download_result = download_res
            self._logger.log("download_complete",
                             f"Downloaded {download_res.size} bytes")

            # Nested callback for processing
            def on_process_error(err):
                self._logger.log("process_error", str(err), level="ERROR")
                result.error = err

            def on_process_complete(process_res):
                result.process_result = process_res
                self._logger.log("process_complete",
                                 process_res.output_data.get("summary", ""))

                # Even more nested callback for uploading
                def on_upload_error(err):
                    self._logger.log("upload_error", str(err), level="ERROR")
                    result.error = err

                def on_upload_complete(upload_res):
                    result.upload_result = upload_res
                    result.success = True
                    self._logger.log("upload_complete",
                                     f"Uploaded to {upload_res.destination}")
                    self._logger.log("pipeline_complete",
                                     "Pipeline finished successfully")

                # Upload (3rd level of nesting)
                self._logger.log("upload_start",
                                 f"Uploading to {destination}")
                self._uploader.upload(
                    data=process_res.output_data,
                    destination=destination,
                    on_upload_start=None,
                    on_upload_complete=on_upload_complete,
                    on_error=on_upload_error,
                )

            # Process (2nd level of nesting)
            self._logger.log("process_start", "Processing downloaded data")
            self._processor.process(
                data=download_res.data,
                on_process_start=None,
                on_process_complete=on_process_complete,
                on_error=on_process_error,
            )

        # Download (1st level of nesting)
        self._logger.log("download_start", f"Downloading {url}")
        self._downloader.download(
            url=url,
            on_start=None,
            on_progress=None,
            on_complete=on_download_complete,
            on_error=on_download_error,
            on_save=None,
        )
        # ---- CALLBACK HELL ENDS HERE ----

        result.log_entries = self._logger.get_entries()
        return result

    @property
    def logger(self) -> Logger:
        return self._logger
