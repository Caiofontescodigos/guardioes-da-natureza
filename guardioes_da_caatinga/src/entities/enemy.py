from src.entities.character import Character
from config import load_enemies, load_skills
import random

class Enemy(Character):
    def __init__(self, enemy_id, level=1):
        data = load_enemies()[enemy_id]
        skill_data = load_skills()

        scaled_stats = self._scale_stats(data["stats"], level)
        skills = [skill_data[sid] for sid in data["skills"] if sid in skill_data]

        super().__init__(data["name"], scaled_stats, skills)
        self.enemy_id = enemy_id
        self.description = data["description"]
        self.skill_ids = data["skills"]
        self.xp_reward = data.get("xp_reward", 10) + (level - 1) * 3
        self.gold_reward = data.get("gold_reward", 5) + (level - 1) * 2
        self.is_elite = data.get("is_elite", False)
        self.is_boss = data.get("is_boss", False)
        self.is_enemy = True
        self.level = level

    def _scale_stats(self, base_stats, level):
        multiplier = 1 + (level - 1) * 0.15
        return {
            "hp": int(base_stats["hp"] * multiplier),
            "attack": int(base_stats["attack"] * multiplier),
            "defense": int(base_stats["defense"] * multiplier),
            "speed": int(base_stats["speed"] * (1 + (level - 1) * 0.03)),
            "crit_chance": min(40, int(base_stats["crit_chance"] * (1 + (level - 1) * 0.02))),
            "dodge": 0
        }

    def apply_elite_multipliers(self):
        from config import (ELITE_HP_MULTIPLIER, ELITE_ATK_MULTIPLIER,
                           ELITE_DEF_MULTIPLIER, ELITE_SPD_MULTIPLIER,
                           ELITE_XP_MULTIPLIER, ELITE_GOLD_MULTIPLIER)
        self.max_hp = int(self.max_hp * ELITE_HP_MULTIPLIER)
        self.hp = self.max_hp
        self.base_attack = int(self.base_attack * ELITE_ATK_MULTIPLIER)
        self.base_defense = int(self.base_defense * ELITE_DEF_MULTIPLIER)
        self.base_speed = int(self.base_speed * ELITE_SPD_MULTIPLIER)
        self.xp_reward = int(self.xp_reward * ELITE_XP_MULTIPLIER)
        self.gold_reward = int(self.gold_reward * ELITE_GOLD_MULTIPLIER)
        self.is_elite = True

    def choose_action(self, allies, enemies):
        alive_allies = [e for e in enemies if e.is_alive and e != self]
        if self.is_elite and alive_allies and random.random() < 0.3:
            for skill in self.skills:
                if skill.get("effect") in ["attack_boost", "defense_boost", "power_up"]:
                    if self.is_skill_ready(skill["id"]):
                        return {"type": "buff", "skill": skill, "targets": enemies}
            return None

        alive_targets = [a for a in allies if a.is_alive]
        if not alive_targets:
            return None

        target = random.choice(alive_targets)

        for skill in self.skills:
            if self.is_skill_ready(skill["id"]):
                return {"type": "attack", "skill": skill, "target": target}

        return {"type": "attack", "skill": {"id": "basic_attack", "name": "Ataque Basico", "damage": self.attack, "target": "single_enemy", "type": "attack", "effect": "none"}, "target": target}

def create_enemy(enemy_id, level=1):
    return Enemy(enemy_id, level)

def create_random_enemy(enemy_types, level=1, weights=None):
    if weights:
        types_with_weights = [(t, weights.get(t, 1)) for t in enemy_types]
        enemy_ids = [t for t, _ in types_with_weights]
        w = [wt for _, wt in types_with_weights]
        enemy_id = random.choices(enemy_ids, weights=w, k=1)[0]
    else:
        enemy_id = random.choice(enemy_types)
    return create_enemy(enemy_id, level)

def create_enemy_group(enemy_types, level, count=None, weights=None):
    if count is None:
        count = random.choices([1, 2, 2, 3], k=1)[0]
    enemies = []
    for _ in range(count):
        enemies.append(create_random_enemy(enemy_types, level, weights))
    return enemies

def create_elite_enemy(enemy_types, level):
    elite = create_enemy(random.choice(enemy_types), level)
    elite.apply_elite_multipliers()
    guard = create_random_enemy(enemy_types, max(1, level - 2))
    return [elite, guard]

def create_boss(biome_id, level):
    from config import load_biomes
    biomes = load_biomes()
    bosses = biomes[biome_id]["bosses"]
    boss_id = random.choice(bosses)
    return create_enemy(boss_id, level)
