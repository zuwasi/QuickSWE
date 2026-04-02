"""Pipeline configuration module."""


class PipelineConfig:
    """Configuration for pipeline execution."""

    DEFAULT_BATCH_SIZE = 10
    MAX_BATCH_SIZE = 1000
    DEFAULT_TIMEOUT = 30.0
    ENABLE_LOGGING = False

    def __init__(self, batch_size=None, lazy=False, timeout=None, log=None):
        self._batch_size = batch_size or self.DEFAULT_BATCH_SIZE
        self._lazy = lazy
        self._timeout = timeout or self.DEFAULT_TIMEOUT
        self._log = log if log is not None else self.ENABLE_LOGGING
        self._stage_configs = {}
        self._validators = []

    @property
    def batch_size(self):
        return self._batch_size

    @batch_size.setter
    def batch_size(self, value):
        if not isinstance(value, int) or value < 1:
            raise ValueError(f"Batch size must be a positive integer, got {value}")
        if value > self.MAX_BATCH_SIZE:
            raise ValueError(f"Batch size {value} exceeds maximum {self.MAX_BATCH_SIZE}")
        self._batch_size = value

    @property
    def lazy(self):
        return self._lazy

    @lazy.setter
    def lazy(self, value):
        self._lazy = bool(value)

    @property
    def timeout(self):
        return self._timeout

    @property
    def logging_enabled(self):
        return self._log

    def set_stage_config(self, stage_name, **kwargs):
        """Set configuration for a specific stage."""
        if stage_name not in self._stage_configs:
            self._stage_configs[stage_name] = {}
        self._stage_configs[stage_name].update(kwargs)

    def get_stage_config(self, stage_name):
        """Get configuration for a specific stage."""
        return self._stage_configs.get(stage_name, {})

    def add_validator(self, validator_fn):
        """Add a validation function to run between stages."""
        if not callable(validator_fn):
            raise TypeError("Validator must be callable")
        self._validators.append(validator_fn)

    def get_validators(self):
        """Return list of validators."""
        return list(self._validators)

    def validate(self):
        """Validate the configuration itself."""
        if self._lazy and self._batch_size < 1:
            raise ValueError("Lazy evaluation requires batch_size >= 1")
        if self._timeout <= 0:
            raise ValueError("Timeout must be positive")
        return True

    def __repr__(self):
        return (
            f"PipelineConfig(batch_size={self._batch_size}, lazy={self._lazy}, "
            f"timeout={self._timeout}, log={self._log})"
        )
