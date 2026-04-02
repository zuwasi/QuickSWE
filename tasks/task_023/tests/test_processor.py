import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.processor import DataProcessor


# ── pass-to-pass: existing processing pipeline behaviour ─────────────

class TestValidation:
    def test_none_data_returns_error(self):
        dp = DataProcessor()
        result = dp.process(None)
        assert result["result"] is None
        assert len(result["errors"]) > 0

    def test_list_of_dicts_with_id(self):
        data = [{"id": 1, "value": "hello"}, {"id": 2, "value": "world"}]
        result = DataProcessor().process(data)
        assert result["result"]["count"] == 2

    def test_dict_with_id(self):
        data = {"id": 1, "value": "single item"}
        result = DataProcessor().process(data)
        assert result["result"]["count"] == 1

    def test_string_input(self):
        result = DataProcessor().process("some text data")
        assert result["result"]["count"] == 1
        assert result["result"]["items"][0]["value"] == "some text data"

    def test_list_of_strings(self):
        data = ["alpha", "beta", "gamma"]
        result = DataProcessor().process(data)
        assert result["result"]["count"] == 3

    def test_mixed_list(self):
        data = [{"id": 1, "value": 42}, "text_item", 99]
        result = DataProcessor().process(data)
        assert result["result"]["count"] == 3

    def test_invalid_items_produce_errors(self):
        data = [{"id": 1}, {"no_id": True}, {"id": 2}]
        result = DataProcessor().process(data)
        assert result["result"]["count"] == 2
        assert result["stats"]["errors"] == 1


class TestTransform:
    def test_keys_lowercased(self):
        data = [{"id": 1, "Name": "Alice", "Email": "ALICE@EXAMPLE.COM"}]
        result = DataProcessor().process(data)
        items = result["result"]["items"]
        assert "name" in items[0]
        assert items[0]["name"] == "alice"

    def test_string_values_stripped_and_lowered(self):
        data = [{"id": 1, "value": "  HELLO  "}]
        result = DataProcessor().process(data)
        assert result["result"]["items"][0]["value"] == "hello"

    def test_type_classification_text(self):
        data = [{"id": 1, "value": "some text"}]
        result = DataProcessor().process(data)
        assert result["result"]["items"][0]["_type"] == "text"

    def test_type_classification_numeric(self):
        data = [{"id": 1, "value": 42}]
        result = DataProcessor().process(data)
        assert result["result"]["items"][0]["_type"] == "numeric"


class TestEnrich:
    def test_string_length_added(self):
        data = [{"id": 1, "value": "test"}]
        result = DataProcessor().process(data)
        assert result["result"]["items"][0]["_length"] == 4

    def test_numeric_tags(self):
        data = [{"id": 1, "value": 150}]
        result = DataProcessor().process(data)
        assert "high" in result["result"]["items"][0]["_tags"]

    def test_text_tags(self):
        data = [{"id": 1, "value": "hello world, this is a test"}]
        result = DataProcessor().process(data)
        tags = result["result"]["items"][0]["_tags"]
        assert "medium_text" in tags

    def test_tag_prefix_from_config(self):
        dp = DataProcessor(config={"tag_prefix": "batch_1"})
        result = dp.process([{"id": 1, "value": "test"}])
        assert "batch_1" in result["result"]["items"][0]["_tags"]


class TestFilter:
    def test_no_filters_keeps_all(self):
        data = [{"id": 1, "value": 5}, {"id": 2, "value": 50}]
        result = DataProcessor().process(data)
        assert result["result"]["count"] == 2

    def test_min_value_filter(self):
        dp = DataProcessor(config={"filters": {"min_value": 10}})
        data = [{"id": 1, "value": 5}, {"id": 2, "value": 50}]
        result = dp.process(data)
        assert result["result"]["count"] == 1
        assert result["stats"]["filtered"] == 1

    def test_exclude_types_filter(self):
        dp = DataProcessor(config={"filters": {"exclude_types": ["text"]}})
        data = [{"id": 1, "value": "text"}, {"id": 2, "value": 42}]
        result = dp.process(data)
        assert result["result"]["count"] == 1
        assert result["result"]["items"][0]["value"] == 42


class TestAggregate:
    def test_numeric_summary(self):
        data = [{"id": 1, "value": 10}, {"id": 2, "value": 20}, {"id": 3, "value": 30}]
        result = DataProcessor().process(data)
        summary = result["result"]["numeric_summary"]
        assert summary["sum"] == 60
        assert summary["min"] == 10
        assert summary["max"] == 30
        assert summary["avg"] == 20.0

    def test_type_distribution(self):
        data = [{"id": 1, "value": "a"}, {"id": 2, "value": "b"}, {"id": 3, "value": 10}]
        result = DataProcessor().process(data)
        dist = result["result"]["type_distribution"]
        assert dist["text"] == 2
        assert dist["numeric"] == 1

    def test_all_tags_collected(self):
        data = [{"id": 1, "value": 150}, {"id": 2, "value": 5}]
        result = DataProcessor().process(data)
        tags = result["result"]["all_tags"]
        assert "high" in tags
        assert "low" in tags

    def test_empty_after_filter(self):
        dp = DataProcessor(config={"filters": {"min_value": 9999}})
        data = [{"id": 1, "value": 1}]
        result = dp.process(data)
        assert result["result"]["count"] == 0


class TestEndToEnd:
    def test_full_pipeline_list_of_dicts(self):
        config = {"tag_prefix": "test", "filters": {"min_value": 5}}
        dp = DataProcessor(config=config)
        data = [
            {"id": 1, "value": 3},
            {"id": 2, "value": 50},
            {"id": 3, "value": 200},
        ]
        result = dp.process(data)
        assert result["result"]["count"] == 2
        assert result["stats"]["filtered"] == 1

    def test_full_pipeline_preserves_data_integrity(self):
        data = [{"id": "a", "value": "Hello World"}]
        result = DataProcessor().process(data)
        items = result["result"]["items"]
        assert len(items) == 1
        assert items[0]["value"] == "hello world"
        assert items[0]["_type"] == "text"
        assert "_length" in items[0]
        assert "_tags" in items[0]


# ── fail-to-pass: plugin architecture ────────────────────────────────

class TestPluginBaseImport:
    @pytest.mark.fail_to_pass
    def test_plugin_base_importable(self):
        from src.processor import PluginBase
        assert PluginBase is not None

    @pytest.mark.fail_to_pass
    def test_plugin_base_is_abstract(self):
        from src.processor import PluginBase
        import abc
        # PluginBase should not be directly instantiable
        with pytest.raises(TypeError):
            PluginBase()


class TestPluginRegistry:
    @pytest.mark.fail_to_pass
    def test_registry_importable(self):
        from src.processor import PluginRegistry
        assert PluginRegistry is not None

    @pytest.mark.fail_to_pass
    def test_register_and_get_plugins(self):
        from src.processor import PluginBase, PluginRegistry

        class DummyPlugin(PluginBase):
            name = "dummy"
            order = 99

            def process(self, data, context):
                return data

        registry = PluginRegistry()
        plugin = DummyPlugin()
        registry.register(plugin)
        plugins = registry.get_plugins()
        assert len(plugins) >= 1
        names = [p.name for p in plugins]
        assert "dummy" in names

    @pytest.mark.fail_to_pass
    def test_plugins_returned_in_order(self):
        from src.processor import PluginBase, PluginRegistry

        class Early(PluginBase):
            name = "early"
            order = 1
            def process(self, data, context):
                return data

        class Late(PluginBase):
            name = "late"
            order = 50
            def process(self, data, context):
                return data

        class Middle(PluginBase):
            name = "middle"
            order = 25
            def process(self, data, context):
                return data

        registry = PluginRegistry()
        registry.register(Late())
        registry.register(Early())
        registry.register(Middle())
        plugins = registry.get_plugins()
        names = [p.name for p in plugins]
        assert names.index("early") < names.index("middle") < names.index("late")


class TestCustomPluginExecution:
    @pytest.mark.fail_to_pass
    def test_custom_plugin_runs_in_pipeline(self):
        """A custom plugin registered in the registry should be executed by DataProcessor."""
        from src.processor import PluginBase, PluginRegistry

        execution_log = []

        class LogPlugin(PluginBase):
            name = "log"
            order = 999  # run last

            def process(self, data, context):
                execution_log.append("log_plugin_ran")
                return data

        registry = PluginRegistry()
        registry.register(LogPlugin())

        dp = DataProcessor(config={}, registry=registry)
        dp.process([{"id": 1, "value": "test"}])

        assert "log_plugin_ran" in execution_log

    @pytest.mark.fail_to_pass
    def test_custom_plugin_can_modify_data(self):
        """A custom plugin that adds a field to every record."""
        from src.processor import PluginBase, PluginRegistry

        class StampPlugin(PluginBase):
            name = "stamp"
            order = 35  # after enrich (30), before filter (40)

            def process(self, data, context):
                if isinstance(data, list):
                    for record in data:
                        record["_stamped"] = True
                return data

        registry = PluginRegistry()
        registry.register(StampPlugin())

        dp = DataProcessor(config={}, registry=registry)
        result = dp.process([{"id": 1, "value": "test"}])

        assert result["result"]["items"][0].get("_stamped") is True

    @pytest.mark.fail_to_pass
    def test_context_shared_between_plugins(self):
        """Plugins can communicate via a shared context dict."""
        from src.processor import PluginBase, PluginRegistry

        class WriterPlugin(PluginBase):
            name = "writer"
            order = 1

            def process(self, data, context):
                context["written_by"] = "writer_plugin"
                return data

        class ReaderPlugin(PluginBase):
            name = "reader"
            order = 999

            def process(self, data, context):
                if isinstance(data, list):
                    for record in data:
                        record["_context_val"] = context.get("written_by", "missing")
                return data

        registry = PluginRegistry()
        registry.register(WriterPlugin())
        registry.register(ReaderPlugin())

        dp = DataProcessor(config={}, registry=registry)
        result = dp.process([{"id": 1, "value": "data"}])

        assert result["result"]["items"][0]["_context_val"] == "writer_plugin"
