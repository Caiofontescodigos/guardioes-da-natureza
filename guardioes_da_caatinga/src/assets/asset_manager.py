import os
import pygame
from src.ui.text import get_font


ANIMAL_SPRITE_MAP = {
    "tatu_bola": {"base": "TatuBola.png", "evolution_1": None, "evolution_2": None},
    "lobo_guara": {"base": "LoboGuara.png", "evolution_1": None, "evolution_2": None},
    "arara_azul": {"base": "AraraAzul.png", "evolution_1": None, "evolution_2": None},
    "tamandua_bandeira": {"base": "Tamandua.png", "evolution_1": None, "evolution_2": None},
    "capivara": {"base": "Capivara.png", "evolution_1": None, "evolution_2": None},
    "onca_pintada": {"base": "Onça-pintada.png", "evolution_1": None, "evolution_2": None},
    "harpia": {"base": "Harpia.png", "evolution_1": None, "evolution_2": None},
    "pirarucu": {"base": "Pirarucu.png", "evolution_1": None, "evolution_2": None},
    "onca_do_pantanal": {"base": "OncaDoPantanal.png", "evolution_1": None, "evolution_2": None},
}

EVOLUTION_STAGE_FILES = {0: "base", 1: "evolution_1", 2: "evolution_2"}

# Full art used inside each frame of the legendary animal selection screen.
LEGENDARY_ART_MAP = {
    "harpia": "fundoharpia.png",
    "pirarucu": "fundopirarucu.png",
    "onca_do_pantanal": "fundoOncaPantanal.png",
}

ENEMY_SPRITE_MAP = {
    "brasa": "Brasa.png",
    "chamas": "Chamas.png",
    "espirito_de_fogo": "espiritodefogo.png",
    "furacao": "furacao.png",
    "lobo_de_fogo": "Lobdefogo.png",
    "lobo_alfa_de_fogo": "LoboAlfaDeFogo.png",
    "vendaval_de_fogo": "VendavaldeFogo.png",
}

UI_BUTTON_MAP = {
    "inicio": "Inicio.png",
    "bestiario": "Bestiario.png",
    "inventario": "Inventario.png",
    "missoes": "Missoes.png",
}

# Item artwork used as the clickable buttons in the shop.
SHOP_ITEM_IMAGES = {
    "cruz_dourada": "CruzDourada.png",
    "attack": "PocaodeAtaque.png",
    "defense": "PocaodeDefesa.png",
    "health": "PocaodeCura.png",
}

MAIN_MENU_BUTTON_MAP = {
    "play": "MenuJogar.png",
    "how_to_play": "MenuSobre.png",
    "bestiary": "MenuBestiario.png",
    "quit": "MenuSair.png",
    "leave_match": "MenuSair.png",
    "achievements": "MenuConquistas.png",
    "settings": "MenuConfiguracoes.png",
    "acampamento": "MenuAcampamento.png",
    "inventory": "Inventario.png",
    "missions": "Missoes.png",
}

NODE_ICON_MAP = {
    "combat": "node_combat.png",
    "elite": "node_elite.png",
    "event": "node_event.png",
    "camp": "node_camp.png",
    "shop": "node_shop.png",
    "boss": "node_boss.png",
    "rescue_animal": "node_animal.png",
    "legendary": "node_legendary.png",
}

NODE_CONNECTION_FILENAME = "node_connection.png"

BACKGROUND_MAP = {
    "main_menu": "TelainicialNova.jpeg",
    "how_to_play": "TelainicialNova.jpeg",
    "animal_select": "SeleçãoEquipe.png",
    "legendary_select": "fundolendarios.png",
    "biome_select": "TelainicialNova.jpeg",
    "settings": "TelainicialNova.jpeg",
    "acampamento": "TelainicialNova.jpeg",
    "saves": "TelaSaves.jpeg",
    "map": "Mapadajornada.png",
    "combat": "Cenariodeluta.jpeg",
    "event": "Momento de escolha.jpeg",
    "shop": "ArmazemdoSeuZe.jpeg",
    "camp": "Momento de escolha.jpeg",
    "level_up": "Momento de escolha.jpeg",
    "rescue": "Momento de escolha.jpeg",
    "cage_reward": "Momento de escolha.jpeg",
    "game_over": "TelaGameOver.png",
}

# Locked-animal placeholder supplied with the team-selection artwork.
LOCKED_ANIMAL_FILENAME = "?.png"


# Artwork sheet with the three save panels, kept exactly as supplied.  Each
# bounds tuple is (left, top, right, bottom) in the original image.
SAVE_PANEL_FILENAME = "Saves.png"
SAVE_PANEL_BOUNDS = (
    (10, 19, 1528, 321),
    (10, 351, 1528, 653),
    (10, 675, 1528, 977),
)

# Region-specific art for the journey map.  The generic map stays as the
# fallback for any biome that does not have dedicated art yet.
MAP_BACKGROUND_MAP = {
    "caatinga": "MapaCaatinga.jpeg",
    "cerrado": "MapaCerrado.jpeg",
    "pantanal": "MapaPantanal.jpeg",
    "mata_atlantica": "MapaMataAtlantica.jpeg",
    "pampa": "MapaPampa.jpeg",
    "amazonia": "MapaAmazonia.jpeg",
    "boss": "MapaChefeFase.jpeg",
}


class AssetManager:
    def __init__(self, images_dir):
        self.images_dir = images_dir
        self._cache = {}
        self._surfaces_cache = {}
        self._scan_files()
        self._load_all()

    def _scan_files(self):
        self.available_files = {}
        if not os.path.isdir(self.images_dir):
            print(f"[AssetManager] Pasta de imagens nao encontrada: {self.images_dir}")
            return
        for root, dirs, files in os.walk(self.images_dir):
            dirs.sort()
            for filename in sorted(files):
                lower = filename.lower()
                if not lower.endswith((".jpeg", ".jpg", ".png", ".bmp")):
                    continue
                if filename in self.available_files:
                    print(f"[AssetManager] Imagem duplicada ignorada: {filename} "
                          f"({os.path.join(root, filename)})")
                    continue
                self.available_files[filename] = os.path.join(root, filename)

    def _load_all(self):
        for name, filepath in self.available_files.items():
            try:
                img = pygame.image.load(filepath).convert_alpha()
                self._cache[name] = img
            except pygame.error as e:
                print(f"[AssetManager] Erro ao carregar '{name}': {e}")

    def get_raw(self, filename):
        return self._cache.get(filename)

    def get_sprite(self, entity_id, is_enemy=False, max_width=140, max_height=140,
                   flip_horizontal=False, evolution_stage=0):
        if is_enemy:
            filename = ENEMY_SPRITE_MAP.get(entity_id)
        else:
            filename = self._resolve_animal_sprite(entity_id, evolution_stage)

        if filename is None:
            print(f"[AssetManager] Sprite nao mapeado para '{entity_id}'")
            return None

        img = self._cache.get(filename)
        if img is None:
            print(f"[AssetManager] Arquivo de sprite ausente: {filename} (entidade: {entity_id})")
            return None

        cache_key = f"sprite_{filename}_{max_width}_{max_height}_{flip_horizontal}"
        if cache_key in self._surfaces_cache:
            return self._surfaces_cache[cache_key]

        scaled = pygame.transform.smoothscale(img, self._fit_size(img, max_width, max_height))
        if flip_horizontal:
            scaled = pygame.transform.flip(scaled, True, False)
        self._surfaces_cache[cache_key] = scaled
        return scaled

    def _resolve_animal_sprite(self, animal_id, evolution_stage):
        """Resolve the sprite filename for an animal, walking the evolution
        sprite chain from the requested stage down to the base form so a
        missing evolution sprite falls back to the previous form's image.
        Returns None when no sprite is available at all."""
        entry = ANIMAL_SPRITE_MAP.get(animal_id)
        if isinstance(entry, str):
            return entry
        if not isinstance(entry, dict):
            return None
        for stage in range(max(0, evolution_stage), -1, -1):
            key = EVOLUTION_STAGE_FILES.get(stage)
            fname = entry.get(key)
            if fname and fname in self._cache:
                return fname
        return None

    def get_animal_sprite(self, animal_id, evolution_stage=0, max_width=140, max_height=140):
        return self.get_sprite(animal_id, is_enemy=False,
                               max_width=max_width, max_height=max_height,
                               evolution_stage=evolution_stage)

    def get_legendary_art(self, animal_id, target_width, target_height):
        """Return the full legendary artwork cropped to fill a frame hole.

        Each legendary animal has a dedicated environment illustration.  The
        image is scaled to cover ``target_width`` x ``target_height`` and then
        centre-cropped, so the frame is completely filled without distortion.
        """
        filename = LEGENDARY_ART_MAP.get(animal_id)
        if filename is None:
            return None

        img = self._cache.get(filename)
        if img is None:
            print(f"[AssetManager] Arte lendaria ausente: {filename} "
                  f"(animal: {animal_id})")
            return None

        target_width = max(1, int(target_width))
        target_height = max(1, int(target_height))
        cache_key = f"legendary_art_{filename}_{target_width}_{target_height}"
        cached = self._surfaces_cache.get(cache_key)
        if cached is not None:
            return cached

        src_w, src_h = img.get_size()
        ratio = max(target_width / src_w, target_height / src_h)
        scaled_w = max(target_width, int(round(src_w * ratio)))
        scaled_h = max(target_height, int(round(src_h * ratio)))
        scaled = pygame.transform.smoothscale(img, (scaled_w, scaled_h))
        left = (scaled_w - target_width) // 2
        top = (scaled_h - target_height) // 2
        art = scaled.subsurface(
            (left, top, target_width, target_height)).copy()
        self._surfaces_cache[cache_key] = art
        return art

    def has_legendary_frame(self):
        """True when the legendary selection artwork was loaded."""
        return "fundolendarios.png" in self._cache

    def get_enemy_sprite(self, enemy_id, max_width=140, max_height=140):
        return self.get_sprite(enemy_id, is_enemy=True, max_width=max_width, max_height=max_height, flip_horizontal=False)

    def get_ui_button(self, name, target_width=190):
        """Return a cached, proportionally scaled UI button image.

        The button artwork lives in the same images directory as the rest of
        the game art and is mapped by :data:`UI_BUTTON_MAP`.
        """
        filename = UI_BUTTON_MAP.get(name)
        if filename is None:
            print(f"[AssetManager] Botao de UI nao mapeado: '{name}'")
            return None

        img = self._cache.get(filename)
        if img is None:
            print(f"[AssetManager] Arquivo de botao ausente: {filename}")
            return None

        cache_key = f"uibtn_{filename}_{target_width}"
        if cache_key in self._surfaces_cache:
            return self._surfaces_cache[cache_key]

        w, h = img.get_size()
        target_height = max(1, int(h * target_width / w))
        scaled = pygame.transform.smoothscale(img, (target_width, target_height))
        self._surfaces_cache[cache_key] = scaled
        return scaled

    def get_main_menu_button(self, action, target_width=380):
        """Return a cached main-menu button image for ``action``."""
        filename = MAIN_MENU_BUTTON_MAP.get(action)
        if filename is None:
            print(f"[AssetManager] Botao de menu nao mapeado: '{action}'")
            return None

        img = self._cache.get(filename)
        if img is None:
            print(f"[AssetManager] Arquivo de botao de menu ausente: {filename}")
            return None

        cache_key = f"menubtn_{filename}_{target_width}"
        if cache_key in self._surfaces_cache:
            return self._surfaces_cache[cache_key]

        w, h = img.get_size()
        target_height = max(1, int(h * target_width / w))
        scaled = pygame.transform.smoothscale(img, (target_width, target_height))
        self._surfaces_cache[cache_key] = scaled
        return scaled

    def get_node_icon(self, node_type, target_height=52):
        """Return a cached map-node icon scaled to ``target_height``.

        ``node_type`` may be a :class:`NodeType` member or its string value.
        The source art already has a transparent background (processed at
        import time), so it can be blitted directly over the parchment.
        """
        key = getattr(node_type, "value", node_type)
        filename = NODE_ICON_MAP.get(key)
        if filename is None:
            print(f"[AssetManager] Icone de no nao mapeado: '{key}'")
            return None

        img = self._cache.get(filename)
        if img is None:
            print(f"[AssetManager] Arquivo de icone ausente: {filename}")
            return None

        cache_key = f"nodeicon_{filename}_{target_height}"
        if cache_key in self._surfaces_cache:
            return self._surfaces_cache[cache_key]

        w, h = img.get_size()
        target_width = max(1, int(w * target_height / h))
        scaled = pygame.transform.smoothscale(img, (target_width, target_height))
        self._surfaces_cache[cache_key] = scaled
        return scaled

    def get_node_connection(self, thickness=9):
        """Return the cached map-path connector strip scaled to ``thickness``."""
        img = self._cache.get(NODE_CONNECTION_FILENAME)
        if img is None:
            return None

        thickness = max(1, int(thickness))
        cache_key = f"nodeconn_{NODE_CONNECTION_FILENAME}_{thickness}"
        if cache_key in self._surfaces_cache:
            return self._surfaces_cache[cache_key]

        w, h = img.get_size()
        target_width = max(1, int(round(w * thickness / h)))
        scaled = pygame.transform.smoothscale(img, (target_width, thickness))
        self._surfaces_cache[cache_key] = scaled
        return scaled

    def get_background(self, screen_key, screen_width, screen_height):
        filename = BACKGROUND_MAP.get(screen_key)
        if filename is None:
            print(f"[AssetManager] Background nao mapeado para tela '{screen_key}'")
            return None

        img = self._cache.get(filename)
        if img is None:
            print(f"[AssetManager] Arquivo de background ausente: {filename} (tela: {screen_key})")
            return None

        cache_key = f"bg_{filename}_{screen_width}_{screen_height}"
        if cache_key in self._surfaces_cache:
            return self._surfaces_cache[cache_key]

        scaled = pygame.transform.smoothscale(img, (screen_width, screen_height))
        self._surfaces_cache[cache_key] = scaled
        return scaled

    def get_save_panel(self, index, target_width):
        """Return one of the three original save panels, scaled uniformly.

        ``index`` is 0-based.  The panel is cropped from ``Saves.png`` at
        runtime; the source artwork is never redrawn or stretched.
        """
        if index < 0 or index >= len(SAVE_PANEL_BOUNDS):
            return None
        img = self._cache.get(SAVE_PANEL_FILENAME)
        if img is None:
            print(f"[AssetManager] Arte de saves ausente: {SAVE_PANEL_FILENAME}")
            return None

        left, top, right, bottom = SAVE_PANEL_BOUNDS[index]
        src_w, src_h = right - left, bottom - top
        target_width = max(1, int(target_width))
        target_height = max(1, int(round(src_h * target_width / src_w)))
        cache_key = f"savepanel_{index}_{target_width}_{target_height}"
        cached = self._surfaces_cache.get(cache_key)
        if cached is not None:
            return cached

        panel = img.subsurface(pygame.Rect(left, top, src_w, src_h)).copy()
        panel = pygame.transform.smoothscale(panel, (target_width, target_height))
        self._surfaces_cache[cache_key] = panel
        return panel

    def get_shop_item_image(self, item_id, max_width, max_height):
        """Return a shop item card fitted inside the available slot."""
        filename = SHOP_ITEM_IMAGES.get(item_id)
        if filename is None:
            print(f"[AssetManager] Carta de loja nao mapeada: '{item_id}'")
            return None
        return self.get_fitted_image(filename, max_width, max_height)

    def get_fitted_image(self, filename, max_width, max_height):
        """Load an image and fit it inside a box, preserving its aspect ratio."""
        img = self._cache.get(filename)
        if img is None:
            print(f"[AssetManager] Imagem ausente: {filename}")
            return None

        max_width = max(1, int(max_width))
        max_height = max(1, int(max_height))
        cache_key = f"fitted_{filename}_{max_width}_{max_height}"
        cached = self._surfaces_cache.get(cache_key)
        if cached is not None:
            return cached

        scaled = pygame.transform.smoothscale(
            img, self._fit_size(img, max_width, max_height))
        self._surfaces_cache[cache_key] = scaled
        return scaled

    def get_locked_animal_image(self, max_width=180, max_height=180):
        """Return the supplied question-mark art for locked animal cards."""
        return self.get_fitted_image(
            LOCKED_ANIMAL_FILENAME, max_width, max_height)

    def get_background_cover(self, screen_key, screen_width, screen_height):
        """Return a background scaled to cover the screen without distortion."""
        filename = BACKGROUND_MAP.get(screen_key)
        if filename is None:
            print(f"[AssetManager] Background nao mapeado para tela '{screen_key}'")
            return None

        img = self._cache.get(filename)
        if img is None:
            print(f"[AssetManager] Arquivo de background ausente: {filename} (tela: {screen_key})")
            return None

        screen_width = max(1, int(screen_width))
        screen_height = max(1, int(screen_height))
        cache_key = f"bgcover_{filename}_{screen_width}_{screen_height}"
        cached = self._surfaces_cache.get(cache_key)
        if cached is not None:
            return cached

        src_w, src_h = img.get_size()
        ratio = max(screen_width / src_w, screen_height / src_h)
        scaled_w = max(screen_width, int(src_w * ratio))
        scaled_h = max(screen_height, int(src_h * ratio))
        scaled = pygame.transform.smoothscale(img, (scaled_w, scaled_h))
        left = (scaled_w - screen_width) // 2
        top = (scaled_h - screen_height) // 2
        cover = scaled.subsurface(
            pygame.Rect(left, top, screen_width, screen_height)).copy()
        self._surfaces_cache[cache_key] = cover
        return cover

    def get_map_background(self, biome_id, boss_phase, screen_width, screen_height):
        """Return the journey map art for a biome, or the boss art.

        When the biome has no dedicated art (or the file is missing), the
        generic journey map is used so older saves and future biomes keep
        working.
        """
        key = "boss" if boss_phase else biome_id
        filename = MAP_BACKGROUND_MAP.get(key)

        img = self._cache.get(filename) if filename else None
        if img is None:
            filename = BACKGROUND_MAP["map"]
            img = self._cache.get(filename)
        if img is None:
            print(f"[AssetManager] Fundo de mapa ausente: {filename}")
            return None

        cache_key = f"mapbg_{filename}_{screen_width}_{screen_height}"
        if cache_key in self._surfaces_cache:
            return self._surfaces_cache[cache_key]

        scaled = pygame.transform.smoothscale(img, (screen_width, screen_height))
        self._surfaces_cache[cache_key] = scaled
        return scaled

    def _fit_size(self, img, max_w, max_h):
        w, h = img.get_size()
        ratio = min(max_w / w, max_h / h)
        return (max(1, int(w * ratio)), max(1, int(h * ratio)))

    def draw_background(self, surface, screen_key):
        bg = self.get_background(screen_key, surface.get_width(), surface.get_height())
        if bg:
            surface.blit(bg, (0, 0))
        else:
            surface.fill((20, 15, 30))

    def draw_background_cover(self, surface, screen_key):
        bg = self.get_background_cover(
            screen_key, surface.get_width(), surface.get_height())
        if bg:
            surface.blit(bg, (0, 0))
        else:
            surface.fill((20, 15, 30))

    def draw_sprite(self, surface, entity_id, center_x, center_y, is_enemy=False, max_width=140, max_height=140):
        sprite = self.get_sprite(entity_id, is_enemy=is_enemy, max_width=max_width, max_height=max_height)
        if sprite:
            rect = sprite.get_rect(center=(center_x, center_y))
            surface.blit(sprite, rect)
        else:
            self._draw_placeholder(surface, center_x, center_y, max_width, max_height, is_enemy)

    def _draw_placeholder(self, surface, cx, cy, w, h, is_enemy):
        rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
        color = (80, 40, 40) if is_enemy else (40, 60, 80)
        pygame.draw.rect(surface, color, rect, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 200), rect, 2, border_radius=8)
        font = get_font(16)
        text = font.render("?", True, (200, 200, 200))
        text_rect = text.get_rect(center=(cx, cy))
        surface.blit(text, text_rect)
