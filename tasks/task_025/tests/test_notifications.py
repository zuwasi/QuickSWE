import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.notification_service import NotificationService


# ── pass-to-pass: existing notification behaviour ────────────────────

class TestEmailNotification:
    def test_send_basic_email(self):
        service = NotificationService()
        result = service.send_email("alice@example.com", "Hello", "Hi Alice!")
        assert result["status"] == "sent"
        assert result["channel"] == "email"
        assert result["to"] == "alice@example.com"

    def test_email_with_cc(self):
        service = NotificationService()
        result = service.send_email(
            "alice@example.com", "Hello", "Hi!",
            cc=["bob@example.com"]
        )
        assert result["status"] == "sent"
        assert "CC: bob@example.com" in result["message"]

    def test_email_with_reply_to(self):
        service = NotificationService()
        result = service.send_email(
            "alice@example.com", "Hello", "Hi!",
            reply_to="noreply@example.com"
        )
        assert "Reply-To: noreply@example.com" in result["message"]

    def test_email_validation_no_at(self):
        service = NotificationService()
        result = service.send_email("invalid", "Subject", "Body")
        assert result["status"] == "error"

    def test_email_empty_fields(self):
        service = NotificationService()
        result = service.send_email("a@b.com", "", "body")
        assert result["status"] == "error"


class TestPriorityEmail:
    def test_priority_email_has_urgent_prefix(self):
        service = NotificationService()
        result = service.send_priority_email(
            "alice@example.com", "Alert", "System down!", priority=1
        )
        assert result["status"] == "sent"
        assert result["channel"] == "email_priority"
        assert result["priority"] == 1
        assert "[URGENT]" in result["message"]

    def test_priority_email_non_urgent(self):
        service = NotificationService()
        result = service.send_priority_email(
            "alice@example.com", "FYI", "Check this.", priority=2
        )
        assert "[PRIORITY]" in result["message"]
        assert "[URGENT]" not in result["message"]


class TestSMSNotification:
    def test_send_sms(self):
        service = NotificationService()
        result = service.send_sms("+1234567890", "Alert", "Server is down")
        assert result["status"] == "sent"
        assert result["channel"] == "sms"
        assert "Alert: Server is down" in result["message"]

    def test_sms_truncation(self):
        service = NotificationService()
        long_body = "A" * 200
        result = service.send_sms("+1234567890", "X", long_body)
        assert len(result["message"]) <= 160

    def test_sms_invalid_phone(self):
        service = NotificationService()
        result = service.send_sms("not-a-phone", "Hello", "World")
        assert result["status"] == "error"


class TestInternationalSMS:
    def test_intl_sms_format(self):
        service = NotificationService()
        result = service.send_international_sms(
            "5551234567", "Alert", "Test", country_code="+44"
        )
        assert result["status"] == "sent"
        assert result["channel"] == "sms_international"
        assert result["country_code"] == "+44"
        assert "[INTL]" in result["message"]

    def test_intl_sms_phone_normalization(self):
        service = NotificationService()
        result = service.send_international_sms(
            "5551234567", "Hi", "Test", country_code="+1"
        )
        assert result["to"] == "+15551234567"

    def test_intl_sms_shorter_limit(self):
        service = NotificationService()
        long_body = "B" * 200
        result = service.send_international_sms("+1234567890", "X", long_body)
        assert len(result["message"]) <= 140


class TestPushNotification:
    def test_send_push(self):
        service = NotificationService()
        result = service.send_push("device_abc123", "New Message", "You have mail")
        assert result["status"] == "sent"
        assert result["channel"] == "push"
        assert result["device_token"] == "device_abc123"

    def test_push_with_badge(self):
        service = NotificationService()
        result = service.send_push("dev123", "Alert", "Check app", badge=3)
        assert result["badge"] == 3
        assert "badge=3" in result["message"]

    def test_push_with_icon_and_action(self):
        service = NotificationService()
        result = service.send_push(
            "dev123", "Alert", "Check",
            icon="alert.png", action_url="https://example.com"
        )
        assert "icon=alert.png" in result["message"]
        assert "action_url=https://example.com" in result["message"]

    def test_push_invalid_token(self):
        service = NotificationService()
        result = service.send_push("has space", "Hi", "Body")
        assert result["status"] == "error"


class TestServiceHistory:
    def test_history_accumulates(self):
        service = NotificationService()
        service.send_email("a@b.com", "S1", "B1")
        service.send_sms("+1234567890", "S2", "B2")
        assert len(service.history) == 2

    def test_clear_history(self):
        service = NotificationService()
        service.send_email("a@b.com", "S", "B")
        service.clear_history()
        assert len(service.history) == 0


# ── fail-to-pass: composition-based architecture ─────────────────────

class TestChannelImports:
    @pytest.mark.fail_to_pass
    def test_channel_base_importable(self):
        from src.notifications import Channel
        assert Channel is not None

    @pytest.mark.fail_to_pass
    def test_email_channel_importable(self):
        from src.notifications import EmailChannel
        assert EmailChannel is not None

    @pytest.mark.fail_to_pass
    def test_sms_channel_importable(self):
        from src.notifications import SMSChannel
        assert SMSChannel is not None

    @pytest.mark.fail_to_pass
    def test_push_channel_importable(self):
        from src.notifications import PushChannel
        assert PushChannel is not None


class TestComposedNotification:
    @pytest.mark.fail_to_pass
    def test_notification_with_email_channel(self):
        from src.notifications import Notification, EmailChannel

        channel = EmailChannel()
        notif = Notification(
            channel=channel,
            recipient="alice@example.com",
            subject="Hello",
            body="Hi Alice!"
        )
        result = notif.send()
        assert result["status"] == "sent"
        assert result["channel"] == "email"
        assert result["to"] == "alice@example.com"

    @pytest.mark.fail_to_pass
    def test_notification_with_sms_channel(self):
        from src.notifications import Notification, SMSChannel

        channel = SMSChannel()
        notif = Notification(
            channel=channel,
            recipient="+1234567890",
            subject="Alert",
            body="Server is down"
        )
        result = notif.send()
        assert result["status"] == "sent"
        assert result["channel"] == "sms"
        assert "Alert: Server is down" in result["message"]

    @pytest.mark.fail_to_pass
    def test_notification_with_push_channel(self):
        from src.notifications import Notification, PushChannel

        channel = PushChannel()
        notif = Notification(
            channel=channel,
            recipient="device_abc123",
            subject="New Message",
            body="You have mail"
        )
        result = notif.send()
        assert result["status"] == "sent"
        assert result["channel"] == "push"


class TestModifiers:
    @pytest.mark.fail_to_pass
    def test_priority_modifier_on_email(self):
        """Priority should be composable without a new subclass."""
        from src.notifications import Notification, EmailChannel

        channel = EmailChannel()
        notif = Notification(
            channel=channel,
            recipient="alice@example.com",
            subject="Alert",
            body="System down!",
            modifiers={"priority": 1}
        )
        result = notif.send()
        assert result["status"] == "sent"
        assert "[URGENT]" in result["message"]

    @pytest.mark.fail_to_pass
    def test_international_modifier_on_sms(self):
        """International flag should be composable without a new subclass."""
        from src.notifications import Notification, SMSChannel

        channel = SMSChannel()
        notif = Notification(
            channel=channel,
            recipient="5551234567",
            subject="Alert",
            body="Test",
            modifiers={"international": True, "country_code": "+44"}
        )
        result = notif.send()
        assert result["status"] == "sent"
        assert "[INTL]" in result["message"]
        assert result["country_code"] == "+44"

    @pytest.mark.fail_to_pass
    def test_badge_modifier_on_push(self):
        from src.notifications import Notification, PushChannel

        channel = PushChannel()
        notif = Notification(
            channel=channel,
            recipient="dev123",
            subject="Alert",
            body="Check app",
            modifiers={"badge": 5, "icon": "alert.png"}
        )
        result = notif.send()
        assert result["status"] == "sent"
        assert result["badge"] == 5
        assert "icon=alert.png" in result["message"]


class TestServiceWithComposition:
    """These tests verify the service still works after refactoring to composition."""

    def test_service_send_email_still_works(self):
        """NotificationService must still produce the same outputs."""
        service = NotificationService()
        result = service.send_email("alice@example.com", "Hi", "Hello!")
        assert result["status"] == "sent"
        assert result["channel"] == "email"
        assert result["to"] == "alice@example.com"

    def test_service_send_priority_email_still_works(self):
        service = NotificationService()
        result = service.send_priority_email(
            "bob@example.com", "Urgent", "Fix now!", priority=1
        )
        assert result["status"] == "sent"
        assert "[URGENT]" in result["message"]
        assert result["priority"] == 1

    def test_service_send_intl_sms_still_works(self):
        service = NotificationService()
        result = service.send_international_sms(
            "5551234567", "Alert", "Test", country_code="+44"
        )
        assert result["status"] == "sent"
        assert result["country_code"] == "+44"
        assert "[INTL]" in result["message"]
