"""A minimal 2-D game engine with player movement, collision, and scoring."""


def create_player(name, x=0, y=0):
    """Create a new player dict at the given position."""
    return {
        "name": name,
        "x": x,
        "y": y,
        "health": 100,
        "score": 0,
        "speed": 4,
        "sprinting": False,
    }


def move_player(player, dx, dy):
    """Move the player by (dx, dy), clamping to screen bounds.

    When sprinting, speed is multiplied by 1.5.
    """
    speed = player["speed"]
    if player["sprinting"]:
        speed = speed * 1.5

    new_x = player["x"] + dx * speed
    new_y = player["y"] + dy * speed

    # clamp to screen boundaries
    if new_x < 0:
        new_x = 0
    elif new_x > 800 - 32:        # screen width minus tile size
        new_x = 800 - 32

    if new_y < 0:
        new_y = 0
    elif new_y > 600 - 32:        # screen height minus tile size
        new_y = 600 - 32

    player["x"] = new_x
    player["y"] = new_y
    return player


def check_collision(player, obj_x, obj_y, obj_w=32, obj_h=32):
    """Check AABB collision between the player tile and an object."""
    px, py = player["x"], player["y"]
    # player occupies a 32×32 tile
    if (px < obj_x + obj_w and
        px + 32 > obj_x and
        py < obj_y + obj_h and
        py + 32 > obj_y):
        return True
    return False


def apply_damage(player, amount):
    """Reduce player health, clamped to [0, 100]."""
    player["health"] -= amount
    if player["health"] < 0:
        player["health"] = 0
    if player["health"] > 100:
        player["health"] = 100
    return player


def heal_player(player, amount):
    """Heal the player, capping at 100."""
    player["health"] += amount
    if player["health"] > 100:
        player["health"] = 100
    return player


def calculate_score(player, enemies_defeated, coins_collected, time_bonus_seconds):
    """Calculate total score.

    Formula: enemies * 100 + coins * 50 + time_bonus * 10
    Score cannot go below 0.
    """
    base = enemies_defeated * 100 + coins_collected * 50 + time_bonus_seconds * 10
    total = player["score"] + base
    if total < 0:
        total = 0
    player["score"] = total
    return total


def get_tile_coords(pixel_x, pixel_y):
    """Convert pixel coordinates to tile coordinates."""
    return pixel_x // 32, pixel_y // 32


def is_on_screen(x, y):
    """Check if position is within the screen bounds."""
    return 0 <= x < 800 and 0 <= y < 600


def get_screen_center():
    """Return the center pixel of the screen."""
    return 800 // 2, 600 // 2


def get_grid_dimensions():
    """Return how many tiles fit on the screen (columns, rows)."""
    return 800 // 32, 600 // 32
