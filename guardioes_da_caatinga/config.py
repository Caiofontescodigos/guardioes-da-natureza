import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(os.path.dirname(BASE_DIR), "Imagensjogo")
MUSIC_DIR = os.path.join(os.path.dirname(BASE_DIR))

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (200, 200, 200)
RED = (220, 50, 50)
GREEN = (50, 180, 50)
BLUE = (50, 100, 220)
YELLOW = (220, 200, 50)
ORANGE = (220, 130, 50)
PURPLE = (150, 50, 200)
BROWN = (139, 90, 43)
CREAM = (255, 248, 230)
DARK_BROWN = (80, 50, 20)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)

GAME_TITLE = "Guardiões da Caatinga"

BIOME_COLORS = {
    "caatinga": (139, 119, 42),
    "cerrado": (180, 140, 60),
    "pantanal": (50, 120, 80),
    "mata_atlantica": (30, 100, 50),
    "amazonia": (20, 80, 30)
}

NODE_COLORS = {
    "combat": (200, 80, 80),
    "elite": (220, 150, 30),
    "event": (100, 180, 220),
    "camp": (80, 180, 80),
    "shop": (180, 130, 200),
    "boss": (200, 50, 50),
    "rescue_animal": (100, 200, 160)
}

def load_json(filename):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filename, data):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_animals():
    return load_json("animals.json")["animals"]

def load_enemies():
    return load_json("enemies.json")["enemies"]

def load_skills():
    return load_json("skills.json")["skills"]

def load_relics():
    return load_json("relics.json")["relics"]

def load_events():
    return load_json("events.json")["events"]

def load_biomes():
    return load_json("biomes.json")["biomes"]

def load_upgrades():
    return load_json("upgrades.json")["upgrades"]

def load_items():
    return load_json("items.json")["items"]
