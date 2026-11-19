"""Inventory overview available from the journey map."""

import pygame

from config import (GRAY, GREEN, RED, YELLOW, SCREEN_HEIGHT, load_animals,
                    load_json, load_upgrades)
from src.consumables import (EFFECT_SHORT_NAMES, ITEM_EFFECTS, ITEM_NAMES,
                             POTION_KEYS, can_target, get_active_potion_effects,
                             get_limit, invalid_target_reason)
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

        # Individual-use selection state. Select one item, then click the
        # animal that should receive it. The item stays selected after each
        # use until the player clicks Cancelar (or the item button again).
        self.selected_item = None
        self.selected_animal_id = None
        self.hover_animal_id = None
        self.hover_cancel = False
        self._use_locked = False
        self.cancel_button = pygame.Rect(1057, 642, 148, 38)

    def _build_potion_buttons(self):
        panel = pygame.Rect(665, 420, 560, 215)
        rects = {}
        for index, key in enumerate(POTION_KEYS):
            y = panel.y + 46 + index * 24
            rects[key] = pygame.Rect(panel.right - 100, y, 80, 22)
        return rects

    def _animal_card_rect(self, index):
        panel = pygame.Rect(55, 105, 590, 530)
        return pygame.Rect(panel.x + 15, panel.y + 56 + index * 152,
                           panel.w - 30, 140)

    def _cancel_selection(self):
        self.selected_item = None
        self.selected_animal_id = None

    def set_feedback(self, message, error=False):
        self.feedback = message
        self.feedback_error = error
        self.feedback_until = pygame.time.get_ticks() + 1800
        # The game calls this after processing a confirmed use. Releasing the
        # lock only here prevents a repeated click from consuming twice.
        self._use_locked = False

    # ------------------------------------------------------------- events
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.selected_item is not None:
                self._cancel_selection()
                return None
            return "back"

        if self._use_locked:
            return None

        if event.type == pygame.MOUSEMOTION:
            mouse_pos = getattr(event, "pos", None) or get_mouse_pos()
            self.hover_back = self.back_button.collidepoint(mouse_pos)
            self.hover_potion = None
            for key, rect in self.potion_buttons.items():
                if rect.collidepoint(mouse_pos):
                    self.hover_potion = key
                    break
            self.hover_animal_id = None
            if self.selected_item is not None:
                for index, animal in enumerate(self.party[:3]):
                    if self._animal_card_rect(index).collidepoint(mouse_pos):
                        self.hover_animal_id = animal.animal_id
                        break
            self.hover_cancel = (self.selected_item is not None
                                 and self.cancel_button.collidepoint(mouse_pos))
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = getattr(event, "pos", None) or get_mouse_pos()
            if self.back_button.collidepoint(mouse_pos):
                return "back"

            if self.selected_item is not None:
                if self.cancel_button.collidepoint(mouse_pos):
                    self._cancel_selection()
                    return None

                for index, animal in enumerate(self.party[:3]):
                    if not self._animal_card_rect(index).collidepoint(mouse_pos):
                        continue
                    if can_target(self.selected_item, animal):
                        return self._use_on_animal(animal)
                    self.set_feedback(
                        invalid_target_reason(self.selected_item),
                        error=True)
                    return None

            for key, rect in self.potion_buttons.items():
                if rect.collidepoint(mouse_pos):
                    if key == self.selected_item:
                        self._cancel_selection()
                        return None
                    self._start_selection(key)
                    return None
        return None

    def _start_selection(self, key):
        if not self._can_use_potion(key):
            counts = self._potion_counts()
            if counts.get(key, 0) <= 0:
                self.set_feedback("Sem item disponivel.", error=True)
            elif not self.party:
                self.set_feedback("Nenhum animal na equipe.", error=True)
            else:
                self.set_feedback(invalid_target_reason(key), error=True)
            return
        self.selected_item = key
        self.selected_animal_id = None
        self.feedback = ""

    def _use_on_animal(self, animal):
        """Consume the selected item directly on the clicked animal.

        The selected item is intentionally kept active after the use so the
        player can use it again on another animal. Only Cancelar clears it.
        """
        if (self._use_locked or self.selected_item is None
                or not can_target(self.selected_item, animal)):
            return None
        key = self.selected_item
        if self._potion_counts().get(key, 0) <= 0:
            self.set_feedback("Sem item disponivel.", error=True)
            return None
        animal_id = animal.animal_id
        self.selected_animal_id = animal_id
        # Lock before returning; Game unlocks through set_feedback after the
        # effect and inventory quantities have been updated. The selection
        # itself is not cleared here.
        self._use_locked = True
        return ("use_potion", key, animal_id)

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
        self._draw_selection_bar(surface)

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
        if self.selected_item is not None:
            draw_text_right(
                surface, "Escolha 1 animal",
                (panel.right - 20, panel.y + 22),
                font_size=16, color=SERTAO_GOLD)

        if not self.party:
            draw_text(surface, "Nenhum animal na equipe.",
                      (panel.centerx, panel.centery), font_size=20,
                      color=GRAY, center=True)
            return

        card_h = 140
        gap = 12
        y = panel.y + 56
        for index, animal in enumerate(self.party[:3]):
            self._draw_animal_card(surface, animal, panel.x + 15, y,
                                   panel.w - 30, card_h, index=index)
            y += card_h + gap

    def _draw_animal_card(self, surface, animal, x, y, w, h, index=None):
        card = pygame.Rect(x, y, w, h)
        draw_sertao_panel(surface, card.x, card.y, card.w, card.h,
                          border_color=SERTAO_LIGHT, alpha=200)

        if self.selected_item is not None:
            eligible = can_target(self.selected_item, animal)
            hovered = animal.animal_id == self.hover_animal_id
            if eligible:
                width = 3 if hovered else 2
                pygame.draw.rect(surface, SERTAO_GOLD, card, width,
                                 border_radius=10)
                if hovered:
                    draw_text_right(surface, "ESCOLHER",
                                    (card.right - 14, card.bottom - 24),
                                    font_size=12, color=SERTAO_GOLD)

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

        effects = get_active_potion_effects(animal)
        if effects:
            parts = []
            for key, value, turns in effects:
                label = EFFECT_SHORT_NAMES.get(key, key.upper())
                suffix = "turno" if turns == 1 else "turnos"
                parts.append("{} +{} ({} {})".format(
                    label, value, turns, suffix))
            draw_text(surface, "Efeitos: " + "   ".join(parts),
                      (text_x, card.y + 118), font_size=11,
                      color=SERTAO_GOLD)

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
        x = panel.x + 20
        for index, key in enumerate(POTION_KEYS):
            y = panel.y + 46 + index * 24
            qty = counts.get(key, 0)
            limit = get_limit(key)
            enabled = self._can_use_potion(key)
            label_color = SERTAO_CREAM if qty > 0 else GRAY
            if qty >= limit:
                label_color = RED
            draw_text(surface, "{} {}/{}".format(ITEM_NAMES[key], qty, limit),
                      (x, y + 2), font_size=14, color=label_color)
            draw_text(surface, ITEM_EFFECTS[key], (x + 190, y + 4),
                      font_size=10, color=SERTAO_LIGHT)
            label = "Cancelar" if key == self.selected_item else "Usar"
            draw_sertao_button(
                surface, self.potion_buttons[key], label,
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

    def _draw_selection_bar(self, surface):
        if self.selected_item is None:
            return
        status = "Clique em um animal destacado para usar {}.".format(
            ITEM_NAMES[self.selected_item])
        draw_text(surface, status, (665, 651), font_size=13,
                  color=SERTAO_CREAM)
        draw_text(surface, "Item selecionado ate Cancelar.",
                  (665, 668), font_size=11, color=SERTAO_LIGHT)
        draw_sertao_button(
            surface, self.cancel_button, "Cancelar",
            is_hovered=self.hover_cancel, font_size=15)

    # ------------------------------------------------------------- helpers
    def _can_use_potion(self, key):
        if not self.party:
            return False
        counts = self._potion_counts()
        if counts.get(key, 0) <= 0:
            return False
        return any(can_target(key, animal) for animal in self.party[:3])

    def _potion_counts(self):
        counts = {key: 0 for key in POTION_KEYS}
        potions = self.save_data.get("potions")
        if isinstance(potions, dict):
            for key in POTION_KEYS:
                try:
                    counts[key] = max(0, int(potions.get(key) or 0))
                except (TypeError, ValueError):
                    counts[key] = 0
            return {key: min(get_limit(key), value)
                    for key, value in counts.items()}

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
        return {key: min(get_limit(key), value)
                for key, value in counts.items()}

    def _owned_relics(self):
        owned = (self.save_data.get("relics")
                 or self.save_data.get("relics_owned") or [])
        if isinstance(owned, dict):
            return [key for key, value in owned.items() if value]
        if isinstance(owned, list):
            return list(owned)
        return []
