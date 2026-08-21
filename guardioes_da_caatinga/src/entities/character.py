from src.state import BuffType, DebuffType

class StatusEffect:
    def __init__(self, effect_type, value, duration, is_buff=True):
        self.effect_type = effect_type
        self.value = value
        self.duration = duration
        self.is_buff = is_buff

    def tick(self):
        self.duration -= 1
        return self.duration > 0

    def __repr__(self):
        return f"{self.effect_type.name}(v={self.value}, d={self.duration})"

class Character:
    def __init__(self, name, stats, skills=None):
        self.name = name
        self.max_hp = stats["hp"]
        self.hp = stats["hp"]
        self.base_attack = stats["attack"]
        self.base_defense = stats["defense"]
        self.base_speed = stats["speed"]
        self.base_crit_chance = stats["crit_chance"]
        self.base_dodge = stats["dodge"]
        self.skills = skills or []
        self.cooldowns = {}
        self.buffs = []
        self.debuffs = []
        self.level = 1
        self.xp = 0
        self.xp_to_level = 50
        self.gold = 0
        self.is_alive = True

    @property
    def attack(self):
        val = self.base_attack
        for b in self.buffs:
            if b.effect_type == BuffType.ATTACK_UP:
                val += b.value
        for d in self.debuffs:
            if d.effect_type == DebuffType.ATTACK_DOWN:
                val -= d.value
        return max(1, val)

    @property
    def defense(self):
        val = self.base_defense
        for b in self.buffs:
            if b.effect_type == BuffType.DEFENSE_UP:
                val += b.value
        for d in self.debuffs:
            if d.effect_type == DebuffType.DEFENSE_DOWN:
                val -= d.value
        return max(0, val)

    @property
    def speed(self):
        val = self.base_speed
        for b in self.buffs:
            if b.effect_type == BuffType.SPEED_UP:
                val += b.value
        for d in self.debuffs:
            if d.effect_type == DebuffType.SPEED_DOWN:
                val -= d.value
        return max(1, val)

    @property
    def crit_chance(self):
        val = self.base_crit_chance
        for b in self.buffs:
            if b.effect_type == BuffType.CRIT_UP:
                val += b.value
        return min(100, val)

    @property
    def dodge_chance(self):
        val = self.base_dodge
        for b in self.buffs:
            if b.effect_type == BuffType.DODGE_UP:
                val += b.value
        return min(100, val)

    @property
    def reduce_damage(self):
        val = 0
        for b in self.buffs:
            if b.effect_type == BuffType.REDUCE_DAMAGE:
                val += b.value
        return val

    @property
    def shield(self):
        val = 0
        for b in self.buffs:
            if b.effect_type == BuffType.SHIELD:
                val += b.value
        return val

    @property
    def has_regen(self):
        for b in self.buffs:
            if b.effect_type == BuffType.REGEN:
                return b.value
        return 0

    @property
    def has_counter_attack(self):
        for b in self.buffs:
            if b.effect_type == BuffType.COUNTER_ATTACK:
                return b.value
        return 0

    def get_poison_damage(self):
        total = 0
        for d in self.debuffs:
            if d.effect_type == DebuffType.POISON:
                total += d.value
        return total

    def get_bleed_damage(self):
        total = 0
        for d in self.debuffs:
            if d.effect_type == DebuffType.BLEED:
                total += d.value
        return total

    def take_damage(self, raw_damage):
        import random
        if random.randint(1, 100) <= self.dodge_chance:
            return 0, True

        actual_damage = max(1, raw_damage - self.defense - self.reduce_damage)
        shield_absorbed = min(actual_damage, self.shield)
        actual_damage -= shield_absorbed
        self.hp -= actual_damage
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False
        return actual_damage + shield_absorbed, False

    def heal(self, amount):
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        if self.hp > 0:
            self.is_alive = True
        return self.hp - old_hp

    def apply_buff(self, buff_type, value, duration):
        for b in self.buffs:
            if b.effect_type == buff_type:
                b.value = max(b.value, value)
                b.duration = max(b.duration, duration)
                return
        self.buffs.append(StatusEffect(buff_type, value, duration, is_buff=True))

    def apply_debuff(self, debuff_type, value, duration):
        for d in self.debuffs:
            if d.effect_type == debuff_type:
                d.value = max(d.value, value)
                d.duration = max(d.duration, duration)
                return
        self.debuffs.append(StatusEffect(debuff_type, value, duration, is_buff=False))

    def tick_effects(self):
        self.buffs = [b for b in self.buffs if b.tick()]
        self.debuffs = [d for d in self.debuffs if d.tick()]

        poison = self.get_poison_damage()
        if poison > 0:
            self.hp -= poison
            if self.hp <= 0:
                self.hp = 0
                self.is_alive = False

        bleed = self.get_bleed_damage()
        if bleed > 0:
            self.hp -= bleed
            if self.hp <= 0:
                self.hp = 0
                self.is_alive = False

        regen = self.has_regen
        if regen > 0:
            self.heal(regen)

    def reduce_cooldowns(self):
        for skill_id in self.cooldowns:
            if self.cooldowns[skill_id] > 0:
                self.cooldowns[skill_id] -= 1

    def is_skill_ready(self, skill_id):
        return self.cooldowns.get(skill_id, 0) == 0

    def put_on_cooldown(self, skill_id, cooldown):
        self.cooldowns[skill_id] = cooldown

    def get_cooldown_with_reduction(self, skill_id):
        for skill in self.skills:
            if skill["id"] == skill_id:
                return skill.get("cooldown", 1)
        return 1

    def add_xp(self, amount):
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_to_level:
            self.xp -= self.xp_to_level
            self.level += 1
            self.xp_to_level = int(self.xp_to_level * 1.5)
            old_hp = self.max_hp
            old_atk = self.base_attack
            old_def = self.base_defense
            old_spd = self.base_speed
            self.level_up_stats()
            print(f"[LEVEL UP] {self.name} Lv {self.level - 1} -> Lv {self.level}")
            print(f"  HP: {old_hp} -> {self.max_hp}")
            print(f"  ATK: {old_atk} -> {self.base_attack}")
            print(f"  DEF: {old_def} -> {self.base_defense}")
            print(f"  SPD: {old_spd} -> {self.base_speed}")
            leveled = True
        return leveled

    def level_up_stats(self):
        self.max_hp += 5
        self.hp = min(self.hp + 5, self.max_hp)
        self.base_attack += 1
        self.base_defense += 1
        self.base_speed += 1

    def __repr__(self):
        return f"{self.name} (HP: {self.hp}/{self.max_hp})"
