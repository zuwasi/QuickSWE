# Task 025: Replace Inheritance Hierarchy with Composition

## Current State

The notification system uses deep inheritance:

```
BaseNotification
├── EmailNotification
│   └── PriorityEmailNotification
├── SMSNotification
│   └── InternationalSMSNotification
└── PushNotification
```

`src/notifications.py` has all these classes. Each overrides `send()` with slight variations — different formatting, different delivery logic, different validation. There's a lot of duplicated setup code across them.

`src/notification_service.py` has a `NotificationService` that creates the right subclass and sends notifications. It has factory-like if/elif logic to pick the right class.

## Code Smells

- Deep inheritance for minor behavioral variations
- Duplicated setup/validation code
- Adding a new combination (e.g., priority push notification) requires a new class
- The service has to know about every subclass

## Requested Refactoring

Replace the inheritance tree with composition:

- A single `Notification` class that takes a **channel** object (email, SMS, push) for the delivery mechanism
- `Channel` base class (or protocol) with `EmailChannel`, `SMSChannel`, `PushChannel` implementations
- Behavioral modifiers like priority and internationalization should be composable — decorators, mixins, or config flags rather than subclasses
- `NotificationService` should use a builder or factory that constructs notifications from channel + modifiers

The end result: sending an email, a priority email, an international SMS — all the same `Notification` class, just different channel and modifier combinations.

## Constraints

- All existing notification outputs must remain the same (same messages, same format)
- The notification service must still be able to send all existing notification types
- Channel implementations should be independently testable

## Acceptance Criteria

- [ ] `Channel`, `EmailChannel`, `SMSChannel`, `PushChannel` importable from `src.notifications`
- [ ] `Notification(channel=EmailChannel(...))` works
- [ ] Priority and international modifiers composable without new classes
- [ ] `NotificationService.send()` still produces correct output for all types
- [ ] No deep inheritance — max 1 level of subclassing
