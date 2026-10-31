from enum import Enum, auto

class GameState(Enum):
    MAIN_MENU = auto()
    HOW_TO_PLAY = auto()
    ANIMAL_SELECT = auto()
    BIOME_SELECT = auto()
    MAP = auto()
    COMBAT = auto()
    EVENT = auto()
    SHOP = auto()
    CAMP = auto()
    LEVEL_UP = auto()
    RESCUE_ANIMAL = auto()
    SETTINGS = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    PAUSE = auto()
    BESTIARY = auto()
    ACAMPAMENTO = auto()
    ANIMAL_ENCOUNTER = auto()
    CAGE_REWARD = auto()
    SAVES = auto()
    SWAP_ANIMAL = auto()
    EVOLUTION = auto()
    ACHIEVEMENTS = auto()
    INVENTORY = auto()
    MUSIC_BOX = auto()

class NodeType(Enum):
    COMBAT = "combat"
    ELITE = "elite"
    EVENT = "event"
    CAMP = "camp"
    SHOP = "shop"
    BOSS = "boss"
    RESCUE_ANIMAL = "rescue_animal"

class BuffType(Enum):
    ATTACK_UP = auto()
    DEFENSE_UP = auto()
    SPEED_UP = auto()
    CRIT_UP = auto()
    DODGE_UP = auto()
    REGEN = auto()
    COUNTER_ATTACK = auto()
    REDUCE_DAMAGE = auto()
    SHIELD = auto()

class DebuffType(Enum):
    ATTACK_DOWN = auto()
    DEFENSE_DOWN = auto()
    SPEED_DOWN = auto()
    POISON = auto()
    BLEED = auto()
    SLOW = auto()
    FEAR = auto()

class SkillTarget(Enum):
    SELF = "self"
    SINGLE_ENEMY = "single_enemy"
    ALL_ENEMIES = "all_enemies"
    SINGLE_ALLY = "single_ally"
    ALL_ALLIES = "all_allies"

class SkillType(Enum):
    ATTACK = "attack"
    DEFENSE = "defense"
    HEAL = "heal"
    BUFF = "buff"
    DEBUFF = "debuff"
    SUPPORT = "support"
