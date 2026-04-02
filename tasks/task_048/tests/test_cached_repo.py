import sys
import os
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.model import User
from src.storage import InMemoryStorage
from src.repository import UserRepository
from src.cache import Cache


# ── pass-to-pass: UserRepository CRUD ──────────────────────────


class TestUserRepositoryCRUD:
    def _make_repo(self):
        return UserRepository(InMemoryStorage())

    def test_create_and_get(self):
        repo = self._make_repo()
        user = User(id="u1", name="Alice", email="alice@test.com")
        repo.create(user)
        found = repo.get_by_id("u1")
        assert found is not None
        assert found.name == "Alice"

    def test_get_nonexistent(self):
        repo = self._make_repo()
        assert repo.get_by_id("nope") is None

    def test_create_duplicate_raises(self):
        repo = self._make_repo()
        user = User(id="u1", name="Alice", email="alice@test.com")
        repo.create(user)
        with pytest.raises(ValueError, match="already exists"):
            repo.create(user)

    def test_update(self):
        repo = self._make_repo()
        user = User(id="u1", name="Alice", email="alice@test.com")
        repo.create(user)
        user.name = "Alice Updated"
        repo.update(user)
        found = repo.get_by_id("u1")
        assert found.name == "Alice Updated"

    def test_update_nonexistent_raises(self):
        repo = self._make_repo()
        user = User(id="u1", name="Ghost", email="ghost@test.com")
        with pytest.raises(ValueError, match="not found"):
            repo.update(user)

    def test_delete(self):
        repo = self._make_repo()
        user = User(id="u1", name="Alice", email="alice@test.com")
        repo.create(user)
        assert repo.delete("u1") is True
        assert repo.get_by_id("u1") is None

    def test_delete_nonexistent(self):
        repo = self._make_repo()
        assert repo.delete("nope") is False

    def test_get_all(self):
        repo = self._make_repo()
        repo.create(User(id="u1", name="Alice", email="a@test.com"))
        repo.create(User(id="u2", name="Bob", email="b@test.com"))
        all_users = repo.get_all()
        assert len(all_users) == 2


class TestUserModel:
    def test_to_dict_and_back(self):
        user = User(id="u1", name="Alice", email="alice@test.com")
        data = user.to_dict()
        restored = User.from_dict(data)
        assert restored.id == "u1"
        assert restored.name == "Alice"

    def test_equality(self):
        u1 = User(id="u1", name="A", email="a@a.com")
        u2 = User(id="u1", name="B", email="b@b.com")
        assert u1 == u2  # same id

    def test_inequality(self):
        u1 = User(id="u1", name="A", email="a@a.com")
        u2 = User(id="u2", name="A", email="a@a.com")
        assert u1 != u2


class TestStorageCounters:
    def test_read_counter(self):
        storage = InMemoryStorage()
        storage.put("k1", {"x": 1})
        storage.reset_counters()
        storage.get("k1")
        storage.get("k1")
        assert storage.read_count == 2

    def test_write_counter(self):
        storage = InMemoryStorage()
        storage.put("k1", {"x": 1})
        assert storage.write_count == 1


# ── fail-to-pass: Cache implementation ──────────────────────────


class TestCacheImplementation:
    @pytest.mark.fail_to_pass
    def test_cache_set_and_get(self):
        """Cache should store and retrieve values."""
        cache = Cache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    @pytest.mark.fail_to_pass
    def test_cache_get_missing(self):
        """Cache.get returns None for missing keys."""
        cache = Cache()
        assert cache.get("nonexistent") is None

    @pytest.mark.fail_to_pass
    def test_cache_delete(self):
        """Cache.delete removes the entry."""
        cache = Cache()
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None

    @pytest.mark.fail_to_pass
    def test_cache_has(self):
        """Cache.has checks existence."""
        cache = Cache()
        cache.set("key1", "value1")
        assert cache.has("key1") is True
        assert cache.has("missing") is False

    @pytest.mark.fail_to_pass
    def test_cache_clear(self):
        """Cache.clear removes all entries."""
        cache = Cache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    @pytest.mark.fail_to_pass
    def test_cache_ttl_expiration(self):
        """Entries with expired TTL should not be returned."""
        cache = Cache()
        cache.set("key1", "value1", ttl=0.1)
        assert cache.get("key1") == "value1"
        time.sleep(0.15)
        assert cache.get("key1") is None

    @pytest.mark.fail_to_pass
    def test_cache_ttl_not_expired(self):
        """Entries within TTL should still be returned."""
        cache = Cache()
        cache.set("key1", "value1", ttl=10)
        assert cache.get("key1") == "value1"

    @pytest.mark.fail_to_pass
    def test_cache_size(self):
        """Cache.size returns count of non-expired entries."""
        cache = Cache()
        cache.set("a", 1)
        cache.set("b", 2)
        assert cache.size == 2


# ── fail-to-pass: CachedRepository ──────────────────────────


class TestCachedRepository:
    @pytest.mark.fail_to_pass
    def test_cached_repo_importable(self):
        """CachedRepository should be importable from src.repository."""
        from src.repository import CachedRepository
        assert CachedRepository is not None

    @pytest.mark.fail_to_pass
    def test_cached_repo_caches_reads(self):
        """Second get_by_id should not hit storage."""
        from src.repository import CachedRepository
        storage = InMemoryStorage()
        base_repo = UserRepository(storage)
        cached_repo = CachedRepository(base_repo)
        user = User(id="u1", name="Alice", email="a@test.com")
        base_repo.create(user)
        storage.reset_counters()

        # First read: should hit storage
        result1 = cached_repo.get_by_id("u1")
        first_reads = storage.read_count

        # Second read: should come from cache
        result2 = cached_repo.get_by_id("u1")
        second_reads = storage.read_count

        assert result1.name == "Alice"
        assert result2.name == "Alice"
        assert second_reads == first_reads  # no additional storage hit

    @pytest.mark.fail_to_pass
    def test_cached_repo_invalidates_on_update(self):
        """update() should invalidate cached entry."""
        from src.repository import CachedRepository
        storage = InMemoryStorage()
        base_repo = UserRepository(storage)
        cached_repo = CachedRepository(base_repo)
        user = User(id="u1", name="Alice", email="a@test.com")
        base_repo.create(user)

        # Cache the read
        cached_repo.get_by_id("u1")

        # Update
        user.name = "Alice Updated"
        cached_repo.update(user)

        # Should fetch fresh from storage
        result = cached_repo.get_by_id("u1")
        assert result.name == "Alice Updated"

    @pytest.mark.fail_to_pass
    def test_cached_repo_invalidates_on_delete(self):
        """delete() should invalidate cached entry."""
        from src.repository import CachedRepository
        storage = InMemoryStorage()
        base_repo = UserRepository(storage)
        cached_repo = CachedRepository(base_repo)
        user = User(id="u1", name="Alice", email="a@test.com")
        base_repo.create(user)

        # Cache the read
        cached_repo.get_by_id("u1")
        # Delete
        cached_repo.delete("u1")
        # Should return None
        assert cached_repo.get_by_id("u1") is None

    @pytest.mark.fail_to_pass
    def test_cached_repo_ttl_expiration(self):
        """Cached entries should expire after TTL."""
        from src.repository import CachedRepository
        storage = InMemoryStorage()
        base_repo = UserRepository(storage)
        cached_repo = CachedRepository(base_repo, ttl=0.1)
        user = User(id="u1", name="Alice", email="a@test.com")
        base_repo.create(user)

        cached_repo.get_by_id("u1")
        storage.reset_counters()
        time.sleep(0.15)

        # Should hit storage again because cache expired
        cached_repo.get_by_id("u1")
        assert storage.read_count > 0

    @pytest.mark.fail_to_pass
    def test_cached_repo_create_delegates(self):
        """create() should delegate to base repo."""
        from src.repository import CachedRepository
        storage = InMemoryStorage()
        base_repo = UserRepository(storage)
        cached_repo = CachedRepository(base_repo)
        user = User(id="u1", name="Alice", email="a@test.com")
        cached_repo.create(user)
        assert base_repo.get_by_id("u1") is not None
