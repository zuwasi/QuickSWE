# Bug Report: Private Tenant Users See Public Data

## Summary

In our multi-tenant application, users who are authenticated and belong to private tenants are sometimes seeing data from the public tenant. This is a serious data isolation issue.

## Steps to Reproduce

1. Set up a private tenant (e.g., "acme-corp")
2. Create a user authenticated via JWT token with `tenant_id: "acme-corp"`
3. Make a request to the API
4. Observe that the response contains data from the "public" tenant instead of "acme-corp"

## Expected Behavior

Authenticated users on private tenants should only see data from their own tenant.

## Actual Behavior

The user gets routed to the "public" tenant's data, as if the tenant resolution failed. The authentication itself works — the user IS authenticated — but the tenant context is wrong.

## Additional Context

- This seems to happen inconsistently across deployments
- The rate limiter was recently added to the middleware stack, not sure if related
- We've checked the JWT tokens and they definitely contain the correct `tenant_id`
- The rate limiter has some unusual counter logic that we haven't fully reviewed
- Public access (unauthenticated) works correctly
- The order we register middlewares might matter? We've tried different orders with mixed results

## Severity

**HIGH** — This is a data isolation violation.
