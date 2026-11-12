import pygame
from config import (WHITE, BLACK, GRAY, DARK_GRAY, RED, GREEN, BLUE, YELLOW, BROWN,
                    CREAM, ORANGE, PURPLE, SCREEN_WIDTH, SCREEN_HEIGHT,
                    DARK_BROWN, GOLD, load_animals, load_biomes,
                    load_enemies, load_upgrades)
from src.ui.layout import (UILayout, LayoutArea, draw_sertao_panel, draw_sertao_button,
                           draw_text, CENTER_X, CENTER_Y, SAFE_MARGIN,
                           SERTAO_DARK, SERTAO_PANEL, SERTAO_BORDER, SERTAO_LIGHT,
                           SERTAO_CREAM, SERTAO_GOLD, SERTAO_RED, SERTAO_GREEN,
                           get_mouse_pos, get_button_metrics,
                           make_centered_tabs, make_back_button)
from src.ui.text import (get_font, wrap_text_chars, wrap_text, draw_text_centered,
                         draw_text_block_colored, draw_text_right, draw_text_left)
from src.ui.components import draw_bar

ANIMAL_EMOJIS = {
    "tatu_bola": "\U0001f994",
    "lobo_guara": "\U0001f98a",
    "arara_azul": "\U0001f426",
    "tamandua_bandeira": "\U0001f41c",
    "capivara": "\U0001f9ab",
    "onca_pintada": "\U0001f406",
}

ENEMY_EMOJIS = {
    "brasa": "\U0001f525",
    "chamas": "\U0001f4a5",
    "espirito_de_fogo": "\U0001f3df",
    "furacao": "\U0001f32a",
    "lobo_de_fogo": "\U0001f43a",
    "lobo_alfa_de_fogo": "\U0001f43a",
    "vendaval_de_fogo": "\U0001f32c",
}

RARITY_COLORS = {"Comum": GRAY, "Raro": BLUE, "\u00c9pico": PURPLE, "Lend\u00e1rio": SERTAO_GOLD}


class MainMenu:
    """The game's front page: only save-independent options live here."""

    ENTRIES = [
        ("JOGAR", "play"),
        ("SOBRE", "how_to_play"),
        ("CONFIGURACOES", "settings"),
        ("SAIR", "quit"),
    ]

    BUTTON_WIDTH = 380
    BUTTON_GAP = 6
    COLUMN_CENTER_Y = 415
    # Actions drawn with the generic wooden style (no illustrated asset).
    FALLBACK_ACTIONS = set()

    def __init__(self, assets=None, achievement_manager=None):
        self.assets = assets
        self.achievement_manager = achievement_manager
        self.hover_index = -1
        self.layout = UILayout()
        self._hover_cache = {}
        self._build()

    def _build(self):
        self.metrics = get_button_metrics("menu")
        images = []
        heights = []
        for _label, action in self.ENTRIES:
            image = None
            if (self.assets is not None
                    and action not in self.FALLBACK_ACTIONS):
                image = self.assets.get_main_menu_button(
                    action, self.BUTTON_WIDTH)
            images.append(image)
            heights.append(image.get_height() if image is not None
                           else self.metrics.height)

        total = sum(heights) + self.BUTTON_GAP * (len(self.ENTRIES) - 1)
        y = self.COLUMN_CENTER_Y - total // 2

        self.buttons = []
        for (label, action), image, height in zip(
                self.ENTRIES, images, heights):
            width = image.get_width() if image is not None else self.metrics.width
            rect = pygame.Rect(CENTER_X - width // 2, y, width, height)
            self.buttons.append({
                "rect": rect,
                "label": label,
                "action": action,
                "image": image,
            })
            y += height + self.BUTTON_GAP

    def _hover_image(self, image):
        """Brighten a button image once and cache the result."""
        key = id(image)
        cached = self._hover_cache.get(key)
        if cached is None:
            cached = image.copy()
            cached.fill((42, 34, 16, 0), special_flags=pygame.BLEND_RGB_ADD)
            self._hover_cache[key] = cached
        return cached

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover_index = -1
            for i, b in enumerate(self.buttons):
                if b["rect"].collidepoint(event.pos):
                    self.hover_index = i
                    break
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for b in self.buttons:
                if b["rect"].collidepoint(event.pos):
                    return b["action"]
        return None

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "main_menu")
        else:
            surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 30))
        surface.blit(overlay, (0, 0))

        for i, b in enumerate(self.buttons):
            hovered = (self.hover_index == i)
            image = b["image"]
            if image is not None:
                if hovered:
                    image = self._hover_image(image)
                surface.blit(image, b["rect"].topleft)
                if hovered:
                    underline = pygame.Surface((b["rect"].w, 5),
                                               pygame.SRCALPHA)
                    pygame.draw.rect(
                        underline, (255, 214, 90, 200),
                        (b["rect"].w // 4, 0, b["rect"].w // 2, 3),
                        border_radius=2)
                    surface.blit(underline,
                                 (b["rect"].x, b["rect"].bottom - 5))
            else:
                draw_sertao_button(surface, b["rect"], b["label"],
                                   is_hovered=hovered,
                                   font_size=self.metrics.font_size)

        fv = get_font(18)
        footer_panel = pygame.Surface((300, 46), pygame.SRCALPHA)
        pygame.draw.rect(footer_panel, (10, 8, 5, 110),
                         (0, 0, 300, 46), border_radius=10)
        pygame.draw.rect(footer_panel, (150, 110, 50, 110),
                         (0, 0, 300, 46), 1, border_radius=10)
        surface.blit(footer_panel,
                     footer_panel.get_rect(
                         center=(CENTER_X, self.layout.footer.center_y)))
        if self.achievement_manager is not None:
            title = self.achievement_manager.current_title()
            ft = get_font(16)
            title_surf = ft.render(f"Titulo: {title}", True, SERTAO_GOLD)
            title_rect = title_surf.get_rect(
                center=(CENTER_X, self.layout.footer.center_y - 10))
            shadow = ft.render(f"Titulo: {title}", True, BLACK)
            surface.blit(shadow, title_rect.move(1, 2))
            surface.blit(title_surf, title_rect)
            vs = fv.render("Versao 1.0", True, SERTAO_CREAM)
            version_rect = vs.get_rect(
                center=(CENTER_X, self.layout.footer.center_y + 12))
            vs_shadow = fv.render("Versao 1.0", True, BLACK)
            surface.blit(vs_shadow, version_rect.move(1, 2))
            surface.blit(vs, version_rect)
        else:
            vs = fv.render("Versao 1.0", True, SERTAO_CREAM)
            version_rect = vs.get_rect(
                center=(CENTER_X, self.layout.footer.center_y))
            vs_shadow = fv.render("Versao 1.0", True, BLACK)
            surface.blit(vs_shadow, version_rect.move(1, 2))
            surface.blit(vs, version_rect)


class MatchMenu(MainMenu):
    """Internal menu of the selected save.

    It reuses the original main-menu artwork and button style, but every
    save-dependent feature is opened from here, after a slot has been chosen.
    """

    ENTRIES = [
        ("JOGAR", "play"),
        ("BESTIARIO", "bestiary"),
        ("ACAMPAMENTO", "acampamento"),
        ("CONQUISTAS", "achievements"),
        ("CONFIGURACOES", "settings"),
        ("SOBRE", "how_to_play"),
        ("SAIR", "leave_match"),
    ]

    BUTTON_WIDTH = 300
    BUTTON_GAP = 4
    COLUMN_CENTER_Y = 415

    def __init__(self, assets=None, achievement_manager=None, slot=None,
                 save_data=None):
        self.slot = slot
        self.save_data = save_data or {}
        super().__init__(assets, achievement_manager)
        self.back_button = pygame.Rect(SAFE_MARGIN, SCREEN_HEIGHT - 68, 190, 42)
        self.hover_back = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "back_to_saves"

        if event.type == pygame.MOUSEMOTION:
            self.hover_back = self.back_button.collidepoint(event.pos)

        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.back_button.collidepoint(event.pos)):
            return "back_to_saves"

        return super().handle_event(event)

    def _match_summary(self):
        biome_id = None
        run = self.save_data.get("run")
        if isinstance(run, dict):
            biome_id = run.get("current_biome")
        if not biome_id:
            unlocked = self.save_data.get("unlocked_biomes") or ["caatinga"]
            biome_id = unlocked[-1]
        biome = load_biomes().get(biome_id, {}).get("name", biome_id)
        run_active = bool(isinstance(run, dict) and run.get("map"))
        status = "Jornada em andamento" if run_active else "Aventura pronta"
        return "SAVE {}  |  {}  |  {}".format(
            self.slot or "-", biome, status)

    def draw(self, surface):
        super().draw(surface)

        summary = self._match_summary()
        panel = pygame.Rect(CENTER_X - 280, SCREEN_HEIGHT - 80, 560, 24)
        draw_sertao_panel(surface, panel.x, panel.y, panel.w, panel.h,
                          alpha=190)
        draw_text(surface, summary, (CENTER_X, panel.centery),
                  font_size=15, color=SERTAO_CREAM, center=True)

        hovered = self.back_button.collidepoint(get_mouse_pos())
        draw_sertao_button(surface, self.back_button, "SELECIONAR SAVE",
                           is_hovered=hovered, font_size=16)


class AnimalSelectScreen:
    """Team selection drawn on top of the supplied ``SeleçãoEquipe.png`` art.

    The six cards, names, roles, title and painted buttons come from the
    original image.  Only animal sprites, locked placeholders, selection
    feedback and the chosen-team row are rendered dynamically.
    """

    SOURCE_WIDTH = 1600
    SOURCE_HEIGHT = 900

    ANIMAL_ORDER = (
        "tatu_bola",
        "lobo_guara",
        "arara_azul",
        "tamandua_bandeira",
        "capivara",
        "onca_pintada",
    )

    # Card geometry measured in the original 1600x900 artwork.
    CARD_CENTERS_X = (152, 415, 673, 931, 1190, 1452)
    CARD_HALF_WIDTH = 115
    CARD_TOP = 265
    CARD_BOTTOM = 635
    SPRITE_CENTER_Y = 426
    SPRITE_BOX = 190

    TEAM_SLOT_CENTERS = ((560, 735), (808, 735), (1056, 735))
    CLEAR_SOURCE_RECT = (58, 720, 312, 116)
    CONFIRM_SOURCE_RECT = (1245, 720, 318, 116)

    def __init__(self, unlocked_animals=None, assets=None, save_data=None,
                 max_selection=3, reteam_mode=False):
        self.animals = load_animals()
        self.unlocked_animals = [
            aid for aid in (unlocked_animals or ["tatu_bola"]) if aid
        ]
        self.save_data = save_data or {}
        self.assets = assets
        self.max_selection = max_selection
        self.reteam_mode = reteam_mode
        self.selected = []
        self.hover_index = -1
        self.hover_clear = False
        self.hover_confirm = False
        self.message = ""
        self.message_error = False
        self.layout = UILayout()
        self._build_ui()

    # ------------------------------------------------------------- layout

    def _source_rect(self, x, y, w, h):
        sx = SCREEN_WIDTH / self.SOURCE_WIDTH
        sy = SCREEN_HEIGHT / self.SOURCE_HEIGHT
        return pygame.Rect(
            int(round(x * sx)), int(round(y * sy)),
            max(1, int(round(w * sx))), max(1, int(round(h * sy))))

    def _source_point(self, x, y):
        return (int(round(x * SCREEN_WIDTH / self.SOURCE_WIDTH)),
                int(round(y * SCREEN_HEIGHT / self.SOURCE_HEIGHT)))

    def _source_size(self, value):
        return max(1, int(round(
            value * SCREEN_HEIGHT / self.SOURCE_HEIGHT)))

    def _build_ui(self):
        animal_data = self.save_data.get("animal_data", {}) or {}
        self.cards = []
        self.card_by_id = {}

        for index, aid in enumerate(self.ANIMAL_ORDER):
            animal = self.animals.get(aid)
            if animal is None:
                continue
            center_x = self.CARD_CENTERS_X[index]
            card_rect = self._source_rect(
                center_x - self.CARD_HALF_WIDTH, self.CARD_TOP,
                self.CARD_HALF_WIDTH * 2,
                self.CARD_BOTTOM - self.CARD_TOP)
            sprite_rect = self._source_rect(
                center_x - self.SPRITE_BOX // 2,
                self.SPRITE_CENTER_Y - self.SPRITE_BOX // 2,
                self.SPRITE_BOX, self.SPRITE_BOX)
            info = animal_data.get(aid, {}) or {}
            saved_hp = info.get("hp")
            saved_alive = info.get("is_alive")
            if isinstance(saved_alive, bool):
                fallen = (not saved_alive) or (
                    isinstance(saved_hp, (int, float)) and saved_hp <= 0)
            else:
                fallen = isinstance(saved_hp, (int, float)) and saved_hp <= 0
            card = {
                "id": aid,
                "animal": animal,
                "rect": card_rect,
                "sprite_rect": sprite_rect,
                "unlocked": aid in self.unlocked_animals,
                "level": info.get("level", 1) or 1,
                "evolution_stage": info.get("evolution_stage", 0) or 0,
                "fallen": fallen,
            }
            self.cards.append(card)
            self.card_by_id[aid] = card

        self.clear_rect = self._source_rect(*self.CLEAR_SOURCE_RECT)
        self.confirm_rect = self._source_rect(*self.CONFIRM_SOURCE_RECT)
        self.back_button = pygame.Rect(12, 12, 44, 40)

    def set_selection(self, ids):
        """Preselect animals coming from the loaded save."""
        selected = []
        for aid in ids or []:
            if (aid in self.unlocked_animals and aid in self.animals
                    and aid not in selected):
                selected.append(aid)
        self.selected = selected[:self.max_selection]

    # -------------------------------------------------------------- events

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "back"

        if event.type == pygame.MOUSEMOTION:
            self.hover_index = -1
            for i, card in enumerate(self.cards):
                if card["rect"].collidepoint(event.pos) and card["unlocked"]:
                    self.hover_index = i
                    break
            self.hover_clear = self.clear_rect.collidepoint(event.pos)
            self.hover_confirm = self.confirm_rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_button.collidepoint(event.pos):
                return "back"

            for card in self.cards:
                if not card["rect"].collidepoint(event.pos):
                    continue
                if not card["unlocked"]:
                    self.message = "Este animal ainda nao foi desbloqueado."
                    self.message_error = True
                    return None
                aid = card["id"]
                if aid in self.selected:
                    self.selected.remove(aid)
                    self.message = ""
                elif len(self.selected) < self.max_selection:
                    self.selected.append(aid)
                    self.message = ""
                else:
                    self.message = "Equipe completa: maximo de {} animais.".format(
                        self.max_selection)
                    self.message_error = True
                    return ("toggle", aid)
                return ("toggle", aid)

            if self.clear_rect.collidepoint(event.pos):
                self.selected = []
                self.message = ""
                return ("clear",)

            if self.confirm_rect.collidepoint(event.pos):
                if not self.selected:
                    self.message = "Escolha pelo menos 1 animal para confirmar."
                    self.message_error = True
                    return None
                self.message = ""
                return "start"
        return None

    # ---------------------------------------------------------------- draw

    def draw(self, surface):
        if self.assets:
            # The supplied PNG has transparent cut-outs around the rounded UI,
            # so it is composited over the regular menu scenery.
            self.assets.draw_background(surface, "main_menu")
            self.assets.draw_background(surface, "animal_select")
        else:
            surface.fill(SERTAO_DARK)

        for i, card in enumerate(self.cards):
            self._draw_card(surface, card, i)

        self._draw_selected_team(surface)

        if self.message:
            draw_text(
                surface, self.message,
                self._source_point(800, 655),
                font_size=self._source_size(19),
                color=SERTAO_RED if self.message_error else SERTAO_GOLD,
                center=True)

        self._draw_hotspot(
            surface, self.clear_rect, self.hover_clear, enabled=True)
        self._draw_hotspot(
            surface, self.confirm_rect, self.hover_confirm,
            enabled=bool(self.selected))

        bh = self.back_button.collidepoint(get_mouse_pos())
        draw_sertao_button(surface, self.back_button, "<", bh, font_size=20)

    def _draw_card(self, surface, card, index):
        sprite_rect = card["sprite_rect"]
        selected = card["id"] in self.selected
        hovered = self.hover_index == index

        sprite = None
        if self.assets:
            if card["unlocked"]:
                sprite = self.assets.get_animal_sprite(
                    card["id"], evolution_stage=card["evolution_stage"],
                    max_width=sprite_rect.w, max_height=sprite_rect.h)
            else:
                sprite = self.assets.get_locked_animal_image(
                    sprite_rect.w, sprite_rect.h)

        if sprite is not None:
            surface.blit(sprite, sprite.get_rect(center=sprite_rect.center))
        elif card["unlocked"]:
            draw_text(surface, ANIMAL_EMOJIS.get(card["id"], "?"),
                      sprite_rect.center, font_size=self._source_size(48),
                      color=SERTAO_CREAM, center=True)
        else:
            draw_text(surface, "?", sprite_rect.center,
                      font_size=self._source_size(56),
                      color=SERTAO_CREAM, center=True)

        if card["unlocked"] and card.get("fallen"):
            shade = pygame.Surface(sprite_rect.size, pygame.SRCALPHA)
            shade.fill((20, 10, 8, 130))
            surface.blit(shade, sprite_rect.topleft)
            tag = pygame.Rect(0, 0, self._source_size(96),
                              self._source_size(26))
            tag.midbottom = (sprite_rect.centerx, sprite_rect.bottom - 6)
            pygame.draw.rect(surface, SERTAO_RED, tag, border_radius=6)
            draw_text(surface, "CAIDO", tag.center,
                      font_size=self._source_size(15),
                      color=SERTAO_CREAM, center=True)

        if card["unlocked"] and selected:
            pygame.draw.rect(surface, SERTAO_GOLD, sprite_rect, 3,
                             border_radius=10)
            badge = (sprite_rect.right - 12, sprite_rect.top + 12)
            pygame.draw.circle(surface, SERTAO_GOLD, badge, 12)
            draw_text(surface, "\u2713", badge, font_size=16,
                      color=SERTAO_DARK, center=True)
        elif card["unlocked"] and hovered:
            pygame.draw.rect(surface, SERTAO_LIGHT, sprite_rect, 2,
                             border_radius=10)

    def _draw_selected_team(self, surface):
        slots = self.selected[:len(self.TEAM_SLOT_CENTERS)]
        if not slots:
            draw_text(
                surface, "Escolha ate {} animais".format(self.max_selection),
                self._source_point(808, 750),
                font_size=self._source_size(22), color=SERTAO_CREAM,
                center=True)
            return

        for index, aid in enumerate(slots):
            card = self.card_by_id.get(aid)
            if card is None:
                continue
            center = self._source_point(*self.TEAM_SLOT_CENTERS[index])
            sprite = None
            if self.assets:
                sprite = self.assets.get_animal_sprite(
                    aid, evolution_stage=card["evolution_stage"],
                    max_width=self._source_size(96),
                    max_height=self._source_size(96))
            if sprite is not None:
                surface.blit(sprite, sprite.get_rect(center=center))
            else:
                draw_text(surface, ANIMAL_EMOJIS.get(aid, "?"), center,
                          font_size=self._source_size(42),
                          color=SERTAO_CREAM, center=True)

            name = card["animal"].get("name", aid)
            name_pos = self._source_point(
                self.TEAM_SLOT_CENTERS[index][0], 815)
            max_width = self._source_size(160)
            font_size = self._fit_font_size(
                name, max_width, self._source_size(19))
            draw_text(surface, name, name_pos, font_size=font_size,
                      color=SERTAO_GOLD, center=True)
            if card.get("fallen"):
                fall_pos = self._source_point(
                    self.TEAM_SLOT_CENTERS[index][0], 842)
                draw_text(surface, "CAIDO", fall_pos,
                          font_size=self._source_size(14),
                          color=SERTAO_RED, center=True)

    def _draw_hotspot(self, surface, rect, hovered, enabled=True):
        if not hovered:
            return
        color = (255, 228, 130) if enabled else SERTAO_RED
        glow = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        if enabled:
            pygame.draw.rect(glow, (255, 220, 90, 30), glow.get_rect(),
                             border_radius=8)
        pygame.draw.rect(glow, color + (210,), glow.get_rect(), 2,
                         border_radius=8)
        surface.blit(glow, rect.topleft)

    def _fit_font_size(self, text, max_width, base_size, min_size=10):
        size = max(min_size, int(base_size))
        while size > min_size and get_font(size).size(str(text))[0] > max_width:
            size -= 1
        return size



class BestiaryScreen:
    def __init__(self, save_data=None, assets=None, party=None):
        self.animals = load_animals()
        self.enemies = load_enemies()
        self.save_data = save_data or {}
        self.assets = assets
        self.party = party or []
        self.animal_data = self.save_data.get("animal_data", {})
        self.unlocked_animals = self.save_data.get("unlocked_animals", [])
        self.bestiary_discovered = self.save_data.get("bestiary_discovered", [])
        self.creatures_discovered = self.save_data.get("creatures_discovered", [])
        self.animal_seen = set(self.unlocked_animals) | set(self.bestiary_discovered)
        self.tab = "ANIMAIS"
        self.selected_idx = 0
        self.hover_idx = -1
        self.layout = UILayout()
        self.tab_metrics = get_button_metrics("tab")
        self.back_metrics = get_button_metrics("nav")
        self.back_button = make_back_button(self.back_metrics)
        tabs = make_centered_tabs(2, self.tab_metrics, y=75)
        self.tab_animals, self.tab_criaturas = tabs
        self._build_grid()

    def _build_grid(self):
        self.grid_rects = []
        if self.tab == "ANIMAIS":
            ids = list(self.animals.keys())
            cell_w, cell_h = 240, 95
            cols = 3
        else:
            CREATURE_ORDER = [
                "brasa", "chamas", "espirito_de_fogo",
                "furacao", "lobo_de_fogo",
                "lobo_alfa_de_fogo", "vendaval_de_fogo"
            ]
            ids = CREATURE_ORDER
            cell_w, cell_h = 220, 85
            cols = 3

        gap_x, gap_y = 12, 12
        start_x = SAFE_MARGIN + 20
        start_y = self.layout.body.y + 120
        grid_w = cols * cell_w + (cols - 1) * gap_x
        actual_start_x = CENTER_X - grid_w // 2

        for i, eid in enumerate(ids):
            row = i // cols
            col = i % cols
            x = actual_start_x + col * (cell_w + gap_x)
            y = start_y + row * (cell_h + gap_y)
            discovered = (eid in self.animal_seen if self.tab == "ANIMAIS"
                          else eid in self.creatures_discovered)
            unlocked = eid in self.unlocked_animals if self.tab == "ANIMAIS" else True
            self.grid_rects.append({
                "id": eid,
                "rect": pygame.Rect(x, y, cell_w, cell_h),
                "discovered": discovered,
                "unlocked": unlocked,
            })

    def _get_current_ids(self):
        if self.tab == "ANIMAIS":
            return list(self.animals.keys())
        return ["brasa", "chamas", "espirito_de_fogo", "furacao", "lobo_de_fogo",
                "lobo_alfa_de_fogo", "vendaval_de_fogo"]

    def _get_selected(self):
        ids = self._get_current_ids()
        idx = min(self.selected_idx, len(ids) - 1)
        return ids[idx]

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover_idx = -1
            for i, cell in enumerate(self.grid_rects):
                if cell["rect"].collidepoint(event.pos):
                    self.hover_idx = i
                    break

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.tab_animals.collidepoint(event.pos):
                self.tab = "ANIMAIS"
                self.selected_idx = 0
                self._build_grid()
                return None
            if self.tab_criaturas.collidepoint(event.pos):
                self.tab = "CRIATURAS"
                self.selected_idx = 0
                self._build_grid()
                return None

            for i, cell in enumerate(self.grid_rects):
                if cell["rect"].collidepoint(event.pos):
                    self.selected_idx = i
                    break
            if self.back_button.collidepoint(event.pos):
                return "back"
        return None

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "main_menu")
        else:
            surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        surface.blit(overlay, (0, 0))

        draw_text(surface, "BESTIARIO", (CENTER_X, 30),
                  font_size=44, color=SERTAO_GOLD, center=True)

        is_animals = self.tab == "ANIMAIS"
        draw_sertao_button(surface, self.tab_animals, "ANIMAIS", is_hovered=is_animals,
                           color=SERTAO_GREEN if is_animals else SERTAO_PANEL,
                           font_size=self.tab_metrics.font_size)
        draw_sertao_button(surface, self.tab_criaturas, "CRIATURAS", is_hovered=not is_animals,
                           color=SERTAO_RED if not is_animals else SERTAO_PANEL,
                           font_size=self.tab_metrics.font_size)

        discovered_list = (list(self.animal_seen) if is_animals else self.creatures_discovered)
        total_ids = self._get_current_ids()
        total = len(total_ids)
        discovered = len([e for e in discovered_list if e in total_ids])
        pct = int((discovered / total) * 100) if total > 0 else 0

        draw_text(surface, f"Descobertas: {discovered} / {total}  ({pct}%)",
                  (CENTER_X, 200), font_size=18, color=SERTAO_CREAM, center=True)

        bar_w = 360
        bar_h = 8
        bar_x = CENTER_X - bar_w // 2
        bar_y = 220
        pygame.draw.rect(surface, (60, 45, 25), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fill_w = int(bar_w * (discovered / total)) if total > 0 else 0
        bar_color = SERTAO_GREEN if is_animals else SERTAO_RED
        pygame.draw.rect(surface, bar_color, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
        pygame.draw.rect(surface, SERTAO_BORDER, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)

        for i, cell in enumerate(self.grid_rects):
            self._draw_cell(surface, cell, i)

        cols = 3
        if is_animals:
            cell_w = 240
        else:
            cell_w = 220
        gap_x = 12
        grid_w = cols * cell_w + (cols - 1) * gap_x
        detail_x = CENTER_X + grid_w // 2 + 20
        detail_w = SCREEN_WIDTH - detail_x - SAFE_MARGIN - 10
        detail_y = self.layout.body.y + 120
        detail_h = SCREEN_HEIGHT - detail_y - 80

        if detail_w > 100:
            self._draw_detail_panel(surface, detail_x, detail_y, detail_w, detail_h)

        self._draw_party_strip(surface, grid_w)

        bh = self.back_button.collidepoint(get_mouse_pos())
        draw_sertao_button(surface, self.back_button, "Voltar", bh,
                           font_size=self.back_metrics.font_size)

    def _draw_party_strip(self, surface, grid_w):
        """Compact team summary moved from the journey map footer."""
        grid_bottom = max(
            (cell["rect"].bottom for cell in self.grid_rects),
            default=self.layout.body.y + 120)
        panel = pygame.Rect(CENTER_X - grid_w // 2, grid_bottom + 8,
                            grid_w, 70)
        panel.y = min(panel.y, SCREEN_HEIGHT - 150)
        draw_sertao_panel(surface, panel.x, panel.y, panel.w, panel.h,
                          alpha=200)

        draw_text(surface, "SUA EQUIPE", (panel.x + 12, panel.y + 6),
                  font_size=16, color=SERTAO_GOLD)
        gold = self.party[0].gold if self.party else 0
        draw_text_right(surface, "Gold: {}".format(gold),
                        (panel.right - 12, panel.y + 6),
                        font_size=16, color=SERTAO_GOLD)

        if not self.party:
            draw_text_centered(surface, "Nenhuma equipe ativa",
                               panel.centerx, panel.y + 42, 15, GRAY)
            return

        col_w = (panel.w - 24) // 3
        top = panel.y + 26
        for index, animal in enumerate(self.party[:3]):
            cx = panel.x + 12 + index * col_w
            sprite = None
            if self.assets:
                sprite = self.assets.get_animal_sprite(
                    animal.animal_id,
                    evolution_stage=getattr(animal, "evolution_stage", 0),
                    max_width=34, max_height=34)
            if sprite:
                surface.blit(sprite, (cx + 2, top + 2))
            else:
                draw_text_centered(surface, ANIMAL_EMOJIS.get(animal.animal_id, "?"),
                                   cx + 19, top + 17, 20, SERTAO_CREAM)

            draw_text(surface, "{} Lv.{}".format(animal.name, animal.level),
                      (cx + 42, top), font_size=14, color=SERTAO_CREAM)
            hp_color = (GREEN if animal.hp > animal.max_hp * 0.5
                        else (YELLOW if animal.hp > animal.max_hp * 0.25 else RED))
            draw_bar(surface, cx + 42, top + 20, col_w - 54, 9,
                     animal.hp, animal.max_hp, hp_color)
            draw_text(surface, "{}/{}".format(animal.hp, animal.max_hp),
                      (cx + 42, top + 31), font_size=11, color=SERTAO_LIGHT)

    def _draw_cell(self, surface, cell, index):
        r = cell["rect"]
        is_hovered = (self.hover_idx == index)
        is_selected = (self.selected_idx == index)
        discovered = cell["discovered"]

        if is_selected:
            border_c = SERTAO_GOLD
        elif is_hovered:
            border_c = SERTAO_LIGHT
        else:
            border_c = SERTAO_BORDER

        if discovered:
            if self.tab == "ANIMAIS":
                unlocked = cell["unlocked"]
                if unlocked:
                    bg = (45, 55, 35) if not is_hovered else (55, 70, 45)
                else:
                    bg = (50, 45, 30)
            else:
                enemy_data = self.enemies.get(cell["id"], {})
                is_boss = enemy_data.get("is_boss", False)
                is_elite = enemy_data.get("is_elite", False)
                if is_boss:
                    bg = (60, 30, 30) if not is_hovered else (75, 40, 40)
                elif is_elite:
                    bg = (55, 45, 25) if not is_hovered else (70, 55, 35)
                else:
                    bg = (45, 35, 25) if not is_hovered else (55, 45, 35)
        else:
            bg = (30, 25, 18)

        pygame.draw.rect(surface, bg, r, border_radius=10)
        pygame.draw.rect(surface, border_c, r, 2, border_radius=10)

        sprite_cy = r.y + 24 if self.tab == "ANIMAIS" else r.y + 21
        if self.tab == "ANIMAIS":
            animal = self.animals.get(cell["id"], {})
            stage = self.animal_data.get(cell["id"], {}).get("evolution_stage", 0)
            stage_tags = ["", " [Evo 1]"]
            if discovered:
                spr = None
                if self.assets and cell.get("unlocked"):
                    spr = self.assets.get_animal_sprite(cell["id"],
                                                       evolution_stage=stage,
                                                       max_width=36, max_height=36)
                if spr:
                    surface.blit(spr, spr.get_rect(center=(r.centerx, sprite_cy)))
                else:
                    emoji_color = (SERTAO_CREAM if cell.get("unlocked")
                                   else (140, 120, 90))
                    draw_text_centered(surface, ANIMAL_EMOJIS.get(cell["id"], "?"),
                                       r.centerx, sprite_cy, 24, emoji_color)

                name = animal.get("name", cell["id"])
                tag = stage_tags[min(stage, 1)]
                draw_text_centered(surface, name + tag, r.centerx, r.y + 50,
                                   15, SERTAO_CREAM)
                draw_text_centered(surface, animal.get("role", ""), r.centerx,
                                   r.y + 66, 12, SERTAO_LIGHT)
                rarity = animal.get("rarity", "")
                rc = RARITY_COLORS.get(rarity, GRAY)
                draw_text_centered(surface, rarity, r.centerx, r.y + 79,
                                   11, rc)
                if cell.get("unlocked"):
                    draw_text_centered(surface, "\u2713", r.right - 14, r.y + 10,
                                       16, GREEN)
            else:
                draw_text_centered(surface, "\U0001f512", r.centerx, sprite_cy,
                                   22, (60, 50, 40))
                draw_text_centered(surface, "???", r.centerx, r.y + 52,
                                   18, (60, 50, 40))
        else:
            enemy_data = self.enemies.get(cell["id"], {})
            emoji = ENEMY_EMOJIS.get(cell["id"], "\U0001f525")
            if discovered:
                spr = None
                if self.assets:
                    spr = self.assets.get_enemy_sprite(cell["id"],
                                                       max_width=36, max_height=36)
                if spr:
                    surface.blit(spr, spr.get_rect(center=(r.centerx, sprite_cy)))
                else:
                    draw_text_centered(surface, emoji, r.centerx, sprite_cy,
                                       24, SERTAO_CREAM)

                name = enemy_data.get("name", cell["id"])
                draw_text_centered(surface, name, r.centerx, r.y + 47,
                                   15, SERTAO_CREAM)

                is_boss = enemy_data.get("is_boss", False)
                is_elite = enemy_data.get("is_elite", False)
                tag = "CHEFE" if is_boss else ("ELITE" if is_elite else "Comum")
                tag_color = SERTAO_RED if is_boss else (ORANGE if is_elite else GRAY)
                region = enemy_data.get("region", "")
                tag_line = tag + ((" · " + region) if region else "")
                draw_text_centered(surface, tag_line, r.centerx, r.y + 63,
                                   12, tag_color)
            else:
                draw_text_centered(surface, "\U0001f512", r.centerx, sprite_cy,
                                   22, (60, 50, 40))
                draw_text_centered(surface, "???", r.centerx, r.y + 51,
                                   18, (60, 50, 40))

    def _draw_detail_panel(self, surface, x, y, w, h):
        draw_sertao_panel(surface, x, y, w, h)
        selected_id = self._get_selected()
        px = x + 15
        py = y + 15

        if self.tab == "ANIMAIS":
            animal = self.animals.get(selected_id, {})
            discovered = selected_id in self.animal_seen if self.tab == "ANIMAIS" else selected_id in self.creatures_discovered
            unlocked = selected_id in self.unlocked_animals
            saved = self.animal_data.get(selected_id, {})
            stage = saved.get("evolution_stage", 0)
            stage_tags = ["", " — Evolucao 1"]
            stage_name = stage_tags[min(stage, 1)]

            if discovered:
                if self.assets and unlocked:
                    spr = self.assets.get_animal_sprite(selected_id,
                                                       evolution_stage=stage,
                                                       max_width=55, max_height=55)
                    if spr:
                        surface.blit(spr, spr.get_rect(topleft=(px, py)))
                    else:
                        icon_rect = pygame.Rect(px, py, 55, 55)
                        pygame.draw.rect(surface, SERTAO_GREEN, icon_rect, border_radius=10)
                else:
                    icon_rect = pygame.Rect(px, py, 55, 55)
                    pygame.draw.rect(surface, SERTAO_GREEN if unlocked else GRAY, icon_rect, border_radius=10)

                draw_text(surface, animal.get("name", "") + stage_name, (px + 65, py + 5),
                          font_size=20, color=SERTAO_CREAM)
                draw_text(surface, animal.get("role", ""), (px + 65, py + 30),
                          font_size=16, color=SERTAO_LIGHT)
                rarity = animal.get("rarity", "")
                rc = RARITY_COLORS.get(rarity, GRAY)
                draw_text(surface, rarity, (px + 65, py + 50), font_size=14, color=rc)

                py += 70
                pygame.draw.line(surface, SERTAO_BORDER, (px, py), (x + w - 15, py), 1)
                py += 8

                desc_lines = wrap_text_chars(animal.get("description", ""), 32)
                for line in desc_lines[:3]:
                    draw_text(surface, line, (px, py), font_size=14, color=SERTAO_CREAM)
                    py += 18

                py += 5
                pygame.draw.line(surface, SERTAO_BORDER, (px, py), (x + w - 15, py), 1)
                py += 8

                if unlocked and saved:
                    draw_text(surface, "Status Reais:", (px, py), font_size=16, color=SERTAO_GOLD)
                    py += 20
                    stats = [
                        (f"HP: {saved.get('max_hp', 0)}", GREEN),
                        (f"ATK: {saved.get('base_attack', 0)}", RED),
                        (f"DEF: {saved.get('base_defense', 0)}", BLUE),
                        (f"SPD: {saved.get('base_speed', 0)}", YELLOW),
                        (f"Crit: {saved.get('crit_chance', 0)}%", PURPLE),
                        (f"Dodge: {saved.get('dodge', 0)}%", ORANGE),
                    ]
                    for stat_text, stat_color in stats:
                        draw_text(surface, stat_text, (px, py), font_size=14, color=stat_color)
                        py += 18
                    py += 5
                    draw_text(surface, f"XP: {saved.get('xp', 0)} / {saved.get('xp_to_level', 100)}",
                              (px, py), font_size=14, color=SERTAO_CREAM)
                    py += 18
                    upgrade_id = saved.get("specific_upgrade_id")
                    if upgrade_id:
                        py += 5
                        pygame.draw.line(surface, SERTAO_BORDER,
                                         (px, py), (x + w - 15, py), 1)
                        py += 8
                        draw_text(surface, "MELHORIA ESPECIFICA:",
                                  (px, py), font_size=16, color=SERTAO_GOLD)
                        py += 20
                        from src.entities.animal import SPECIFIC_UPGRADES
                        for udata in SPECIFIC_UPGRADES.values():
                            if udata["id"] == upgrade_id:
                                draw_text(surface,
                                          f"{udata['icon']} {udata['name']}",
                                          (px, py), font_size=15, color=GREEN)
                                py += 18
                                udesc_lines = wrap_text_chars(
                                    udata.get("description", ""), 32)
                                for line in udesc_lines[:3]:
                                    draw_text(surface, line, (px, py),
                                              font_size=12,
                                              color=SERTAO_CREAM)
                                    py += 16
                                break
                else:
                    draw_text(surface, "Status Base:", (px, py), font_size=16, color=SERTAO_GOLD)
                    py += 20
                    s = animal.get("base_stats", {})
                    stats = [
                        (f"HP: {s.get('hp', 0)}", GREEN),
                        (f"ATK: {s.get('attack', 0)}", RED),
                        (f"DEF: {s.get('defense', 0)}", BLUE),
                        (f"SPD: {s.get('speed', 0)}", YELLOW),
                        (f"Crit: {s.get('crit_chance', 0)}%", PURPLE),
                        (f"Dodge: {s.get('dodge', 0)}%", ORANGE),
                    ]
                    for stat_text, stat_color in stats:
                        draw_text(surface, stat_text, (px, py), font_size=14, color=stat_color)
                        py += 18

                py += 5
                pygame.draw.line(surface, SERTAO_BORDER, (px, py), (x + w - 15, py), 1)
                py += 8

                draw_text(surface, "COMO RESGATAR:", (px, py), font_size=16, color=SERTAO_GOLD)
                py += 20
                rescue = animal.get("rescue_description", "Derrote o chefe da regiao.")
                rescue_lines = wrap_text_chars(rescue, 32)
                for line in rescue_lines[:3]:
                    draw_text(surface, line, (px, py), font_size=14, color=SERTAO_CREAM)
                    py += 18

                if unlocked:
                    py += 6
                    draw_text(surface, "\u2713 Resgatado!", (px, py), font_size=16, color=GREEN)
            else:
                draw_text(surface, "???", (px + 10, py + 10), font_size=28, color=GRAY)
                draw_text(surface, "Nao Descoberto", (px + 10, py + 45),
                          font_size=18, color=(120, 100, 70))
                py += 80
                pygame.draw.line(surface, (80, 60, 40), (px, py), (x + w - 15, py), 1)
                py += 12
                draw_text(surface, "Encontre este animal para", (px, py), font_size=14, color=(100, 80, 60))
                py += 18
                draw_text(surface, "desbloquear sua ficha.", (px, py), font_size=14, color=(100, 80, 60))
        else:
            enemy_data = self.enemies.get(selected_id, {})
            discovered = selected_id in self.creatures_discovered

            if discovered:
                is_boss = enemy_data.get("is_boss", False)
                is_elite = enemy_data.get("is_elite", False)

                if self.assets:
                    spr = self.assets.get_enemy_sprite(selected_id, max_width=55, max_height=55)
                    if spr:
                        surface.blit(spr, spr.get_rect(topleft=(px, py)))
                    else:
                        icon_color = SERTAO_RED if is_boss else (ORANGE if is_elite else SERTAO_CREAM)
                        icon_rect = pygame.Rect(px, py, 55, 55)
                        pygame.draw.rect(surface, icon_color, icon_rect, border_radius=10)
                else:
                    icon_color = SERTAO_RED if is_boss else (ORANGE if is_elite else SERTAO_CREAM)
                    icon_rect = pygame.Rect(px, py, 55, 55)
                    pygame.draw.rect(surface, icon_color, icon_rect, border_radius=10)

                draw_text(surface, enemy_data.get("name", selected_id), (px + 65, py + 5),
                          font_size=22, color=SERTAO_CREAM)
                tag = "CHEFE" if is_boss else ("ELITE" if is_elite else "Comum")
                tag_color = SERTAO_RED if is_boss else (ORANGE if is_elite else GRAY)
                draw_text(surface, tag, (px + 65, py + 30), font_size=16, color=tag_color)

                py += 70
                pygame.draw.line(surface, SERTAO_BORDER, (px, py), (x + w - 15, py), 1)
                py += 8

                desc = enemy_data.get("description", "")
                desc_lines = wrap_text_chars(desc, 32)
                for line in desc_lines[:3]:
                    draw_text(surface, line, (px, py), font_size=14, color=SERTAO_CREAM)
                    py += 18

                py += 5
                pygame.draw.line(surface, SERTAO_BORDER, (px, py), (x + w - 15, py), 1)
                py += 8

                draw_text(surface, "Status Base:", (px, py), font_size=16, color=SERTAO_GOLD)
                py += 20
                s = enemy_data.get("stats", {})
                stats = [
                    (f"HP: {s.get('hp', 0)}", GREEN),
                    (f"ATK: {s.get('attack', 0)}", RED),
                    (f"DEF: {s.get('defense', 0)}", BLUE),
                    (f"SPD: {s.get('speed', 0)}", YELLOW),
                    (f"Crit: {s.get('crit_chance', 0)}%", PURPLE),
                    (f"Dodge: {s.get('dodge', 0)}%", ORANGE),
                ]
                for stat_text, stat_color in stats:
                    draw_text(surface, stat_text, (px, py), font_size=14, color=stat_color)
                    py += 18

                py += 5
                pygame.draw.line(surface, SERTAO_BORDER, (px, py), (x + w - 15, py), 1)
                py += 8

                draw_text(surface, "Regiao:", (px, py), font_size=16, color=SERTAO_GOLD)
                py += 20
                draw_text(surface, enemy_data.get("region", "Desconhecida"), (px, py),
                          font_size=16, color=SERTAO_CREAM)

                if is_boss:
                    py += 25
                    pygame.draw.line(surface, SERTAO_RED, (px, py), (x + w - 15, py), 1)
                    py += 8
                    draw_text(surface, "Protege:", (px, py), font_size=14, color=SERTAO_GOLD)
                    py += 18
                    biomes = load_biomes()
                    animals = load_animals()
                    for bid, bdata in biomes.items():
                        if selected_id in bdata.get("bosses", []):
                            rescue = bdata.get("rescue_animal", "")
                            if rescue:
                                rname = animals.get(rescue, {}).get("name", rescue)
                                draw_text(surface, rname, (px, py), font_size=14, color=GREEN)
                                py += 18
            else:
                draw_text(surface, "???", (px + 10, py + 10), font_size=28, color=(60, 50, 40))
                draw_text(surface, "Criatura Desconhecida", (px + 10, py + 45),
                          font_size=18, color=(80, 70, 50))
                py += 80
                pygame.draw.line(surface, (80, 60, 40), (px, py), (x + w - 15, py), 1)
                py += 12
                draw_text(surface, "Derrote esta criatura para", (px, py),
                          font_size=14, color=(100, 80, 60))
                py += 18
                draw_text(surface, "desbloquear sua ficha.", (px, py),
                          font_size=14, color=(100, 80, 60))


class AcampamentoScreen:
    SECTIONS = ["MELHORIAS", "EQUIPE"]
    STAGE_NAMES = ["Base", "Evo 1"]

    def __init__(self, save_data=None, assets=None, party=None):
        self.save_data = save_data or {}
        self.assets = assets
        self.party = party or []
        self.animals = load_animals()
        self.upgrades_data = load_upgrades()
        self.unlocked = self.save_data.get("unlocked_animals", [])
        self.sel_section = 0
        self.sel_animal = 0
        self.hover_item = -1
        self.layout = UILayout()
        self._build_tabs()

    def _build_tabs(self):
        self.tab_metrics = get_button_metrics("tab")
        self.back_metrics = get_button_metrics("nav")
        self.tab_rects = make_centered_tabs(len(self.SECTIONS), self.tab_metrics, y=75)
        self.back_button = make_back_button(self.back_metrics)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, tab in enumerate(self.tab_rects):
                if tab.collidepoint(event.pos):
                    self.sel_section = i
                    return None

            if self.back_button.collidepoint(event.pos):
                return ("back", None)

            if self.sel_section == 0:
                return self._handle_melhorias_events(event)
            elif self.sel_section == 1:
                return self._handle_equipe_events(event)

        if event.type == pygame.MOUSEMOTION:
            self.hover_item = -1

        return None

    def _handle_melhorias_events(self, event):
        return None

    def _handle_equipe_events(self, event):
        rects = self._get_party_rects()
        for i in range(len(self.party)):
            if i < len(rects) and rects[i].collidepoint(event.pos):
                self.sel_animal = i
        return None

    def _get_party_rects(self):
        bw, bh = 500, 60
        gap = 10
        sy = 170
        rects = []
        for i in range(len(self.party)):
            x = CENTER_X - bw // 2
            y = sy + i * (bh + gap)
            rects.append(pygame.Rect(x, y, bw, bh))
        return rects

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "main_menu")
        else:
            surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        surface.blit(overlay, (0, 0))

        draw_text(surface, "ACAMPAMENTO", (CENTER_X, 30),
                  font_size=44, color=SERTAO_GOLD, center=True)
        pygame.draw.line(surface, SERTAO_BORDER, (CENTER_X - 170, 62), (CENTER_X + 170, 62), 2)

        for i, tab in enumerate(self.tab_rects):
            is_sel = (i == self.sel_section)
            draw_sertao_button(surface, tab, self.SECTIONS[i], is_hovered=is_sel,
                               color=SERTAO_GREEN if is_sel else SERTAO_PANEL,
                               font_size=self.tab_metrics.font_size)

        if self.sel_section == 0:
            self._draw_melhorias_section(surface)
        elif self.sel_section == 1:
            self._draw_equipe_section(surface)

        bh = self.back_button.collidepoint(get_mouse_pos())
        draw_sertao_button(surface, self.back_button, "Voltar", bh,
                           font_size=self.back_metrics.font_size)

    def _draw_melhorias_section(self, surface):
        draw_text(surface, "Melhorias permanentes dos animais",
                  (CENTER_X, 155), font_size=16, color=SERTAO_CREAM, center=True)

        if not self.party:
            draw_text(surface, "Nenhum animal na equipe.", (CENTER_X, 300),
                      font_size=20, color=GRAY, center=True)
            return

        animal = self.party[min(self.sel_animal, len(self.party) - 1)]
        upgrades = load_upgrades()

        y = 180
        for uid, udata in upgrades.items():
            btn = pygame.Rect(CENTER_X - 250, y, 500, 48)
            draw_sertao_panel(surface, btn.x, btn.y, btn.w, btn.h)
            emoji = "\u2694\ufe0f" if udata.get("category") == "offense" else "\U0001f6e1"
            draw_text(surface, f"{emoji} {udata['name']}", (btn.x + 15, btn.y + 8),
                      font_size=18, color=SERTAO_CREAM)
            draw_text(surface, udata.get("description", ""), (btn.x + 15, btn.y + 28),
                      font_size=13, color=SERTAO_LIGHT)
            y += 56

    def _draw_equipe_section(self, surface):
        draw_text(surface, "Equipe atual (max 3)",
                  (CENTER_X, 155), font_size=16, color=SERTAO_CREAM, center=True)

        if not self.party:
            draw_text(surface, "Nenhum animal na equipe.", (CENTER_X, 300),
                      font_size=20, color=GRAY, center=True)
            return

        rects = self._get_party_rects()
        animal_data = self.save_data.get("animal_data", {})
        for i, member in enumerate(self.party):
            if i >= len(rects):
                break
            r = rects[i]
            is_hov = (self.hover_item == i)
            draw_sertao_panel(surface, r.x, r.y, r.w, r.h,
                              SERTAO_GOLD if is_hov else SERTAO_BORDER)

            stage = animal_data.get(member.animal_id, {}).get("evolution_stage", 0)
            if self.assets:
                spr = self.assets.get_animal_sprite(member.animal_id,
                                                   evolution_stage=stage,
                                                   max_width=44, max_height=44)
                if spr:
                    surface.blit(spr, spr.get_rect(center=(r.x + 30, r.centery)))
                else:
                    emoji = ANIMAL_EMOJIS.get(member.animal_id, "?")
                    draw_text(surface, emoji, (r.x + 12, r.y + 8), font_size=28)
            else:
                emoji = ANIMAL_EMOJIS.get(member.animal_id, "?")
                draw_text(surface, emoji, (r.x + 12, r.y + 8), font_size=28)

            form_name = self.STAGE_NAMES[min(stage, 1)]
            draw_text(surface, f"{member.name} [{form_name}]", (r.x + 65, r.y + 8),
                      font_size=18, color=SERTAO_CREAM)
            draw_text(surface, member.role, (r.x + 65, r.y + 28), font_size=14, color=SERTAO_LIGHT)
            draw_text(surface, f"Lv.{member.level}  HP:{member.hp}/{member.max_hp}  ATK:{member.attack} DEF:{member.defense} SPD:{member.speed}",
                      (r.x + 65, r.y + 45), font_size=13, color=SERTAO_GOLD)


class BiomeSelectScreen:
    def __init__(self, unlocked_biomes=None, assets=None):
        self.biomes = load_biomes()
        self.unlocked_biomes = unlocked_biomes or ["caatinga"]
        self.selected_biome = None
        self.assets = assets
        self.hover_index = -1
        self.layout = UILayout()
        self._build()

    def _build(self):
        self.buttons = []
        bw = 600
        gap = 10 if len(self.biomes) >= 7 else 12
        count = len(self.biomes)
        available_h = self.layout.body.h - 30
        bh = min(72, max(56, (available_h - (count - 1) * gap) // max(count, 1)))
        total = count * bh + (count - 1) * gap
        sy = self.layout.body.y + (self.layout.body.h - total) // 2

        for i, (bid, biome) in enumerate(self.biomes.items()):
            x = CENTER_X - bw // 2
            y = sy + i * (bh + gap)
            self.buttons.append({
                "id": bid, "biome": biome,
                "rect": pygame.Rect(x, y, bw, bh),
                "unlocked": bid in self.unlocked_biomes,
            })

        self.back_button = pygame.Rect(SAFE_MARGIN, SCREEN_HEIGHT - 65, 140, 42)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover_index = -1
            for i, b in enumerate(self.buttons):
                if b["rect"].collidepoint(event.pos) and b["unlocked"]:
                    self.hover_index = i
                    break
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for b in self.buttons:
                if b["rect"].collidepoint(event.pos) and b["unlocked"]:
                    return b["id"]
            if self.back_button.collidepoint(event.pos):
                return "back"
        return None

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "biome_select")
        else:
            surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        surface.blit(overlay, (0, 0))

        draw_text(surface, "Selecione o Bioma", (CENTER_X, 50),
                  font_size=44, color=SERTAO_GOLD, center=True)

        for i, b in enumerate(self.buttons):
            r = b["rect"]
            hov = (self.hover_index == i)
            if b["unlocked"]:
                bc = b["biome"]["color"]
                if hov:
                    bc = tuple(min(255, c + 30) for c in bc)
                pygame.draw.rect(surface, bc, r, border_radius=10)
                bdr = SERTAO_GOLD if hov else WHITE
            else:
                pygame.draw.rect(surface, DARK_GRAY, r, border_radius=10)
                bdr = GRAY
            pygame.draw.rect(surface, bdr, r, 2, border_radius=10)

            draw_text(surface, b["biome"]["name"], (r.x + 20, r.y + (8 if r.h < 70 else 15)),
                      font_size=26, color=SERTAO_CREAM)
            draw_text(surface, b["biome"]["description"], (r.x + 20, r.y + (34 if r.h < 70 else 48)),
                      font_size=17, color=SERTAO_CREAM)
            if not b["unlocked"]:
                draw_text(surface, "Bloqueado", (r.right - 100, r.y + 28),
                          font_size=22, color=RED)

        bh = self.back_button.collidepoint(get_mouse_pos())
        draw_sertao_button(surface, self.back_button, "Voltar", bh)


class CageRewardScreen:
    def __init__(self, animal_data=None, assets=None):
        self.animal_data = animal_data
        self.assets = assets
        self.layout = UILayout()
        self.anim_timer = 0
        self.revealed = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if not self.revealed:
                self.revealed = True
                self.anim_timer = 0
                return None
            return "continue"
        return None

    def update(self):
        if not self.revealed:
            self.anim_timer += 1

    def draw(self, surface):
        surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        panel_w, panel_h = 500, 400
        panel_x = CENTER_X - panel_w // 2
        panel_y = CENTER_Y - panel_h // 2
        draw_sertao_panel(surface, panel_x, panel_y, panel_w, panel_h, SERTAO_GOLD)

        if not self.revealed:
            draw_text(surface, "\U0001faa4", (CENTER_X, CENTER_Y - 60),
                      font_size=80, color=SERTAO_GOLD, center=True)
            draw_text(surface, "JAULA MISTERIOSA", (CENTER_X, CENTER_Y + 40),
                      font_size=32, color=SERTAO_GOLD, center=True)
            draw_text(surface, "Clique para abrir...", (CENTER_X, CENTER_Y + 80),
                      font_size=20, color=SERTAO_CREAM, center=True)
        else:
            if self.animal_data:
                aid = self.animal_data.get("id", "")
                draw_text(surface, "\U0001f389", (CENTER_X, CENTER_Y - 100),
                          font_size=50, color=SERTAO_GOLD, center=True)
                draw_text(surface, "NOVO ANIMAL LIBERTADO!", (CENTER_X, CENTER_Y - 40),
                          font_size=28, color=SERTAO_GOLD, center=True)

                if self.assets:
                    spr = self.assets.get_animal_sprite(aid, max_width=100, max_height=100)
                    if spr:
                        surface.blit(spr, spr.get_rect(center=(CENTER_X, CENTER_Y + 20)))
                    else:
                        emoji = ANIMAL_EMOJIS.get(aid, "?")
                        draw_text(surface, emoji, (CENTER_X, CENTER_Y + 20),
                                  font_size=60, color=SERTAO_CREAM, center=True)
                else:
                    emoji = ANIMAL_EMOJIS.get(aid, "?")
                    draw_text(surface, emoji, (CENTER_X, CENTER_Y + 20),
                              font_size=60, color=SERTAO_CREAM, center=True)

                draw_text(surface, self.animal_data.get("name", aid), (CENTER_X, CENTER_Y + 80),
                          font_size=28, color=SERTAO_CREAM, center=True)
                draw_text(surface, self.animal_data.get("role", ""), (CENTER_X, CENTER_Y + 110),
                          font_size=20, color=SERTAO_LIGHT, center=True)
            else:
                draw_text(surface, "A jaula estava vazia...", (CENTER_X, CENTER_Y),
                          font_size=28, color=GRAY, center=True)

            draw_text(surface, "Clique para continuar", (CENTER_X, CENTER_Y + 160),
                      font_size=18, color=SERTAO_CREAM, center=True)


class JourneySelectScreen:
    """Save-slot selector built on top of the original ``Saves.png`` art.

    The supplied sheet is cropped at runtime into three horizontal panels and
    drawn without stretching.  Only animal sprites, save values and the
    transparent click target over the painted SELECIONAR button are rendered
    by code.
    """

    PANEL_COUNT = 3
    SOURCE_PANEL_WIDTH = 1518
    SOURCE_PANEL_HEIGHT = 302

    # Centres of the three square portrait openings, in source-panel pixels.
    SOURCE_SLOT_CENTERS = ((153.0, 173.0), (316.0, 173.0), (479.5, 173.0))
    SOURCE_SLOT_SIZE = 118.0

    # Visible SELECIONAR button in the source artwork (panel-relative
    # coordinates, including its painted border).
    SOURCE_SELECT_RECT = (1197, 123, 275, 118)

    # Value positions sit immediately after the painted labels.  The third
    # value is the maximum width available on the source panel, used to shrink
    # long region names/values without touching the artwork.
    SOURCE_VALUE_ANCHORS = {
        "biome": (768.0, 135.5, 190.0),
        "gold": (1066.0, 134.5, 124.0),
        "animals": (776.0, 217.0, 182.0),
        "bosses": (1084.0, 219.5, 104.0),
    }

    def __init__(self, save_manager, assets=None):
        self.save_manager = save_manager
        self.assets = assets
        self.layout = UILayout()
        self.hover_button = -1
        self.corrupt_slot = None
        self.confirm_slot = None
        self.action_slot = None
        self._build_layout()
        self._refresh()

    # ------------------------------------------------------------- layout

    def _build_layout(self):
        """Size the three panels proportionally to the virtual canvas."""
        side_margin = max(56, int(SCREEN_WIDTH * 0.045))
        top_margin = max(6, int(SCREEN_HEIGHT * 0.012))
        gap = max(4, int(SCREEN_HEIGHT * 0.012))

        avail_w = SCREEN_WIDTH - side_margin * 2
        avail_h = SCREEN_HEIGHT - top_margin * 2 - gap * 2
        panel_h = max(120, avail_h // self.PANEL_COUNT)
        aspect = self.SOURCE_PANEL_WIDTH / self.SOURCE_PANEL_HEIGHT
        panel_w = int(panel_h * aspect)
        if panel_w > avail_w:
            panel_w = avail_w
            panel_h = int(panel_w / aspect)

        total_h = panel_h * self.PANEL_COUNT + gap * (self.PANEL_COUNT - 1)
        start_x = (SCREEN_WIDTH - panel_w) // 2
        start_y = (SCREEN_HEIGHT - total_h) // 2

        self.panel_rects = [
            pygame.Rect(start_x, start_y + i * (panel_h + gap),
                        panel_w, panel_h)
            for i in range(self.PANEL_COUNT)
        ]

        self.panel_surfaces = []
        for i in range(self.PANEL_COUNT):
            surface = None
            if self.assets is not None:
                surface = self.assets.get_save_panel(i, panel_w)
            self.panel_surfaces.append(surface)

        self.select_rects = [
            self._source_rect_to_screen(rect, self.SOURCE_SELECT_RECT)
            for rect in self.panel_rects
        ]

        back_w = max(36, min(64, start_x - 16))
        self.back_button = pygame.Rect(8, SCREEN_HEIGHT - 48, back_w, 40)

    def _source_rect_to_screen(self, panel_rect, source_rect):
        sx = panel_rect.w / self.SOURCE_PANEL_WIDTH
        sy = panel_rect.h / self.SOURCE_PANEL_HEIGHT
        x, y, w, h = source_rect
        return pygame.Rect(
            panel_rect.x + int(x * sx), panel_rect.y + int(y * sy),
            max(1, int(w * sx)), max(1, int(h * sy)))

    def _source_point_to_screen(self, panel_rect, point):
        sx = panel_rect.w / self.SOURCE_PANEL_WIDTH
        sy = panel_rect.h / self.SOURCE_PANEL_HEIGHT
        return (panel_rect.x + int(point[0] * sx),
                panel_rect.y + int(point[1] * sy))

    # -------------------------------------------------------------- saves

    def _refresh(self):
        self.info_cache = {}
        self.corrupt_cache = {}
        for slot in range(1, self.PANEL_COUNT + 1):
            status = self.save_manager.get_slot_status(slot)
            if status == "corrupt":
                self.corrupt_cache[slot] = True
                self.info_cache[slot] = None
            elif status == "ok":
                info = self.save_manager.get_slot_info(slot)
                if info is None:
                    self.corrupt_cache[slot] = True
                    self.info_cache[slot] = None
                else:
                    self.info_cache[slot] = info
            else:
                self.info_cache[slot] = None

    def _action_options(self, has_run=None):
        # Selecting a slot always opens its internal menu first.  The team
        # screen is only opened later from the match menu's JOGAR action.
        return ["reteam", "delete", "back"]

    def _action_modal_rects(self, has_run):
        options = self._action_options(has_run)
        btn_w, btn_h, gap = 340, 46, 14
        content_h = len(options) * btn_h + (len(options) - 1) * gap
        title_h = 34
        sub_h = 24
        padding_top = 24
        padding_bottom = 24
        separation = 30
        panel_w = 620
        panel_h = padding_top + title_h + sub_h + separation + content_h + padding_bottom
        px = CENTER_X - panel_w // 2
        py = CENTER_Y - panel_h // 2

        rects = {}
        y = py + padding_top + title_h + sub_h + separation
        for i, opt in enumerate(options):
            rects[opt] = pygame.Rect(CENTER_X - btn_w // 2,
                                     y + i * (btn_h + gap), btn_w, btn_h)
        return rects, panel_w, panel_h

    def _corrupt_modal_rects(self):
        cy = CENTER_Y + 70
        return {
            "recover": pygame.Rect(CENTER_X - 280, cy, 165, 42),
            "delete": pygame.Rect(CENTER_X - 85, cy, 160, 42),
            "cancel": pygame.Rect(CENTER_X + 105, cy, 160, 42),
        }

    def _confirm_modal_rects(self):
        return {
            "cancel": pygame.Rect(CENTER_X - 210, CENTER_Y + 85, 190, 42),
            "delete": pygame.Rect(CENTER_X + 20, CENTER_Y + 85, 190, 42),
        }

    def is_corrupt(self, slot):
        return self.save_manager.get_slot_status(slot) == "corrupt"

    # ------------------------------------------------------------- events

    def handle_event(self, event):
        if self.confirm_slot is not None:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                rects = self._confirm_modal_rects()
                if rects["cancel"].collidepoint(event.pos):
                    self.confirm_slot = None
                elif rects["delete"].collidepoint(event.pos):
                    slot = self.confirm_slot
                    self.confirm_slot = None
                    self.save_manager.delete_slot(slot)
                    self._refresh()
                    return ("deleted", slot)
            return None

        if self.corrupt_slot is not None:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                rects = self._corrupt_modal_rects()
                slot = self.corrupt_slot
                if rects["recover"].collidepoint(event.pos):
                    recovered = self.save_manager.restore_save(slot)
                    self._refresh()
                    if recovered:
                        self.corrupt_slot = None
                        return ("team", slot)
                elif rects["delete"].collidepoint(event.pos):
                    self.corrupt_slot = None
                    self.save_manager.delete_slot(slot)
                    self._refresh()
                    return ("deleted", slot)
                elif rects["cancel"].collidepoint(event.pos):
                    self.corrupt_slot = None
            return None

        if self.action_slot is not None:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                slot = self.action_slot
                info = self.info_cache.get(slot)
                has_run = bool(info and info.get("run_active"))
                rects, _, _ = self._action_modal_rects(has_run)

                if rects["reteam"].collidepoint(event.pos):
                    self.action_slot = None
                    return ("team", slot)
                if rects["delete"].collidepoint(event.pos):
                    self.action_slot = None
                    self.confirm_slot = slot
                    return None
                if rects["back"].collidepoint(event.pos):
                    self.action_slot = None
            return None

        if event.type == pygame.MOUSEMOTION:
            self.hover_button = -1
            for i, rect in enumerate(self.select_rects):
                if rect.collidepoint(event.pos):
                    self.hover_button = i
                    break

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_button.collidepoint(event.pos):
                return "back"

            # Only the painted SELECIONAR buttons are clickable, never the
            # whole panel.
            for i, rect in enumerate(self.select_rects):
                if not rect.collidepoint(event.pos):
                    continue
                slot = i + 1
                if self.corrupt_cache.get(slot):
                    self.corrupt_slot = slot
                    return None
                return ("team", slot)
            return None

        # Right-click keeps the previous reteam/delete actions available
        # without turning the panel itself into a selection target.
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            for i, rect in enumerate(self.panel_rects):
                if rect.collidepoint(event.pos):
                    slot = i + 1
                    if self.corrupt_cache.get(slot):
                        self.corrupt_slot = slot
                    elif self.info_cache.get(slot):
                        self.action_slot = slot
                    break
        return None

    # -------------------------------------------------------------- draw

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background_cover(surface, "saves")
        else:
            surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 28))
        surface.blit(overlay, (0, 0))

        for i, rect in enumerate(self.panel_rects):
            surface_image = self.panel_surfaces[i]
            if surface_image is not None:
                surface.blit(surface_image, rect.topleft)
            else:
                draw_sertao_panel(surface, rect.x, rect.y, rect.w, rect.h)

            slot = i + 1
            self._draw_panel_contents(
                surface, rect, slot,
                self.info_cache.get(slot),
                self.corrupt_cache.get(slot, False))

        if 0 <= self.hover_button < len(self.select_rects):
            self._draw_select_hover(surface, self.select_rects[self.hover_button])

        bh = self.back_button.collidepoint(get_mouse_pos())
        draw_sertao_button(surface, self.back_button, "<", bh, font_size=20)

        if self.corrupt_slot is not None:
            self._draw_corrupt_msg(surface)
        elif self.confirm_slot is not None:
            self._draw_confirm_msg(surface)
        elif self.action_slot is not None:
            self._draw_action_msg(surface)

    def _draw_select_hover(self, surface, rect):
        glow = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(glow, (255, 220, 90, 34), glow.get_rect(),
                         border_radius=8)
        pygame.draw.rect(glow, (255, 228, 130, 210), glow.get_rect(), 2,
                         border_radius=8)
        surface.blit(glow, rect.topleft)

    def _draw_panel_contents(self, surface, rect, slot, info, corrupt):
        sx = rect.w / self.SOURCE_PANEL_WIDTH
        sy = rect.h / self.SOURCE_PANEL_HEIGHT

        details = (info or {}).get("party_details") or []
        sprite_size = max(24, int(self.SOURCE_SLOT_SIZE * min(sx, sy) * 0.96))
        for index, member in enumerate(details[:3]):
            cx, cy = self._source_point_to_screen(
                rect, self.SOURCE_SLOT_CENTERS[index])
            sprite = None
            if self.assets is not None:
                sprite = self.assets.get_animal_sprite(
                    member.get("id", ""),
                    evolution_stage=member.get("evolution_stage", 0),
                    max_width=sprite_size, max_height=sprite_size)
            if sprite is not None:
                surface.blit(sprite, sprite.get_rect(center=(cx, cy)))
            else:
                draw_text(surface, "?", (cx, cy), font_size=max(14, sprite_size // 2),
                          color=SERTAO_CREAM, center=True)

        values = self._panel_values(info, corrupt)
        base_size = max(13, int(rect.h * 0.132))
        colors = {
            "biome": SERTAO_RED if corrupt else SERTAO_CREAM,
            "gold": (255, 220, 90),
            "animals": SERTAO_CREAM,
            "bosses": SERTAO_CREAM,
        }
        for key, (src_x, src_y, src_max_w) in self.SOURCE_VALUE_ANCHORS.items():
            text = values[key]
            x, y = self._source_point_to_screen(rect, (src_x, src_y))
            max_w = max(18, int(src_max_w * sx))
            font_size = self._fit_font_size(text, max_w, base_size)
            draw_text_left(surface, text, (x + 1, y + 2), font_size=font_size,
                           color=BLACK)
            draw_text_left(surface, text, (x, y), font_size=font_size,
                           color=colors[key])

    def _panel_values(self, info, corrupt):
        if corrupt:
            return {
                "biome": "CORROMPIDO",
                "gold": "--",
                "animals": "--",
                "bosses": "--",
            }
        if info:
            return {
                "biome": str(info.get("biome", "-")),
                "gold": str(info.get("gold", 0)),
                "animals": str(info.get("animals_count", 0)),
                "bosses": str(info.get("bosses_defeated", 0)),
            }
        return {"biome": "VAZIO", "gold": "--", "animals": "--", "bosses": "--"}

    def _fit_font_size(self, text, max_width, base_size, min_size=11):
        size = max(min_size, int(base_size))
        while size > min_size and get_font(size).size(str(text))[0] > max_width:
            size -= 1
        return size

    # ------------------------------------------------------------- modals

    def _draw_modal_backdrop(self, surface, pw, ph, border_color=SERTAO_RED):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        pr = pygame.Rect(CENTER_X - pw // 2, CENTER_Y - ph // 2, pw, ph)
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((*SERTAO_PANEL, 248))
        surface.blit(panel, pr.topleft)
        pygame.draw.rect(surface, border_color, pr, 3, border_radius=10)
        return pr

    def _draw_confirm_msg(self, surface):
        pw, ph = 500, 210
        pr = self._draw_modal_backdrop(surface, pw, ph)

        draw_text(surface, "Apagar esta jornada?", (CENTER_X, pr.y + 55),
                  font_size=26, color=SERTAO_GOLD, center=True)
        draw_text(surface, "Todo o progresso deste slot", (CENTER_X, pr.y + 95),
                  font_size=18, color=SERTAO_CREAM, center=True)
        draw_text(surface, "sera perdido.", (CENTER_X, pr.y + 118),
                  font_size=18, color=SERTAO_CREAM, center=True)

        rects = self._confirm_modal_rects()
        cancel_h = rects["cancel"].collidepoint(get_mouse_pos())
        delete_h = rects["delete"].collidepoint(get_mouse_pos())
        draw_sertao_button(surface, rects["cancel"], "CANCELAR", cancel_h)
        draw_sertao_button(surface, rects["delete"], "APAGAR", delete_h)

    def _draw_action_msg(self, surface):
        info = self.info_cache.get(self.action_slot)
        has_run = bool(info and info.get("run_active"))
        rects, pw, ph = self._action_modal_rects(has_run)
        pr = self._draw_modal_backdrop(surface, pw, ph, border_color=SERTAO_BORDER)

        draw_text(surface, "ESCOLHER A\u00c7\u00c3O", (CENTER_X, pr.y + 40),
                  font_size=26, color=SERTAO_GOLD, center=True)
        draw_text(surface, "Escolha uma acao para este save.",
                  (CENTER_X, pr.y + 68), font_size=16, color=SERTAO_CREAM, center=True)

        ret_h = rects["reteam"].collidepoint(get_mouse_pos())
        del_h = rects["delete"].collidepoint(get_mouse_pos())
        back_h = rects["back"].collidepoint(get_mouse_pos())
        draw_sertao_button(surface, rects["reteam"], "ABRIR PARTIDA", ret_h)
        draw_sertao_button(surface, rects["delete"], "APAGAR SAVE", del_h,
                           color=(90, 40, 40) if not del_h else (120, 55, 55))
        draw_sertao_button(surface, rects["back"], "VOLTAR", back_h)

    def _draw_corrupt_msg(self, surface):
        pw, ph = 540, 230
        pr = self._draw_modal_backdrop(surface, pw, ph)

        draw_text(surface, "\u26a0", (CENTER_X, pr.y + 34),
                  font_size=34, color=SERTAO_RED, center=True)
        draw_text(surface, "SAVE CORROMPIDO", (CENTER_X, pr.y + 74),
                  font_size=26, color=SERTAO_RED, center=True)
        draw_text(surface, "O arquivo nao pode ser carregado.",
                  (CENTER_X, pr.y + 108), font_size=17, color=SERTAO_CREAM, center=True)
        draw_text(surface, "Tente recuperar um backup ou apague o slot.",
                  (CENTER_X, pr.y + 132), font_size=15, color=SERTAO_CREAM, center=True)

        rects = self._corrupt_modal_rects()
        rec_h = rects["recover"].collidepoint(get_mouse_pos())
        del_h = rects["delete"].collidepoint(get_mouse_pos())
        can_h = rects["cancel"].collidepoint(get_mouse_pos())
        draw_sertao_button(surface, rects["recover"], "TENTAR RECUPERAR", rec_h)
        draw_sertao_button(surface, rects["delete"], "APAGAR", del_h)
        draw_sertao_button(surface, rects["cancel"], "VOLTAR", can_h)


class SwapAnimalScreen:
    def __init__(self, party, new_animal_id, new_animal_name, assets=None):
        self.party = party
        self.new_animal_id = new_animal_id
        self.new_animal_name = new_animal_name
        self.assets = assets
        self.layout = UILayout()
        self.hover_index = -1
        self.cancel_hover = False
        self.slot_rects = []
        btn_w, btn_h = 380, 60
        start_y = self.layout.body.y + 100
        for i in range(3):
            x = CENTER_X - btn_w // 2
            y = start_y + i * (btn_h + 14)
            self.slot_rects.append(pygame.Rect(x, y, btn_w, btn_h))
        self.cancel_rect = pygame.Rect(CENTER_X - 100, start_y + 3 * (btn_h + 14), 200, 44)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover_index = -1
            self.cancel_hover = False
            for i, r in enumerate(self.slot_rects):
                if i < len(self.party) and r.collidepoint(event.pos):
                    self.hover_index = i
                    break
            if self.cancel_rect.collidepoint(event.pos):
                self.cancel_hover = True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self.slot_rects):
                if i < len(self.party) and r.collidepoint(event.pos):
                    return ("swap", i)
            if self.cancel_rect.collidepoint(event.pos):
                return "cancel"
        return None

    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        draw_text(surface, f"Equipe cheia! Substituir por {self.new_animal_name}?",
                  (CENTER_X, self.layout.header.center_y + 20),
                  font_size=28, color=SERTAO_GOLD, center=True)

        for i in range(3):
            if i < len(self.party):
                self._draw_slot(surface, self.party[i], i)

        is_h = self.cancel_rect.collidepoint(get_mouse_pos())
        draw_sertao_button(surface, self.cancel_rect, "Cancelar", is_h)

    def _draw_slot(self, surface, animal, index):
        r = self.slot_rects[index]
        is_h = self.hover_index == index
        border = SERTAO_GOLD if is_h else SERTAO_BORDER
        bg = (*SERTAO_PANEL, 220)

        panel = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        panel.fill(bg)
        surface.blit(panel, r.topleft)
        pygame.draw.rect(surface, border, r, 2, border_radius=6)

        stage = getattr(animal, "evolution_stage", 0)
        stage_names = ["Base", "Evo 1"]
        if self.assets:
            spr = self.assets.get_animal_sprite(animal.animal_id,
                                               evolution_stage=stage,
                                               max_width=40, max_height=40)
            if spr:
                surface.blit(spr, spr.get_rect(center=(r.x + 25, r.centery)))
            else:
                emoji = ANIMAL_EMOJIS.get(animal.animal_id, "?")
                draw_text(surface, emoji, (r.x + 25, r.y + r.h // 2),
                          font_size=30, color=SERTAO_CREAM, center=True)
        else:
            emoji = ANIMAL_EMOJIS.get(animal.animal_id, "?")
            draw_text(surface, emoji, (r.x + 25, r.y + r.h // 2),
                      font_size=30, color=SERTAO_CREAM, center=True)
        form = stage_names[min(stage, 1)]
        draw_text(surface, f"{animal.name} [{form}]", (r.x + 55, r.y + 14),
                  font_size=20, color=SERTAO_CREAM)
        draw_text(surface, f"Nv {animal.level}", (r.x + 55, r.y + 38),
                  font_size=16, color=SERTAO_LIGHT)
