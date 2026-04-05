import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.plugin_loader import PluginLoader, CircularDependencyError, MissingDependencyError


class TestPluginLoaderPassToPass:
    """Tests that should pass both before and after the fix."""

    def test_register_single_plugin(self):
        loader = PluginLoader()
        info = loader.register("core", "1.0.0")
        assert info.name == "core"
        assert loader.get_plugin("core") is not None

    def test_missing_dependency_raises(self):
        loader = PluginLoader()
        loader.register("app", dependencies=["missing"])
        with pytest.raises(MissingDependencyError):
            loader.resolve_order()

    def test_no_dependencies_any_order(self):
        loader = PluginLoader()
        loader.register("a")
        loader.register("b")
        loader.register("c")
        order = loader.resolve_order()
        assert set(order) == {"a", "b", "c"}


@pytest.mark.fail_to_pass
class TestPluginLoaderFailToPass:
    """Tests that fail before the fix and pass after."""

    def test_linear_dependency_chain(self):
        loader = PluginLoader()
        loader.register("database")
        loader.register("orm", dependencies=["database"])
        loader.register("api", dependencies=["orm"])
        loader.register("frontend", dependencies=["api"])
        order = loader.resolve_order()
        assert order.index("database") < order.index("orm")
        assert order.index("orm") < order.index("api")
        assert order.index("api") < order.index("frontend")

    def test_diamond_dependency(self):
        loader = PluginLoader()
        loader.register("core")
        loader.register("auth", dependencies=["core"])
        loader.register("db", dependencies=["core"])
        loader.register("app", dependencies=["auth", "db"])
        order = loader.resolve_order()
        assert order.index("core") < order.index("auth")
        assert order.index("core") < order.index("db")
        assert order.index("auth") < order.index("app")
        assert order.index("db") < order.index("app")

    def test_load_all_initializes_in_order(self):
        init_order = []

        def make_init(name):
            def init(config, deps):
                init_order.append(name)
                return f"{name}_ready"
            return init

        loader = PluginLoader()
        loader.register("base", init_func=make_init("base"))
        loader.register("middle", dependencies=["base"],
                        init_func=make_init("middle"))
        loader.register("top", dependencies=["middle"],
                        init_func=make_init("top"))
        loader.load_all()
        assert init_order == ["base", "middle", "top"]
        assert loader.is_loaded("top")

    def test_deps_available_during_init(self):
        def base_init(config, deps):
            return {"connection": "db://localhost"}

        def app_init(config, deps):
            assert "base" in deps
            assert deps["base"]["connection"] == "db://localhost"
            return {"status": "ok"}

        loader = PluginLoader()
        loader.register("base", init_func=base_init)
        loader.register("app", dependencies=["base"], init_func=app_init)
        log = loader.load_all()
        assert all(entry.startswith("OK:") for entry in log)
