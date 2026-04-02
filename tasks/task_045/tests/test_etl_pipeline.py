import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.database import MockDatabase
from src.file_io import read_source, parse_csv_data
from src.report import generate_report
from src.etl import extract_transform_load

SAMPLE_CSV = """name,age,email,salary
Alice,30,alice@example.com,75000
Bob,25,bob@example.com,55000
Charlie,40,charlie@example.com,120000
Diana,35,diana@example.com,45000
"""

DIRTY_CSV = """name,age,email,salary
Alice,30,alice@example.com,75000
,25,missing@example.com,55000
Bob,200,bob@example.com,60000
Charlie,abc,charlie@example.com,50000
Diana,28,invalid-email,45000
Eve,22,eve@example.com,-5000
"""

# ── pass-to-pass: basic utilities still work ──────────────────────────


class TestDatabaseBasic:
    def test_insert_and_query(self):
        db = MockDatabase()
        db.create_table("test")
        db.insert("test", {"name": "Alice", "age": 30})
        results = db.query("test", name="Alice")
        assert len(results) == 1
        assert results[0]["name"] == "Alice"

    def test_count(self):
        db = MockDatabase()
        db.create_table("test")
        db.insert("test", {"x": 1})
        db.insert("test", {"x": 2})
        assert db.count("test") == 2

    def test_insert_many(self):
        db = MockDatabase()
        db.create_table("test")
        ids = db.insert_many("test", [{"a": 1}, {"a": 2}])
        assert len(ids) == 2


class TestFileIOBasic:
    def test_parse_csv_data(self):
        records = parse_csv_data(SAMPLE_CSV)
        assert len(records) == 4
        assert records[0]["name"] == "Alice"
        assert records[0]["age"] == "30"

    def test_read_source(self):
        records = read_source(SAMPLE_CSV)
        assert len(records) == 4

    def test_empty_csv(self):
        records = parse_csv_data("")
        assert records == []


class TestMonolithETL:
    """These tests verify the monolith produces correct output.
    They should pass before and after refactoring (pass-to-pass)."""

    def test_end_to_end_clean_data(self):
        db = MockDatabase()
        report = extract_transform_load(SAMPLE_CSV, db)
        assert db.count("records") == 4
        assert "Records Extracted: 4" in report
        assert "Records Loaded: 4" in report

    def test_end_to_end_dirty_data(self):
        db = MockDatabase()
        report = extract_transform_load(DIRTY_CSV, db)
        # Missing name skipped, invalid age/email/salary skipped
        assert db.count("records") < 6

    def test_salary_bands_computed(self):
        db = MockDatabase()
        extract_transform_load(SAMPLE_CSV, db)
        records = db.all_records("records")
        bands = {r["name"]: r["salary_band"] for r in records}
        assert bands["Alice"] == "medium"
        assert bands["Charlie"] == "high"
        assert bands["Diana"] == "low"

    def test_name_upper_computed(self):
        db = MockDatabase()
        extract_transform_load(SAMPLE_CSV, db)
        records = db.all_records("records")
        for r in records:
            assert r["name_upper"] == r["name"].upper()


# ── fail-to-pass: Pipeline/Step architecture ──────────────────────────


class TestStepClasses:
    @pytest.mark.fail_to_pass
    def test_step_base_class_exists(self):
        """Step base class should be importable with execute method."""
        from src.etl import Step
        assert hasattr(Step, "execute")

    @pytest.mark.fail_to_pass
    def test_extract_step(self):
        """ExtractStep should parse CSV source data."""
        from src.etl import ExtractStep, PipelineContext
        step = ExtractStep()
        ctx = PipelineContext()
        ctx.config["source"] = SAMPLE_CSV
        result = step.execute(None, ctx)
        assert len(result) == 4
        assert result[0]["name"] == "Alice"

    @pytest.mark.fail_to_pass
    def test_clean_step(self):
        """CleanStep should remove records with missing required fields."""
        from src.etl import CleanStep, PipelineContext
        step = CleanStep(required_fields=["name", "id"])
        data = [
            {"name": "Alice", "id": "1", "age": "30"},
            {"name": "", "id": "2", "age": "25"},
            {"name": "Bob", "id": "null", "age": "40"},
        ]
        ctx = PipelineContext()
        result = step.execute(data, ctx)
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    @pytest.mark.fail_to_pass
    def test_validate_step(self):
        """ValidateStep should reject records with invalid field values."""
        from src.etl import ValidateStep, PipelineContext
        step = ValidateStep()
        data = [
            {"name": "Alice", "age": "30", "email": "a@b.com", "salary": "50000"},
            {"name": "Bob", "age": "200", "email": "b@c.com", "salary": "60000"},
            {"name": "Eve", "age": "25", "email": "invalid", "salary": "40000"},
        ]
        ctx = PipelineContext()
        result = step.execute(data, ctx)
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    @pytest.mark.fail_to_pass
    def test_transform_step(self):
        """TransformStep should add salary_band and name_upper fields."""
        from src.etl import TransformStep, PipelineContext
        step = TransformStep()
        data = [
            {"name": "Alice", "age": "30", "salary": "75000"},
        ]
        ctx = PipelineContext()
        result = step.execute(data, ctx)
        assert result[0]["salary"] == 75000.0
        assert result[0]["age"] == 30
        assert result[0]["salary_band"] == "medium"
        assert result[0]["name_upper"] == "ALICE"

    @pytest.mark.fail_to_pass
    def test_load_step(self):
        """LoadStep should insert records into the database."""
        from src.etl import LoadStep, PipelineContext
        db = MockDatabase()
        ctx = PipelineContext()
        ctx.config["db"] = db
        ctx.config["table_name"] = "output"
        step = LoadStep()
        data = [{"name": "Alice", "age": 30}]
        result = step.execute(data, ctx)
        assert db.count("output") == 1

    @pytest.mark.fail_to_pass
    def test_report_step(self):
        """ReportStep should generate a summary report string."""
        from src.etl import ReportStep, PipelineContext
        ctx = PipelineContext()
        ctx.step_results["ExtractStep"] = {"count": 5}
        ctx.step_results["CleanStep"] = {"count": 4}
        ctx.step_results["ValidateStep"] = {"count": 3}
        ctx.step_results["LoadStep"] = {"count": 3}
        ctx.config["table_name"] = "test_table"
        step = ReportStep()
        data = [{"name": "x"}] * 3
        result = step.execute(data, ctx)
        assert isinstance(ctx.report, str)
        assert "test_table" in ctx.report


class TestPipeline:
    @pytest.mark.fail_to_pass
    def test_pipeline_class_exists(self):
        """Pipeline class should be importable."""
        from src.etl import Pipeline
        assert hasattr(Pipeline, "run")

    @pytest.mark.fail_to_pass
    def test_pipeline_runs_steps_in_order(self):
        """Pipeline should execute steps in order and pass data through."""
        from src.etl import Pipeline, Step, PipelineContext

        class AddOneStep(Step):
            name = "AddOne"
            def execute(self, data, ctx):
                return [x + 1 for x in data]

        class DoubleStep(Step):
            name = "Double"
            def execute(self, data, ctx):
                return [x * 2 for x in data]

        pipeline = Pipeline(steps=[AddOneStep(), DoubleStep()])
        ctx = PipelineContext()
        result = pipeline.run([1, 2, 3], ctx)
        assert result == [4, 6, 8]

    @pytest.mark.fail_to_pass
    def test_pipeline_tracks_step_results(self):
        """Pipeline context should record each step's results."""
        from src.etl import Pipeline, Step, PipelineContext

        class CountStep(Step):
            name = "Count"
            def execute(self, data, ctx):
                ctx.step_results[self.name] = {"count": len(data)}
                return data

        pipeline = Pipeline(steps=[CountStep()])
        ctx = PipelineContext()
        pipeline.run([1, 2, 3], ctx)
        assert "Count" in ctx.step_results
        assert ctx.step_results["Count"]["count"] == 3

    @pytest.mark.fail_to_pass
    def test_full_pipeline_matches_monolith(self):
        """Full pipeline should produce same DB state as monolith."""
        from src.etl import (
            Pipeline, PipelineContext, ExtractStep, CleanStep,
            ValidateStep, TransformStep, LoadStep, ReportStep,
        )
        # Run monolith
        db_mono = MockDatabase()
        extract_transform_load(SAMPLE_CSV, db_mono)
        mono_records = db_mono.all_records("records")

        # Run pipeline
        db_pipe = MockDatabase()
        ctx = PipelineContext()
        ctx.config["source"] = SAMPLE_CSV
        ctx.config["db"] = db_pipe
        ctx.config["table_name"] = "records"
        pipeline = Pipeline(steps=[
            ExtractStep(),
            CleanStep(required_fields=["name"]),
            ValidateStep(),
            TransformStep(),
            LoadStep(),
            ReportStep(),
        ])
        pipeline.run(None, ctx)

        pipe_records = db_pipe.all_records("records")
        assert len(pipe_records) == len(mono_records)

        for mono_r, pipe_r in zip(
            sorted(mono_records, key=lambda r: r["name"]),
            sorted(pipe_records, key=lambda r: r["name"]),
        ):
            assert mono_r["name"] == pipe_r["name"]
            assert mono_r["salary_band"] == pipe_r["salary_band"]
            assert mono_r["name_upper"] == pipe_r["name_upper"]

    @pytest.mark.fail_to_pass
    def test_pipeline_error_handling(self):
        """Pipeline should record errors from failing steps."""
        from src.etl import Pipeline, Step, PipelineContext

        class FailingStep(Step):
            name = "Failing"
            def execute(self, data, ctx):
                raise ValueError("step failed")

        pipeline = Pipeline(steps=[FailingStep()], abort_on_error=False)
        ctx = PipelineContext()
        pipeline.run([1, 2], ctx)
        assert len(ctx.errors) > 0
