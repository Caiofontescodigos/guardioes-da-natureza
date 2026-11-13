"""Definicoes unicas de pocoes e crucifixos.

Este modulo nao guarda inventario: a fonte de dados continua sendo o dicionario
``save_data["potions"]`` gerenciado pelo SaveManager/Game. Aqui ficam apenas os
limites, textos e a aplicacao do efeito em um unico animal.
"""

from src.state import BuffType


POTION_KEYS = ("health", "defense", "attack", "revive")
CRUCIFIX_KEY = "revive"

POTION_LIMIT = 30
CRUCIFIX_LIMIT = 5

ITEM_LIMITS = {
    "health": POTION_LIMIT,
    "defense": POTION_LIMIT,
    "attack": POTION_LIMIT,
    "revive": CRUCIFIX_LIMIT,
}

ITEM_NAMES = {
    "health": "Pocao de Cura",
    "defense": "Pocao de Defesa",
    "attack": "Pocao de Ataque",
    "revive": "Cruz Dourada",
}

# Textos exibidos na interface. Devem corresponder exatamente ao efeito
# aplicado por ``apply_effect`` abaixo.
ITEM_EFFECTS = {
    "health": "cura 50% da vida maxima",
    "defense": "+30% DEF por 3 turnos (acumula)",
    "attack": "+30% ATK por 3 turnos (acumula)",
    "revive": "reanima 1 animal caido (50% HP)",
}

HEAL_FRACTION = 0.50
BUFF_FRACTION = 0.30

# Buffs created by potions: (BuffType, attribute used for the percentage,
# percentage, duration). Using another potion of the same type adds its
# duration to the active buff.
POTION_BUFFS = {
    "attack": (BuffType.ATTACK_UP, "base_attack", BUFF_FRACTION, 3),
    "defense": (BuffType.DEFENSE_UP, "base_defense", BUFF_FRACTION, 3),
}

EFFECT_SHORT_NAMES = {
    "attack": "ATQ",
    "defense": "DEF",
}

TARGET_REASONS = {
    "health": "Nenhum animal ferido pode receber a cura.",
    "defense": "Nenhum animal vivo pode receber a defesa.",
    "attack": "Nenhum animal vivo pode receber o ataque.",
    "revive": "Nenhum animal caido para reanimar.",
}


def get_limit(key):
    """Return the maximum stack size for an item key."""
    return ITEM_LIMITS.get(key, 0)


def clamp_count(key, value):
    """Clamp an inventory quantity to the item's allowed range."""
    try:
        count = int(value)
    except (TypeError, ValueError):
        count = 0
    return max(0, min(get_limit(key), count))


def can_target(key, animal):
    """Whether ``animal`` can receive the effect of item ``key`` right now."""
    if animal is None:
        return False

    if key == "health":
        return (bool(getattr(animal, "is_alive", True))
                and animal.hp > 0 and animal.hp < animal.max_hp)
    if key == "revive":
        return (not getattr(animal, "is_alive", True)) or animal.hp <= 0
    if key in ("defense", "attack"):
        return bool(getattr(animal, "is_alive", True)) and animal.hp > 0
    return False


def invalid_target_reason(key):
    return TARGET_REASONS.get(key, "Nenhum animal elegivel para este item.")


def get_active_potion_effects(animal):
    """Return active potion effects as ``[(key, value, turns_left), ...]``."""
    effects = []
    if animal is None:
        return effects
    for key in ("attack", "defense"):
        buff_type = POTION_BUFFS[key][0]
        for buff in getattr(animal, "buffs", []):
            if buff.effect_type == buff_type:
                effects.append((key, buff.value, buff.duration))
                break
    return effects


def get_potion_buff_value(key, animal):
    """Return the flat bonus equivalent to 30% of the animal's attribute."""
    data = POTION_BUFFS.get(key)
    if data is None or animal is None:
        return 0
    _buff_type, attribute, fraction, _duration = data
    base = getattr(animal, attribute, 0) or 0
    return max(1, int(round(base * fraction)))


def _add_potion_buff(animal, buff_type, value, duration):
    """Extend an existing potion buff instead of resetting its duration.

    The bonus value is not stacked (the potion keeps its defined strength),
    but every new use adds its full duration to the buff. Example: 3 remaining
    turns + another potion = 6 turns.
    """
    for buff in getattr(animal, "buffs", []):
        if buff.effect_type == buff_type:
            buff.value = max(buff.value, value)
            buff.duration += duration
            return
    animal.apply_buff(buff_type, value, duration)


def apply_effect(key, animal):
    """Apply the item effect to exactly one animal.

    Returns True when the effect was applied and False when the target is not
    eligible. No party-wide effect is ever performed here.
    """
    if not can_target(key, animal):
        return False

    if key == "health":
        animal.heal(max(1, int(round(animal.max_hp * HEAL_FRACTION))))
    elif key in POTION_BUFFS:
        buff_type = POTION_BUFFS[key][0]
        duration = POTION_BUFFS[key][3]
        value = get_potion_buff_value(key, animal)
        _add_potion_buff(animal, buff_type, value, duration)
    elif key == "revive":
        animal.hp = max(1, int(animal.max_hp * 0.5))
        animal.is_alive = True
    else:
        return False
    return True
