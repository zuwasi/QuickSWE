"""Pipeline stage implementations."""

from abc import ABC, abstractmethod


class Stage(ABC):
    """Base class for pipeline stages."""

    def __init__(self, name=None):
        self._name = name or self.__class__.__name__
        self._processed_count = 0
        self._error_count = 0

    @property
    def name(self):
        return self._name

    @property
    def processed_count(self):
        return self._processed_count

    @abstractmethod
    def process(self, item, context=None):
        """Process a single item. Return the item or None to filter it out."""
        pass

    def process_batch(self, items, context=None):
        """Process a batch of items. Returns list of results."""
        results = []
        for item in items:
            try:
                result = self.process(item, context)
                if result is not None:
                    results.append(result)
                    self._processed_count += 1
            except Exception as e:
                self._error_count += 1
                if context:
                    context.log_error(self._name, e, item)
        return results

    def setup(self, context=None):
        """Called before processing begins."""
        pass

    def teardown(self, context=None):
        """Called after processing completes."""
        pass

    def reset(self):
        """Reset stage counters."""
        self._processed_count = 0
        self._error_count = 0

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self._name}')"


class FilterStage(Stage):
    """Filters items based on a predicate function."""

    def __init__(self, predicate, name=None):
        super().__init__(name=name or "FilterStage")
        self._predicate = predicate
        self._filtered_count = 0

    @property
    def filtered_count(self):
        return self._filtered_count

    def process(self, item, context=None):
        if self._predicate(item):
            return item
        self._filtered_count += 1
        return None


class MapStage(Stage):
    """Transforms items using a mapping function.

    The mapping function receives an item and should return the transformed item.
    If the function modifies the item in place (e.g., mutating a dict), that's
    acceptable — the stage will return whatever the function returns.
    """

    def __init__(self, transform_fn, name=None):
        super().__init__(name=name or "MapStage")
        self._transform_fn = transform_fn

    def process(self, item, context=None):
        return self._transform_fn(item)


class AggregateStage(Stage):
    """Aggregates items using a reduce-like function.

    Collects all items and produces a single aggregated result.
    Note: this stage buffers all items internally before producing output.
    """

    def __init__(self, aggregate_fn, initial=None, name=None):
        super().__init__(name=name or "AggregateStage")
        self._aggregate_fn = aggregate_fn
        self._initial = initial
        self._accumulator = initial
        self._items_collected = []

    def process(self, item, context=None):
        self._items_collected.append(item)
        return item

    def finalize(self, context=None):
        """Run the aggregation over collected items and return result."""
        result = self._initial
        for item in self._items_collected:
            result = self._aggregate_fn(result, item)
        if context:
            context.set_metadata(self._name, 'aggregate_result', result)
            context.set_metadata(self._name, 'items_count', len(self._items_collected))
        return result

    def reset(self):
        super().reset()
        self._accumulator = self._initial
        self._items_collected = []


class EnrichStage(Stage):
    """Enriches items by adding computed fields.

    Takes a dict of field_name -> compute_fn pairs. Each compute_fn
    receives the item and returns the value for that field.
    """

    def __init__(self, enrichments, name=None):
        super().__init__(name=name or "EnrichStage")
        self._enrichments = enrichments

    def process(self, item, context=None):
        if not isinstance(item, dict):
            return item
        enriched = dict(item)
        for field_name, compute_fn in self._enrichments.items():
            try:
                enriched[field_name] = compute_fn(item)
            except Exception:
                enriched[field_name] = None
        return enriched


class ValidateStage(Stage):
    """Validates items against a schema (dict of field -> type)."""

    def __init__(self, schema, strict=False, name=None):
        super().__init__(name=name or "ValidateStage")
        self._schema = schema
        self._strict = strict
        self._validation_errors = []

    @property
    def validation_errors(self):
        return list(self._validation_errors)

    def process(self, item, context=None):
        if not isinstance(item, dict):
            if self._strict:
                self._validation_errors.append(
                    f"Expected dict, got {type(item).__name__}"
                )
                return None
            return item

        for field, expected_type in self._schema.items():
            if field not in item:
                if self._strict:
                    self._validation_errors.append(f"Missing field: {field}")
                    return None
                continue
            if not isinstance(item[field], expected_type):
                self._validation_errors.append(
                    f"Field '{field}' expected {expected_type.__name__}, "
                    f"got {type(item[field]).__name__}"
                )
                if self._strict:
                    return None
        return item
