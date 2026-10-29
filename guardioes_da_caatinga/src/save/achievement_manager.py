"""Global achievement tracking.

Achievements are stored outside the journey slots so they survive new runs.
The manager keeps lifetime counters, unions of collected ids and record
values, then evaluates the definitions from ``data/achievements.json``.
"""

import json
import os
import time
from copy import deepcopy

from config import DATA_DIR, SAVE_DIR
from src.save.save_manager import MAX_SLOTS

TIER_POINTS = {
    "bronze": 1,
    "prata": 2,
    "ouro": 3,
    "platina": 5,
}

TIER_LABELS = {
    "bronze": "Bronze",
    "prata": "Prata",
    "ouro": "Ouro",
    "platina": "Platina",
}

CATEGORY_LABELS = {
    "jornada": "Jornada",
    "combate": "Combate",
    "animais": "Animais",
    "bestiario": "Bestiário",
    "extras": "Extras",
}

# Values read from the save statistics and accumulated as lifetime totals.
CUMULATIVE_KEYS = [
    "combats_won",
    "combats_lost",
    "enemies_defeated",
    "gold_earned",
    "levels_gained",
    "animals_rescued",
    "bosses_defeated",
    "play_time",
]

DEFAULT_STATE = {
    "version": 1,
    "unlocked": {},
    "counters": {},
    "sets": {},
    "max_values": {},
    "min_values": {},
    "slot_snapshots": {},
    "flags": {},
    "initial_sync_done": False,
}


class AchievementManager:
    def __init__(self, save_manager=None, state_path=None):
        self.save_manager = save_manager
        self.state_path = state_path or os.path.join(
            SAVE_DIR, "achievements.json")
        self.definitions = []
        self.by_id = {}
        self.titles = []
        self.state = deepcopy(DEFAULT_STATE)
        self._pending_unlocks = []
        self.active_slot = None

        self._load_definitions()
        self._load_state()

    # ----------------------------------------------------------- definitions
    def _load_definitions(self):
        path = os.path.join(DATA_DIR, "achievements.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"[Achievements] Falha ao carregar definicoes: {e}")
            data = {}

        self.definitions = [d for d in data.get("achievements", [])
                            if isinstance(d, dict) and d.get("id")]
        self.by_id = {d["id"]: d for d in self.definitions}
        self.titles = sorted(
            [t for t in data.get("titles", []) if isinstance(t, dict)],
            key=lambda t: t.get("points", 0))
        if not self.titles:
            self.titles = [{"points": 0, "name": "Novato"}]

    def _load_state(self):
        if not os.path.exists(self.state_path):
            return
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("estado invalido")
        except (OSError, ValueError, json.JSONDecodeError) as e:
            print(f"[Achievements] Estado corrompido, recriando: {e}")
            try:
                os.replace(self.state_path, self.state_path + ".bak")
            except OSError:
                pass
            return
        self._merge_state(data)

    def _merge_state(self, data):
        for key, default in DEFAULT_STATE.items():
            value = data.get(key, deepcopy(default))
            if isinstance(default, dict) and not isinstance(value, dict):
                value = deepcopy(default)
            if key == "version" and not isinstance(value, int):
                value = default
            if isinstance(default, bool) and not isinstance(value, bool):
                value = default
            if isinstance(default, list) and not isinstance(value, list):
                value = deepcopy(default)
            self.state[key] = value
        # Make sure every collection uses the expected shape.
        for key in ("unlocked", "counters", "sets", "max_values",
                    "min_values", "slot_snapshots", "flags"):
            if not isinstance(self.state.get(key), dict):
                self.state[key] = {}

    # ---------------------------------------------------------------- storage
    def save(self):
        try:
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            tmp = self.state_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=4, ensure_ascii=False)
            os.replace(tmp, self.state_path)
        except OSError as e:
            print(f"[Achievements] Falha ao salvar: {e}")

    # -------------------------------------------------------------- slot sync
    def bind_slot(self, slot):
        self.active_slot = slot

    def _read_slot(self, slot):
        if not self.save_manager:
            return None
        reader = getattr(self.save_manager, "read_slot", None)
        if reader:
            return reader(slot)
        return self.save_manager._read_slot(slot)

    def sync_all_slots(self, save_manager=None):
        """Seed lifetime progress from every existing journey (once)."""
        if self.state.get("initial_sync_done"):
            return
        manager = save_manager or self.save_manager
        if manager:
            for slot in range(1, int(MAX_SLOTS) + 1):
                try:
                    status = manager.get_slot_status(slot)
                except Exception:
                    status = "empty"
                if status != "ok":
                    continue
                try:
                    data = self._read_slot(slot)
                except Exception:
                    data = None
                if data:
                    self._sync_slot_data(slot, data)
        self.state["initial_sync_done"] = True
        self.save()
        self.evaluate(silent=True)

    def sync_from_save(self, slot, save_data):
        if not save_data:
            return
        if slot is None:
            slot = self.active_slot
        if slot is None:
            return
        self.active_slot = slot
        self._sync_slot_data(slot, save_data)
        self.save()
        self.evaluate(silent=False)

    def _sync_slot_data(self, slot, save_data):
        slot_key = str(slot)
        snapshots = self.state.setdefault("slot_snapshots", {})
        snapshot = snapshots.setdefault(slot_key, {})
        statistics = save_data.get("statistics") or {}

        for key in CUMULATIVE_KEYS:
            if key == "play_time":
                current = save_data.get("play_time", 0) or 0
            else:
                current = statistics.get(key, 0) or 0
            try:
                current = float(current)
            except (TypeError, ValueError):
                current = 0.0
            previous = snapshot.get(key, 0)
            try:
                previous = float(previous)
            except (TypeError, ValueError):
                previous = 0.0
            delta = current - previous
            if delta > 0:
                self.state["counters"][key] = (
                    self.state["counters"].get(key, 0) + delta)
            snapshot[key] = current

        self._add_to_set("animals_unlocked",
                         save_data.get("unlocked_animals", []))
        self._add_to_set("biomes_unlocked",
                         save_data.get("unlocked_biomes", []))
        self._add_to_set("bestiary_animals",
                         save_data.get("bestiary_discovered", []))
        self._add_to_set("bestiary_creatures",
                         save_data.get("creatures_discovered", []))
        self._add_to_set("evolved_animals",
                         [aid for aid, entry in
                          (save_data.get("animal_data") or {}).items()
                          if isinstance(entry, dict)
                          and (entry.get("evolution_stage", 0) or 0) >= 1])
        specific = []
        for aid, entry in (save_data.get("animal_data") or {}).items():
            if not isinstance(entry, dict):
                continue
            upgrade_id = entry.get("specific_upgrade_id")
            if upgrade_id:
                specific.append(f"{aid}:{upgrade_id}")
        self._add_to_set("specific_upgrades", specific)

        # Permanent upgrade choices are cumulative and can be seeded from the
        # existing save, so veteran players keep their progress.
        upgrades_total = 0
        permanent = save_data.get("permanent_upgrades") or {}
        if isinstance(permanent, dict):
            for values in permanent.values():
                if isinstance(values, (list, tuple)):
                    upgrades_total += len(values)
        try:
            previous_upgrades = float(
                snapshot.get("__upgrades_total", 0) or 0)
        except (TypeError, ValueError):
            previous_upgrades = 0.0
        if upgrades_total > previous_upgrades:
            delta = upgrades_total - previous_upgrades
            self.state["counters"]["upgrades_chosen"] = (
                self.state["counters"].get("upgrades_chosen", 0) + delta)
        snapshot["__upgrades_total"] = upgrades_total

        party_size = len(save_data.get("active_party") or [])
        self._update_max("party_size", party_size)

        max_level = 0
        max_gold = 0
        max_attribute = 0
        for entry in (save_data.get("animal_data") or {}).values():
            if not isinstance(entry, dict):
                continue
            try:
                max_level = max(max_level, int(entry.get("level", 0) or 0))
                max_gold = max(max_gold, int(entry.get("gold", 0) or 0))
                max_attribute = max(
                    max_attribute,
                    int(entry.get("base_attack", 0) or 0),
                    int(entry.get("base_defense", 0) or 0),
                    int(entry.get("base_speed", 0) or 0),
                )
            except (TypeError, ValueError):
                continue
        self._update_max("animal_level", max_level)
        self._update_max("max_gold", max_gold)
        self._update_max("max_combat_attribute", max_attribute)

    # ---------------------------------------------------------- event records
    def record(self, key, amount=1, save=True, evaluate=True):
        self.state["counters"][key] = (
            self.state["counters"].get(key, 0) + amount)
        if save:
            self.save()
        if evaluate:
            self.evaluate()

    def record_max(self, key, value, save=True, evaluate=True):
        self._update_max(key, value)
        if save:
            self.save()
        if evaluate:
            self.evaluate()

    def record_min(self, key, value, save=True, evaluate=True):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return
        if value <= 0:
            return
        current = self.state["min_values"].get(key)
        if current is None or value < current:
            self.state["min_values"][key] = value
        if save:
            self.save()
        if evaluate:
            self.evaluate()

    def add_to_set(self, key, values, save=True, evaluate=True):
        self._add_to_set(key, values)
        if save:
            self.save()
        if evaluate:
            self.evaluate()

    def set_flag(self, key, value=True, save=True, evaluate=True):
        self.state["flags"][key] = bool(value)
        if save:
            self.save()
        if evaluate:
            self.evaluate()

    def check_and_clear_flag(self, key):
        if not self.state["flags"].get(key):
            return False
        self.state["flags"][key] = False
        self.save()
        return True

    def record_combat(self, stats, won=True):
        """Apply all per-combat achievements in one write."""
        if not won:
            return
        stats = stats or {}
        damage_taken = int(stats.get("damage_taken", 0) or 0)
        if damage_taken <= 0:
            self.record("flawless_wins", 1, save=False, evaluate=False)
        if stats.get("low_hp_win"):
            self.record("low_hp_wins", 1, save=False, evaluate=False)
        self.record_max("max_crit_damage",
                        int(stats.get("max_crit_damage", 0) or 0),
                        save=False, evaluate=False)
        self.record_max("max_dodges_combat",
                        int(stats.get("dodges", 0) or 0),
                        save=False, evaluate=False)
        turns = int(stats.get("turns", 0) or 0)
        if turns > 0:
            self.record_min("fastest_win_turns", turns,
                            save=False, evaluate=False)
        # Zero damage is a valid (best) value for the Muralha achievement.
        self.record_min("min_damage_taken", max(1, damage_taken),
                        save=False, evaluate=False)
        self.save()
        self.evaluate()

    def _update_max(self, key, value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return
        current = self.state["max_values"].get(key)
        if current is None or value > current:
            self.state["max_values"][key] = value

    def _add_to_set(self, key, values):
        bucket = self.state["sets"].setdefault(key, [])
        existing = set(bucket)
        for value in values or []:
            if not value or value in existing:
                continue
            bucket.append(value)
            existing.add(value)

    # ------------------------------------------------------------ evaluation
    def evaluate(self, silent=False):
        """Unlock every achievement whose condition is now met."""
        unlocked = self.state["unlocked"]
        changed = False

        for entry in self.definitions:
            aid = entry["id"]
            if aid in unlocked:
                continue
            condition = entry.get("condition") or {}
            if condition.get("type") == "all_achievements":
                continue
            if self._is_met(condition):
                self._unlock(aid, silent=silent)
                changed = True

        # Platinum-style achievements are evaluated after the others.
        total = len(self.definitions)
        for entry in self.definitions:
            aid = entry["id"]
            if aid in unlocked:
                continue
            condition = entry.get("condition") or {}
            if condition.get("type") == "all_achievements":
                if len(unlocked) >= total - 1:
                    self._unlock(aid, silent=silent)
                    changed = True

        if changed:
            self.save()
        return changed

    def _unlock(self, achievement_id, silent=False):
        self.state["unlocked"][achievement_id] = time.strftime(
            "%Y-%m-%dT%H:%M:%S")
        if not silent:
            self._pending_unlocks.append(achievement_id)

    def drain_new_unlocks(self):
        pending = self._pending_unlocks
        self._pending_unlocks = []
        return pending

    # -------------------------------------------------------------- progress
    def _is_met(self, condition):
        current, target = self._progress_values(condition)
        if condition.get("type") == "min":
            return current > 0 and current <= target
        if condition.get("type") == "flag":
            return bool(current)
        return current >= target

    def _progress_values(self, condition):
        ctype = condition.get("type")
        key = condition.get("key", "")
        target = condition.get("target", 1)
        if ctype == "counter":
            return self.state["counters"].get(key, 0), target
        if ctype == "max":
            return self.state["max_values"].get(key, 0), target
        if ctype == "min":
            return self.state["min_values"].get(key, 0), target
        if ctype == "set_size":
            return len(self.state["sets"].get(key, [])), target
        if ctype == "set_contains":
            values = self.state["sets"].get(key, [])
            return (1 if condition.get("value") in values else 0), 1
        if ctype == "flag":
            return (1 if self.state["flags"].get(key) else 0), 1
        if ctype == "all_achievements":
            total = len(self.definitions)
            return len(self.state["unlocked"]), max(0, total - 1)
        return 0, target

    def entry_progress(self, entry):
        condition = entry.get("condition") or {}
        current, target = self._progress_values(condition)
        unlocked = entry["id"] in self.state["unlocked"]
        return {
            "current": current,
            "target": target,
            "text": self._format_progress(condition, current, target),
            "ratio": 1.0 if unlocked else self._ratio(condition, current,
                                                      target),
        }

    def _ratio(self, condition, current, target):
        ctype = condition.get("type")
        if ctype == "min":
            if current <= 0:
                return 0.0
            return max(0.0, min(1.0, target / current))
        if target <= 0:
            return 1.0
        return max(0.0, min(1.0, current / target))

    def _format_progress(self, condition, current, target):
        ctype = condition.get("type")
        key = condition.get("key", "")
        if ctype == "flag":
            return "Concluído" if current else "Pendente"
        if ctype == "set_contains":
            return "Concluído" if current else "Pendente"
        if key == "play_time":
            return f"{int(current) // 3600}h / {int(target) // 3600}h"
        if ctype == "min" and current <= 0:
            return f"— / {int(target)}"
        current_i = int(current)
        target_i = int(target)
        return f"{current_i}/{target_i}"

    # --------------------------------------------------------------- display
    def get_entry(self, achievement_id):
        entry = self.by_id.get(achievement_id)
        if not entry:
            return None
        return self._make_entry(entry)

    def get_entries(self, category="todas"):
        entries = []
        for definition in self.definitions:
            if category != "todas" and definition.get("category") != category:
                continue
            entries.append(self._make_entry(definition))
        return entries

    def _make_entry(self, definition):
        progress = self.entry_progress(definition)
        tier = definition.get("tier", "bronze")
        return {
            "id": definition["id"],
            "name": definition.get("name", definition["id"]),
            "description": definition.get("description", ""),
            "category": definition.get("category", "extras"),
            "tier": tier,
            "tier_label": TIER_LABELS.get(tier, tier.title()),
            "points": TIER_POINTS.get(tier, 1),
            "secret": bool(definition.get("secret")),
            "unlocked": definition["id"] in self.state["unlocked"],
            "unlocked_at": self.state["unlocked"].get(definition["id"]),
            "progress": progress,
        }

    def total_achievements(self):
        return len(self.definitions)

    def unlocked_count(self):
        return len(self.state["unlocked"])

    def points(self):
        return sum(TIER_POINTS.get(d.get("tier"), 1) for d in self.definitions
                   if d["id"] in self.state["unlocked"])

    def max_points(self):
        return sum(TIER_POINTS.get(d.get("tier"), 1)
                   for d in self.definitions)

    def current_title(self):
        points = self.points()
        title = self.titles[0].get("name", "Novato")
        for item in self.titles:
            if points >= item.get("points", 0):
                title = item.get("name", title)
            else:
                break
        return title

    def next_title(self):
        points = self.points()
        for item in self.titles:
            if points < item.get("points", 0):
                return item
        return None

    def completion_ratio(self):
        total = self.total_achievements()
        return (self.unlocked_count() / total) if total else 0.0
