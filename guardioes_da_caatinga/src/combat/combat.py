import random
from src.state import BuffType, DebuffType

class FloatingText:
    def __init__(self, text, x, y, color, duration=60):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.duration = duration
        self.max_duration = duration
        self.alpha = 255

    def update(self):
        self.duration -= 1
        self.y -= 0.8
        self.alpha = max(0, int(255 * (self.duration / self.max_duration)))
        return self.duration > 0

class CombatEvent:
    def __init__(self, event_type, source_name, target_name, value, x=0, y=0, is_crit=False, heal=False):
        self.event_type = event_type
        self.source_name = source_name
        self.target_name = target_name
        self.value = value
        self.x = x
        self.y = y
        self.is_crit = is_crit
        self.heal = heal

class CombatSystem:
    def __init__(self, party, enemies):
        self.party = party
        self.enemies = enemies
        self.turn_order = []
        self.current_turn_index = 0
        self.turn_count = 0
        self.combat_log = []
        self.combat_ended = False
        self.player_won = False
        self.pending_events = []

    def start_combat(self):
        all_units = [(u, u.speed) for u in self.party if u.is_alive] + \
                    [(u, u.speed) for u in self.enemies if u.is_alive]
        all_units.sort(key=lambda x: x[1], reverse=True)
        self.turn_order = [u[0] for u in all_units]
        self.turn_count = 1
        self.current_turn_index = 0
        self._log(f"=== Combate Iniciado ===")

    def step_combat(self):
        if self.combat_ended:
            return []

        events = []
        self.pending_events = []

        attempts = 0
        while attempts < len(self.turn_order) * 2:
            unit = self.get_current_unit()
            if unit and unit.is_alive:
                break
            self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
            if self.current_turn_index == 0:
                self.turn_count += 1
            attempts += 1

        unit = self.get_current_unit()
        if not unit or not unit.is_alive:
            self._check_combat_end()
            return events

        unit.tick_effects()
        unit.reduce_cooldowns()

        if not unit.is_alive:
            self._check_combat_end()
            return events

        if unit in self.party:
            action = self._ally_choose_action(unit)
        else:
            action = unit.choose_action(self.party, self.enemies)

        if action:
            if action["type"] == "attack":
                evts = self.execute_skill(unit, action["skill"], action["target"])
                events.extend(evts)
            elif action["type"] == "buff":
                evts = self.execute_skill(unit, action["skill"], action["targets"])
                events.extend(evts)

        self._check_combat_end()

        self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
        if self.current_turn_index == 0:
            self.turn_count += 1

        return events

    def _ally_choose_action(self, unit):
        alive_enemies = [e for e in self.enemies if e.is_alive]
        if not alive_enemies:
            return None

        for skill in unit.skills:
            if unit.is_skill_ready(skill["id"]):
                skill_type = skill.get("type", "attack")
                if skill_type in ("heal", "buff", "defense", "support"):
                    allies = [a for a in self.party if a.is_alive and a.hp < a.max_hp]
                    if skill_type == "heal" and allies:
                        lowest = min(allies, key=lambda a: a.hp / a.max_hp)
                        return {"type": "buff", "skill": skill, "targets": lowest}
                    elif skill_type in ("buff", "defense"):
                        return {"type": "buff", "skill": skill, "targets": unit}
                    elif skill_type == "support":
                        debuffed = [a for a in self.party if a.is_alive and a.debuffs]
                        if debuffed:
                            return {"type": "buff", "skill": skill, "targets": debuffed[0]}

        for skill in unit.skills:
            if unit.is_skill_ready(skill["id"]):
                skill_type = skill.get("type", "attack")
                if skill_type in ("attack", "debuff"):
                    target = random.choice(alive_enemies)
                    return {"type": "attack", "skill": skill, "target": target}

        target = random.choice(alive_enemies)
        basic = {
            "id": "basic_attack", "name": "Ataque Básico",
            "damage": 0, "target": "single_enemy", "type": "attack", "effect": "none"
        }
        return {"type": "attack", "skill": basic, "target": target}

    def execute_skill(self, unit, skill, targets):
        if not unit.is_alive:
            return []

        events = []
        skill_type = skill.get("type", "attack")

        if skill_type == "attack":
            events.extend(self._execute_attack(unit, skill, targets))
        elif skill_type == "heal":
            events.extend(self._execute_heal(unit, skill, targets))
        elif skill_type == "buff":
            events.extend(self._execute_buff(unit, skill, targets))
        elif skill_type == "debuff":
            events.extend(self._execute_debuff(unit, skill, targets))
        elif skill_type == "defense":
            events.extend(self._execute_defense(unit, skill))
        elif skill_type == "support":
            events.extend(self._execute_support(unit, skill))

        cooldown = unit.get_cooldown_with_reduction(skill["id"])
        unit.put_on_cooldown(skill["id"], cooldown)
        return events

    def _execute_attack(self, unit, skill, targets):
        events = []
        damage = skill.get("damage", 0) + unit.attack
        effect = skill.get("effect", "none")
        if effect == "scale_with_defense":
            damage += unit.defense

        target_list = []
        target_type = skill.get("target", "single_enemy")
        if target_type == "all_enemies":
            allies = self.party if unit in self.enemies else self.enemies
            target_list = [t for t in allies if t.is_alive]
        else:
            target_list = [targets] if targets and targets.is_alive else []

        for target in target_list:
            actual_damage = damage
            is_crit = False

            crit_boost = skill.get("crit_boost", 0) if effect == "crit_boost" else 0
            if random.randint(1, 100) <= (unit.crit_chance + crit_boost):
                actual_damage = int(actual_damage * 1.5)
                is_crit = True

            dmg_dealt, dodged = target.take_damage(actual_damage)
            if dodged:
                self._log(f"{unit.name} ataca {target.name} - ESQUIVOU!")
                events.append(CombatEvent("dodge", unit.name, target.name, 0))
            else:
                crit_text = " CRÍTICO!" if is_crit else ""
                self._log(f"{unit.name} ataca {target.name} por {dmg_dealt}{crit_text}")
                events.append(CombatEvent("damage", unit.name, target.name, dmg_dealt, is_crit=is_crit))

                if effect == "bleed":
                    dot = skill.get("dot_damage", 3)
                    target.apply_debuff(DebuffType.BLEED, dot, skill.get("duration", 3))
                elif effect == "poison":
                    dot = skill.get("dot_damage", 4)
                    target.apply_debuff(DebuffType.POISON, dot, skill.get("duration", 3))
                elif effect == "slow":
                    target.apply_debuff(DebuffType.SPEED_DOWN, skill.get("slow_amount", 3), skill.get("duration", 2))
                elif effect == "fear":
                    target.apply_debuff(DebuffType.ATTACK_DOWN, skill.get("attack_down", 3), skill.get("duration", 2))

                if unit.has_counter_attack > 0 and target.is_alive:
                    counter_dmg = unit.has_counter_attack
                    target.take_damage(counter_dmg)
                    events.append(CombatEvent("damage", unit.name, target.name, counter_dmg))
                    self._log(f"Contra-ataque: {unit.name} -> {target.name} por {counter_dmg}")

        if effect == "double_hit" and target_list:
            alive = [t for t in target_list if t.is_alive]
            if alive:
                second_target = random.choice(alive)
                dmg_dealt, dodged = second_target.take_damage(damage)
                if not dodged:
                    events.append(CombatEvent("damage", unit.name, second_target.name, dmg_dealt))
                    self._log(f"{unit.name} ataca novamente {second_target.name} por {dmg_dealt}")

        return events

    def _execute_heal(self, unit, skill, targets):
        events = []
        healing = skill.get("healing", 0)
        target_type = skill.get("target", "single_ally")

        if target_type == "all_allies":
            allies = self.party if unit in self.party else self.enemies
            for ally in allies:
                if ally.is_alive:
                    healed = ally.heal(healing)
                    if healed > 0:
                        events.append(CombatEvent("heal", unit.name, ally.name, healed, heal=True))
                        self._log(f"{unit.name} cura {ally.name} por {healed}")
        else:
            target = targets if targets else unit
            if target and target.is_alive:
                healed = target.heal(healing)
                if healed > 0:
                    events.append(CombatEvent("heal", unit.name, target.name, healed, heal=True))
                    self._log(f"{unit.name} cura {target.name} por {healed}")
        return events

    def _execute_buff(self, unit, skill, targets):
        events = []
        effect = skill.get("effect", "none")
        duration = skill.get("duration", 2)
        target_type = skill.get("target", "self")

        allies = self.party if unit in self.party else self.enemies
        if target_type == "all_allies":
            targets_list = [a for a in allies if a.is_alive]
        else:
            targets_list = [targets] if targets else [unit]

        for target in targets_list:
            if not target.is_alive:
                continue
            if effect == "attack_boost":
                boost = skill.get("attack_boost", 3)
                target.apply_buff(BuffType.ATTACK_UP, boost, duration)
                events.append(CombatEvent("buff", unit.name, target.name, boost))
                self._log(f"{target.name} recebe +{boost} ataque")
            elif effect == "defense_boost":
                boost = skill.get("defense_bonus", 5)
                target.apply_buff(BuffType.DEFENSE_UP, boost, duration)
                events.append(CombatEvent("buff", unit.name, target.name, boost))
                self._log(f"{target.name} recebe +{boost} defesa")
            elif effect == "dodge_boost":
                boost = skill.get("dodge_boost", 25)
                target.apply_buff(BuffType.DODGE_UP, boost, duration)
                events.append(CombatEvent("buff", unit.name, target.name, boost))
            elif effect == "power_up":
                target.apply_buff(BuffType.ATTACK_UP, 5, duration)
                target.apply_buff(BuffType.DEFENSE_UP, 5, duration)
                healed = target.heal(skill.get("healing", 20))
                if healed > 0:
                    events.append(CombatEvent("heal", unit.name, target.name, healed, heal=True))
                events.append(CombatEvent("buff", unit.name, target.name, 5))
            elif effect == "counter_attack":
                counter = skill.get("damage", 8)
                target.apply_buff(BuffType.COUNTER_ATTACK, counter, duration)
                events.append(CombatEvent("buff", unit.name, target.name, counter))
        return events

    def _execute_debuff(self, unit, skill, targets):
        events = []
        effect = skill.get("effect", "none")
        duration = skill.get("duration", 2)

        target_type = skill.get("target", "single_enemy")
        if target_type == "all_enemies":
            enemies = self.enemies if unit in self.party else self.party
            targets_list = [e for e in enemies if e.is_alive]
        else:
            targets_list = [targets] if targets and targets.is_alive else []

        for target in targets_list:
            if effect == "attack_down":
                down = skill.get("attack_down", 3)
                target.apply_debuff(DebuffType.ATTACK_DOWN, down, duration)
                events.append(CombatEvent("debuff", unit.name, target.name, down))
                self._log(f"{target.name} perde {down} ataque")
            elif effect == "slow":
                slow = skill.get("slow_amount", 3)
                target.apply_debuff(DebuffType.SPEED_DOWN, slow, duration)
                events.append(CombatEvent("debuff", unit.name, target.name, slow))
            elif effect == "fear":
                down = skill.get("attack_down", 4)
                target.apply_debuff(DebuffType.ATTACK_DOWN, down, duration)
                events.append(CombatEvent("debuff", unit.name, target.name, down))
        return events

    def _execute_defense(self, unit, skill):
        events = []
        defense_bonus = skill.get("defense_bonus", 8)
        duration = skill.get("duration", 2)
        effect = skill.get("effect", "none")

        if effect == "reduce_damage":
            unit.apply_buff(BuffType.REDUCE_DAMAGE, defense_bonus, duration)
        elif effect == "shield":
            unit.apply_buff(BuffType.SHIELD, defense_bonus, duration)
        else:
            unit.apply_buff(BuffType.DEFENSE_UP, defense_bonus, duration)

        events.append(CombatEvent("buff", unit.name, unit.name, defense_bonus))
        self._log(f"{unit.name} usa {skill['name']}")
        return events

    def _execute_support(self, unit, skill):
        events = []
        effect = skill.get("effect", "none")
        allies = self.party if unit in self.party else self.enemies

        if effect == "cleanse_ally":
            for ally in allies:
                if ally.is_alive and ally.debuffs:
                    ally.debuffs.clear()
                    self._log(f"{unit.name} remove debuffs de {ally.name}")
            enemies = self.enemies if unit in self.party else self.party
            alive = [e for e in enemies if e.is_alive]
            if alive:
                target = random.choice(alive)
                dmg = skill.get("damage", 6) + unit.attack
                dmg_dealt, _ = target.take_damage(dmg)
                events.append(CombatEvent("damage", unit.name, target.name, dmg_dealt))
        elif effect == "cleanse_all":
            for ally in allies:
                if ally.is_alive:
                    ally.debuffs.clear()
                    healed = ally.heal(skill.get("healing", 5))
                    if healed > 0:
                        events.append(CombatEvent("heal", unit.name, ally.name, healed, heal=True))
        return events

    def _check_combat_end(self):
        all_party_dead = all(not u.is_alive for u in self.party)
        all_enemies_dead = all(not u.is_alive for u in self.enemies)
        if all_enemies_dead:
            self.combat_ended = True
            self.player_won = True
            self._log("Vitória!")
        elif all_party_dead:
            self.combat_ended = True
            self.player_won = False
            self._log("Derrota...")

    def get_current_unit(self):
        if self.current_turn_index < len(self.turn_order):
            return self.turn_order[self.current_turn_index]
        return None

    def get_rewards(self):
        if not self.player_won:
            return {"xp": 0, "gold": 0}
        total_xp = sum(e.xp_reward for e in self.enemies)
        total_gold = sum(e.gold_reward for e in self.enemies)
        return {"xp": total_xp, "gold": total_gold}

    def _log(self, message):
        self.combat_log.append(message)

    def get_log(self, last_n=12):
        return self.combat_log[-last_n:]
