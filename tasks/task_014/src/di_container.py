"""Dependency injection container."""

from typing import Any, Callable, Dict, Optional


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected during resolution."""
    pass


class ServiceNotFoundError(Exception):
    """Raised when a requested service is not registered."""
    pass


class Lifetime:
    TRANSIENT = "transient"
    SINGLETON = "singleton"


class ServiceDescriptor:
    """Describes a registered service."""

    def __init__(self, name: str, factory: Callable, lifetime: str):
        self.name = name
        self.factory = factory
        self.lifetime = lifetime


class Container:
    """A simple dependency injection container.

    Supports singleton and transient lifetimes. Factories receive the
    container as their sole argument so they can resolve dependencies.
    """

    def __init__(self):
        self._services: Dict[str, ServiceDescriptor] = {}
        self._singletons: Dict[str, Any] = {}
        self._parent: Optional["Container"] = None

    def register(self, name: str, factory: Callable,
                 lifetime: str = Lifetime.TRANSIENT) -> "Container":
        """Register a service with a factory function.

        The factory receives the container as its only argument:
            container.register("db", lambda c: Database(c.resolve("config")))
        """
        if lifetime not in (Lifetime.TRANSIENT, Lifetime.SINGLETON):
            raise ValueError(f"Invalid lifetime: {lifetime}")
        self._services[name] = ServiceDescriptor(name, factory, lifetime)
        return self

    def register_instance(self, name: str, instance: Any) -> "Container":
        """Register an existing instance as a singleton."""
        self._services[name] = ServiceDescriptor(
            name, lambda c: instance, Lifetime.SINGLETON
        )
        self._singletons[name] = instance
        return self

    def resolve(self, name: str) -> Any:
        """Resolve a service by name.

        If the service has singleton lifetime and was already created,
        returns the cached instance.
        """
        if name not in self._services:
            if self._parent is not None:
                return self._parent.resolve(name)
            raise ServiceNotFoundError(f"Service '{name}' is not registered")

        descriptor = self._services[name]

        if descriptor.lifetime == Lifetime.SINGLETON:
            if name in self._singletons:
                return self._singletons[name]

        instance = descriptor.factory(self)

        if descriptor.lifetime == Lifetime.SINGLETON:
            self._singletons[name] = instance

        return instance

    def has(self, name: str) -> bool:
        """Check if a service is registered."""
        if name in self._services:
            return True
        if self._parent is not None:
            return self._parent.has(name)
        return False

    def create_child(self) -> "Container":
        """Create a child container that falls back to this container."""
        child = Container()
        child._parent = self
        return child

    def get_registered_names(self) -> list:
        """Return all registered service names."""
        names = list(self._services.keys())
        if self._parent is not None:
            names.extend(self._parent.get_registered_names())
        return list(set(names))

    def clear(self) -> None:
        """Remove all registrations and cached singletons."""
        self._services.clear()
        self._singletons.clear()
