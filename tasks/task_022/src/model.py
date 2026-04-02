"""Simple ORM model base class."""


class Field:
    """Describes a column in a model."""

    def __init__(self, field_type: str = "TEXT", primary_key: bool = False,
                 nullable: bool = True):
        self.field_type = field_type
        self.primary_key = primary_key
        self.nullable = nullable
        self.name = None  # set by ModelMeta

    def __repr__(self):
        return f"Field({self.field_type}, pk={self.primary_key})"


class ModelMeta(type):
    """Metaclass that collects Field descriptors."""

    def __new__(mcs, name, bases, namespace):
        fields = {}
        for key, value in namespace.items():
            if isinstance(value, Field):
                value.name = key
                fields[key] = value
        namespace["_fields"] = fields
        return super().__new__(mcs, name, bases, namespace)


class Model(metaclass=ModelMeta):
    """Base model class. Subclasses define fields and a table_name."""

    table_name = None  # must be set by subclasses

    def __init__(self, **kwargs):
        for field_name in self._fields:
            setattr(self, field_name, kwargs.get(field_name))

    @classmethod
    def get_field_names(cls):
        return list(cls._fields.keys())

    def __repr__(self):
        vals = ", ".join(f"{k}={getattr(self, k, None)!r}" for k in self._fields)
        return f"{self.__class__.__name__}({vals})"


# ── Example models for testing ──────────────────────────────────────

class User(Model):
    table_name = "users"
    id = Field("INTEGER", primary_key=True)
    name = Field("TEXT", nullable=False)
    email = Field("TEXT", nullable=False)
    active = Field("INTEGER")
    department_id = Field("INTEGER")


class Order(Model):
    table_name = "orders"
    id = Field("INTEGER", primary_key=True)
    user_id = Field("INTEGER")
    product = Field("TEXT")
    amount = Field("REAL")
    status = Field("TEXT")


class Department(Model):
    table_name = "departments"
    id = Field("INTEGER", primary_key=True)
    name = Field("TEXT")
    budget = Field("REAL")
