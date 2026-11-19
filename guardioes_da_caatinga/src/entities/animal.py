from src.entities.character import Character
from config import load_animals, load_skills

EVOLUTION_LEVELS = {1: 6}
EVOLUTION_STAGE_NAMES = ["Base", "Evolucao 1"]


def get_evolution_stage_for_level(level):
    if level >= EVOLUTION_LEVELS[1]:
        return 1
    return 0


EVOLUTION_1_BONUS = {
    "permanent_max_hp": 15,
    "permanent_attack": 4,
    "permanent_defense": 4,
    "permanent_speed": 2,
}


SPECIFIC_UPGRADES = {
    "tatu_bola": {
        "id": "carapaca_reforcada",
        "name": "Carapaca Reforcada",
        "icon": "\U0001f6e1\ufe0f",
        "description": "A carapaça do tatu-bola tornou-se ainda mais resistente, "
                       "reduzindo o dano recebido em combate.",
        "bonuses": {
            "permanent_defense": 5,
            "damage_reduction": 3,
        },
    },
    "lobo_guara": {
        "id": "passos_velozes",
        "name": "Passos Velozes",
        "icon": "\U0001f4a8",
        "description": "Movimentos rapidos e precisos que aumentam a velocidade "
                       "e a capacidade de critico.",
        "bonuses": {
            "permanent_speed": 4,
            "permanent_crit": 8,
        },
    },
    "arara_azul": {
        "id": "ataque_preciso",
        "name": "Ataque Preciso",
        "icon": "\U0001fabd",
        "description": "Penas afiadas como laminas, aumentando o poder ofensivo "
                       "e o dano critico.",
        "bonuses": {
            "permanent_attack": 6,
            "crit_damage_boost": 20,
        },
    },
    "tamandua_bandeira": {
        "id": "defesa_natural",
        "name": "Defesa Natural",
        "icon": "\U0001f6e1\ufe0f",
        "description": "Pelagem espessa como armadura natural, aumentando "
                       "defesa e vida maxima.",
        "bonuses": {
            "permanent_defense": 5,
            "permanent_max_hp": 15,
        },
    },
    "capivara": {
        "id": "vitalidade",
        "name": "Vitalidade",
        "icon": "\u2764\ufe0f",
        "description": "Vigor renovado com vida maxima elevada e "
                       "regeneracao natural.",
        "bonuses": {
            "permanent_max_hp": 18,
            "regen_per_turn": 3,
        },
    },
    "onca_pintada": {
        "id": "instinto_predador",
        "name": "Instinto Predador",
        "icon": "\U0001f406",
        "description": "Instinto de caça apurado, com dano critico devastador "
                       "e golpes fatais.",
        "bonuses": {
            "permanent_attack": 6,
            "crit_damage_boost": 25,
            "execute_bonus": 3,
        },
    },
    "harpia": {
        "id": "asas_tempestuosas",
        "name": "Asas Tempestuosas",
        "icon": "\U0001f985",
        "description": "As asas da harpia cortam o ar como lâminas, "
                       "aumentando velocidade e precisão dos golpes críticos.",
        "bonuses": {
            "permanent_speed": 5,
            "permanent_crit": 8,
            "crit_damage_boost": 20,
        },
    },
    "pirarucu": {
        "id": "couraca_do_rio",
        "name": "Couraça do Rio",
        "icon": "\U0001f41f",
        "description": "Escamas ancestrais formam uma couraça viva, "
                       "aumentando vida, defesa e resistência ao dano.",
        "bonuses": {
            "permanent_max_hp": 25,
            "permanent_defense": 6,
            "damage_reduction": 4,
        },
    },
    "onca_do_pantanal": {
        "id": "predador_do_pantano",
        "name": "Predador do Pântano",
        "icon": "\U0001f406",
        "description": "O instinto da onça lendária transforma cada bote "
                       "em uma sentença de morte.",
        "bonuses": {
            "permanent_attack": 8,
            "crit_damage_boost": 25,
            "execute_bonus": 4,
        },
    },
}


class Animal(Character):
    def __init__(self, animal_id):
        data = load_animals()[animal_id]
        skill_data = load_skills()
        skills = [skill_data[sid] for sid in data["skills"] if sid in skill_data]
        super().__init__(data["name"], data["base_stats"], skills)
        self.animal_id = animal_id
        self.role = data["role"]
        self.description = data["description"]
        self.skill_ids = data["skills"]
        self.unlocked = False
        self.regen_per_turn = 0
        self.damage_reduction = 0
        self.execute_bonus = 0
        self.crit_damage_boost = 0
        self.cooldown_reduction = 0
        self.evolution_stage = 0
        self.specific_upgrade_id = None

    def get_skill_data(self, skill_index):
        if 0 <= skill_index < len(self.skills):
            return self.skills[skill_index]
        return None

    def level_up_stats(self):
        lvl = self.level
        cycle = (lvl - 1) % 4
        if cycle == 0:
            self.max_hp += 3
            self.hp = min(self.hp + 3, self.max_hp)
            self.base_defense += 1
            self.base_speed += 1
        elif cycle == 1:
            self.max_hp += 2
            self.hp = min(self.hp + 2, self.max_hp)
            self.base_attack += 1
            self.base_speed += 1
        elif cycle == 2:
            self.base_attack += 2
            self.base_speed += 1
        elif cycle == 3:
            self.max_hp += 5
            self.hp = min(self.hp + 5, self.max_hp)
            self.base_defense += 2
            self.base_speed += 1

        if self.role == "Tanque":
            self.base_defense += 1
            self.max_hp += 2
            self.hp = min(self.hp + 2, self.max_hp)
        elif self.role == "Assassino":
            self.base_attack += 1
            self.base_speed += 1
        elif self.role == "Ataque a Distancia":
            self.base_attack += 1
            self.base_crit_chance += 1
        elif self.role == "Controle":
            self.base_defense += 1
            self.base_attack += 1
        elif self.role == "Suporte":
            self.max_hp += 3
            self.hp = min(self.hp + 3, self.max_hp)
            self.base_defense += 1
        elif self.role == "DPS":
            self.base_attack += 2
            self.base_crit_chance += 1

    def get_form_name(self):
        index = min(self.evolution_stage, len(EVOLUTION_STAGE_NAMES) - 1)
        return EVOLUTION_STAGE_NAMES[index]

    def check_evolution(self):
        target = get_evolution_stage_for_level(self.level)
        reached = []
        while self.evolution_stage < target:
            self.evolution_stage += 1
            self._apply_evolution_bonus(self.evolution_stage)
            self._apply_specific_upgrade()
            reached.append(self.evolution_stage)
        if reached:
            self.hp = self.max_hp
            self.is_alive = True
        return reached

    def _apply_evolution_bonus(self, stage):
        if stage == 1:
            for effect, value in EVOLUTION_1_BONUS.items():
                self._apply_stat_bonus(effect, value)

    def _apply_specific_upgrade(self):
        upgrade = SPECIFIC_UPGRADES.get(self.animal_id)
        if not upgrade:
            return
        if self.specific_upgrade_id:
            return
        self.specific_upgrade_id = upgrade["id"]
        for effect, value in upgrade["bonuses"].items():
            self._apply_stat_bonus(effect, value)

    def _apply_stat_bonus(self, effect, value):
        if effect == "permanent_attack":
            self.base_attack += value
        elif effect == "permanent_defense":
            self.base_defense += value
        elif effect == "permanent_speed":
            self.base_speed += value
        elif effect == "permanent_crit":
            self.base_crit_chance += value
        elif effect == "permanent_dodge":
            self.base_dodge += value
        elif effect == "permanent_max_hp":
            self.max_hp += value
            self.hp += value
        elif effect == "regen_per_turn":
            self.regen_per_turn += value
        elif effect == "damage_reduction":
            self.damage_reduction += value
        elif effect == "execute_bonus":
            self.execute_bonus += value
        elif effect == "crit_damage_boost":
            self.crit_damage_boost += value
        elif effect == "cooldown_reduction":
            self.cooldown_reduction += value

    def apply_permanent_upgrade(self, effect, value):
        self._apply_stat_bonus(effect, value)

    def get_cooldown_with_reduction(self, skill_id):
        for s in self.skills:
            if s["id"] == skill_id:
                return max(0, s["cooldown"] - self.cooldown_reduction)
        return 0

    def get_specific_upgrade_data(self):
        if not self.specific_upgrade_id:
            return None
        for upgrade in SPECIFIC_UPGRADES.values():
            if upgrade["id"] == self.specific_upgrade_id:
                return upgrade
        return None

    def to_dict(self):
        return {
            "animal_id": self.animal_id,
            "level": self.level,
            "xp": self.xp,
            "xp_to_level": self.xp_to_level,
            "unlocked": self.unlocked,
            "evolution_stage": self.evolution_stage,
            "specific_upgrade_id": self.specific_upgrade_id,
        }

    @classmethod
    def from_dict(cls, data):
        animal = cls(data["animal_id"])
        animal.level = data.get("level", 1)
        animal.xp = data.get("xp", 0)
        animal.xp_to_level = data.get("xp_to_level", 50)
        animal.unlocked = data.get("unlocked", False)
        animal.evolution_stage = data.get("evolution_stage", 0)
        animal.specific_upgrade_id = data.get("specific_upgrade_id")
        return animal


STAT_BONUS_KEYS = {
    "permanent_attack": "base_attack",
    "permanent_defense": "base_defense",
    "permanent_speed": "base_speed",
    "permanent_crit": "base_crit_chance",
    "permanent_dodge": "base_dodge",
    "permanent_max_hp": "max_hp",
    "regen_per_turn": "regen_per_turn",
    "damage_reduction": "damage_reduction",
    "execute_bonus": "execute_bonus",
    "crit_damage_boost": "crit_damage_boost",
    "cooldown_reduction": "cooldown_reduction",
}

STAT_BONUS_DEFAULTS = {
    "base_attack": 10,
    "base_defense": 10,
    "base_speed": 10,
    "base_crit_chance": 5,
    "base_dodge": 5,
    "max_hp": 50,
    "regen_per_turn": 0,
    "damage_reduction": 0,
    "execute_bonus": 0,
    "crit_damage_boost": 0,
    "cooldown_reduction": 0,
}


def apply_stat_bonus_to_dict(entry, effect, value):
    key = STAT_BONUS_KEYS.get(effect)
    if key is None:
        return
    entry[key] = entry.get(key, STAT_BONUS_DEFAULTS.get(key, 0)) + value
    if effect == "permanent_max_hp" and entry.get("hp", 0) > 0:
        entry["hp"] = entry["hp"] + value


def apply_evolution_1_to_dict(entry):
    for effect, value in EVOLUTION_1_BONUS.items():
        apply_stat_bonus_to_dict(entry, effect, value)


def apply_specific_upgrade_to_dict(animal_id, entry):
    upgrade = SPECIFIC_UPGRADES.get(animal_id)
    if not upgrade:
        return
    entry["specific_upgrade_id"] = upgrade["id"]
    for effect, value in upgrade["bonuses"].items():
        apply_stat_bonus_to_dict(entry, effect, value)


EVOLUTION_1_STAT_LABELS = {
    "permanent_max_hp": "HP",
    "permanent_attack": "ATK",
    "permanent_defense": "DEF",
    "permanent_speed": "SPD",
    "permanent_crit": "Crit",
    "permanent_dodge": "Esquiva",
    "regen_per_turn": "Regen/turno",
    "damage_reduction": "Res. dano",
    "execute_bonus": "Execucao",
    "crit_damage_boost": "Dano critico",
    "cooldown_reduction": "Recarga",
}


def get_evolution_1_details(animal_id):
    """Return the stat deltas and specific upgrade granted by evolution 1."""
    deltas = {}
    for effect, value in EVOLUTION_1_BONUS.items():
        deltas[effect] = deltas.get(effect, 0) + value
    upgrade = SPECIFIC_UPGRADES.get(animal_id)
    if upgrade:
        for effect, value in upgrade["bonuses"].items():
            deltas[effect] = deltas.get(effect, 0) + value
    return {"deltas": deltas, "upgrade": upgrade}