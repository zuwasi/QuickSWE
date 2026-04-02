"""Notification system with deep inheritance hierarchy."""

from datetime import datetime


class BaseNotification:
    """Base class for all notifications."""

    def __init__(self, recipient: str, subject: str, body: str):
        self.recipient = recipient
        self.subject = subject
        self.body = body
        self.created_at = datetime.now()
        self.sent = False
        self._delivery_log = []

    def validate(self) -> bool:
        """Check that the notification has required fields."""
        if not self.recipient or not self.recipient.strip():
            return False
        if not self.subject or not self.subject.strip():
            return False
        if not self.body or not self.body.strip():
            return False
        return True

    def format_message(self) -> str:
        """Format the notification message."""
        return f"To: {self.recipient}\nSubject: {self.subject}\n\n{self.body}"

    def send(self) -> dict:
        """Send the notification. Returns delivery result."""
        if not self.validate():
            return {"status": "error", "message": "Validation failed"}

        formatted = self.format_message()
        result = self._deliver(formatted)
        self.sent = True
        self._delivery_log.append(result)
        return result

    def _deliver(self, message: str) -> dict:
        """Override in subclass for actual delivery."""
        return {"status": "sent", "channel": "base", "message": message}

    def get_delivery_log(self) -> list:
        return list(self._delivery_log)


class EmailNotification(BaseNotification):
    """Email notification."""

    def __init__(self, recipient: str, subject: str, body: str,
                 cc: list = None, reply_to: str = None):
        super().__init__(recipient, subject, body)
        self.cc = cc or []
        self.reply_to = reply_to

    def validate(self) -> bool:
        if not super().validate():
            return False
        if "@" not in self.recipient:
            return False
        for addr in self.cc:
            if "@" not in addr:
                return False
        return True

    def format_message(self) -> str:
        lines = [f"To: {self.recipient}"]
        if self.cc:
            lines.append(f"CC: {', '.join(self.cc)}")
        if self.reply_to:
            lines.append(f"Reply-To: {self.reply_to}")
        lines.append(f"Subject: {self.subject}")
        lines.append("")
        lines.append(self.body)
        return "\n".join(lines)

    def _deliver(self, message: str) -> dict:
        return {
            "status": "sent",
            "channel": "email",
            "to": self.recipient,
            "cc": self.cc,
            "message": message,
        }


class PriorityEmailNotification(EmailNotification):
    """High-priority email with urgency markers."""

    def __init__(self, recipient: str, subject: str, body: str,
                 cc: list = None, reply_to: str = None, priority: int = 1):
        super().__init__(recipient, subject, body, cc, reply_to)
        self.priority = priority

    def format_message(self) -> str:
        base = super().format_message()
        priority_header = f"X-Priority: {self.priority}\n"
        prefix = "[URGENT] " if self.priority == 1 else "[PRIORITY] "
        # Insert priority header after To: line
        lines = base.split("\n")
        lines.insert(1, priority_header.strip())
        # Prefix subject
        for i, line in enumerate(lines):
            if line.startswith("Subject:"):
                original_subject = line[len("Subject: "):]
                lines[i] = f"Subject: {prefix}{original_subject}"
                break
        return "\n".join(lines)

    def _deliver(self, message: str) -> dict:
        result = super()._deliver(message)
        result["priority"] = self.priority
        result["channel"] = "email_priority"
        return result


class SMSNotification(BaseNotification):
    """SMS notification."""

    MAX_LENGTH = 160

    def __init__(self, recipient: str, subject: str, body: str):
        super().__init__(recipient, subject, body)

    def validate(self) -> bool:
        if not super().validate():
            return False
        # Phone number should be digits (with optional +)
        phone = self.recipient.replace("+", "").replace("-", "").replace(" ", "")
        if not phone.isdigit():
            return False
        if len(phone) < 7:
            return False
        return True

    def format_message(self) -> str:
        text = f"{self.subject}: {self.body}"
        if len(text) > self.MAX_LENGTH:
            text = text[:self.MAX_LENGTH - 3] + "..."
        return text

    def _deliver(self, message: str) -> dict:
        return {
            "status": "sent",
            "channel": "sms",
            "to": self.recipient,
            "message": message,
            "length": len(message),
        }


class InternationalSMSNotification(SMSNotification):
    """International SMS with country code handling and extended encoding."""

    MAX_LENGTH = 140  # shorter for international

    def __init__(self, recipient: str, subject: str, body: str,
                 country_code: str = "+1"):
        super().__init__(recipient, subject, body)
        self.country_code = country_code

    def validate(self) -> bool:
        if not super().validate():
            return False
        if not self.country_code.startswith("+"):
            return False
        return True

    def format_message(self) -> str:
        text = f"[INTL] {self.subject}: {self.body}"
        if len(text) > self.MAX_LENGTH:
            text = text[:self.MAX_LENGTH - 3] + "..."
        return text

    def _deliver(self, message: str) -> dict:
        result = super()._deliver(message)
        result["channel"] = "sms_international"
        result["country_code"] = self.country_code
        # Normalize phone with country code
        phone = self.recipient
        if not phone.startswith("+"):
            phone = self.country_code + phone
        result["to"] = phone
        return result


class PushNotification(BaseNotification):
    """Push notification for mobile/web."""

    def __init__(self, recipient: str, subject: str, body: str,
                 icon: str = None, action_url: str = None, badge: int = 0):
        super().__init__(recipient, subject, body)
        self.icon = icon
        self.action_url = action_url
        self.badge = badge

    def validate(self) -> bool:
        if not super().validate():
            return False
        # Recipient should be a device token (non-empty string, no spaces)
        if " " in self.recipient:
            return False
        return True

    def format_message(self) -> str:
        payload = {
            "title": self.subject,
            "body": self.body,
        }
        if self.icon:
            payload["icon"] = self.icon
        if self.action_url:
            payload["action_url"] = self.action_url
        if self.badge > 0:
            payload["badge"] = self.badge
        # Return as a simple string representation
        parts = [f"{k}={v}" for k, v in payload.items()]
        return "; ".join(parts)

    def _deliver(self, message: str) -> dict:
        return {
            "status": "sent",
            "channel": "push",
            "device_token": self.recipient,
            "message": message,
            "badge": self.badge,
        }
