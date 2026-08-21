from src.entities.character import Character
from config import load_animals, load_skills, load_items


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
        self.equipped_item = None

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

    def equip_item(self, item_id):
        self.equipped_item = item_id

    def unequip_item(self):
        self.equipped_item = None

    def get_equipped_item_data(self):
        if not self.equipped_item:
            return None
        items = load_items()
        return items.get(self.equipped_item)

    def apply_item_bonuses(self):
        item_data = self.get_equipped_item_data()
        if not item_data:
            return
        effect = item_data.get("effect", "")
        value = item_data.get("value", 0)
        self._apply_stat_bonus(effect, value)
        effect2 = item_data.get("effect2")
        value2 = item_data.get("value2", 0)
        if effect2:
            self._apply_stat_bonus(effect2, value2)

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

    def apply_permanent_upgrade(self, effect, value):
        self._apply_stat_bonus(effect, value)

    def get_cooldown_with_reduction(self, skill_id):
        for s in self.skills:
            if s["id"] == skill_id:
                return max(0, s["cooldown"] - self.cooldown_reduction)
        return 0

    def to_dict(self):
        return {
            "animal_id": self.animal_id,
            "level": self.level,
            "xp": self.xp,
            "xp_to_level": self.xp_to_level,
            "unlocked": self.unlocked,
            "equipped_item": self.equipped_item
        }

    @classmethod
    def from_dict(cls, data):
        animal = cls(data["animal_id"])
        animal.level = data.get("level", 1)
        animal.xp = data.get("xp", 0)
        animal.xp_to_level = data.get("xp_to_level", 50)
        animal.unlocked = data.get("unlocked", False)
        animal.equipped_item = data.get("equipped_item", None)
        return animal
