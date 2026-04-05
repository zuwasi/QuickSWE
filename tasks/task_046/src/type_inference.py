"""
Hindley-Milner type inference engine.

Supports type variables, function types, and constructed types (List, Option, etc.).
Implements Algorithm W for type inference with unification.
"""

from typing import Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field


class TypeError(Exception):
    """Type inference error."""
    pass


class Type:
    """Base class for types."""
    pass


class TypeVar(Type):
    """A type variable that can be unified with other types."""
    _counter = 0

    def __init__(self, name: Optional[str] = None):
        if name is None:
            TypeVar._counter += 1
            self.name = f"t{TypeVar._counter}"
        else:
            self.name = name
        self.bound: Optional[Type] = None

    def resolve(self) -> Type:
        """Follow the chain of bindings to find the actual type."""
        if self.bound is not None:
            resolved = self.bound
            while isinstance(resolved, TypeVar) and resolved.bound is not None:
                resolved = resolved.bound
            self.bound = resolved
            return resolved
        return self

    def __repr__(self):
        if self.bound:
            return repr(self.resolve())
        return f"'{self.name}"

    def __eq__(self, other):
        if isinstance(other, TypeVar):
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)


class ConcreteType(Type):
    """A concrete type like Int, Bool, String."""

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, ConcreteType) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class FunctionType(Type):
    """A function type: param -> return."""

    def __init__(self, param_type: Type, return_type: Type):
        self.param_type = param_type
        self.return_type = return_type

    def __repr__(self):
        return f"({self.param_type} -> {self.return_type})"

    def __eq__(self, other):
        return (isinstance(other, FunctionType) and
                self.param_type == other.param_type and
                self.return_type == other.return_type)

    def __hash__(self):
        return hash(("fn", self.param_type, self.return_type))


class ConstructedType(Type):
    """A constructed/generic type like List[T], Option[T], Pair[A, B]."""

    def __init__(self, name: str, type_args: List[Type]):
        self.name = name
        self.type_args = type_args

    def __repr__(self):
        if self.type_args:
            args = ", ".join(repr(a) for a in self.type_args)
            return f"{self.name}[{args}]"
        return self.name

    def __eq__(self, other):
        return (isinstance(other, ConstructedType) and
                self.name == other.name and
                self.type_args == other.type_args)

    def __hash__(self):
        return hash((self.name, tuple(self.type_args)))


# Common concrete types
INT = ConcreteType("Int")
BOOL = ConcreteType("Bool")
STRING = ConcreteType("String")
FLOAT = ConcreteType("Float")
UNIT = ConcreteType("Unit")


def fresh_type_var() -> TypeVar:
    """Create a fresh type variable."""
    return TypeVar()


def list_type(elem_type: Type) -> ConstructedType:
    return ConstructedType("List", [elem_type])


def option_type(elem_type: Type) -> ConstructedType:
    return ConstructedType("Option", [elem_type])


def pair_type(a: Type, b: Type) -> ConstructedType:
    return ConstructedType("Pair", [a, b])


def resolve_type(t: Type) -> Type:
    """Fully resolve a type, following all type variable bindings."""
    if isinstance(t, TypeVar):
        return t.resolve()
    return t


def free_type_vars(t: Type) -> Set[TypeVar]:
    """Find all unbound type variables in a type."""
    t = resolve_type(t)
    if isinstance(t, TypeVar):
        return {t}
    if isinstance(t, ConcreteType):
        return set()
    if isinstance(t, FunctionType):
        return free_type_vars(t.param_type) | free_type_vars(t.return_type)
    if isinstance(t, ConstructedType):
        result: Set[TypeVar] = set()
        for arg in t.type_args:
            result |= free_type_vars(arg)
        return result
    return set()


def unify(t1: Type, t2: Type):
    """
    Unify two types, binding type variables as needed.
    Raises TypeError if types cannot be unified.
    """
    t1 = resolve_type(t1)
    t2 = resolve_type(t2)

    if t1 is t2:
        return

    if isinstance(t1, TypeVar):
        t1.bound = t2
        return

    if isinstance(t2, TypeVar):
        t2.bound = t1
        return

    if isinstance(t1, ConcreteType) and isinstance(t2, ConcreteType):
        if t1.name != t2.name:
            raise TypeError(f"Cannot unify {t1} with {t2}")
        return

    if isinstance(t1, FunctionType) and isinstance(t2, FunctionType):
        unify(t1.param_type, t2.param_type)
        unify(t1.return_type, t2.return_type)
        return

    if isinstance(t1, ConstructedType) and isinstance(t2, ConstructedType):
        if t1.name != t2.name:
            raise TypeError(f"Cannot unify {t1.name} with {t2.name}")
        if len(t1.type_args) != len(t2.type_args):
            raise TypeError(
                f"Type argument count mismatch: {t1.name} has "
                f"{len(t1.type_args)} vs {len(t2.type_args)}"
            )
        for a1, a2 in zip(t1.type_args, t2.type_args):
            unify(a1, a2)
        return

    raise TypeError(f"Cannot unify {t1} with {t2}")


def type_to_string(t: Type) -> str:
    """Pretty-print a type."""
    t = resolve_type(t)
    if isinstance(t, TypeVar):
        return t.name
    if isinstance(t, ConcreteType):
        return t.name
    if isinstance(t, FunctionType):
        param = type_to_string(t.param_type)
        ret = type_to_string(t.return_type)
        return f"({param} -> {ret})"
    if isinstance(t, ConstructedType):
        if t.type_args:
            args = ", ".join(type_to_string(a) for a in t.type_args)
            return f"{t.name}[{args}]"
        return t.name
    return str(t)


@dataclass
class TypeScheme:
    """A polymorphic type scheme: forall vars. type"""
    bound_vars: List[TypeVar]
    body: Type

    def instantiate(self) -> Type:
        """Create a fresh instance of this scheme."""
        subst: Dict[str, TypeVar] = {}
        for v in self.bound_vars:
            subst[v.name] = fresh_type_var()
        return self._apply_subst(self.body, subst)

    def _apply_subst(self, t: Type, subst: Dict[str, TypeVar]) -> Type:
        t = resolve_type(t)
        if isinstance(t, TypeVar):
            if t.name in subst:
                return subst[t.name]
            return t
        if isinstance(t, ConcreteType):
            return t
        if isinstance(t, FunctionType):
            return FunctionType(
                self._apply_subst(t.param_type, subst),
                self._apply_subst(t.return_type, subst),
            )
        if isinstance(t, ConstructedType):
            return ConstructedType(
                t.name,
                [self._apply_subst(a, subst) for a in t.type_args],
            )
        return t


class TypeEnv:
    """Type environment mapping names to type schemes."""

    def __init__(self, parent: Optional["TypeEnv"] = None):
        self._bindings: Dict[str, TypeScheme] = {}
        self.parent = parent

    def bind(self, name: str, scheme: TypeScheme):
        self._bindings[name] = scheme

    def bind_type(self, name: str, t: Type):
        self._bindings[name] = TypeScheme([], t)

    def lookup(self, name: str) -> Optional[TypeScheme]:
        if name in self._bindings:
            return self._bindings[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def extend(self) -> "TypeEnv":
        return TypeEnv(parent=self)

    def free_type_vars(self) -> Set[TypeVar]:
        result: Set[TypeVar] = set()
        for scheme in self._bindings.values():
            body_ftvs = free_type_vars(scheme.body)
            bound_names = {v.name for v in scheme.bound_vars}
            result |= {v for v in body_ftvs if v.name not in bound_names}
        if self.parent:
            result |= self.parent.free_type_vars()
        return result

    def generalize(self, t: Type) -> TypeScheme:
        env_ftvs = self.free_type_vars()
        type_ftvs = free_type_vars(t)
        gen_vars = [v for v in type_ftvs if v not in env_ftvs]
        return TypeScheme(gen_vars, t)
