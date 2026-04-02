"""Permission checking with deeply nested conditionals — the arrow anti-pattern."""


def check_access(user, resource, action):
    """Determine whether *user* may perform *action* on *resource*.

    Args:
        user: dict with keys "id", "role" (admin|editor|viewer|guest),
              "active" (bool), "department" (str).
        resource: dict with keys "id", "type" (public|internal|confidential),
                  "owner_id" (str), "department" (str).
        action: one of "read", "write", "delete".

    Returns:
        "allow"  — access granted
        "deny"   — access denied
        "error"  — bad input
    """
    result = "error"
    if user is not None and resource is not None and action is not None:
        if isinstance(user, dict) and isinstance(resource, dict):
            if user.get("active") is True:
                if user.get("role") == "admin":
                    # admins can do anything
                    result = "allow"
                else:
                    if resource.get("type") == "public":
                        if action == "read":
                            result = "allow"
                        else:
                            if user.get("role") == "editor":
                                if action == "write":
                                    result = "allow"
                                else:
                                    # editors can't delete public resources
                                    result = "deny"
                            else:
                                result = "deny"
                    else:
                        if resource.get("type") == "internal":
                            if user.get("department") == resource.get("department"):
                                if action == "read":
                                    result = "allow"
                                else:
                                    if user.get("role") == "editor":
                                        if action == "write":
                                            result = "allow"
                                        else:
                                            result = "deny"
                                    else:
                                        if str(user.get("id")) == str(resource.get("owner_id")):
                                            if action == "write":
                                                result = "allow"
                                            else:
                                                result = "deny"
                                        else:
                                            result = "deny"
                            else:
                                result = "deny"
                        else:
                            if resource.get("type") == "confidential":
                                if str(user.get("id")) == str(resource.get("owner_id")):
                                    if action in ("read", "write"):
                                        result = "allow"
                                    else:
                                        result = "deny"
                                else:
                                    if user.get("role") == "editor" and user.get("department") == resource.get("department"):
                                        if action == "read":
                                            result = "allow"
                                        else:
                                            result = "deny"
                                    else:
                                        result = "deny"
                            else:
                                result = "deny"
            else:
                result = "deny"
        else:
            result = "error"
    else:
        result = "error"
    return result
