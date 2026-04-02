"""Service for creating and sending notifications."""

from src.notifications import (
    EmailNotification,
    PriorityEmailNotification,
    SMSNotification,
    InternationalSMSNotification,
    PushNotification,
)


class NotificationService:
    """Creates and sends notifications through various channels."""

    def __init__(self):
        self._sent_history = []

    def send_email(self, to: str, subject: str, body: str,
                   cc: list = None, reply_to: str = None) -> dict:
        """Send a standard email notification."""
        notification = EmailNotification(to, subject, body, cc=cc, reply_to=reply_to)
        result = notification.send()
        self._sent_history.append(result)
        return result

    def send_priority_email(self, to: str, subject: str, body: str,
                            priority: int = 1, cc: list = None) -> dict:
        """Send a high-priority email."""
        notification = PriorityEmailNotification(
            to, subject, body, cc=cc, priority=priority
        )
        result = notification.send()
        self._sent_history.append(result)
        return result

    def send_sms(self, to: str, subject: str, body: str) -> dict:
        """Send an SMS notification."""
        notification = SMSNotification(to, subject, body)
        result = notification.send()
        self._sent_history.append(result)
        return result

    def send_international_sms(self, to: str, subject: str, body: str,
                                country_code: str = "+1") -> dict:
        """Send an international SMS."""
        notification = InternationalSMSNotification(
            to, subject, body, country_code=country_code
        )
        result = notification.send()
        self._sent_history.append(result)
        return result

    def send_push(self, device_token: str, subject: str, body: str,
                  icon: str = None, action_url: str = None, badge: int = 0) -> dict:
        """Send a push notification."""
        notification = PushNotification(
            device_token, subject, body, icon=icon,
            action_url=action_url, badge=badge
        )
        result = notification.send()
        self._sent_history.append(result)
        return result

    @property
    def history(self) -> list:
        return list(self._sent_history)

    def clear_history(self):
        self._sent_history.clear()
