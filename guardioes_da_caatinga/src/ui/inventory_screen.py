"""Inventory overview available from the journey map."""

import pygame

from config import (GRAY, GREEN, RED, YELLOW, SCREEN_HEIGHT, load_animals,
                    load_json, load_upgrades)
from src.ui.components import draw_bar
from src.ui.layout import (CENTER_X, SERTAO_DARK, SERTAO_CREAM, SERTAO_GOLD,
                           SERTAO_LIGHT, draw_sertao_panel,
                           draw_sertao_button, get_mouse_pos, make_back_button)
from src.ui.text import draw_text, draw_text_right, wrap_text


def _load_relics():
    try:
        return load_json("relics.json").get("relics", {})
    except Exception:
        return {}


class InventoryScreen:
    """Shows the party, permanent upgrades, potions and relics.

    The journey map opens this screen. Everything is read from the current
    save/party, so no extra state is created.
    """

    def __init__(self, save_data=None, assets=None, party=None):
        self.save_data = save_data or {}
        self.assets = assets
        self.party = party or []
        self.animals = load_animals()
        self.upgrades = load_upgrades()
        self.relics = _load_relics()
        self.back_button = make_back_button()
        self.hover_back = False
        self.potion_buttons = self._build_potion_buttons()
        self.hover_potion = None
        self.feedback = ""
        self.feedback_error = False
        self.feedback_until = 0

    def _build_potion_buttons(self):
        panel = pygame.Rect(665, 420, 560, 215)
        rects = {}
        for index, key in enumerate(("health", "defense", "attack", "revive")):
            y = panel.y + 46 + index * 24
            rects[key] = pygame.Rect(panel.right - 100, y, 80, 22)
        return rects

    def set_feedback(self, message, error=False):
        self.feedback = message
        self.feedback_error = error
        self.feedback_until = pygame.time.get_ticks() + 1800

    # ------------------------------------------------------------- events
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "back"

        if event.type == pygame.MOUSEMOTION:
            mouse_pos = getattr(event, "pos", None) or get_mouse_pos()
            self.hover_back = self.back_button.collidepoint(mouse_pos)
            self.hover_potion = None
            for key, rect in self.potion_buttons.items():
                if rect.collidepoint(mouse_pos):
                    self.hover_potion = key
                    break
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = getattr(event, "pos", None) or get_mouse_pos()
            if self.back_button.collidepoint(mouse_pos):
                return "back"
            for key, rect in self.potion_buttons.items():
                if rect.collidepoint(mouse_pos):
                    if self._can_use_potion(key):
                        return ("use_potion", key)
                    counts = self._potion_counts()
                    if counts.get(key, 0) <= 0:
                        self.set_feedback("Sem item disponivel.", error=True)
                    elif key == "revive":
                        self.set_feedback(
                            "Nenhum animal caido para reanimar.", error=True)
                    else:
                        self.set_feedback("Vida ja esta cheia.", error=True)
                    return None
        return None

    # --------------------------------------------------------------- draw
    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "main_menu")
        else:
            surface.fill(SERTAO_DARK)

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 125))
        surface.blit(overlay, (0, 0))

        draw_text(surface, "INVENTARIO", (CENTER_X, 32),
                  font_size=44, color=SERTAO_GOLD, center=True)
        draw_text(surface, "Equipe, melhorias, pocoes e reliquias da jornada",
                  (CENTER_X, 74), font_size=17, color=SERTAO_LIGHT, center=True)
        pygame.draw.line(surface, SERTAO_GOLD, (CENTER_X - 190, 90),
                         (CENTER_X + 190, 90), 2)

        self._draw_party_panel(surface)
        self._draw_upgrades_panel(surface)
        self._draw_items_panel(surface)

        draw_sertao_button(surface, self.back_button, "Voltar",
                           is_hovered=self.hover_back, font_size=22)

        if self.feedback and pygame.time.get_ticks() < self.feedback_until:
            color = RED if self.feedback_error else GREEN
            draw_text(surface, self.feedback, (CENTER_X, SCREEN_HEIGHT - 30),
                      font_size=18, color=color, center=True)

    def _draw_party_panel(self, surface):
        panel = pygame.Rect(55, 105, 590, 530)
        draw_sertao_panel(surface, panel.x, panel.y, panel.w, panel.h)
        draw_text(surface, "EQUIPE", (panel.x + 20, panel.y + 16),
                  font_size=24, color=SERTAO_GOLD)

        if not self.party:
            draw_text(surface, "Nenhum animal na equipe.",
                      (panel.centerx, panel.centery), font_size=20,
                      color=GRAY, center=True)
            return

        card_h = 140
        gap = 12
        y = panel.y + 56
        for animal in self.party[:3]:
            self._draw_animal_card(surface, animal, panel.x + 15, y,
                                   panel.w - 30, card_h)
            y += card_h + gap

    def _draw_animal_card(self, surface, animal, x, y, w, h):
        card = pygame.Rect(x, y, w, h)
        draw_sertao_panel(surface, card.x, card.y, card.w, card.h,
                          border_color=SERTAO_LIGHT, alpha=200)

        sprite = None
        if self.assets:
            sprite = self.assets.get_animal_sprite(
                animal.animal_id,
                evolution_stage=getattr(animal, "evolution_stage", 0),
                max_width=96, max_height=96)
        if sprite:
            surface.blit(sprite, sprite.get_rect(
                center=(card.x + 60, card.centery)))
        else:
            pygame.draw.rect(surface, (40, 60, 80),
                             (card.x + 14, card.y + 22, 92, 96),
                             border_radius=8)
            draw_text(surface, "?", (card.x + 60, card.centery),
                      font_size=36, color=SERTAO_CREAM, center=True)

        text_x = card.x + 120
        draw_text(surface, "{}  Lv.{}".format(animal.name, animal.level),
                  (text_x, card.y + 14), font_size=22, color=SERTAO_CREAM)

        stage = getattr(animal, "evolution_stage", 0)
        stage_label = "Base" if stage <= 0 else "Evolucao {}".format(stage)
        draw_text(surface, stage_label, (text_x, card.y + 42),
                  font_size=14, color=SERTAO_LIGHT)

        hp_color = (GREEN if animal.hp > animal.max_hp * 0.5
                    else (YELLOW if animal.hp > animal.max_hp * 0.25 else RED))
        draw_bar(surface, text_x, card.y + 66, 190, 18,
                 animal.hp, animal.max_hp, hp_color)

        stats = "ATQ {}   DEF {}   VEL {}".format(
            animal.attack, animal.defense, animal.speed)
        draw_text(surface, stats, (text_x, card.y + 96),
                  font_size=17, color=SERTAO_CREAM)

        if not animal.is_alive or animal.hp <= 0:
            draw_text_right(surface, "CAIDO",
                            (card.right - 14, card.y + 16),
                            font_size=18, color=RED)

    def _draw_upgrades_panel(self, surface):
        panel = pygame.Rect(665, 105, 560, 300)
        draw_sertao_panel(surface, panel.x, panel.y, panel.w, panel.h)
        draw_text(surface, "MELHORIAS PERMANENTES",
                  (panel.x + 20, panel.y + 16),
                  font_size=22, color=SERTAO_GOLD)

        permanent = self.save_data.get("permanent_upgrades") or {}
        x = panel.x + 20
        y = panel.y + 52
        max_width = panel.w - 40
        line_h = 17

        if not self.party:
            draw_text(surface, "Sem animais para exibir.",
                      (x, y), font_size=16, color=GRAY)
            return

        for animal in self.party[:3]:
            owned_ids = permanent.get(animal.animal_id, [])
            names = []
            for upgrade_id in owned_ids:
                data = self.upgrades.get(upgrade_id, {})
                names.append(data.get("name", upgrade_id.replace("_", " ")))

            header = "{} ({})".format(animal.name, len(names))
            draw_text(surface, header, (x, y), font_size=17,
                      color=SERTAO_CREAM)
            y += 20

            if names:
                lines = wrap_text(", ".join(names), 14, max_width)
                for line in lines[:3]:
                    draw_text(surface, line, (x + 12, y), font_size=14,
                              color=SERTAO_LIGHT)
                    y += line_h
            else:
                draw_text(surface, "Nenhuma melhoria permanente.",
                          (x + 12, y), font_size=14, color=GRAY)
                y += line_h
            y += 6

            if y > panel.bottom - 20:
                break

    def _draw_items_panel(self, surface):
        panel = pygame.Rect(665, 420, 560, 215)
        draw_sertao_panel(surface, panel.x, panel.y, panel.w, panel.h)
        draw_text(surface, "ITENS E RELIQUIAS",
                  (panel.x + 20, panel.y + 16),
                  font_size=22, color=SERTAO_GOLD)

        gold = self.party[0].gold if self.party else 0
        draw_text_right(surface, "Gold: {}".format(gold),
                        (panel.right - 20, panel.y + 18),
                        font_size=18, color=SERTAO_GOLD)

        counts = self._potion_counts()
        labels = {
            "health": "Pocao de Cura",
            "defense": "Pocao de Defesa",
            "attack": "Pocao de Ataque",
            "revive": "Cruz Dourada",
        }
        effects = {
            "health": "cura 30 HP",
            "defense": "+5 DEF / 3 turnos",
            "attack": "+3 ATK / 3 turnos",
            "revive": "reanima os caidos",
        }
        x = panel.x + 20
        for index, key in enumerate(("health", "defense", "attack", "revive")):
            y = panel.y + 46 + index * 24
            qty = counts.get(key, 0)
            enabled = self._can_use_potion(key)
            label_color = SERTAO_CREAM if qty > 0 else GRAY
            draw_text(surface, "{}  x{}".format(labels[key], qty),
                      (x, y + 2), font_size=15, color=label_color)
            draw_text(surface, effects[key], (x + 175, y + 4),
                      font_size=11, color=SERTAO_LIGHT)
            draw_sertao_button(
                surface, self.potion_buttons[key], "Usar",
                is_hovered=(self.hover_potion == key and enabled),
                enabled=enabled, font_size=13)

        y = panel.y + 148
        owned = self._owned_relics()
        if owned:
            draw_text(surface, "Reliquias:", (x, y), font_size=16,
                      color=SERTAO_CREAM)
            y += 20
            for relic_id in owned[:3]:
                data = self.relics.get(relic_id, {})
                name = data.get("name", relic_id.replace("_", " "))
                draw_text(surface, "- {}".format(name), (x + 12, y),
                          font_size=15, color=SERTAO_LIGHT)
                y += 17
        else:
            draw_text(surface, "Nenhuma reliquia encontrada.",
                      (x, y), font_size=15, color=GRAY)

    # ------------------------------------------------------------- helpers
    def _can_use_potion(self, key):
        if not self.party:
            return False
        counts = self._potion_counts()
        if counts.get(key, 0) <= 0:
            return False
        if key == "health":
            return any(a.is_alive and a.hp < a.max_hp for a in self.party)
        if key == "revive":
            return any(not a.is_alive or a.hp <= 0 for a in self.party)
        return True

    def _potion_counts(self):
        counts = {"health": 0, "defense": 0, "attack": 0, "revive": 0}
        potions = self.save_data.get("potions")
        if isinstance(potions, dict):
            for key in counts:
                try:
                    counts[key] = max(0, int(potions.get(key) or 0))
                except (TypeError, ValueError):
                    counts[key] = 0
            return counts

        inv = (self.save_data.get("inventory")
               or self.save_data.get("potions") or {})
        if isinstance(inv, dict):
            counts["health"] = int(
                inv.get("health_potion") or inv.get("health")
                or inv.get("pocao_vida") or 0)
            counts["defense"] = int(
                inv.get("defense_potion") or inv.get("defense")
                or inv.get("pocao_defesa") or 0)
            counts["attack"] = int(
                inv.get("attack_potion") or inv.get("attack")
                or inv.get("pocao_ataque") or inv.get("strength_potion") or 0)
            counts["revive"] = int(
                inv.get("revive") or inv.get("cruz_dourada")
                or inv.get("revive_potion") or 0)
        elif isinstance(inv, list):
            for item in inv:
                if not isinstance(item, dict):
                    continue
                item_id = (item.get("id") or item.get("type")
                           or item.get("name") or "").lower()
                qty = int(item.get("quantity") or item.get("count") or 1)
                if "vida" in item_id or "heal" in item_id or item_id == "health":
                    counts["health"] += qty
                elif "def" in item_id:
                    counts["defense"] += qty
                elif "ataque" in item_id or "attack" in item_id:
                    counts["attack"] += qty
                elif "revive" in item_id or "cruz" in item_id:
                    counts["revive"] += qty
        return counts

    def _owned_relics(self):
        owned = (self.save_data.get("relics")
                 or self.save_data.get("relics_owned") or [])
        if isinstance(owned, dict):
            return [key for key, value in owned.items() if value]
        if isinstance(owned, list):
            return list(owned)
        return []
