"""
Plugin loader with dependency resolution.

Supports registering plugins with their dependencies, resolving the load order
via topological sort, and initializing plugins in the correct sequence.
"""

from typing import List, Dict, Set, Optional, Callable, Any
from collections import defaultdict
from enum import Enum


class PluginState(Enum):
    REGISTERED = "registered"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"
    DISABLED = "disabled"


class PluginError(Exception):
    """Base exception for plugin system errors."""
    pass


class CircularDependencyError(PluginError):
    """Raised when a circular dependency is detected."""
    pass


class MissingDependencyError(PluginError):
    """Raised when a required dependency is not registered."""
    pass


class PluginInfo:
    """Metadata and state for a registered plugin."""

    def __init__(self, name: str, version: str, dependencies: List[str],
                 init_func: Optional[Callable] = None,
                 config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.version = version
        self.dependencies = list(dependencies)
        self.init_func = init_func
        self.config = config or {}
        self.state = PluginState.REGISTERED
        self.init_result = None

    def __repr__(self):
        return f"PluginInfo({self.name!r}, v{self.version}, state={self.state.value})"


class PluginLoader:
    """Manages plugin registration, dependency resolution, and initialization."""

    def __init__(self):
        self._plugins: Dict[str, PluginInfo] = {}
        self._load_order: List[str] = []
        self._init_log: List[str] = []

    def register(self, name: str, version: str = "1.0.0",
                 dependencies: Optional[List[str]] = None,
                 init_func: Optional[Callable] = None,
                 config: Optional[Dict[str, Any]] = None) -> PluginInfo:
        if name in self._plugins:
            raise PluginError(f"Plugin '{name}' is already registered")
        info = PluginInfo(name, version, dependencies or [], init_func, config)
        self._plugins[name] = info
        return info

    def unregister(self, name: str) -> bool:
        if name not in self._plugins:
            return False
        dependents = self._find_dependents(name)
        if dependents:
            raise PluginError(
                f"Cannot unregister '{name}': required by {dependents}")
        del self._plugins[name]
        return True

    def _find_dependents(self, name: str) -> List[str]:
        return [p.name for p in self._plugins.values()
                if name in p.dependencies]

    def resolve_order(self) -> List[str]:
        self._validate_dependencies()
        adj: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = {name: 0 for name in self._plugins}

        for name, info in self._plugins.items():
            for dep in info.dependencies:
                adj[name].append(dep)
                in_degree[dep] += 1

        queue = []
        for name in self._plugins:
            if in_degree[name] == 0:
                queue.append(name)
        queue.sort()

        result = []
        while queue:
            node = queue.pop()
            result.append(node)
            for neighbor in sorted(adj[node]):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
            queue.sort()

        if len(result) != len(self._plugins):
            loaded = set(result)
            remaining = set(self._plugins.keys()) - loaded
            raise CircularDependencyError(
                f"Circular dependency detected among: {remaining}")

        self._load_order = result
        return list(result)

    def _validate_dependencies(self):
        for name, info in self._plugins.items():
            for dep in info.dependencies:
                if dep not in self._plugins:
                    raise MissingDependencyError(
                        f"Plugin '{name}' requires '{dep}' which is not registered")

    def _detect_cycle(self, start: str) -> Optional[List[str]]:
        visited: Set[str] = set()
        path: List[str] = []

        def dfs(node: str) -> Optional[List[str]]:
            if node in visited:
                idx = path.index(node) if node in path else -1
                if idx >= 0:
                    return path[idx:] + [node]
                return None
            visited.add(node)
            path.append(node)
            for dep in self._plugins[node].dependencies:
                cycle = dfs(dep)
                if cycle:
                    return cycle
            path.pop()
            return None

        return dfs(start)

    def load_all(self) -> List[str]:
        order = self.resolve_order()
        self._init_log = []

        for name in order:
            plugin = self._plugins[name]
            plugin.state = PluginState.LOADING

            deps_ok = all(
                self._plugins[d].state == PluginState.LOADED
                for d in plugin.dependencies
            )

            if not deps_ok:
                plugin.state = PluginState.FAILED
                self._init_log.append(f"FAIL:{name}:deps_not_ready")
                continue

            try:
                if plugin.init_func:
                    dep_results = {
                        d: self._plugins[d].init_result
                        for d in plugin.dependencies
                    }
                    plugin.init_result = plugin.init_func(plugin.config, dep_results)
                plugin.state = PluginState.LOADED
                self._init_log.append(f"OK:{name}")
            except Exception as e:
                plugin.state = PluginState.FAILED
                self._init_log.append(f"FAIL:{name}:{e}")

        return self._init_log

    def get_load_order(self) -> List[str]:
        return list(self._load_order)

    def get_plugin(self, name: str) -> Optional[PluginInfo]:
        return self._plugins.get(name)

    def get_all_plugins(self) -> Dict[str, PluginInfo]:
        return dict(self._plugins)

    def get_init_log(self) -> List[str]:
        return list(self._init_log)

    def is_loaded(self, name: str) -> bool:
        plugin = self._plugins.get(name)
        return plugin is not None and plugin.state == PluginState.LOADED

    def get_dependency_tree(self, name: str) -> Dict:
        if name not in self._plugins:
            return {}
        plugin = self._plugins[name]
        tree = {"name": name, "version": plugin.version, "deps": []}
        for dep in plugin.dependencies:
            tree["deps"].append(self.get_dependency_tree(dep))
        return tree
