"""Tests for multi-tenant middleware stack."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.middleware import MiddlewareStack, Request, Response
from src.auth import AuthMiddleware
from src.tenant import TenantMiddleware, TenantRegistry
from src.rate_limiter import RateLimitMiddleware
from src.router import Router


def _make_tenant_registry():
    """Create a registry with a private tenant."""
    registry = TenantRegistry()
    registry.register('acme-corp', 'Acme Corporation', is_private=True)
    registry.register('beta-inc', 'Beta Inc', is_private=True)
    return registry


@pytest.mark.fail_to_pass
class TestTenantResolutionWithAuth:
    """Tests that verify tenant resolution works correctly for authenticated users.

    These tests FAIL because TenantMiddleware is added before AuthMiddleware
    in the stack, so it tries to access request.user before auth sets it.
    The fix: MiddlewareStack should support priority ordering, OR the
    TenantMiddleware should be added AFTER AuthMiddleware, OR the
    MiddlewareStack.add() should accept a priority parameter.
    """

    def test_authenticated_user_gets_correct_private_tenant(self):
        """An authenticated user should be routed to their own tenant."""
        registry = _make_tenant_registry()
        stack = MiddlewareStack()

        # This is the typical setup order — tenant before auth
        # because tenant "logically" should resolve first, but auth
        # needs to run first to set request.user
        tenant_mw = TenantMiddleware(registry=registry)
        auth_mw = AuthMiddleware(secret='test-secret')

        stack.add(tenant_mw)
        stack.add(auth_mw)

        # Create an authenticated request
        token = auth_mw.create_token(
            user_id='user-1',
            username='john',
            tenant_id='acme-corp',
            roles=['member']
        )
        request = Request(
            path='/api/data',
            headers={'Authorization': f'Bearer {token}'}
        )

        def handler(req):
            return Response(
                status=200,
                body={
                    'tenant': req.tenant.tenant_id,
                    'tenant_name': req.tenant.name,
                    'user': req.user.username if hasattr(req, 'user') else None
                }
            )

        response = stack.process_request(request, handler)

        assert response.status == 200, f"Expected 200, got {response.status}: {response.body}"
        assert response.body['tenant'] == 'acme-corp', (
            f"Expected tenant 'acme-corp', got '{response.body['tenant']}'. "
            f"User was routed to wrong tenant!"
        )
        assert response.body['user'] == 'john'

    def test_authenticated_user_not_routed_to_public(self):
        """An authenticated private-tenant user should NOT see public tenant data."""
        registry = _make_tenant_registry()
        stack = MiddlewareStack()

        tenant_mw = TenantMiddleware(registry=registry)
        auth_mw = AuthMiddleware(secret='test-secret')
        rate_mw = RateLimitMiddleware(max_requests=1000)

        # Add in "natural" order: tenant, rate limiter, auth
        stack.add(tenant_mw)
        stack.add(rate_mw)
        stack.add(auth_mw)

        token = auth_mw.create_token(
            user_id='user-2',
            username='jane',
            tenant_id='beta-inc',
            roles=['admin']
        )
        request = Request(
            path='/api/dashboard',
            headers={
                'Authorization': f'Bearer {token}',
                'X-Real-IP': '192.168.1.100'
            }
        )

        def handler(req):
            return Response(
                status=200,
                body={'tenant': req.tenant.tenant_id}
            )

        response = stack.process_request(request, handler)

        assert response.status == 200, f"Expected 200, got {response.status}: {response.body}"
        assert response.body['tenant'] != 'public', (
            f"Authenticated user was incorrectly routed to public tenant! "
            f"This is a data isolation violation."
        )
        assert response.body['tenant'] == 'beta-inc'


class TestPublicAccessWorks:
    """Tests that verify public (unauthenticated) access works.
    These should always pass.
    """

    def test_unauthenticated_gets_public_tenant(self):
        registry = _make_tenant_registry()
        stack = MiddlewareStack()

        auth_mw = AuthMiddleware(secret='test-secret', required=False)
        tenant_mw = TenantMiddleware(registry=registry)

        stack.add(auth_mw)
        stack.add(tenant_mw)

        request = Request(path='/api/public-data')

        def handler(req):
            return Response(status=200, body={'tenant': req.tenant.tenant_id})

        response = stack.process_request(request, handler)
        assert response.status == 200
        assert response.body['tenant'] == 'public'

    def test_subdomain_based_tenant_resolution(self):
        registry = _make_tenant_registry()
        tenant_mw = TenantMiddleware(registry=registry)
        stack = MiddlewareStack()
        stack.add(tenant_mw)

        request = Request(
            path='/api/data',
            subdomain='acme-corp'
        )

        def handler(req):
            return Response(status=200, body={'tenant': req.tenant.tenant_id})

        response = stack.process_request(request, handler)
        assert response.status != 200  # Should be 403 because private + no auth


class TestRateLimiterWorks:
    """Tests that verify the rate limiter works correctly.
    These should always pass — the rate limiter is NOT the bug.
    """

    def test_rate_limiter_allows_requests_within_limit(self):
        stack = MiddlewareStack()
        rate_mw = RateLimitMiddleware(max_requests=5, window_size=60)
        stack.add(rate_mw)

        for i in range(5):
            request = Request(
                path='/api/test',
                headers={'X-Real-IP': '10.0.0.1'}
            )
            response = stack.process_request(
                request,
                lambda req: Response(status=200, body={'ok': True})
            )
            assert response.status == 200, f"Request {i+1} was blocked unexpectedly"

    def test_rate_limiter_blocks_excess_requests(self):
        stack = MiddlewareStack()
        rate_mw = RateLimitMiddleware(max_requests=3, window_size=60)
        stack.add(rate_mw)

        responses = []
        for i in range(5):
            request = Request(
                path='/api/test',
                headers={'X-Real-IP': '10.0.0.2'}
            )
            response = stack.process_request(
                request,
                lambda req: Response(status=200)
            )
            responses.append(response.status)

        assert 429 in responses, "Rate limiter should have blocked some requests"

    def test_rate_limiter_per_client(self):
        stack = MiddlewareStack()
        rate_mw = RateLimitMiddleware(max_requests=2, window_size=60)
        stack.add(rate_mw)

        # Client A makes 2 requests
        for _ in range(2):
            req = Request(path='/api/test', headers={'X-Real-IP': '10.0.0.1'})
            resp = stack.process_request(req, lambda r: Response(status=200))
            assert resp.status == 200

        # Client B should still be able to make requests
        req = Request(path='/api/test', headers={'X-Real-IP': '10.0.0.99'})
        resp = stack.process_request(req, lambda r: Response(status=200))
        assert resp.status == 200


class TestRouterWorks:
    """Tests for the router itself — should always pass."""

    def test_basic_routing(self):
        router = Router()
        router.get('/api/hello', lambda req: Response(status=200, body='hello'))

        request = Request(path='/api/hello', method='GET')
        response = router.dispatch(request)
        assert response.status == 200

    def test_route_not_found(self):
        router = Router()
        request = Request(path='/nonexistent', method='GET')
        response = router.dispatch(request)
        assert response.status == 404
