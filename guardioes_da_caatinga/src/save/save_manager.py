import json
import os
import time
from config import BASE_DIR

SAVE_DIR = os.path.join(BASE_DIR, "saves")
MAX_SLOTS = 3


class SaveManager:
    def __init__(self):
        self.ensure_save_dir()
        self.active_slot = None

    def ensure_save_dir(self):
        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)

    def _slot_path(self, slot):
        return os.path.join(SAVE_DIR, f"save_{slot}.json")

    def save_game(self, game_data, slot=None):
        if slot is None:
            slot = self.active_slot
        if slot is None:
            return False
        try:
            game_data["last_save_time"] = time.time()
            if "play_time" not in game_data:
                game_data["play_time"] = 0
            with open(self._slot_path(slot), 'w', encoding='utf-8') as f:
                json.dump(game_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar: {e}")
            return False

    def load_game(self, slot=None):
        if slot is None:
            for s in range(1, MAX_SLOTS + 1):
                if self.has_save(s):
                    data = self._read_slot(s)
                    if data:
                        self.active_slot = s
                        return data
            return None
        try:
            path = self._slot_path(slot)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.active_slot = slot
                return data
            return None
        except Exception as e:
            print(f"Erro ao carregar: {e}")
            return None

    def _read_slot(self, slot):
        try:
            path = self._slot_path(slot)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def delete_save(self, slot):
        try:
            path = self._slot_path(slot)
            if os.path.exists(path):
                os.remove(path)
            if self.active_slot == slot:
                self.active_slot = None
            return True
        except Exception as e:
            print(f"Erro ao deletar: {e}")
            return False

    def has_save(self, slot):
        return os.path.exists(self._slot_path(slot))

    def get_slot_info(self, slot):
        try:
            data = self._read_slot(slot)
            if not data:
                return None
            unlocked = data.get("unlocked_animals", [])
            biomes = data.get("unlocked_biomes", [])
            play_time = data.get("play_time", 0)
            last_animal = ""
            if unlocked:
                last_id = unlocked[-1]
                from config import load_animals
                animals = load_animals()
                if last_id in animals:
                    last_animal = animals[last_id].get("name", last_id)
            hours = int(play_time // 3600)
            minutes = int((play_time % 3600) // 60)
            return {
                "slot": slot,
                "animals_count": len(unlocked),
                "animals_total": len(load_animals()),
                "biomes_count": len(biomes),
                "biomes_total": 5,
                "play_time": f"{hours:02d}:{minutes:02d}",
                "last_animal": last_animal,
            }
        except Exception:
            return None

    def create_initial_save(self):
        return {
            "version": "2.0",
            "unlocked_animals": ["tatu_bola"],
            "unlocked_biomes": ["caatinga"],
            "permanent_upgrades": [],
            "animal_data": {},
            "inventory": [],
            "active_party": ["tatu_bola"],
            "bestiary_discovered": ["tatu_bola"],
            "creatures_discovered": [],
            "statistics": {
                "combats_won": 0,
                "combats_lost": 0,
                "enemies_defeated": 0,
                "gold_earned": 0,
                "levels_gained": 0,
                "animals_rescued": 0,
                "bosses_defeated": 0,
            },
            "settings": {
                "music_volume": 0.7,
                "sfx_volume": 0.8,
                "fullscreen": False,
            },
            "play_time": 0,
            "last_save_time": 0,
        }

    def new_game(self, slot):
        data = self.create_initial_save()
        self.active_slot = slot
        self.save_game(data, slot)
        return data

    def update_statistics(self, data, stat_name, value=1):
        if "statistics" not in data:
            data["statistics"] = self.create_initial_save()["statistics"]
        if stat_name in data["statistics"]:
            data["statistics"][stat_name] += value
        return data

    def add_unlocked_animal(self, data, animal_id):
        if "unlocked_animals" not in data:
            data["unlocked_animals"] = []
        if animal_id not in data["unlocked_animals"]:
            data["unlocked_animals"].append(animal_id)
        if "animal_data" not in data:
            data["animal_data"] = {}
        if animal_id not in data["animal_data"]:
            from config import load_animals
            animals = load_animals()
            adata = animals.get(animal_id, {})
            base_stats = adata.get("base_stats", {})
            data["animal_data"][animal_id] = {
                "level": 1,
                "xp": 0,
                "xp_to_level": 50,
                "base_attack": base_stats.get("attack", 10),
                "base_defense": base_stats.get("defense", 10),
                "base_speed": base_stats.get("speed", 10),
                "base_crit_chance": base_stats.get("crit_chance", 5),
                "base_dodge": base_stats.get("dodge", 5),
                "max_hp": base_stats.get("hp", 50),
                "regen_per_turn": 0,
                "damage_reduction": 0,
                "execute_bonus": 0,
                "crit_damage_boost": 0,
                "equipped_item": None,
            }
        return data

    def add_unlocked_biome(self, data, biome_id):
        if "unlocked_biomes" not in data:
            data["unlocked_biomes"] = []
        if biome_id not in data["unlocked_biomes"]:
            data["unlocked_biomes"].append(biome_id)
        return data

    def save_animal_data(self, data, animal_id, animal_save_data):
        if "animal_data" not in data:
            data["animal_data"] = {}
        data["animal_data"][animal_id] = animal_save_data
        return data

    def get_animal_data(self, data, animal_id):
        if "animal_data" not in data:
            return None
        return data["animal_data"].get(animal_id)

    def save_animal_stats(self, data, animal):
        save_data = {
            "level": animal.level,
            "xp": animal.xp,
            "xp_to_level": animal.xp_to_level,
            "base_attack": animal.base_attack,
            "base_defense": animal.base_defense,
            "base_speed": animal.base_speed,
            "base_crit_chance": animal.base_crit_chance,
            "base_dodge": animal.base_dodge,
            "max_hp": animal.max_hp,
            "regen_per_turn": animal.regen_per_turn,
            "damage_reduction": animal.damage_reduction,
            "execute_bonus": animal.execute_bonus,
            "crit_damage_boost": animal.crit_damage_boost,
            "cooldown_reduction": animal.cooldown_reduction,
            "equipped_item": animal.equipped_item,
        }
        return self.save_animal_data(data, animal.animal_id, save_data)

    def restore_animal_stats(self, animal, data):
        saved = self.get_animal_data(data, animal.animal_id)
        if not saved:
            return animal
        animal.level = saved.get("level", 1)
        animal.xp = saved.get("xp", 0)
        animal.xp_to_level = saved.get("xp_to_level", 50)
        animal.base_attack = saved.get("base_attack", animal.base_attack)
        animal.base_defense = saved.get("base_defense", animal.base_defense)
        animal.base_speed = saved.get("base_speed", animal.base_speed)
        animal.base_crit_chance = saved.get("base_crit_chance", animal.base_crit_chance)
        animal.base_dodge = saved.get("base_dodge", animal.base_dodge)
        animal.max_hp = saved.get("max_hp", animal.max_hp)
        animal.hp = animal.max_hp
        animal.regen_per_turn = saved.get("regen_per_turn", 0)
        animal.damage_reduction = saved.get("damage_reduction", 0)
        animal.execute_bonus = saved.get("execute_bonus", 0)
        animal.crit_damage_boost = saved.get("crit_damage_boost", 0)
        animal.cooldown_reduction = saved.get("cooldown_reduction", 0)
        animal.equipped_item = saved.get("equipped_item", None)
        return animal

    def save_party(self, data, party):
        if "active_party" not in data:
            data["active_party"] = []
        data["active_party"] = [a.animal_id for a in party]
        return data

    def load_party_ids(self, data):
        return data.get("active_party", ["tatu_bola"])

    def add_item_to_inventory(self, data, item_id):
        if "inventory" not in data:
            data["inventory"] = []
        if item_id not in data["inventory"]:
            data["inventory"].append(item_id)
        return data

    def remove_item_from_inventory(self, data, item_id):
        if "inventory" in data and item_id in data["inventory"]:
            data["inventory"].remove(item_id)
        return data

    def equip_item(self, data, animal_id, item_id):
        if "animal_data" not in data:
            data["animal_data"] = {}
        saved = data["animal_data"].get(animal_id, {})
        old_item = saved.get("equipped_item")
        if old_item and old_item != item_id:
            self.add_item_to_inventory(data, old_item)
        saved["equipped_item"] = item_id
        self.remove_item_from_inventory(data, item_id)
        data["animal_data"][animal_id] = saved
        return data

    def unequip_item(self, data, animal_id):
        if "animal_data" not in data:
            data["animal_data"] = {}
        saved = data["animal_data"].get(animal_id, {})
        old_item = saved.get("equipped_item")
        if old_item:
            self.add_item_to_inventory(data, old_item)
            saved["equipped_item"] = None
            data["animal_data"][animal_id] = saved
        return data

    def discover_bestiary(self, data, animal_id):
        if "bestiary_discovered" not in data:
            data["bestiary_discovered"] = []
        is_new = animal_id not in data["bestiary_discovered"]
        if is_new:
            data["bestiary_discovered"].append(animal_id)
        return data, is_new

    def discover_creature(self, data, enemy_id):
        if "creatures_discovered" not in data:
            data["creatures_discovered"] = []
        is_new = enemy_id not in data["creatures_discovered"]
        if is_new:
            data["creatures_discovered"].append(enemy_id)
        return data, is_new

    def is_bestiary_discovered(self, data, animal_id):
        return animal_id in data.get("bestiary_discovered", [])

    def is_creature_discovered(self, data, enemy_id):
        return enemy_id in data.get("creatures_discovered", [])
