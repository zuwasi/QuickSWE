# Task 013: Break God Class into Components

## Current State

`src/user_manager.py` contains a single `UserManager` class that handles **everything** related to users:

- **User CRUD** — `create_user()`, `get_user()`, `update_user()`, `delete_user()`, `list_users()`
- **Authentication** — `authenticate()`, `change_password()`
- **Password hashing** — `_hash_password()`, `_verify_password()` (simplified stub using hashlib)
- **Session management** — `create_session()`, `validate_session()`, `destroy_session()`, `cleanup_expired_sessions()`
- **Email sending** — `send_welcome_email()`, `send_password_reset_email()` (stubs that append to a log list)

The class is 200+ lines and violates the Single Responsibility Principle.

## Code Smell

- **God Class** — one class with too many responsibilities.
- Every new feature touches this one massive class.

## Requested Refactoring

Split into three focused classes, all in the same `src/user_manager.py` file:

1. **`UserRepository`** — user CRUD operations (`create_user`, `get_user`, `update_user`, `delete_user`, `list_users`). Owns the `_users` dict.
2. **`AuthService`** — authentication and password management (`authenticate`, `change_password`, `hash_password`, `verify_password`). Receives a `UserRepository` instance.
3. **`SessionManager`** — session lifecycle (`create_session`, `validate_session`, `destroy_session`, `cleanup_expired_sessions`). Owns the `_sessions` dict.

`UserManager` should still exist but **delegate** to these three components. Its public API must remain unchanged.

## Acceptance Criteria

- [ ] `UserRepository`, `AuthService`, `SessionManager` are importable from `src.user_manager`.
- [ ] Each component works independently (can be instantiated and used without `UserManager`).
- [ ] `UserManager` still exposes the same public methods with the same signatures.
- [ ] All existing behaviour is preserved.
