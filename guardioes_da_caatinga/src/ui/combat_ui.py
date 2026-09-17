import pygame
import math
from config import (WHITE, BLACK, GRAY, DARK_GRAY, RED, GREEN, BLUE, YELLOW, BROWN,
                    CREAM, SCREEN_WIDTH, SCREEN_HEIGHT, NODE_COLORS)
from src.ui.components import draw_text, draw_bar
from src.ui.text import get_font

CARD_W, CARD_H = 185, 340
CARD_GAP = 200


class FloatingText:
    def __init__(self, text, x, y, color, duration=50, size=28):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.duration = duration
        self.max_duration = duration
        self.size = size

    def update(self):
        self.duration -= 1
        self.y -= 0.7
        return self.duration > 0

    def draw(self, surface):
        alpha = max(0, min(255, int(255 * (self.duration / self.max_duration))))
        text_surface = get_font(self.size).render(self.text, True, self.color)
        text_surface.set_alpha(alpha)
        surface.blit(text_surface, (self.x - text_surface.get_width() // 2, self.y))


class CombatUI:
    def __init__(self, combat_system):
        self.combat = combat_system
        self.floating_texts = []
        self.step_timer = 0
        self.step_delay = 20
        self.combat_speed = 1
        self.finished = False

    def reset(self):
        self.floating_texts = []
        self.step_timer = 0
        self.finished = False

    def update(self):
        self.floating_texts = [ft for ft in self.floating_texts if ft.update()]

        if not self.combat.combat_ended and not self.finished:
            self.step_timer += 1
            if self.step_timer >= self.step_delay:
                self.step_timer = 0
                events = self.combat.step_combat()
                self._process_events(events)
                if self.combat.combat_ended:
                    self.finished = True

    def _process_events(self, events):
        for evt in events:
            target_pos = self._get_unit_center(evt.target_name)
            if not target_pos:
                continue

            if evt.event_type == "damage":
                color = YELLOW if evt.is_crit else RED
                size = 34 if evt.is_crit else 28
                text = f"-{evt.value}"
                if evt.is_crit:
                    text = f"CRIT! -{evt.value}"
                self.floating_texts.append(FloatingText(text, target_pos[0], target_pos[1] - 30, color, size=size))
            elif evt.event_type == "heal":
                self.floating_texts.append(FloatingText(f"+{evt.value}", target_pos[0], target_pos[1] - 30, GREEN, size=28))
            elif evt.event_type == "dodge":
                self.floating_texts.append(FloatingText("ESQUIVA!", target_pos[0], target_pos[1] - 30, GRAY, size=24))
            elif evt.event_type == "buff":
                self.floating_texts.append(FloatingText(f"BUFF +{evt.value}", target_pos[0], target_pos[1] - 30, BLUE, size=22))
            elif evt.event_type == "debuff":
                self.floating_texts.append(FloatingText(f"DEBUFF -{evt.value}", target_pos[0], target_pos[1] - 30, (150, 50, 200), size=22))

    def _get_unit_center(self, name):
        n_party = len(self.combat.party)
        n_enemies = len(self.combat.enemies)
        party_total_w = n_party * 200
        enemies_total_w = n_enemies * 200
        party_start = (SCREEN_WIDTH // 2 - party_total_w) // 2
        enemies_start = SCREEN_WIDTH // 2 + (SCREEN_WIDTH - enemies_total_w) // 2

        for i, unit in enumerate(self.combat.party):
            if unit.name == name:
                x = party_start + i * 200
                return (x + 100, 280)
        for i, unit in enumerate(self.combat.enemies):
            if unit.name == name:
                x = enemies_start + i * 200
                return (x + 100, 280)
        return None

    def draw(self, surface, assets=None):
        if assets:
            assets.draw_background(surface, "combat")
        else:
            surface.fill((15, 12, 25))

        self._draw_turn_bar(surface)
        self._draw_party(surface, assets)
        self._draw_enemies(surface, assets)
        self._draw_combat_log(surface)
        self._draw_floating_texts(surface)
        self._draw_controls(surface)

    def _draw_turn_bar(self, surface):
        bar_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 42)
        overlay = pygame.Surface((SCREEN_WIDTH, 42), pygame.SRCALPHA)
        overlay.fill((15, 12, 25, 200))
        surface.blit(overlay, (0, 0))
        pygame.draw.line(surface, GRAY, (0, 42), (SCREEN_WIDTH, 42))

        current = self.combat.get_current_unit()
        if current and not self.combat.combat_ended:
            side = "ALIADO" if current in self.combat.party else "INIMIGO"
            side_color = GREEN if current in self.combat.party else RED
            draw_text(surface, f"Turno {self.combat.turn_count}", (20, 11), font_size=22, color=CREAM)
            draw_text(surface, f"Vez de: {current.name}", (200, 11), font_size=22, color=WHITE)
            draw_text(surface, f"[{side}]", (460, 11), font_size=22, color=side_color)
        elif self.combat.combat_ended:
            result = "VITORIA!" if self.combat.player_won else "DERROTA..."
            color = GREEN if self.combat.player_won else RED
            draw_text(surface, result, (SCREEN_WIDTH // 2, 11), font_size=26, color=color, center=True)

    def _draw_party(self, surface, assets=None):
        n = len(self.combat.party)
        total_w = n * 200
        start_x = (SCREEN_WIDTH // 2 - total_w) // 2

        draw_text(surface, "SEU TIME", (start_x + total_w // 2, 55), font_size=24, color=GREEN, center=True)

        for i, unit in enumerate(self.combat.party):
            x = start_x + i * 200
            y = 75
            self._draw_character_card(surface, unit, x, y, is_ally=True, assets=assets)

    def _draw_enemies(self, surface, assets=None):
        n = len(self.combat.enemies)
        total_w = n * 200
        start_x = SCREEN_WIDTH // 2 + (SCREEN_WIDTH // 2 - total_w) // 2

        draw_text(surface, "INIMIGOS", (start_x + total_w // 2, 55), font_size=24, color=RED, center=True)

        for i, unit in enumerate(self.combat.enemies):
            x = start_x + i * 200
            y = 75
            self._draw_character_card(surface, unit, x, y, is_ally=False, assets=assets)

    def _draw_character_card(self, surface, unit, x, y, is_ally=True, assets=None):
        card_w, card_h = 185, 340
        is_active = self.combat.get_current_unit() == unit

        if not unit.is_alive:
            card_color = (25, 22, 30) if is_ally else (30, 22, 22)
            border_color = (50, 45, 55) if is_ally else (55, 40, 40)
        elif is_active:
            card_color = (40, 65, 40) if is_ally else (65, 35, 35)
            border_color = YELLOW
        else:
            card_color = (32, 48, 32) if is_ally else (50, 30, 30)
            border_color = (100, 160, 100) if is_ally else (160, 80, 80)

        rect = pygame.Rect(x, y, card_w, card_h)
        shadow_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 80), (4, 4, card_w, card_h), border_radius=10)
        surface.blit(shadow_surf, (x, y))

        pygame.draw.rect(surface, card_color, rect, border_radius=10)
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=10)

        if is_active and unit.is_alive:
            glow_surf = pygame.Surface((card_w + 4, card_h + 4), pygame.SRCALPHA)
            glow_color = (255, 255, 100, 35) if is_ally else (255, 100, 100, 35)
            pygame.draw.rect(glow_surf, glow_color, (0, 0, card_w + 4, card_h + 4), border_radius=11)
            surface.blit(glow_surf, (x - 2, y - 2))

        sprite_x = x + card_w // 2
        sprite_y = y + 70

        if assets and unit.is_alive:
            entity_id = getattr(unit, 'animal_id', None) or getattr(unit, 'enemy_id', None)
            if entity_id:
                is_enemy = not is_ally
                sprite = assets.get_sprite(entity_id, is_enemy=is_enemy, max_width=130, max_height=100,
                                           flip_horizontal=False)
                if sprite:
                    sprite_rect = sprite.get_rect(center=(sprite_x, sprite_y))
                    surface.blit(sprite, sprite_rect)

        name = unit.name
        if hasattr(unit, 'is_boss') and unit.is_boss:
            name = f"* {name}"
        elif hasattr(unit, 'is_elite') and unit.is_elite:
            name = f"<> {name}"

        draw_text(surface, name, (sprite_x, y + 125), font_size=18, color=WHITE, center=True)
        draw_text(surface, f"Lv.{unit.level}", (sprite_x, y + 145), font_size=15, color=YELLOW, center=True)

        bar_x = x + 12
        bar_y = y + 165
        bar_w = card_w - 24
        hp_color = GREEN if unit.hp > unit.max_hp * 0.5 else (YELLOW if unit.hp > unit.max_hp * 0.25 else RED)
        draw_bar(surface, bar_x, bar_y, bar_w, 16, unit.hp, unit.max_hp, hp_color)

        stats_y = bar_y + 22
        draw_text(surface, f"ATK:{unit.attack}", (bar_x, stats_y), font_size=13, color=CREAM)
        draw_text(surface, f"DEF:{unit.defense}", (bar_x + 75, stats_y), font_size=13, color=CREAM)
        draw_text(surface, f"SPD:{unit.speed}", (bar_x, stats_y + 16), font_size=13, color=CREAM)

        crit_val = getattr(unit, 'crit_chance', 0)
        draw_text(surface, f"CRT:{crit_val}%", (bar_x + 75, stats_y + 16), font_size=13, color=CREAM)

        if unit.shield > 0:
            draw_text(surface, f"ESC:{unit.shield}", (bar_x, stats_y + 32), font_size=13, color=BLUE)

        self._draw_effects(surface, unit, bar_x, stats_y + 48)

        if not unit.is_alive:
            draw_text(surface, "DERROTADO", (sprite_x, y + 180), font_size=22, color=RED, center=True)

    def _draw_effects(self, surface, unit, x, y):
        y_off = 0
        for buff in unit.buffs[:3]:
            draw_text(surface, f"+{buff.effect_type.name[:6]}", (x, y + y_off), font_size=12, color=GREEN)
            draw_text(surface, f"({buff.duration})", (x + 80, y + y_off), font_size=12, color=(100, 200, 100))
            y_off += 14
        for debuff in unit.debuffs[:3]:
            draw_text(surface, f"-{debuff.effect_type.name[:6]}", (x, y + y_off), font_size=12, color=RED)
            draw_text(surface, f"({debuff.duration})", (x + 80, y + y_off), font_size=12, color=(200, 100, 100))
            y_off += 14

    def _draw_combat_log(self, surface):
        log_w, log_h = 410, 190
        log_x = SCREEN_WIDTH - log_w - 15
        log_y = SCREEN_HEIGHT - log_h - 60

        log_bg = pygame.Surface((log_w, log_h), pygame.SRCALPHA)
        pygame.draw.rect(log_bg, (10, 8, 18, 210), (0, 0, log_w, log_h), border_radius=8)
        surface.blit(log_bg, (log_x, log_y))
        pygame.draw.rect(surface, GRAY, (log_x, log_y, log_w, log_h), 1, border_radius=8)

        draw_text(surface, "Log de Combate", (log_x + 10, log_y + 6), font_size=17, color=YELLOW)

        log_lines = self.combat.get_log(9)
        for i, line in enumerate(log_lines):
            draw_text(surface, line, (log_x + 10, log_y + 28 + i * 18), font_size=14, color=CREAM)

    def _draw_floating_texts(self, surface):
        for ft in self.floating_texts:
            ft.draw(surface)

    def _draw_controls(self, surface):
        ctrl_y = SCREEN_HEIGHT - 22
        if self.combat.combat_ended:
            draw_text(surface, "Clique para continuar", (SCREEN_WIDTH // 2, ctrl_y),
                      font_size=20, color=YELLOW, center=True)
        else:
            draw_text(surface, "Combate Automatico - Aguarde a batalha",
                      (SCREEN_WIDTH // 2, ctrl_y), font_size=18, color=GRAY, center=True)
