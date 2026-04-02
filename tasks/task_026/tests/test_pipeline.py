"""Tests for pipeline with batched mode."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pipeline import Pipeline
from src.stages import FilterStage, MapStage, EnrichStage, ValidateStage
from src.config import PipelineConfig
from src.serializer import PipelineSerializer


@pytest.mark.fail_to_pass
class TestBatchedPipelineDataIntegrity:
    """Tests that verify data integrity in batched pipeline mode.

    These tests should FAIL before the fix because the buffer stores
    references to dict objects that get mutated by downstream stages,
    corrupting the 'previous_batch' and 'input' records.
    """

    def test_batched_stage_input_not_corrupted_by_later_stages(self):
        """The recorded input to a stage should not be modified by later stages."""
        config = PipelineConfig(batch_size=100, lazy=True)
        pipeline = Pipeline(config)

        # Stage 1: Filter items with value > 5
        pipeline.add_stage(FilterStage(
            lambda item: item['value'] > 5,
            name="filter"
        ))

        # Stage 2: Map — MUTATES the dict in-place by doubling value
        def double_value(item):
            item['value'] = item['value'] * 2  # In-place mutation!
            return item

        pipeline.add_stage(MapStage(double_value, name="doubler"))

        data = [
            {'id': 1, 'value': 3},
            {'id': 2, 'value': 8},
            {'id': 3, 'value': 12},
            {'id': 4, 'value': 2},
            {'id': 5, 'value': 15},
        ]

        results = pipeline.run(data)

        # The filter stage's recorded input should show the ORIGINAL values
        filter_input = pipeline.get_stage_input("filter")
        assert filter_input is not None

        # Find the items that passed the filter
        original_values = {item['id']: item['value'] for item in filter_input}

        # These should be the ORIGINAL values, not doubled
        assert original_values.get(2) == 8, (
            f"Expected original value 8 for id=2, got {original_values.get(2)}. "
            f"Data was corrupted by the doubler stage."
        )
        assert original_values.get(3) == 12, (
            f"Expected original value 12 for id=3, got {original_values.get(3)}."
        )
        assert original_values.get(5) == 15, (
            f"Expected original value 15 for id=5, got {original_values.get(5)}."
        )

    def test_batched_previous_batch_preserved(self):
        """Buffer's previous_batch should reflect data BEFORE downstream mutation."""
        config = PipelineConfig(batch_size=50, lazy=True)
        pipeline = Pipeline(config)

        # Stage 1: pass everything through
        pipeline.add_stage(FilterStage(lambda x: True, name="passthrough"))

        # Stage 2: mutate items in place
        def add_processed_flag(item):
            item['processed'] = True
            item['original_value'] = item['value']
            item['value'] = item['value'] + 100
            return item

        pipeline.add_stage(MapStage(add_processed_flag, name="processor"))

        data = [
            {'id': 'a', 'value': 10},
            {'id': 'b', 'value': 20},
            {'id': 'c', 'value': 30},
        ]

        results = pipeline.run(data)

        # Check the passthrough stage's input — should NOT have 'processed' flag
        passthrough_input = pipeline.get_stage_input("passthrough")
        assert passthrough_input is not None

        for item in passthrough_input:
            assert 'processed' not in item, (
                f"Item {item['id']} in passthrough input has 'processed' flag — "
                f"data was corrupted by downstream processor stage"
            )
            # Values should be original
            if item['id'] == 'a':
                assert item['value'] == 10
            elif item['id'] == 'b':
                assert item['value'] == 20
            elif item['id'] == 'c':
                assert item['value'] == 30


class TestEagerPipelineWorks:
    """Tests that verify eager (non-batched) pipeline works correctly.
    These should always pass.
    """

    def test_eager_filter_then_map(self):
        config = PipelineConfig(lazy=False)
        pipeline = Pipeline(config)

        pipeline.add_stage(FilterStage(lambda x: x['value'] > 5, name="filter"))
        pipeline.add_stage(MapStage(
            lambda x: {**x, 'value': x['value'] * 2},  # Non-mutating transform
            name="doubler"
        ))

        data = [
            {'id': 1, 'value': 3},
            {'id': 2, 'value': 8},
            {'id': 3, 'value': 12},
        ]

        results = pipeline.run(data)
        assert len(results) == 2
        assert results[0] == {'id': 2, 'value': 16}
        assert results[1] == {'id': 3, 'value': 24}

    def test_eager_enrich_stage(self):
        config = PipelineConfig(lazy=False)
        pipeline = Pipeline(config)

        pipeline.add_stage(EnrichStage({
            'name_upper': lambda x: x['name'].upper(),
            'name_len': lambda x: len(x['name']),
        }))

        data = [
            {'name': 'alice', 'age': 30},
            {'name': 'bob', 'age': 25},
        ]

        results = pipeline.run(data)
        assert results[0]['name_upper'] == 'ALICE'
        assert results[0]['name_len'] == 5
        assert results[1]['name_upper'] == 'BOB'

    def test_eager_validate_stage(self):
        config = PipelineConfig(lazy=False)
        pipeline = Pipeline(config)

        pipeline.add_stage(ValidateStage(
            {'name': str, 'age': int},
            strict=True
        ))

        data = [
            {'name': 'alice', 'age': 30},
            {'name': 'bob', 'age': '25'},  # Wrong type
        ]

        results = pipeline.run(data)
        assert len(results) == 1
        assert results[0]['name'] == 'alice'


class TestSerializerWorks:
    """Tests that verify the serializer works correctly.
    These should always pass — the serializer is NOT the bug.
    """

    def test_serialize_basic_dicts(self):
        serializer = PipelineSerializer(format='dict')
        items = [
            {'name': 'test', 'value': 42},
            {'name': 'other', 'value': 99},
        ]
        result = serializer.serialize(items)
        assert result == items

    def test_serialize_with_nan(self):
        serializer = PipelineSerializer(format='dict')
        items = [{'value': float('nan')}]
        result = serializer.serialize(items)
        assert result[0]['value'] is None

    def test_serialize_to_json(self):
        serializer = PipelineSerializer(format='json')
        items = [{'a': 1}, {'a': 2}]
        result = serializer.serialize(items)
        assert '"a": 1' in result

    def test_serialize_to_csv(self):
        serializer = PipelineSerializer(format='csv')
        items = [
            {'name': 'alice', 'age': 30},
            {'name': 'bob', 'age': 25},
        ]
        result = serializer.serialize(items)
        lines = result.strip().split('\n')
        assert len(lines) == 3  # header + 2 rows

    def test_serialize_nested_dicts_no_mutation(self):
        """Verify serializer does not mutate input data."""
        import copy
        original = [
            {'name': 'test', 'nested': {'a': 1, 'b': [2, 3]}},
        ]
        frozen = copy.deepcopy(original)
        serializer = PipelineSerializer(format='dict')
        serializer.serialize(original)
        assert original == frozen, "Serializer mutated input data!"
