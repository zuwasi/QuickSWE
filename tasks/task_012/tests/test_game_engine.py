import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.game_engine import (
    create_player,
    move_player,
    check_collision,
    apply_damage,
    heal_player,
    calculate_score,
    get_tile_coords,
    is_on_screen,
    get_screen_center,
    get_grid_dimensions,
)


# ── pass-to-pass: function behaviour ────────────────────────────────

class TestCreatePlayer:
    def test_default_position(self):
        p = create_player("Alice")
        assert p["x"] == 0 and p["y"] == 0

    def test_initial_health(self):
        p = create_player("Bob")
        assert p["health"] == 100

    def test_initial_score(self):
        p = create_player("Eve")
        assert p["score"] == 0


class TestMovement:
    def test_basic_move(self):
        p = create_player("P", x=100, y=100)
        move_player(p, 1, 0)
        assert p["x"] == 104  # speed=4

    def test_clamp_left(self):
        p = create_player("P", x=2, y=100)
        move_player(p, -1, 0)
        assert p["x"] == 0

    def test_clamp_right(self):
        p = create_player("P", x=770, y=100)
        move_player(p, 1, 0)
        assert p["x"] == 768  # 800 - 32

    def test_clamp_bottom(self):
        p = create_player("P", x=100, y=570)
        move_player(p, 0, 1)
        assert p["y"] == 568  # 600 - 32

    def test_sprint_multiplier(self):
        p = create_player("P", x=100, y=100)
        p["sprinting"] = True
        move_player(p, 1, 0)
        assert p["x"] == 106  # 4 * 1.5 = 6


class TestCollision:
    def test_overlapping(self):
        p = create_player("P", x=50, y=50)
        assert check_collision(p, 60, 60) is True

    def test_no_overlap(self):
        p = create_player("P", x=0, y=0)
        assert check_collision(p, 200, 200) is False

    def test_edge_touching(self):
        p = create_player("P", x=0, y=0)
        # player occupies [0,32) — object starts at 32 → no overlap
        assert check_collision(p, 32, 0) is False


class TestHealth:
    def test_damage(self):
        p = create_player("P")
        apply_damage(p, 30)
        assert p["health"] == 70

    def test_damage_floor(self):
        p = create_player("P")
        apply_damage(p, 999)
        assert p["health"] == 0

    def test_heal(self):
        p = create_player("P")
        apply_damage(p, 50)
        heal_player(p, 20)
        assert p["health"] == 70

    def test_heal_cap(self):
        p = create_player("P")
        heal_player(p, 999)
        assert p["health"] == 100


class TestScore:
    def test_basic_score(self):
        p = create_player("P")
        s = calculate_score(p, enemies_defeated=3, coins_collected=2, time_bonus_seconds=5)
        # 3*100 + 2*50 + 5*10 = 450
        assert s == 450

    def test_score_accumulates(self):
        p = create_player("P")
        calculate_score(p, 1, 0, 0)
        s = calculate_score(p, 1, 0, 0)
        assert s == 200


class TestTileHelpers:
    def test_tile_coords(self):
        assert get_tile_coords(64, 96) == (2, 3)

    def test_on_screen(self):
        assert is_on_screen(400, 300) is True
        assert is_on_screen(800, 300) is False

    def test_screen_center(self):
        assert get_screen_center() == (400, 300)

    def test_grid_dimensions(self):
        assert get_grid_dimensions() == (25, 18)


# ── fail-to-pass: named constants must exist ────────────────────────

class TestNamedConstants:
    @pytest.mark.fail_to_pass
    def test_screen_width_constant(self):
        import src.game_engine as ge
        assert hasattr(ge, "SCREEN_WIDTH")
        assert ge.SCREEN_WIDTH == 800

    @pytest.mark.fail_to_pass
    def test_screen_height_constant(self):
        import src.game_engine as ge
        assert hasattr(ge, "SCREEN_HEIGHT")
        assert ge.SCREEN_HEIGHT == 600

    @pytest.mark.fail_to_pass
    def test_tile_size_constant(self):
        import src.game_engine as ge
        assert hasattr(ge, "TILE_SIZE")
        assert ge.TILE_SIZE == 32

    @pytest.mark.fail_to_pass
    def test_max_health_constant(self):
        import src.game_engine as ge
        assert hasattr(ge, "MAX_HEALTH")
        assert ge.MAX_HEALTH == 100

    @pytest.mark.fail_to_pass
    def test_speed_multiplier_constant(self):
        import src.game_engine as ge
        assert hasattr(ge, "SPEED_MULTIPLIER")
        assert ge.SPEED_MULTIPLIER == 1.5
