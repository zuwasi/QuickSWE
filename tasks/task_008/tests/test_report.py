import sys
import os
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.report import ReportGenerator


SAMPLE_DATA = [
    {"name": "Widget A", "price": 9.99, "quantity": 100},
    {"name": "Widget B", "price": 19.99, "quantity": 50},
    {"name": "Widget C", "price": 4.99, "quantity": 200},
]


# ──────────────────────────────────────────────
# Pass-to-pass: existing functionality tests
# ──────────────────────────────────────────────

class TestExistingFunctionality:
    def test_generate_text_contains_title(self):
        rg = ReportGenerator("Sales Report", SAMPLE_DATA)
        text = rg.generate_text()
        assert "Sales Report" in text

    def test_generate_text_contains_records(self):
        rg = ReportGenerator("Sales Report", SAMPLE_DATA)
        text = rg.generate_text()
        assert "Records: 3" in text

    def test_generate_text_contains_data(self):
        rg = ReportGenerator("Sales Report", SAMPLE_DATA)
        text = rg.generate_text()
        assert "Widget A" in text
        assert "Widget B" in text
        assert "Widget C" in text

    def test_generate_text_contains_values(self):
        rg = ReportGenerator("Sales Report", SAMPLE_DATA)
        text = rg.generate_text()
        assert "9.99" in text
        assert "19.99" in text

    def test_empty_data(self):
        rg = ReportGenerator("Empty Report", [])
        text = rg.generate_text()
        assert "Empty Report" in text
        assert "Records: 0" in text

    def test_title_and_data_stored(self):
        rg = ReportGenerator("Test", SAMPLE_DATA)
        assert rg.title == "Test"
        assert len(rg.data) == 3


# ──────────────────────────────────────────────
# Fail-to-pass: JSON export feature tests
# ──────────────────────────────────────────────

class TestJSONExport:
    @pytest.mark.fail_to_pass
    def test_generate_json_returns_valid_json(self):
        rg = ReportGenerator("Sales Report", SAMPLE_DATA)
        result = rg.generate_json()
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    @pytest.mark.fail_to_pass
    def test_generate_json_has_title(self):
        rg = ReportGenerator("Sales Report", SAMPLE_DATA)
        parsed = json.loads(rg.generate_json())
        assert parsed["title"] == "Sales Report"

    @pytest.mark.fail_to_pass
    def test_generate_json_has_record_count(self):
        rg = ReportGenerator("Sales Report", SAMPLE_DATA)
        parsed = json.loads(rg.generate_json())
        assert parsed["record_count"] == 3

    @pytest.mark.fail_to_pass
    def test_generate_json_has_data(self):
        rg = ReportGenerator("Sales Report", SAMPLE_DATA)
        parsed = json.loads(rg.generate_json())
        assert len(parsed["data"]) == 3
        assert parsed["data"][0]["name"] == "Widget A"

    @pytest.mark.fail_to_pass
    def test_generate_json_has_generated_at(self):
        rg = ReportGenerator("Sales Report", SAMPLE_DATA)
        parsed = json.loads(rg.generate_json())
        assert "generated_at" in parsed
        assert len(parsed["generated_at"]) > 0


class TestExportMethod:
    @pytest.mark.fail_to_pass
    def test_export_json_to_file(self, tmp_path):
        rg = ReportGenerator("Sales Report", SAMPLE_DATA)
        filepath = str(tmp_path / "report.json")
        rg.export("json", filepath)
        with open(filepath, "r") as f:
            parsed = json.loads(f.read())
        assert parsed["title"] == "Sales Report"

    @pytest.mark.fail_to_pass
    def test_export_text_to_file(self, tmp_path):
        rg = ReportGenerator("Sales Report", SAMPLE_DATA)
        filepath = str(tmp_path / "report.txt")
        rg.export("text", filepath)
        with open(filepath, "r") as f:
            content = f.read()
        assert "Sales Report" in content

    @pytest.mark.fail_to_pass
    def test_export_invalid_format_raises(self):
        rg = ReportGenerator("Sales Report", SAMPLE_DATA)
        with pytest.raises(ValueError):
            rg.export("xml", "report.xml")
