import os
import pygame
from src.ui.text import get_font


ANIMAL_SPRITE_MAP = {
    "tatu_bola": {"base": "TatuBola.jpeg", "evolution_1": None, "evolution_2": None},
    "lobo_guara": {"base": "LoboGuara.jpeg", "evolution_1": None, "evolution_2": None},
    "arara_azul": {"base": "AraraAzul.jpeg", "evolution_1": None, "evolution_2": None},
    "tamandua_bandeira": {"base": "Tamandua.jpeg", "evolution_1": None, "evolution_2": None},
    "capivara": {"base": "Capivara.jpeg", "evolution_1": None, "evolution_2": None},
    "onca_pintada": {"base": "OnçaPintada.jpeg", "evolution_1": None, "evolution_2": None},
}

EVOLUTION_STAGE_FILES = {0: "base", 1: "evolution_1", 2: "evolution_2"}

ENEMY_SPRITE_MAP = {
    "brasa": "Brasa.jpeg",
    "chamas": "Chamas.jpeg",
    "espirito_de_fogo": "espiritodefogo.jpeg",
    "furacao": "Furacao.jpeg",
    "lobo_de_fogo": "Lobdefogo.jpeg",
    "lobo_alfa_de_fogo": "LoboAlfaDeFogo.jpeg",
    "vendaval_de_fogo": "VendavaldeFogo.jpeg",
}

BACKGROUND_MAP = {
    "main_menu": "Telainicial.jpeg",
    "animal_select": "Telainicial.jpeg",
    "biome_select": "Telainicial.jpeg",
    "settings": "Telainicial.jpeg",
    "acampamento": "Telainicial.jpeg",
    "map": "Mapadajornada.jpeg",
    "combat": "Cenariodeluta.jpeg",
    "event": "Momento de escolha.jpeg",
    "shop": "MercadoseuZé.jpeg",
    "camp": "Momento de escolha.jpeg",
    "level_up": "Momento de escolha.jpeg",
    "rescue": "Momento de escolha.jpeg",
    "cage_reward": "Momento de escolha.jpeg",
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
        for filename in os.listdir(self.images_dir):
            lower = filename.lower()
            if lower.endswith((".jpeg", ".jpg", ".png", ".bmp")):
                self.available_files[filename] = os.path.join(self.images_dir, filename)

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

    def get_enemy_sprite(self, enemy_id, max_width=140, max_height=140):
        return self.get_sprite(enemy_id, is_enemy=True, max_width=max_width, max_height=max_height, flip_horizontal=False)

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
