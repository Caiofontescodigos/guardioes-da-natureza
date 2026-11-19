import json
import os
import time
from copy import deepcopy

from config import BASE_DIR, SAVE_DIR as CONFIG_SAVE_DIR, DEFAULT_GLOBAL_SETTINGS

MAX_SLOTS = 3
SAVE_VERSION = "3.2"

SAVE_DIR = CONFIG_SAVE_DIR

REQUIRED_KEYS = [
    "version",
    "unlocked_animals",
    "unlocked_biomes",
    "permanent_upgrades",
    "animal_data",
    "active_party",
    "bestiary_discovered",
    "creatures_discovered",
    "statistics",
    "settings",
    "run",
    "run_active",
    "play_time",
    "last_save_time",
]


class SaveError(Exception):
    """Raised when a save cannot be loaded or written."""


class SaveManager:
    """Single source of truth for all save operations."""

    def __init__(self):
        self.active_slot = None
        self.on_save_status = None
        self.ensure_save_dir()
        self.migrate_all()

    # ---------------------------------------------------------------- paths

    def ensure_save_dir(self):
        try:
            os.makedirs(SAVE_DIR, exist_ok=True)
        except OSError as e:
            print(f"[SaveManager] Nao foi possivel criar {SAVE_DIR}: {e}")

    def _slot_path(self, slot):
        return os.path.join(SAVE_DIR, f"save_{slot}.json")

    def get_save_path(self, slot=1):
        return self._slot_path(slot)

    # ----------------------------------------------------- status callbacks

    def set_status_callback(self, callback):
        self.on_save_status = callback

    def _notify_saving(self):
        if self.on_save_status:
            try:
                self.on_save_status("saving")
            except Exception:
                pass

    def _notify_saved(self, success=True, message=None):
        if self.on_save_status:
            try:
                self.on_save_status("saved", success=success, message=message)
            except Exception:
                pass

    # -------------------------------------------------------- data creation

    def create_save(self):
        return {
            "version": SAVE_VERSION,
            "unlocked_animals": ["tatu_bola"],
            "unlocked_biomes": ["caatinga"],
            "permanent_upgrades": {},
            "animal_data": {},
            "active_party": [],
            "potions": {"health": 0, "defense": 0, "attack": 0, "revive": 0},
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
                "legendary_bosses_defeated": 0,
                "legendary_animals_unlocked": 0,
            },
            "settings": deepcopy(DEFAULT_GLOBAL_SETTINGS),
            "run": None,
            "run_active": False,
            "play_time": 0,
            "last_save_time": 0,
        }

    def create_initial_save(self):
        return self.create_save()

    def _ensure_defaults(self, data):
        run = data.get("run")
        data["run_active"] = bool(isinstance(run, dict) and run.get("map"))
        defaults = self.create_save()
        for key, value in defaults.items():
            if key not in data:
                data[key] = value
        if "settings" not in data or not isinstance(data["settings"], dict):
            data["settings"] = deepcopy(defaults["settings"])
        else:
            for key, value in defaults["settings"].items():
                data["settings"].setdefault(key, deepcopy(value))
        if "statistics" not in data or not isinstance(data["statistics"], dict):
            data["statistics"] = defaults["statistics"].copy()
        else:
            for stat_key, stat_value in defaults["statistics"].items():
                data["statistics"].setdefault(stat_key, stat_value)
        if "animal_data" not in data or not isinstance(data["animal_data"], dict):
            data["animal_data"] = {}
        if "permanent_upgrades" not in data or not isinstance(
                data["permanent_upgrades"], dict):
            data["permanent_upgrades"] = {}
        if data.get("active_party") is None:
            data["active_party"] = []
        potions = data.get("potions")
        if not isinstance(potions, dict):
            potions = {}
            data["potions"] = potions
        for potion_key in ("health", "defense", "attack", "revive"):
            try:
                potions[potion_key] = max(0, int(potions.get(potion_key) or 0))
            except (TypeError, ValueError):
                potions[potion_key] = 0
        unlocked_biomes = data.get("unlocked_biomes")
        if isinstance(unlocked_biomes, list):
            # Pampa was inserted before Amazonia.  Players who already
            # unlocked Amazonia should also have access to the new region.
            if "amazonia" in unlocked_biomes and "pampa" not in unlocked_biomes:
                index = unlocked_biomes.index("amazonia")
                unlocked_biomes.insert(index, "pampa")
        self._normalize_animal_evolution(data)

    def _normalize_animal_evolution(self, data):
        """Migrate evolution-related fields on loaded saves.

        Idempotent: derives ``evolution_stage`` from the level when missing and
        grants the level-6 evolution (status bonuses + species-specific
        upgrade) exactly once, tracked by ``specific_upgrade_id``.
        """
        from src.entities.animal import (get_evolution_stage_for_level,
                                         EVOLUTION_LEVELS,
                                         apply_evolution_1_to_dict,
                                         apply_specific_upgrade_to_dict)
        animal_data = data.get("animal_data")
        if not isinstance(animal_data, dict):
            return
        for animal_id, entry in animal_data.items():
            if not isinstance(entry, dict):
                continue
            entry.pop("equipped_item", None)
            level = entry.get("level", 1)
            if not isinstance(level, (int, float)):
                level = 1
            if "evolution_stage" not in entry:
                entry["evolution_stage"] = get_evolution_stage_for_level(level)
            stage = int(entry.get("evolution_stage", 0) or 0)
            stage = min(stage, 1)
            entry["evolution_stage"] = stage
            upgrade_id = entry.get("specific_upgrade_id")
            if stage >= 1 and not upgrade_id:
                apply_specific_upgrade_to_dict(animal_id, entry)
            elif stage == 0 and level >= EVOLUTION_LEVELS[1] and not upgrade_id:
                entry["evolution_stage"] = 1
                apply_evolution_1_to_dict(entry)
                apply_specific_upgrade_to_dict(animal_id, entry)

    # ------------------------------------------------------------- status
    # Returns "empty" | "ok" | "corrupt"
    def get_slot_status(self, slot):
        path = self._slot_path(slot)
        if not os.path.exists(path):
            return "empty"
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, TypeError, OSError):
            return "corrupt"
        if not isinstance(data, dict):
            return "corrupt"
        if str(data.get("version", "")) not in (SAVE_VERSION, "3.0", "2.1", "2.0", "1.0"):
            return "corrupt"
        return "ok"

    def validate_save(self, slot):
        ok, msg = self.validate_data(self._read_slot(slot))
        return ok, msg

    def validate_data(self, data):
        if not isinstance(data, dict):
            return False, "Dados de save invalidos"
        for key in REQUIRED_KEYS:
            if key not in data:
                return False, f"Campo ausente: {key}"
        if str(data.get("version", "")) not in (SAVE_VERSION, "3.0", "2.1", "2.0", "1.0"):
            return False, "Versao de save desconhecida"
        if not isinstance(data.get("unlocked_animals"), list):
            return False, "unlocked_animals invalido"
        if not isinstance(data.get("animal_data"), dict):
            return False, "animal_data invalido"
        return True, "OK"

    def has_save(self, slot):
        return self.get_slot_status(slot) == "ok"

    def is_corrupt(self, slot):
        return self.get_slot_status(slot) == "corrupt"

    def is_slot_empty(self, slot):
        return self.get_slot_status(slot) == "empty"

    def get_slot_corrupt(self, slot):
        return self.is_corrupt(slot)

    # --------------------------------------------------------------- backup

    def _backup_slot(self, slot):
        path = self._slot_path(slot)
        if not os.path.exists(path):
            return False
        try:
            bak = path + ".bak"
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(bak, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except OSError as e:
            print(f"[SaveManager] Falha ao criar backup do save {slot}: {e}")
            return False

    def backup_save(self, slot):
        return self._backup_slot(slot)

    def restore_save(self, slot):
        """Restore a (possibly corrupt) slot from its .bak backup file."""
        path = self._slot_path(slot)
        bak = path + ".bak"
        if not os.path.exists(bak):
            return False
        try:
            with open(bak, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            os.remove(bak)
        except OSError as e:
            print(f"[SaveManager] Falha ao restaurar save {slot}: {e}")
            return False
        self._migrate_slot(slot)
        return self.get_slot_status(slot) == "ok"

    def migrate_save(self, slot):
        self._migrate_slot(slot)
        return self.get_slot_status(slot) == "ok"

    # ------------------------------------------------------ read / validate

    def _read_slot(self, slot):
        path = self._slot_path(slot)
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return None
            return data
        except (json.JSONDecodeError, TypeError, OSError):
            return None

    # ---------------------------------------------------------- migration

    def migrate_all(self):
        for slot in range(1, MAX_SLOTS + 1):
            self._migrate_slot(slot)

    def _migrate_slot(self, slot):
        data = self._read_slot(slot)
        if data is None:
            return
        version = str(data.get("version", ""))
        if version == SAVE_VERSION:
            ok, _ = self.validate_data(data)
            if ok:
                return
        # Migrate older/partial saves: back up then upgrade in place.
        if version != SAVE_VERSION:
            self._backup_slot(slot)
        data["version"] = SAVE_VERSION
        data.pop("inventory", None)
        self._ensure_defaults(data)
        self._write(data, slot, notify=False)

    # ------------------------------------------------------------- writing

    def _write(self, data, slot, notify=True):
        try:
            self._ensure_defaults(data)
            data["last_save_time"] = time.time()
            tmp_path = self._slot_path(slot) + ".tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            os.replace(tmp_path, self._slot_path(slot))
            if notify:
                self._notify_saving()
                self._notify_saved(True)
            return True
        except OSError as e:
            print(f"[SaveManager] Erro ao salvar: {e}")
            if notify:
                self._notify_saved(False)
            return False

    def save_game(self, data, slot=None):
        if slot is None:
            slot = self.active_slot
        if slot is None:
            return False
        self.ensure_save_dir()
        return self._write(data, slot)

    def save_slot(self, data, slot):
        self.active_slot = slot
        return self._write(data, slot)

    # -------------------------------------------------------------- loading

    def load_game(self, slot=None):
        if slot is None:
            slot = self.active_slot
        if slot is None:
            return None
        if self.get_slot_status(slot) != "ok":
            return None
        data = self._read_slot(slot)
        if data is None:
            return None
        self.active_slot = slot
        self._migrate_slot(slot)
        data = self._read_slot(slot) or data
        return data

    def load_slot(self, slot):
        return self.load_game(slot)

    def read_slot(self, slot):
        """Read a slot without changing the active slot (used by profiles)."""
        if self.get_slot_status(slot) != "ok":
            return None
        return self._read_slot(slot)

    # -------------------------------------------------------------- delete

    def delete_slot(self, slot):
        try:
            for suffix in ("", ".tmp", ".bak"):
                path = self._slot_path(slot) + suffix
                if os.path.exists(path):
                    os.remove(path)
            if self.active_slot == slot:
                self.active_slot = None
            return True
        except OSError as e:
            print(f"[SaveManager] Erro ao deletar save {slot}: {e}")
            return False

    delete_save = delete_slot

    # ---------------------------------------------------------- slot info

    def get_slot_info(self, slot):
        if self.get_slot_status(slot) != "ok":
            return None
        self._migrate_slot(slot)
        data = self._read_slot(slot)
        if not data:
            return None
        unlocked = [a for a in data.get("unlocked_animals", []) if a]
        biomes = data.get("unlocked_biomes", [])
        animal_data = data.get("animal_data", {})
        stats = data.get("statistics", {}) or {}
        from config import load_animals
        animals = load_animals()

        levels = [a.get("level", 1) for a in animal_data.values()
                  if isinstance(a, dict) and a.get("level")]
        best_level = max(levels) if levels else 1

        last_animal = ""
        if unlocked:
            last_id = unlocked[-1]
            if last_id in animals:
                last_animal = animals[last_id].get("name", last_id)

        party_names = []
        party_details = []
        for pid in data.get("active_party", []):
            if pid in unlocked:
                adata = animal_data.get(pid, {}) or {}
                name = animals.get(pid, {}).get("name", pid)
                party_names.append(name)
                party_details.append({
                    "id": pid,
                    "name": name,
                    "level": adata.get("level", 1) or 1,
                    "evolution_stage": adata.get("evolution_stage", 0) or 0,
                })

        total_gold = 0
        for akey, aval in animal_data.items():
            if isinstance(aval, dict):
                total_gold += aval.get("gold", 0) or 0

        run = data.get("run")
        biome_id = None
        if isinstance(run, dict) and run.get("current_biome"):
            biome_id = run["current_biome"]
        elif biomes:
            biome_id = biomes[-1]
        biome_name = biome_id or "caatinga"
        from config import load_biomes
        all_biomes = load_biomes()
        if biome_id in all_biomes:
            biome_name = all_biomes[biome_id].get("name", biome_id)

        play_time = data.get("play_time", 0) or 0
        hours = int(play_time // 3600)
        minutes = int((play_time % 3600) // 60)

        return {
            "slot": slot,
            "animals_count": len(unlocked),
            "biomes_count": len(biomes),
            "best_level": best_level,
            "bosses_defeated": stats.get("bosses_defeated", 0),
            "play_time": f"{hours:02d}:{minutes:02d}",
            "last_animal": last_animal,
            "run_active": bool(isinstance(run, dict) and run.get("map")),
            "party": party_names,
            "party_ids": [d["id"] for d in party_details],
            "party_details": party_details,
            "gold": total_gold,
            "biome": biome_name,
        }

    # ----------------------------------------------------- permanent data

    def update_statistics(self, data, stat_name, value=1):
        if "statistics" not in data or not isinstance(data["statistics"], dict):
            data["statistics"] = self.create_save()["statistics"]
        if stat_name in data["statistics"]:
            data["statistics"][stat_name] += value
        return data

    def add_unlocked_animal(self, data, animal_id):
        if "unlocked_animals" not in data:
            data["unlocked_animals"] = []
        if animal_id not in data["unlocked_animals"]:
            data["unlocked_animals"].append(animal_id)
        if "bestiary_discovered" not in data:
            data["bestiary_discovered"] = []
        if animal_id not in data["bestiary_discovered"]:
            data["bestiary_discovered"].append(animal_id)
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
                "hp": base_stats.get("hp", 50),
                "regen_per_turn": 0,
                "cooldown_reduction": 0,
                "damage_reduction": 0,
                "execute_bonus": 0,
                "crit_damage_boost": 0,
                "evolution_stage": 0,
                "specific_upgrade_id": None,
                "gold": 0,
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
            "hp": max(0, animal.hp),
            "is_alive": bool(getattr(animal, "is_alive", animal.hp > 0)),
            "regen_per_turn": animal.regen_per_turn,
            "cooldown_reduction": animal.cooldown_reduction,
            "damage_reduction": animal.damage_reduction,
            "execute_bonus": animal.execute_bonus,
            "crit_damage_boost": animal.crit_damage_boost,
            "evolution_stage": animal.evolution_stage,
            "specific_upgrade_id": getattr(animal, "specific_upgrade_id", None),
            "gold": getattr(animal, "gold", 0),
        }
        return self.save_animal_data(data, animal.animal_id, save_data)

    def restore_animal_stats(self, animal, data):
        from src.entities.animal import get_evolution_stage_for_level
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
        saved_hp = saved.get("hp")
        if isinstance(saved_hp, (int, float)):
            # Keep 0 HP: fallen animals stay fallen until revived by the
            # Golden Cross or the Camp, instead of silently healing on load.
            animal.hp = max(0, int(saved_hp))
        else:
            animal.hp = animal.max_hp
        saved_alive = saved.get("is_alive")
        if isinstance(saved_alive, bool):
            animal.is_alive = saved_alive and animal.hp > 0
        else:
            animal.is_alive = animal.hp > 0
        animal.regen_per_turn = saved.get("regen_per_turn", 0)
        animal.cooldown_reduction = saved.get("cooldown_reduction", 0)
        animal.damage_reduction = saved.get("damage_reduction", 0)
        animal.execute_bonus = saved.get("execute_bonus", 0)
        animal.crit_damage_boost = saved.get("crit_damage_boost", 0)
        animal.gold = saved.get("gold", 0)
        animal.evolution_stage = saved.get(
            "evolution_stage", get_evolution_stage_for_level(animal.level))
        animal.specific_upgrade_id = saved.get("specific_upgrade_id")
        if animal.hp < 0:
            animal.hp = 0
        return animal

    def save_party(self, data, party):
        data["active_party"] = [a.animal_id for a in party][:MAX_SLOTS]
        return data

    def load_party_ids(self, data):
        ids = data.get("active_party", [])
        if not isinstance(ids, list):
            ids = []
        seen = []
        for aid in ids:
            if aid and aid not in seen:
                seen.append(aid)
        return seen

    # ------------------------------------------------------------ upgrades

    def add_permanent_upgrade(self, data, animal_id, upgrade_id):
        pu = data.get("permanent_upgrades")
        if not isinstance(pu, dict):
            pu = {}
            data["permanent_upgrades"] = pu
        if animal_id not in pu:
            pu[animal_id] = []
        if upgrade_id not in pu[animal_id]:
            pu[animal_id].append(upgrade_id)
        return data

    # ---------------------------------------------------------- bestiary

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

    # ------------------------------------------------------------ run state

    def set_run(self, data, biome_id, map_dict):
        data["run"] = {"current_biome": biome_id, "map": map_dict}
        data["run_active"] = True
        return data

    def clear_run(self, data):
        data["run"] = None
        data["run_active"] = False
        return data