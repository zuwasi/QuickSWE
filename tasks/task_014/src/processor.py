"""Data processing pipeline — every method returns (success, result_or_error) tuples."""

import json
import math


class DataProcessor:
    """Processes data records with verbose tuple-based error handling."""

    def parse_json(self, raw_string):
        """Parse a JSON string into a Python object.

        Returns:
            (True, parsed_object) on success
            (False, error_message) on failure
        """
        if not isinstance(raw_string, str):
            return (False, "Input must be a string")
        try:
            data = json.loads(raw_string)
        except json.JSONDecodeError as exc:
            return (False, f"Invalid JSON: {exc}")
        return (True, data)

    def validate_record(self, record):
        """Validate that a record dict has required fields.

        Required: 'id' (int), 'name' (str, non-empty), 'value' (numeric).

        Returns:
            (True, record) on success
            (False, error_message) on failure
        """
        if not isinstance(record, dict):
            return (False, "Record must be a dictionary")
        if "id" not in record:
            return (False, "Missing required field: id")
        if not isinstance(record["id"], int):
            return (False, "Field 'id' must be an integer")
        if "name" not in record:
            return (False, "Missing required field: name")
        if not isinstance(record["name"], str) or len(record["name"].strip()) == 0:
            return (False, "Field 'name' must be a non-empty string")
        if "value" not in record:
            return (False, "Missing required field: value")
        if not isinstance(record["value"], (int, float)):
            return (False, "Field 'value' must be numeric")
        if math.isnan(record["value"]) or math.isinf(record["value"]):
            return (False, "Field 'value' must be finite")
        return (True, record)

    def clean_data(self, record):
        """Strip whitespace from string fields and clamp value to [0, 10000].

        Returns:
            (True, cleaned_record) on success
            (False, error_message) on failure
        """
        ok, result = self.validate_record(record)
        if not ok:
            return (False, f"Cleaning failed: {result}")

        cleaned = dict(record)
        cleaned["name"] = cleaned["name"].strip()
        val = cleaned["value"]
        if val < 0:
            val = 0
        elif val > 10000:
            val = 10000
        cleaned["value"] = val
        return (True, cleaned)

    def transform_record(self, record, multiplier=1.0):
        """Multiply the record's value by a multiplier.

        Returns:
            (True, transformed_record) on success
            (False, error_message) on failure
        """
        if not isinstance(multiplier, (int, float)):
            return (False, "Multiplier must be numeric")
        if multiplier < 0:
            return (False, "Multiplier must be non-negative")
        ok, cleaned = self.clean_data(record)
        if not ok:
            return (False, f"Transform failed: {cleaned}")
        transformed = dict(cleaned)
        transformed["value"] = round(transformed["value"] * multiplier, 4)
        return (True, transformed)

    def aggregate(self, records):
        """Compute sum and average of a list of validated records.

        Returns:
            (True, {"count": N, "sum": S, "average": A}) on success
            (False, error_message) on failure
        """
        if not isinstance(records, list):
            return (False, "Records must be a list")
        if len(records) == 0:
            return (False, "Cannot aggregate empty list")
        total = 0
        for idx, rec in enumerate(records):
            ok, result = self.validate_record(rec)
            if not ok:
                return (False, f"Record at index {idx} invalid: {result}")
            total += rec["value"]
        avg = total / len(records)
        return (True, {"count": len(records), "sum": total, "average": round(avg, 4)})

    def process_batch(self, json_strings):
        """Parse, validate, and clean a batch of JSON strings.

        Returns:
            (True, list_of_cleaned_records) on success
            (False, error_message) on first failure
        """
        if not isinstance(json_strings, list):
            return (False, "Batch input must be a list of strings")
        results = []
        for idx, raw in enumerate(json_strings):
            ok, parsed = self.parse_json(raw)
            if not ok:
                return (False, f"Batch item {idx}: {parsed}")
            ok, cleaned = self.clean_data(parsed)
            if not ok:
                return (False, f"Batch item {idx}: {cleaned}")
            results.append(cleaned)
        return (True, results)
