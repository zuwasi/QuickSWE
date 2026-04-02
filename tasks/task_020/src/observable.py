"""Observable base class implementing the Observer pattern."""


class Observable:
    """Base class that allows observers to subscribe to notifications.

    Observers are callbacks (functions or bound methods) that are called
    when ``notify`` is invoked with event data.
    """

    def __init__(self):
        self._observers = []
        self._name = self.__class__.__name__

    def attach(self, callback) -> None:
        """Register an observer callback.

        Args:
            callback: A callable that will be invoked on notification.
                     Typically a bound method of an observer object.
        """
        if callback not in self._observers:
            self._observers.append(callback)

    def detach(self, callback) -> bool:
        """Remove an observer callback.

        Returns:
            True if the callback was found and removed.
        """
        try:
            self._observers.remove(callback)
            return True
        except ValueError:
            return False

    def notify(self, event_type: str, data=None) -> int:
        """Notify all observers of an event.

        Args:
            event_type: Type of event.
            data: Event data payload.

        Returns:
            Number of observers notified.
        """
        count = 0
        for callback in self._observers:
            callback(event_type, data)
            count += 1
        return count

    @property
    def observer_count(self) -> int:
        """Return the number of registered observers."""
        return len(self._observers)
