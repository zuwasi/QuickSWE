"""Binding — connects two observables for synchronization.

TODO: Implement two-way binding with loop prevention.
When source changes, target updates (via optional transform).
When target changes, source updates (via optional reverse_transform).
Must prevent infinite update loops.
"""


class Binding:
    """Two-way binding between two ObservableValues.

    Args:
        source: The source ObservableValue.
        target: The target ObservableValue.
        transform: Optional function to transform source -> target value.
        reverse_transform: Optional function to transform target -> source value.
    """

    def __init__(self, source, target, transform=None, reverse_transform=None):
        self._source = source
        self._target = target
        self._transform = transform or (lambda x: x)
        self._reverse_transform = reverse_transform or (lambda x: x)
        self._active = True
        # TODO: Set up bidirectional subscriptions with loop prevention

    def destroy(self):
        """Remove all subscriptions and deactivate the binding."""
        self._active = False
        # TODO: Clean up subscriptions

    @property
    def is_active(self):
        return self._active
