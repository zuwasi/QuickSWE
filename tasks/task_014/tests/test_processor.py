import sys
import os
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.processor import DataProcessor


# ── pass-to-pass: correct results for valid inputs ──────────────────

class TestParseJsonValid:
    def setup_method(self):
        self.dp = DataProcessor()

    def test_parse_simple_object(self):
        ok, data = self.dp.parse_json('{"id": 1, "name": "x", "value": 5}')
        assert ok is True
        assert data == {"id": 1, "name": "x", "value": 5}

    def test_parse_array(self):
        ok, data = self.dp.parse_json('[1, 2, 3]')
        assert ok is True
        assert data == [1, 2, 3]


class TestParseJsonInvalid:
    def setup_method(self):
        self.dp = DataProcessor()

    def test_parse_bad_json(self):
        ok, err = self.dp.parse_json("{bad}")
        assert ok is False
        assert "Invalid JSON" in err

    def test_parse_non_string(self):
        ok, err = self.dp.parse_json(12345)
        assert ok is False
        assert "string" in err.lower()


class TestValidateRecord:
    def setup_method(self):
        self.dp = DataProcessor()

    def test_valid_record(self):
        rec = {"id": 1, "name": "Widget", "value": 42.5}
        ok, result = self.dp.validate_record(rec)
        assert ok is True
        assert result is rec

    def test_missing_id(self):
        ok, err = self.dp.validate_record({"name": "x", "value": 1})
        assert ok is False
        assert "id" in err.lower()

    def test_non_dict(self):
        ok, err = self.dp.validate_record("not a dict")
        assert ok is False


class TestCleanData:
    def setup_method(self):
        self.dp = DataProcessor()

    def test_clean_strips_name(self):
        rec = {"id": 1, "name": "  Widget  ", "value": 50}
        ok, cleaned = self.dp.clean_data(rec)
        assert ok is True
        assert cleaned["name"] == "Widget"

    def test_clean_clamps_high_value(self):
        rec = {"id": 1, "name": "x", "value": 99999}
        ok, cleaned = self.dp.clean_data(rec)
        assert ok is True
        assert cleaned["value"] == 10000

    def test_clean_clamps_negative(self):
        rec = {"id": 1, "name": "x", "value": -5}
        ok, cleaned = self.dp.clean_data(rec)
        assert ok is True
        assert cleaned["value"] == 0


class TestTransformRecord:
    def setup_method(self):
        self.dp = DataProcessor()

    def test_transform_doubles(self):
        rec = {"id": 1, "name": "x", "value": 10}
        ok, t = self.dp.transform_record(rec, multiplier=2.0)
        assert ok is True
        assert t["value"] == 20.0

    def test_transform_bad_multiplier(self):
        rec = {"id": 1, "name": "x", "value": 10}
        ok, err = self.dp.transform_record(rec, multiplier=-1)
        assert ok is False


class TestAggregate:
    def setup_method(self):
        self.dp = DataProcessor()

    def test_aggregate_two_records(self):
        recs = [
            {"id": 1, "name": "a", "value": 10},
            {"id": 2, "name": "b", "value": 20},
        ]
        ok, agg = self.dp.aggregate(recs)
        assert ok is True
        assert agg["count"] == 2
        assert agg["sum"] == 30
        assert agg["average"] == 15.0

    def test_aggregate_empty(self):
        ok, err = self.dp.aggregate([])
        assert ok is False


class TestProcessBatch:
    def setup_method(self):
        self.dp = DataProcessor()

    def test_batch_success(self):
        batch = [
            json.dumps({"id": 1, "name": "a", "value": 5}),
            json.dumps({"id": 2, "name": " b ", "value": 15}),
        ]
        ok, results = self.dp.process_batch(batch)
        assert ok is True
        assert len(results) == 2
        assert results[1]["name"] == "b"

    def test_batch_with_bad_json(self):
        ok, err = self.dp.process_batch(["{bad}"])
        assert ok is False


# ── fail-to-pass: exception classes and raise behaviour ─────────────

class TestExceptionClassesExist:
    @pytest.mark.fail_to_pass
    def test_processing_error_importable(self):
        from src.processor import ProcessingError
        assert issubclass(ProcessingError, Exception)

    @pytest.mark.fail_to_pass
    def test_validation_error_importable(self):
        from src.processor import ValidationError
        assert issubclass(ValidationError, Exception)


class TestMethodsRaiseExceptions:
    @pytest.mark.fail_to_pass
    def test_parse_json_returns_directly(self):
        """After refactoring, parse_json should return the parsed object, NOT a tuple."""
        dp = DataProcessor()
        result = dp.parse_json('{"a": 1}')
        # Must be the parsed dict, not (True, {...})
        assert isinstance(result, dict)
        assert result == {"a": 1}

    @pytest.mark.fail_to_pass
    def test_parse_json_raises_on_bad_input(self):
        from src.processor import ProcessingError
        dp = DataProcessor()
        with pytest.raises(ProcessingError):
            dp.parse_json("{bad}")

    @pytest.mark.fail_to_pass
    def test_validate_record_raises_on_missing_field(self):
        from src.processor import ValidationError
        dp = DataProcessor()
        with pytest.raises(ValidationError):
            dp.validate_record({"name": "x"})

    @pytest.mark.fail_to_pass
    def test_validate_record_returns_directly(self):
        dp = DataProcessor()
        rec = {"id": 1, "name": "ok", "value": 5}
        result = dp.validate_record(rec)
        assert isinstance(result, dict)
        assert result["id"] == 1

    @pytest.mark.fail_to_pass
    def test_clean_data_returns_directly(self):
        dp = DataProcessor()
        rec = {"id": 1, "name": " hi ", "value": 3}
        result = dp.clean_data(rec)
        assert isinstance(result, dict)
        assert result["name"] == "hi"

    @pytest.mark.fail_to_pass
    def test_aggregate_raises_on_empty(self):
        from src.processor import ProcessingError
        dp = DataProcessor()
        with pytest.raises(ProcessingError):
            dp.aggregate([])
