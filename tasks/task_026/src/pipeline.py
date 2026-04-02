"""Main pipeline module with support for eager and lazy evaluation."""

from .buffer import Buffer
from .context import PipelineContext
from .config import PipelineConfig


class Pipeline:
    """Data processing pipeline that chains stages together.

    Supports two evaluation modes:
    - Eager: processes all items through each stage before moving to the next
    - Lazy (batched): uses buffers to batch items between stages
    """

    def __init__(self, config=None):
        self._config = config or PipelineConfig()
        self._stages = []
        self._context = PipelineContext(self._config)
        self._buffers = []
        self._results = []
        self._finalized = False

    @property
    def config(self):
        return self._config

    @property
    def context(self):
        return self._context

    @property
    def stages(self):
        return list(self._stages)

    @property
    def results(self):
        return list(self._results)

    def add_stage(self, stage):
        """Add a processing stage to the pipeline."""
        if self._finalized:
            raise RuntimeError("Cannot add stages to a finalized pipeline")
        self._stages.append(stage)
        return self

    def _setup_buffers(self):
        """Create buffers between stages for batched processing."""
        self._buffers = []
        for i in range(len(self._stages)):
            self._buffers.append(Buffer(batch_size=self._config.batch_size))

    def _run_eager(self, items):
        """Run pipeline in eager mode — process all items through each stage."""
        current = list(items)
        for stage in self._stages:
            stage.setup(self._context)
            current = stage.process_batch(current, self._context)
            self._context.record_stage_result(stage.name, list(current))
            stage.teardown(self._context)
        return current

    def _run_batched(self, items):
        """Run pipeline in batched mode using buffers between stages.

        Items flow through the pipeline in batches. Each buffer sits
        between two stages and collects items until a batch is full,
        then flushes to the next stage.
        """
        self._setup_buffers()

        for stage in self._stages:
            stage.setup(self._context)

        # Feed all items into the first buffer
        input_buffer = self._buffers[0]
        input_buffer.add_many(items)

        # Process each stage
        all_results = []
        for i, stage in enumerate(self._stages):
            buffer = self._buffers[i]
            batch = buffer.flush()

            if not batch:
                continue

            processed = stage.process_batch(batch, self._context)

            # Record stage results using the previous batch from the buffer
            # This is meant to capture what the stage received as input
            self._context.record_stage_result(
                stage.name,
                {
                    'input': buffer.previous_batch,
                    'output': list(processed)
                }
            )

            # Feed processed items into the next buffer (or collect as final)
            if i + 1 < len(self._stages):
                self._buffers[i + 1].add_many(processed)
            else:
                all_results = processed

        for stage in self._stages:
            stage.teardown(self._context)

        return all_results

    def run(self, items):
        """Execute the pipeline on the given items.

        Uses batched mode if config.lazy is True, otherwise eager mode.
        """
        if not self._stages:
            return list(items)

        self._context.start()

        try:
            if self._config.lazy:
                self._results = self._run_batched(items)
            else:
                self._results = self._run_eager(items)
        except Exception as e:
            self._context.log_error('pipeline', e)
            raise
        finally:
            self._context.finish()
            self._finalized = True

        return list(self._results)

    def get_stage_input(self, stage_name):
        """Get what a stage received as input (only available in batched mode)."""
        result = self._context.get_stage_result(stage_name)
        if result and isinstance(result, dict):
            return result.get('input')
        return None

    def get_stage_output(self, stage_name):
        """Get what a stage produced as output."""
        result = self._context.get_stage_result(stage_name)
        if result and isinstance(result, dict):
            return result.get('output')
        elif result and isinstance(result, list):
            return result
        return None

    def reset(self):
        """Reset the pipeline for re-use."""
        self._context.clear()
        self._buffers.clear()
        self._results.clear()
        self._finalized = False
        for stage in self._stages:
            stage.reset()

    def summary(self):
        """Return a summary of the pipeline execution."""
        return {
            'stages': [s.name for s in self._stages],
            'config': repr(self._config),
            'context': self._context.summary(),
            'result_count': len(self._results),
            'finalized': self._finalized
        }
