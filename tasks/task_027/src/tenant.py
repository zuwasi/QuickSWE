"""Tenant resolution middleware for multi-tenant applications."""

from .middleware import Middleware, Response


class Tenant:
    """Represents a tenant in the system."""

    def __init__(self, tenant_id, name, is_private=False, settings=None):
        self.tenant_id = tenant_id
        self.name = name
        self.is_private = is_private
        self.settings = settings or {}

    def __repr__(self):
        return f"Tenant(id='{self.tenant_id}', name='{self.name}', private={self.is_private})"


class TenantRegistry:
    """Registry of known tenants."""

    def __init__(self):
        self._tenants = {}
        # Always have a public tenant
        self._tenants['public'] = Tenant('public', 'Public', is_private=False)

    def register(self, tenant_id, name, is_private=False, settings=None):
        """Register a new tenant."""
        self._tenants[tenant_id] = Tenant(tenant_id, name, is_private, settings)

    def get(self, tenant_id):
        """Get a tenant by ID."""
        return self._tenants.get(tenant_id)

    def exists(self, tenant_id):
        """Check if a tenant exists."""
        return tenant_id in self._tenants

    def list_tenants(self):
        """List all tenant IDs."""
        return list(self._tenants.keys())

    def get_public_tenant(self):
        """Get the default public tenant."""
        return self._tenants['public']


class TenantMiddleware(Middleware):
    """Resolves the current tenant for each request.

    Resolution strategy:
    1. Check if authenticated user has a tenant_id -> use that
    2. Check subdomain -> resolve to tenant
    3. Default to public tenant

    BUG: This middleware accesses request.user to check the user's tenant_id,
    but if it runs BEFORE AuthMiddleware, request.user doesn't exist yet.
    The AttributeError is caught silently and falls through to the default
    "public" tenant, causing authenticated users on private tenants to
    incorrectly get routed to the public tenant's data.
    """

    def __init__(self, registry=None, name=None):
        super().__init__(name=name or "TenantMiddleware")
        self._registry = registry or TenantRegistry()
        self._resolution_count = 0
        self._fallback_count = 0

    @property
    def registry(self):
        return self._registry

    def _resolve_tenant_from_user(self, request):
        """Try to resolve tenant from authenticated user."""
        try:
            # BUG: If AuthMiddleware hasn't run yet, request.user
            # doesn't exist, causing AttributeError which is caught below
            user = request.user
            if user and user.tenant_id:
                tenant = self._registry.get(user.tenant_id)
                if tenant:
                    return tenant
        except AttributeError:
            # User not authenticated (or auth hasn't run yet)
            # Silently fall through to other resolution methods
            pass
        return None

    def _resolve_tenant_from_subdomain(self, request):
        """Try to resolve tenant from request subdomain."""
        if request.subdomain:
            tenant = self._registry.get(request.subdomain)
            if tenant:
                return tenant
        return None

    def before_request(self, request):
        """Resolve the tenant and set it on the request."""
        tenant = None

        # Strategy 1: From authenticated user
        tenant = self._resolve_tenant_from_user(request)

        # Strategy 2: From subdomain
        if tenant is None:
            tenant = self._resolve_tenant_from_subdomain(request)

        # Strategy 3: Default to public
        if tenant is None:
            tenant = self._registry.get_public_tenant()
            self._fallback_count += 1

        request.tenant = tenant
        self._resolution_count += 1

        # If tenant is private and user is not authenticated for it,
        # deny access
        if tenant.is_private:
            try:
                if not hasattr(request, 'user') or request.user is None:
                    return Response(status=403, body={'error': 'Access denied to private tenant'})
                if request.user.tenant_id != tenant.tenant_id:
                    return Response(status=403, body={'error': 'Tenant mismatch'})
            except AttributeError:
                return Response(status=403, body={'error': 'Authentication required for private tenant'})

        return None
