from src.combat.combat import CombatSystem
from src.entities.animal import Animal
from src.entities.enemy import create_enemy_group, create_elite_enemy, create_boss
from src.map.map_generator import MapGenerator
from src.progression.level_up import LevelUpSystem
from src.save.save_manager import SaveManager
from src.state import GameState, NodeType
from src.ui.map_ui import MapUI
from src.ui.combat_ui import CombatUI
from src.assets.asset_manager import AssetManager
from src.audio.music_manager import MusicManager
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WHITE, BLACK, GRAY, RED, GREEN,
                    BLUE, YELLOW, BROWN, CREAM, DARK_GRAY, ORANGE, PURPLE,
                    DARK_BROWN, GOLD, load_biomes, load_animals, load_events,
                    load_global_settings, save_global_settings,
                    IMAGES_DIR, MUSIC_DIR)
import random
import pygame
import sys
import time

from src.ui.layout import get_mouse_pos
from src.ui.text import (draw_text, draw_text_centered, draw_text_centered_in_rect,
                         draw_text_left, draw_text_right, draw_text_block,
                         draw_text_block_colored, draw_multiline_centered,
                         draw_fitted_text, draw_button_text,
                         wrap_text, wrap_text_chars, get_font, text_size)

SERTAO_DARK = (25, 18, 10)
SERTAO_PANEL = (45, 32, 18)
SERTAO_BORDER = (139, 90, 43)
SERTAO_LIGHT = (180, 140, 60)
SERTAO_CREAM = (255, 240, 210)
SERTAO_GOLD = (255, 215, 0)
SERTAO_GREEN = (110, 170, 90)

EVENT_ICONS = ["Procurar", "Curar", "Fugir", "Lutar", "Explorar", "Descansar", "Comprar", "Ignorar"]

MAX_PARTY_SIZE = 3

ANIMAL_EMOJIS = {
    "tatu_bola": "\U0001f994",
    "lobo_guara": "\U0001f98a",
    "arara_azul": "\U0001f426",
    "tamandua_bandeira": "\U0001f41c",
    "capivara": "\U0001f9ab",
    "onca_pintada": "\U0001f406",
}

ENCOUNTER_TEXTS = [
    "Voce encontrou um animal ferido escondido entre a vegetacao.",
    "Um animal preso conseguiu escapar das criaturas elementais.",
    "Um animal silvestre aparece, buscando protecao.",
    "Voce ouve um gemido fraco e encontra um animal necessitando de ajuda.",
]



def _draw_panel(surface, rect, fill_color, border_color, radius=14, alpha=230,
                shadow=True, border_width=2):
    """Draw a reusable rounded panel with a soft shadow."""
    rect = pygame.Rect(rect)
    if shadow:
        shadow_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 120), (6, 6, rect.w, rect.h),
                         border_radius=radius)
        surface.blit(shadow_surf, (rect.x, rect.y))
    panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*fill_color, alpha), (0, 0, rect.w, rect.h),
                     border_radius=radius)
    surface.blit(panel, rect.topleft)
    pygame.draw.rect(surface, border_color, rect, border_width, border_radius=radius)
    return rect


def draw_bar(surface, x, y, width, height, current, maximum, fill_color=GREEN):
    pygame.draw.rect(surface, GRAY, (x, y, width, height))
    fill_width = int((current / maximum) * width) if maximum > 0 else 0
    pygame.draw.rect(surface, fill_color, (x, y, fill_width, height))
    pygame.draw.rect(surface, WHITE, (x, y, width, height), 1)
    font = get_font(16)
    text = font.render(f"{current}/{maximum}", True, WHITE)
    text_rect = text.get_rect(center=(x + width // 2, y + height // 2))
    surface.blit(text, text_rect)


def draw_sertao_button(surface, rect, text, is_hovered=False, enabled=True, color=None):
    if color is None:
        color = SERTAO_PANEL

    if not enabled:
        bg = (40, 30, 20)
        border_c = GRAY
        text_color = GRAY
    elif is_hovered:
        bg = tuple(min(255, c + 30) for c in color)
        border_c = SERTAO_GOLD
        text_color = SERTAO_GOLD
    else:
        bg = color
        border_c = SERTAO_BORDER
        text_color = SERTAO_CREAM

    pygame.draw.rect(surface, bg, rect, border_radius=8)
    pygame.draw.rect(surface, border_c, rect, 2, border_radius=8)
    draw_button_text(surface, text, rect, color=text_color, font_size=24)


class Game:
    def __init__(self):
        pygame.init()
        self.global_settings = load_global_settings()
        self.fullscreen = self.global_settings.get("fullscreen", False)
        self.base_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen = self.base_surface
        self._apply_display_mode(self.fullscreen)
        pygame.display.set_caption("Guardioes da Caatinga")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MAIN_MENU

        self.save_manager = SaveManager()
        self.save_manager.set_status_callback(self._on_save_status)
        from src.save.bestiary_manager import BestiaryManager
        self.bestiary_manager = BestiaryManager(self.save_manager)
        self.save_data = None
        self.active_slot = None

        self.save_status_message = None
        self.save_status_success = True
        self.save_status_timer = 0
        self.save_status_duration = 3

        self.level_up_system = LevelUpSystem()
        self.assets = AssetManager(IMAGES_DIR)
        self.music_manager = MusicManager(MUSIC_DIR)
        self.music_manager.set_volume(self.global_settings.get("music_volume", 0.7))

        self.party = []
        self.current_biome = None
        self.map_generator = None
        self.combat_system = None
        self.current_event = None

        self.map_ui = None
        self.combat_ui = None
        self.level_up_offers = None
        self.combat_rewards = None
        self.victory_message = ""
        self.pending_rescue_animal = None
        self.pending_bonus_rescue = None

        self.node_xp_bonus = 0
        self.node_gold_bonus = 1

        self.event_hover = -1
        self.shop_hover = -1
        self.victory_time = 0
        self.victory_xp_gained = 0
        self.victory_gold_gained = 0
        self.level_up_hover = -1
        self.menu_fade_alpha = 0

        self.pending_level_ups = 0
        self.pending_level_up_animals = []
        self.current_level_up_animal = None
        self.next_biome_pending = None

        self.encounter_animal_id = None
        self.encounter_hover = -1
        self.encounter_swap_hover = -1
        self.encounter_animal_level = 1
        self.encounter_text = ""
        self.encounter_step = "main"
        self.encounter_swap_index = -1

        self.cage_reward_screen = None
        self.pending_cage_animal = None
        self.journey_select_screen = None
        self.swap_screen = None
        self.swap_pending_new_id = None
        self.swap_pending_new_name = None
        self.swap_return_state = GameState.VICTORY

        self._run_start_time = 0

        self.setup_screens()

    def _apply_display_mode(self, fullscreen):
        if fullscreen:
            try:
                self.actual_screen = pygame.display.set_mode(
                    (0, 0), pygame.FULLSCREEN)
            except pygame.error as e:
                print(f"[Game] Tela cheia indisponivel, usando janela: {e}")
                self.fullscreen = False
                self.actual_screen = pygame.display.set_mode(
                    (SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            self.actual_screen = pygame.display.set_mode(
                (SCREEN_WIDTH, SCREEN_HEIGHT))
        self._compute_scaling()

    def _compute_scaling(self):
        win_w, win_h = self.actual_screen.get_size()
        ratio = min(win_w / SCREEN_WIDTH, win_h / SCREEN_HEIGHT)
        self.scale = max(0.01, ratio)
        self.scaled_w = int(SCREEN_WIDTH * self.scale)
        self.scaled_h = int(SCREEN_HEIGHT * self.scale)
        self.scaled_offset_x = (win_w - self.scaled_w) // 2
        self.scaled_offset_y = (win_h - self.scaled_h) // 2
        from src.ui.layout import update_mouse_transform
        update_mouse_transform(self.scale, self.scaled_offset_x, self.scaled_offset_y)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self._apply_display_mode(self.fullscreen)
        self.global_settings["fullscreen"] = self.fullscreen
        if self.save_data:
            if "settings" not in self.save_data:
                self.save_data["settings"] = {}
            self.save_data["settings"]["fullscreen"] = self.fullscreen
        save_global_settings(self.global_settings)
        if self.save_data:
            self.save_manager.save_game(self.save_data)
        self._notify_save("Modo de tela alterado")

    def _on_save_status(self, phase, success=True, message=None):
        if phase == "saving":
            self.save_status_message = "\U0001f4be SALVANDO..."
            self.save_status_success = None
            self.save_status_timer = 0.55
        else:
            self.save_status_message = ("\u2713 JOGO SALVO" if success
                                        else "Erro ao salvar")
            self.save_status_success = bool(success)
            self.save_status_timer = 2.5

    def _notify_save(self, message):
        self.save_status_message = message
        self.save_status_success = True
        self.save_status_timer = self.save_status_duration

    def _screen_to_virtual(self, pos):
        if pos is None:
            return pos
        px, py = pos
        vx = (px - self.scaled_offset_x) / self.scale
        vy = (py - self.scaled_offset_y) / self.scale
        return (int(vx), int(vy))

    @property
    def current_animal(self):
        return self.party[0] if self.party else None

    def _continue_save(self, slot):
        if self.save_manager.get_slot_status(slot) != "ok":
            return
        data = self.save_manager.load_slot(slot)
        if not data or not data.get("run_active"):
            return
        self.save_data = data
        self.active_slot = slot
        self.save_manager.active_slot = slot
        self._rebuild_party_from_save()
        self.setup_screens()
        self._resume_saved_run()

    def _resume_saved_run(self):
        run = self.save_data.get("run")
        biome = run.get("current_biome") if isinstance(run, dict) else None
        map_data = run.get("map") if isinstance(run, dict) else None
        if biome and map_data and isinstance(map_data, dict) and biome in load_biomes():
            try:
                restored = MapGenerator.from_dict(map_data)
                if not restored.is_map_complete():
                    self.current_biome = biome
                    self.map_generator = restored
                    self.map_ui = None
                    self._run_start_time = time.time()
                    self.music_manager.start_playlist()
                    self.state = GameState.MAP
                    return
            except Exception as e:
                print(f"[Game] Falha ao restaurar run: {e}")

        biomes = self.save_data.get("unlocked_biomes", ["caatinga"])
        self.current_biome = biomes[-1] if biomes else "caatinga"
        self.start_new_run()

    def _start_new_journey(self, slot):
        if self.save_manager.get_slot_status(slot) == "ok":
            return
        self.save_data = self.save_manager.create_save()
        self.active_slot = slot
        self.save_manager.active_slot = slot
        self.party = []
        self.setup_screens()
        self.save_manager.save_game(self.save_data)
        self.state = GameState.ANIMAL_SELECT

    def _sync_party_from_selection(self):
        if not self.save_data:
            return
        new_party = []
        for aid in self.animal_select.selected[:MAX_PARTY_SIZE]:
            self.save_data = self.save_manager.add_unlocked_animal(self.save_data, aid)
            animal = Animal(aid)
            animal.unlocked = True
            self.save_manager.restore_animal_stats(animal, self.save_data)
            animal.check_evolution()
            animal.hp = animal.max_hp
            new_party.append(animal)
        self.party = new_party
        self.save_data = self.save_manager.save_party(self.save_data, self.party)

    def _start_initial_run(self):
        biomes = self.save_data.get("unlocked_biomes", ["caatinga"])
        self.current_biome = biomes[0] if biomes else "caatinga"
        self.start_new_run()
        self._save_permanent_data()

    def _rebuild_party_from_save(self):
        if not self.save_data:
            self.party = []
            return
        party_ids = self.save_manager.load_party_ids(self.save_data)
        self.party = []
        for aid in party_ids:
            animal = Animal(aid)
            animal.unlocked = True
            self.save_manager.restore_animal_stats(animal, self.save_data)
            animal.check_evolution()
            self.party.append(animal)
        if not self.party:
            animal = Animal("tatu_bola")
            animal.unlocked = True
            self.save_manager.restore_animal_stats(animal, self.save_data)
            animal.hp = animal.max_hp
            self.party = [animal]
            self.save_data = self.save_manager.save_animal_stats(self.save_data, animal)

    def setup_screens(self):
        from src.ui.menu import (MainMenu, AnimalSelectScreen, BiomeSelectScreen,
                                  SettingsScreen, BestiaryScreen, AcampamentoScreen,
                                  JourneySelectScreen)
        self.main_menu = MainMenu(self.assets)
        unlocked = self.save_data.get("unlocked_animals", ["tatu_bola"]) if self.save_data else ["tatu_bola"]
        biomes = self.save_data.get("unlocked_biomes", ["caatinga"]) if self.save_data else ["caatinga"]
        self.animal_select = AnimalSelectScreen(unlocked, self.assets, self.save_data or {})
        self.biome_select = BiomeSelectScreen(biomes, self.assets)
        self.settings_screen = SettingsScreen(self.assets)
        self.settings_screen.set_fullscreen(self.fullscreen)
        self.bestiary_screen = BestiaryScreen(self.save_data or {}, self.assets)
        self.acampamento_screen = AcampamentoScreen(self.save_data or {}, self.assets, self.party)
        self.journey_select_screen = JourneySelectScreen(self.save_manager, self.assets)
        self.cage_reward_screen = None

    def _save_run_state(self):
        if not self.save_data:
            return
        if self.map_generator is not None and self.state != GameState.GAME_OVER:
            self.save_data["run"] = {
                "current_biome": self.current_biome,
                "map": self.map_generator.to_dict(),
            }
            self.save_data["run_active"] = True
        else:
            self.save_data["run"] = None
            self.save_data["run_active"] = False

    def _save_permanent_data(self):
        if not self.save_data:
            return
        for animal in self.party:
            self.save_data = self.save_manager.save_animal_stats(
                self.save_data, animal)
        self.save_data = self.save_manager.save_party(self.save_data, self.party)
        if self._run_start_time > 0:
            elapsed = time.time() - self._run_start_time
            self.save_data["play_time"] = self.save_data.get("play_time", 0) + elapsed
            self._run_start_time = time.time()
        self._save_run_state()
        self.save_manager.save_game(self.save_data)

    def _defeat_run(self):
        self.map_generator = None
        self.combat_system = None
        self.combat_ui = None
        self._save_permanent_data()
        self.music_manager.stop()
        self.state = GameState.GAME_OVER

    def _convert_event(self, event):
        if hasattr(event, 'pos'):
            event.pos = self._screen_to_virtual(event.pos)
        if event.type == pygame.MOUSEWHEEL:
            pass
        return event

    def run(self):
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                if event.type == pygame.QUIT:
                    self._save_permanent_data()
                    self.running = False
                    return
                self.music_manager.update(event)
            self.handle_events_clone(events)
            self._save_status_update()
            self.update()
            self.render()
            self.clock.tick(FPS)
        pygame.quit()

    def handle_events_clone(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    continue
            if hasattr(event, 'pos'):
                event.pos = self._screen_to_virtual(event.pos)
            if hasattr(event, 'rel'):
                event.rel = self._screen_to_virtual(event.rel)
            self.handle_event_single(event)

    def handle_event_single(self, event):
        if event.type == pygame.QUIT:
            return

        if self.state == GameState.MAIN_MENU:
            self.music_manager.stop()
            result = self.main_menu.handle_event(event)
            if result is not None:
                actions = {
                    0: self._open_journey_select,
                    1: self._open_bestiary,
                    2: self._open_acampamento,
                    3: lambda: setattr(self, 'state', GameState.SETTINGS),
                    4: self._quit_game,
                }
                if result in actions:
                    actions[result]()

        elif self.state == GameState.ANIMAL_SELECT:
            result = self.animal_select.handle_event(event)
            if result == "back":
                if self.animal_select.reteam_mode:
                    self._open_journey_select()
                else:
                    self.state = GameState.MAIN_MENU
            elif result == "start":
                if self.animal_select.selected:
                    self._sync_party_from_selection()
                    self._start_initial_run()
            elif isinstance(result, tuple) and result[0] == "reteam_confirm":
                self._finish_reteam()
            elif isinstance(result, tuple) and result[0] == "toggle":
                self._sync_party_from_selection()
                self._save_permanent_data()

        elif self.state == GameState.BIOME_SELECT:
            result = self.biome_select.handle_event(event)
            if result == "back":
                self.state = GameState.MAIN_MENU
            elif result:
                self.current_biome = result
                self.start_new_run()

        elif self.state == GameState.MAP:
            self.handle_map_events(event)

        elif self.state == GameState.COMBAT:
            self.handle_combat_events(event)

        elif self.state == GameState.EVENT:
            self.handle_event_screen(event)

        elif self.state == GameState.SHOP:
            self.handle_shop_events(event)

        elif self.state == GameState.CAMP:
            self.handle_camp_events(event)

        elif self.state == GameState.LEVEL_UP:
            self.handle_level_up_events(event)

        elif self.state == GameState.RESCUE_ANIMAL:
            self.handle_rescue_events(event)

        elif self.state == GameState.SETTINGS:
            result = self.settings_screen.handle_event(event)
            if isinstance(result, tuple) and result[0] == "toggle_fullscreen":
                self.toggle_fullscreen()
                self.settings_screen.set_fullscreen(self.fullscreen)
            elif result is True:
                self.state = GameState.MAIN_MENU

        elif self.state == GameState.ACAMPAMENTO:
            self.handle_acampamento_events(event)

        elif self.state == GameState.BESTIARY:
            if self.bestiary_screen:
                result = self.bestiary_screen.handle_event(event)
                if result == "back":
                    self.state = GameState.MAIN_MENU

        elif self.state == GameState.SAVES:
            self.handle_saves_events(event)

        elif self.state == GameState.SWAP_ANIMAL:
            self.handle_swap_events(event)

        elif self.state == GameState.GAME_OVER:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for animal in self.party:
                    if not animal.is_alive or animal.hp <= 0:
                        animal.hp = max(1, animal.max_hp // 4)
                        animal.is_alive = True
                self.map_generator = None
                self._save_permanent_data()
                self.music_manager.stop()
                self.state = GameState.MAIN_MENU
                self.map_ui = None
                self.combat_system = None
                self.combat_ui = None
                self.pending_level_ups = 0
                self.pending_level_up_animals = []
                self.current_level_up_animal = None
                self.pending_evolutions = []
                self.current_evolution_animal = None
                self.current_evolution_stage = 0
                self.next_biome_pending = None
                self.pending_rescue_animal = None
                self.pending_bonus_rescue = None
                self.encounter_animal_id = None
                self.encounter_step = "main"
                self.encounter_swap_index = -1
                self.cage_reward_screen = None
                self.swap_screen = None
                self.setup_screens()

        elif self.state == GameState.VICTORY:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.next_biome_pending:
                    self.current_biome = self.next_biome_pending
                    self.next_biome_pending = None
                    self.start_new_run()
                    self._save_permanent_data()
                elif self.map_generator and self.map_generator.is_map_complete():
                    self.map_generator = None
                    self._save_permanent_data()
                    self.state = GameState.MAIN_MENU
                    self.map_ui = None
                    self.setup_screens()
                else:
                    self._save_permanent_data()
                    self.music_manager.resume_playlist()
                    self.state = GameState.MAP

        elif self.state == GameState.PAUSE:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = GameState.MAP
                elif event.key == pygame.K_q:
                    self._save_permanent_data()
                    self.music_manager.stop()
                    self.state = GameState.MAIN_MENU
                    self.map_ui = None
                    self.combat_system = None
                    self.combat_ui = None
                    self.pending_level_ups = 0
                    self.pending_level_up_animals = []
                    self.current_level_up_animal = None
                    self.pending_evolutions = []
                    self.current_evolution_animal = None
                    self.current_evolution_stage = 0
                    self.next_biome_pending = None
                    self.pending_bonus_rescue = None
                    self.encounter_animal_id = None
                    self.encounter_step = "main"
                    self.encounter_swap_index = -1
                    self.cage_reward_screen = None
                    self.swap_screen = None
                    self.setup_screens()

        elif self.state == GameState.ANIMAL_ENCOUNTER:
            self.handle_animal_encounter_events(event)

        elif self.state == GameState.EVOLUTION:
            self.handle_evolution_events(event)

        elif self.state == GameState.CAGE_REWARD:
            if self.cage_reward_screen:
                result = self.cage_reward_screen.handle_event(event)
                if result == "continue":
                    self.cage_reward_screen = None
                    if self.pending_cage_animal:
                        self._add_to_party(self.pending_cage_animal, return_state=GameState.VICTORY)
                        self.pending_cage_animal = None
                    self._save_permanent_data()
                    self.victory_message = f"Vitoria! +{self.victory_xp_gained} XP, +{self.victory_gold_gained} Gold"
                    self.music_manager.resume_playlist()
                    if self.state != GameState.SWAP_ANIMAL:
                        self.state = GameState.VICTORY

    def _save_status_update(self):
        if self.save_status_timer > 0:
            self.save_status_timer -= 1 / FPS

    def _open_acampamento(self):
        from src.ui.menu import AcampamentoScreen
        self.acampamento_screen = AcampamentoScreen(self.save_data, self.assets, self.party)
        self.state = GameState.ACAMPAMENTO

    def _open_bestiary(self):
        from src.ui.menu import BestiaryScreen
        self.bestiary_screen = BestiaryScreen(self.save_data or {}, self.assets)
        self.state = GameState.BESTIARY

    def _open_journey_select(self):
        from src.ui.menu import JourneySelectScreen
        self.journey_select_screen = JourneySelectScreen(self.save_manager, self.assets)
        self.state = GameState.SAVES

    def _open_reteam(self, slot):
        if self.save_manager.get_slot_status(slot) != "ok":
            return
        data = self.save_manager.load_slot(slot)
        if not data:
            return
        self.save_data = data
        self.active_slot = slot
        self.save_manager.active_slot = slot
        self.party = []
        self._rebuild_party_from_save()
        self.setup_screens()
        from src.ui.menu import AnimalSelectScreen
        unlocked = self.save_data.get("unlocked_animals", ["tatu_bola"])
        self.animal_select = AnimalSelectScreen(
            unlocked, self.assets, self.save_data,
            max_selection=MAX_PARTY_SIZE, reteam_mode=True)
        self.state = GameState.ANIMAL_SELECT

    def _finish_reteam(self):
        if not self.animal_select.selected:
            return
        self._sync_party_from_selection()
        biomes = self.save_data.get("unlocked_biomes", ["caatinga"])
        self.current_biome = biomes[0] if biomes else "caatinga"
        self.start_new_run()
        self._save_permanent_data()

    def handle_saves_events(self, event):
        if not self.journey_select_screen:
            return
        result = self.journey_select_screen.handle_event(event)
        if result is None:
            return
        if result == "back":
            self.state = GameState.MAIN_MENU
            self.setup_screens()
        elif isinstance(result, tuple) and result[0] == "continue":
            self._continue_save(result[1])
        elif isinstance(result, tuple) and result[0] == "reteam":
            self._open_reteam(result[1])
        elif isinstance(result, tuple) and result[0] == "new":
            self._start_new_journey(result[1])
        elif isinstance(result, tuple) and result[0] == "deleted":
            from src.ui.menu import JourneySelectScreen
            if self.active_slot == result[1]:
                self.active_slot = None
                self.save_manager.active_slot = None
                self.save_data = None
                self.party = []
                self.journey_select_screen = JourneySelectScreen(
                    self.save_manager, self.assets)

    def handle_swap_events(self, event):
        if not self.swap_screen:
            return
        result = self.swap_screen.handle_event(event)
        if result is None:
            return
        if result == "cancel":
            self.swap_screen = None
            self.state = self.swap_return_state
        elif isinstance(result, tuple) and result[0] == "swap":
            idx = result[1]
            old_animal = self.party[idx]
            self.save_data = self.save_manager.save_animal_stats(self.save_data, old_animal)
            new_animal = Animal(self.swap_pending_new_id)
            new_animal.unlocked = True
            self.save_manager.restore_animal_stats(new_animal, self.save_data)
            new_animal.check_evolution()
            new_animal.hp = new_animal.max_hp
            self.party[idx] = new_animal
            self.save_data = self.save_manager.save_party(self.save_data, self.party)
            self._save_permanent_data()
            self.swap_screen = None
            self.swap_pending_new_id = None
            self.swap_pending_new_name = None
            self.state = self.swap_return_state

    def _add_to_party(self, animal_id, return_state=GameState.VICTORY):
        if len(self.party) < 3:
            animal = Animal(animal_id)
            animal.unlocked = True
            self.save_manager.restore_animal_stats(animal, self.save_data)
            animal.check_evolution()
            animal.hp = animal.max_hp
            self.party.append(animal)
            self.save_data = self.save_manager.save_party(self.save_data, self.party)
            return True
        else:
            from config import load_animals
            animals = load_animals()
            name = animals.get(animal_id, {}).get("name", animal_id)
            self.swap_pending_new_id = animal_id
            self.swap_pending_new_name = name
            self.swap_return_state = return_state
            from src.ui.menu import SwapAnimalScreen
            self.swap_screen = SwapAnimalScreen(
                self.party, animal_id, name, self.assets)
            self.state = GameState.SWAP_ANIMAL
            return False

    def _quit_game(self):
        self._save_permanent_data()
        self.running = False

    def handle_acampamento_events(self, event):
        result = self.acampamento_screen.handle_event(event)
        if result is None:
            return

        action = result[0]

        if action == "back":
            self.state = GameState.MAIN_MENU
            self.acampamento_screen.sel_animal = 0

    def start_new_run(self):
        self.map_generator = MapGenerator(self.current_biome)
        self.map_generator.generate()
        self.map_ui = None
        self.pending_level_ups = 0
        self.pending_level_up_animals = []
        self.current_level_up_animal = None
        self.pending_evolutions = []
        self.current_evolution_animal = None
        self.current_evolution_stage = 0
        self.next_biome_pending = None
        self.pending_bonus_rescue = None
        self._run_start_time = time.time()
        self.music_manager.start_playlist()
        self.state = GameState.MAP

    def handle_map_events(self, event):
        if not self.map_ui:
            self.map_ui = MapUI(self.map_generator, self.current_biome, self.assets)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = GameState.PAUSE
            return

        node_id = self.map_ui.handle_event(event)
        if node_id is not None:
            node = self.map_generator.visit_node(node_id)
            if node:
                self.process_node(node)

    def process_node(self, node):
        if node.node_type == NodeType.COMBAT:
            self.node_xp_bonus = 1
            self.node_gold_bonus = 1
            self.start_combat(is_elite=False)
        elif node.node_type == NodeType.ELITE:
            self.node_xp_bonus = 1
            self.node_gold_bonus = 1
            self.start_combat(is_elite=True)
        elif node.node_type == NodeType.BOSS:
            self.node_xp_bonus = 3
            self.node_gold_bonus = 1
            self.start_combat(is_boss=True)
        elif node.node_type == NodeType.EVENT:
            self.start_event()
        elif node.node_type == NodeType.SHOP:
            self.start_shop()
        elif node.node_type == NodeType.CAMP:
            self.start_camp()
        elif node.node_type == NodeType.RESCUE_ANIMAL:
            self.start_animal_encounter()

    def start_combat(self, is_elite=False, is_boss=False):
        biome_data = load_biomes()[self.current_biome]
        enemy_types = biome_data["enemy_types"]
        level_range = biome_data["enemy_level_range"]
        spawn_weights = biome_data.get("spawn_weights", None)
        min_level, max_level = level_range

        if is_boss:
            level = max_level + 2
            enemies = [create_boss(self.current_biome, level)]
        elif is_elite:
            level = max_level
            enemies = create_elite_enemy(enemy_types, level)
        else:
            level = random.randint(min_level, max_level)
            enemies = create_enemy_group(enemy_types, level, weights=spawn_weights)

        alive_party = [a for a in self.party if a.is_alive]
        if not alive_party:
            alive_party = [self.party[0]] if self.party else []

        self.combat_system = CombatSystem(alive_party, enemies)
        self.combat_system.start_combat()
        self.combat_ui = CombatUI(self.combat_system)
        if is_boss:
            self.music_manager.play_boss()
        self.state = GameState.COMBAT

    def handle_combat_events(self, event):
        if not self.combat_system:
            return

        if self.combat_system.combat_ended:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._resolve_combat_rewards()
            return

    def _resolve_combat_rewards(self):
        if self.combat_system.player_won:
            rewards = self.combat_system.get_rewards()
            xp_multiplier = self.node_xp_bonus
            gold_multiplier = self.node_gold_bonus
            total_xp = rewards["xp"] * xp_multiplier
            total_gold = rewards["gold"] * gold_multiplier

            leveled_animals = []
            levels_gained = 0
            for animal in self.party:
                if animal.is_alive:
                    old_level = animal.level
                    leveled = animal.add_xp(total_xp)
                    if leveled:
                        leveled_animals.append(animal)
                    levels_gained += (animal.level - old_level)
                    animal.gold += total_gold

            for animal in self.party:
                if not animal.is_alive:
                    animal.hp = max(1, animal.max_hp // 4)
                    animal.is_alive = True

            self.save_data = self.save_manager.update_statistics(self.save_data, "combats_won")
            self.save_data = self.save_manager.update_statistics(self.save_data, "gold_earned", total_gold)
            self.save_data = self.save_manager.update_statistics(self.save_data, "enemies_defeated", len(self.combat_system.enemies))
            if levels_gained > 0:
                self.save_data = self.save_manager.update_statistics(self.save_data, "levels_gained", levels_gained)

            for enemy in self.combat_system.enemies:
                self.save_data, is_new = self.bestiary_manager.register_creature(
                    self.save_data, enemy.enemy_id)
                if is_new and not self.victory_message:
                    self.victory_message = f"NOVA ENTRADA DESBLOQUEADA: {enemy.name}"

            evolved = self._check_party_evolutions()

            self._save_permanent_data()

            if evolved:
                self.pending_evolutions = evolved
                self._start_next_evolution()
                return

            boss_node = self._was_boss_node()

            if leveled_animals:
                self.pending_level_up_animals = list(leveled_animals)
                self.pending_level_ups = sum(1 for _ in leveled_animals)
                self._start_next_level_up()
                return

            self.victory_xp_gained = total_xp
            self.victory_gold_gained = total_gold
            self._after_leveling(
                f"Vitoria! +{total_xp} XP, +{total_gold} Gold")
        else:
            self.save_data = self.save_manager.update_statistics(self.save_data, "combats_lost")
            self._defeat_run()

    def _check_party_evolutions(self):
        evolved = []
        for animal in self.party:
            for stage in animal.check_evolution():
                evolved.append((animal, stage))
        return evolved

    def _start_next_evolution(self):
        if not self.pending_evolutions:
            self.current_evolution_animal = None
            self.current_evolution_stage = 0
            if self.pending_level_up_animals:
                self._start_next_level_up()
            else:
                self._after_leveling(self.victory_message or "Vitoria!")
            return
        self.current_evolution_animal, self.current_evolution_stage = \
            self.pending_evolutions.pop(0)
        self.state = GameState.EVOLUTION

    def handle_evolution_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._save_permanent_data()
            self._start_next_evolution()

    def _after_leveling(self, message):
        self.current_level_up_animal = None
        boss_node = self._was_boss_node()
        if boss_node:
            self.next_biome_pending = self._get_next_biome()
            if self.next_biome_pending:
                self.save_data = self.save_manager.add_unlocked_biome(
                    self.save_data, self.next_biome_pending)
            self.save_data = self.save_manager.update_statistics(self.save_data, "bosses_defeated")
            biome_data = load_biomes()[self.current_biome]
            rescue_id = biome_data.get("rescue_animal")
            self.pending_bonus_rescue = biome_data.get("bonus_rescue")
            if rescue_id and rescue_id not in self.save_data.get("unlocked_animals", []):
                self.start_rescue(rescue_id)
                return
            bosses_defeated = self.save_data.get("statistics", {}).get("bosses_defeated", 0)
            if bosses_defeated <= 3:
                self._check_cage_drop()
                return
        self.victory_message = message
        self.victory_time = time.time()
        self.music_manager.resume_playlist()
        self.state = GameState.VICTORY

    def _start_next_level_up(self):
        if not self.pending_level_up_animals:
            self.pending_level_ups = 0
            self.current_level_up_animal = None
            return
        self.current_level_up_animal = self.pending_level_up_animals[0]
        self.level_up_offers = self.level_up_system.get_available_upgrades(
            self.current_level_up_animal)
        self.state = GameState.LEVEL_UP

    def _check_cage_drop(self):
        bosses_defeated = self.save_data.get("statistics", {}).get("bosses_defeated", 0)
        if bosses_defeated >= 3:
            return
        unlocked = set(self.save_data.get("unlocked_animals", []))
        all_animals = set(load_animals().keys())
        undiscovered = list(all_animals - unlocked)
        if not undiscovered:
            return
        cage_id = random.choice(undiscovered)
        self.pending_cage_animal = cage_id
        animals_data = load_animals()
        animal_info = animals_data.get(cage_id, {})
        from src.ui.menu import CageRewardScreen
        self.cage_reward_screen = CageRewardScreen(animal_info, self.assets)
        self.save_data = self.save_manager.add_unlocked_animal(self.save_data, cage_id)
        self.save_data, _ = self.save_manager.discover_bestiary(self.save_data, cage_id)
        self._save_permanent_data()
        self.state = GameState.CAGE_REWARD

    def _was_boss_node(self):
        visited = [n for n in self.map_generator.nodes.values() if n.visited]
        if visited:
            last = max(visited, key=lambda n: n.floor)
            return last.node_type == NodeType.BOSS
        return False

    def _get_next_biome(self):
        biomes_order = ["caatinga", "cerrado", "pantanal", "mata_atlantica", "amazonia"]
        idx = biomes_order.index(self.current_biome) if self.current_biome in biomes_order else -1
        if 0 <= idx < len(biomes_order) - 1:
            return biomes_order[idx + 1]
        return None

    def start_event(self):
        events = load_events()
        event_id = random.choice(list(events.keys()))
        self.current_event = events[event_id]
        self.event_hover = -1
        self.state = GameState.EVENT

    def _event_layout(self):
        panel_w, panel_h = 620, 560
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        title_area = pygame.Rect(panel_x + 20, panel_y + 14, panel_w - 40, 42)
        desc_area = pygame.Rect(panel_x + 40, panel_y + 78, panel_w - 80, 58)
        choices = self.current_event["choices"] if self.current_event else []
        buttons = [pygame.Rect(panel_x + 35, panel_y + 145 + i * 95,
                               panel_w - 70, 80) for i in range(len(choices))]
        return {"panel": panel, "title": title_area, "desc": desc_area,
                "buttons": buttons}

    def handle_event_screen(self, event):
        layout = self._event_layout()

        if event.type == pygame.MOUSEMOTION:
            self.event_hover = -1
            for i, btn_rect in enumerate(layout["buttons"]):
                if btn_rect.collidepoint(event.pos):
                    self.event_hover = i
                    break

        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, choice in enumerate(self.current_event["choices"]):
                btn_rect = layout["buttons"][i]
                if btn_rect.collidepoint(event.pos):
                    self.apply_event_choice(choice)
                    break

    def apply_event_choice(self, choice):
        if "hp_cost" in choice and choice["hp_cost"] > 0:
            for animal in self.party:
                animal.hp -= choice["hp_cost"]
                if animal.hp <= 0:
                    animal.hp = 0
            alive = [a for a in self.party if a.is_alive]
            if not alive:
                self._defeat_run()
                return

        if "heal_amount" in choice:
            for animal in self.party:
                if animal.is_alive:
                    animal.heal(choice["heal_amount"])

        if "xp_reward" in choice and choice["xp_reward"] > 0:
            leveled_animals = []
            levels_gained = 0
            for animal in self.party:
                old_level = animal.level
                leveled = animal.add_xp(choice["xp_reward"])
                if leveled:
                    leveled_animals.append(animal)
                levels_gained += (animal.level - old_level)
            if levels_gained > 0:
                self.save_data = self.save_manager.update_statistics(self.save_data, "levels_gained", levels_gained)
            evolved = self._check_party_evolutions()
            self._save_permanent_data()
            if evolved:
                self.pending_evolutions = evolved
                self._start_next_evolution()
                return
            if leveled_animals:
                self.pending_level_up_animals = leveled_animals
                self.pending_level_ups = len(leveled_animals)
                self._start_next_level_up()
                return

        if "gold_reward" in choice and choice["gold_reward"] > 0:
            for animal in self.party:
                animal.gold += choice["gold_reward"]

        if "hp_loss_chance" in choice:
            if random.randint(1, 100) <= choice["hp_loss_chance"]:
                for animal in self.party:
                    animal.hp -= choice.get("hp_loss_amount", 5)
                    if animal.hp <= 0:
                        animal.hp = 0
                alive = [a for a in self.party if a.is_alive]
                if not alive:
                    self._defeat_run()
                    return

        self._save_permanent_data()
        self.state = GameState.MAP
        self.map_ui = None

    def start_shop(self):
        self.shop_hover = -1
        self.state = GameState.SHOP

    def _shop_layout(self):
        panel_w, panel_h = 600, 520
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        items = [
            ("Pocao de Vida", "Cura 30 HP a todos", 20),
            ("Elixir de Forca", "+3 ATK por 3 batalhas", 25),
            ("Escudo Leve", "+5 DEF por 3 batalhas", 25),
        ]
        buttons = [pygame.Rect(panel_x + 35, panel_y + 120 + i * 90,
                               panel_w - 70, 75) for i in range(len(items))]
        back_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80,
                                200, 45)
        return {"panel": panel, "items": items, "buttons": buttons,
                "back": back_rect}

    def handle_shop_events(self, event):
        shop_items = [
            ("Pocao de Vida", "Cura 30 HP a todos", 20, lambda: self._shop_heal_all(30)),
            ("Elixir de Forca", "+3 ATK por 3 batalhas", 25, lambda: self._shop_buff_stat("attack", 3, 3)),
            ("Escudo Leve", "+5 DEF por 3 batalhas", 25, lambda: self._shop_buff_stat("defense", 5, 3)),
        ]
        layout = self._shop_layout()

        if event.type == pygame.MOUSEMOTION:
            self.shop_hover = -1
            for i, btn_rect in enumerate(layout["buttons"]):
                if btn_rect.collidepoint(event.pos):
                    self.shop_hover = i
                    break

        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, (name, desc, cost, effect) in enumerate(shop_items):
                btn_rect = layout["buttons"][i]
                if btn_rect.collidepoint(event.pos):
                    gold = self.party[0].gold if self.party else 0
                    if gold >= cost:
                        for a in self.party:
                            a.gold -= cost
                        effect()
                        self._save_permanent_data()
                    break

            if layout["back"].collidepoint(event.pos):
                self._save_permanent_data()
                self.state = GameState.MAP
                self.map_ui = None

    def _shop_heal_all(self, amount):
        for animal in self.party:
            if animal.is_alive:
                animal.heal(amount)

    def _shop_buff_stat(self, stat, amount, duration):
        from src.state import BuffType
        buff_type = BuffType.ATTACK_UP if stat == "attack" else BuffType.DEFENSE_UP
        for animal in self.party:
            if animal.is_alive:
                animal.apply_buff(buff_type, amount, duration)

    def start_camp(self):
        self.state = GameState.CAMP

    def handle_camp_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for animal in self.party:
                if not animal.is_alive:
                    animal.hp = max(1, animal.max_hp // 4)
                    animal.is_alive = True
                heal_amount = int(animal.max_hp * 0.3)
                animal.heal(heal_amount)
            self._save_permanent_data()
            self.state = GameState.MAP
            self.map_ui = None

    def _level_up_layout(self):
        remaining = len(self.pending_level_up_animals)
        start_y = 190 if remaining <= 1 else 185
        buttons = [pygame.Rect(SCREEN_WIDTH // 2 - 230, start_y + i * 140, 460, 120)
                   for i in range(len(self.level_up_offers or []))]
        return {"start_y": start_y, "buttons": buttons}

    def handle_level_up_events(self, event):
        layout = self._level_up_layout()

        if event.type == pygame.MOUSEMOTION:
            self.level_up_hover = -1
            if self.level_up_offers:
                for i, btn_rect in enumerate(layout["buttons"]):
                    if btn_rect.collidepoint(event.pos):
                        self.level_up_hover = i
                        break

        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, upgrade in enumerate(self.level_up_offers):
                btn_rect = layout["buttons"][i]
                if btn_rect.collidepoint(event.pos):
                    target_animal = self.current_level_up_animal or self.party[0]
                    self.level_up_system.apply_upgrade(target_animal, upgrade)
                    upgrade_id = upgrade.get("id") or upgrade.get("name")
                    if upgrade_id and target_animal:
                        self.save_data = self.save_manager.add_permanent_upgrade(
                            self.save_data, target_animal.animal_id, upgrade_id)
                    self.level_up_offers = None

                    if self.pending_level_up_animals:
                        self.pending_level_up_animals.pop(0)
                    self.pending_level_ups = max(0, self.pending_level_ups - 1)

                    self._save_permanent_data()

                    if self.pending_level_up_animals:
                        self._start_next_level_up()
                        return

                    self._after_leveling(f"Melhoria: {upgrade['name']}")
                    break

    def start_rescue(self, animal_id):
        self.pending_rescue_animal = animal_id
        self.save_data = self.save_manager.add_unlocked_animal(self.save_data, animal_id)
        self.save_data = self.save_manager.update_statistics(self.save_data, "animals_rescued")
        self.save_data, is_new = self.save_manager.discover_bestiary(self.save_data, animal_id)
        self._save_permanent_data()
        self.state = GameState.RESCUE_ANIMAL

    def _handle_bonus_rescue(self):
        biome_data = load_biomes()[self.current_biome]
        bonus_id = biome_data.get("bonus_rescue")
        if bonus_id and bonus_id not in self.save_data.get("unlocked_animals", []):
            self.save_data = self.save_manager.add_unlocked_animal(self.save_data, bonus_id)
            self.save_data = self.save_manager.update_statistics(self.save_data, "animals_rescued")
            self.save_data, _ = self.save_manager.discover_bestiary(self.save_data, bonus_id)
            self._save_permanent_data()
            return bonus_id
        return None

    def handle_rescue_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.pending_rescue_animal:
                self._add_to_party(self.pending_rescue_animal, return_state=GameState.VICTORY)
                bonus_id = self._handle_bonus_rescue()
                if bonus_id:
                    self.pending_rescue_animal = bonus_id
                    return
            self.pending_rescue_animal = None
            self.pending_bonus_rescue = None
            if self.state != GameState.SWAP_ANIMAL:
                self._save_permanent_data()
                self.state = GameState.VICTORY
            self.map_ui = None

    def start_animal_encounter(self):
        self.encounter_text = random.choice(ENCOUNTER_TEXTS)
        biome_data = load_biomes().get(self.current_biome, {})
        level_range = biome_data.get("enemy_level_range", [1, 3])

        all_animal_ids = list(load_animals().keys())
        unlocked = set(self.save_data.get("unlocked_animals", []))
        party_ids = set(a.animal_id for a in self.party)

        undiscovered = [aid for aid in all_animal_ids if aid not in unlocked and aid not in party_ids]

        if undiscovered:
            self.encounter_animal_id = random.choice(undiscovered)
        else:
            candidates = [aid for aid in unlocked if aid not in party_ids]
            if not candidates:
                self.encounter_animal_id = None
                self.encounter_animal_level = 1
                self.encounter_text = ""
                self._reset_encounter_state("none")
                return
            self.encounter_animal_id = random.choice(candidates)

        self.encounter_animal_level = random.randint(level_range[0], level_range[1])

        if self.encounter_animal_id in party_ids:
            self._reset_encounter_state("already_in_party")
        else:
            self._reset_encounter_state("main")

    def _create_encounter_animal(self, animal_id):
        animal = Animal(animal_id)
        animal.unlocked = True
        self.save_manager.restore_animal_stats(animal, self.save_data)
        already_unlocked = animal_id in self.save_data.get("animal_data", {})
        if not already_unlocked and self.encounter_animal_level > 1:
            guard = 0
            while animal.level < self.encounter_animal_level and guard < 100:
                animal.add_xp(animal.xp_to_level)
                guard += 1
        animal.check_evolution()
        animal.hp = animal.max_hp
        return animal

    def handle_animal_encounter_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._finish_animal_encounter()
            return

        if event.type == pygame.MOUSEMOTION:
            self._update_encounter_hover(event.pos)
            return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        rects = self._encounter_layout()
        step = self.encounter_step

        if step == "none":
            if rects["continue_center"].collidepoint(event.pos):
                self._finish_animal_encounter()
            return

        animal_id = self.encounter_animal_id
        if not animal_id:
            self._finish_animal_encounter()
            return

        if step == "already_in_party":
            if rects["continue_center"].collidepoint(event.pos):
                self._finish_animal_encounter()
            return

        if step == "main":
            if animal_id in [a.animal_id for a in self.party]:
                self.encounter_step = "already_in_party"
                return

            party_full = len(self.party) >= MAX_PARTY_SIZE
            if party_full:
                for i in range(len(self.party)):
                    if rects[f"member_{i}"].collidepoint(event.pos):
                        self.encounter_swap_index = i
                        self.encounter_swap_hover = -1
                        self.encounter_step = "swap_confirm"
                        return
                if rects["continue_center"].collidepoint(event.pos):
                    self._register_encounter_animal()
                    self._finish_animal_encounter()
                return

            if rects["add"].collidepoint(event.pos):
                self._add_encounter_animal_to_party(animal_id)
                return
            if rects["continue_right"].collidepoint(event.pos):
                self._register_encounter_animal()
                self._finish_animal_encounter()
            return

        if step == "swap_confirm":
            if rects["confirm"].collidepoint(event.pos):
                idx = self.encounter_swap_index
                if 0 <= idx < len(self.party):
                    old = self.party[idx]
                    self.save_data = self.save_manager.save_animal_stats(self.save_data, old)
                    was_new = animal_id not in self.save_data.get("unlocked_animals", [])
                    new_animal = self._create_encounter_animal(animal_id)
                    self.party[idx] = new_animal
                    self.save_data = self.save_manager.save_party(self.save_data, self.party)
                    self.save_data = self.save_manager.add_unlocked_animal(self.save_data, animal_id)
                    if was_new:
                        self.save_data = self.save_manager.update_statistics(self.save_data, "animals_rescued")
                    self.save_data, _ = self.save_manager.discover_bestiary(self.save_data, animal_id)
                    self._save_permanent_data()
                    self.encounter_step = "swapped"
                    self.encounter_swap_index = -1
                    self._notify_save("Membro da equipe substituido!")
                return
            if rects["cancel"].collidepoint(event.pos):
                self.encounter_step = "main"
                self.encounter_swap_index = -1
            return

        if step in ("added", "swapped"):
            if rects["continue_center"].collidepoint(event.pos):
                self._finish_animal_encounter()
            return

    def _add_encounter_animal_to_party(self, animal_id):
        was_new = animal_id not in self.save_data.get("unlocked_animals", [])
        new_animal = self._create_encounter_animal(animal_id)
        self.party.append(new_animal)
        self.save_data = self.save_manager.save_party(self.save_data, self.party)
        self.save_data = self.save_manager.add_unlocked_animal(self.save_data, animal_id)
        if was_new:
            self.save_data = self.save_manager.update_statistics(self.save_data, "animals_rescued")
        self.save_data, _ = self.save_manager.discover_bestiary(self.save_data, animal_id)
        self._save_permanent_data()
        self.encounter_swap_hover = -1
        self.encounter_step = "added"
        self._notify_save("Animal adicionado a equipe!")

    def _register_encounter_animal(self):
        """Registra o animal como descoberto/desbloqueado sem alterar a equipe."""
        aid = self.encounter_animal_id
        if not aid:
            return
        self.save_data = self.save_manager.add_unlocked_animal(self.save_data, aid)
        self.save_data, _ = self.save_manager.discover_bestiary(self.save_data, aid)
        self._save_permanent_data()

    def _finish_animal_encounter(self):
        self._register_encounter_animal()
        self.encounter_animal_id = None
        self.encounter_animal_level = 1
        self.encounter_text = ""
        self.encounter_step = "main"
        self.encounter_swap_index = -1
        self.encounter_hover = -1
        self.encounter_swap_hover = -1
        self.state = GameState.MAP
        self.map_ui = None

    def _reset_encounter_state(self, step="main"):
        self.encounter_step = step
        self.encounter_swap_index = -1
        self.encounter_hover = -1
        self.encounter_swap_hover = -1
        self.state = GameState.ANIMAL_ENCOUNTER

    def _update_encounter_hover(self, pos):
        self.encounter_hover = -1
        self.encounter_swap_hover = -1
        if self.encounter_step != "main":
            return
        if len(self.party) < MAX_PARTY_SIZE:
            return
        rects = self._encounter_layout()
        for i in range(len(self.party)):
            if rects[f"member_{i}"].collidepoint(pos):
                self.encounter_swap_hover = i
                return

    def _encounter_layout(self):
        panel_w, panel_h = 760, 600
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        btn_w, btn_h = 250, 50
        btn_y = panel_y + 505
        rects = {
            "panel": panel,
            "add": pygame.Rect(panel.centerx - btn_w - 12, btn_y, btn_w, btn_h),
            "continue_right": pygame.Rect(panel.centerx + 12, btn_y, btn_w, btn_h),
            "continue_center": pygame.Rect(panel.centerx - btn_w // 2, btn_y, btn_w, btn_h),
            "confirm": pygame.Rect(panel.centerx - btn_w - 12, btn_y, btn_w, btn_h),
            "cancel": pygame.Rect(panel.centerx + 12, btn_y, btn_w, btn_h),
        }
        slot_x = panel.centerx - 230
        for i in range(MAX_PARTY_SIZE):
            rects[f"member_{i}"] = pygame.Rect(slot_x, panel_y + 315 + i * 58, 460, 50)
        return rects

    def _draw_encounter_panel(self, rect):
        _draw_panel(self.screen, rect, SERTAO_PANEL, GREEN, radius=14, alpha=235)

    def _draw_encounter_title(self, text):
        panel = self._encounter_layout()["panel"]
        title_y = panel.y + 45
        draw_text(self.screen, text, (panel.centerx, title_y),
                  font_size=38, color=SERTAO_GOLD, center=True)
        pygame.draw.line(self.screen, GREEN,
                         (panel.x + 40, title_y + 38),
                         (panel.right - 40, title_y + 38), 1)

    def _draw_encounter_sprite(self, animal_id, size, cy):
        stage = 0
        if self.save_data:
            stage = self.save_data.get("animal_data", {}).get(
                animal_id, {}).get("evolution_stage", 0) or 0
        spr = self.assets.get_animal_sprite(
            animal_id, evolution_stage=stage, max_width=size, max_height=size)
        if spr:
            self.screen.blit(spr, spr.get_rect(center=(SCREEN_WIDTH // 2, cy)))
        else:
            emoji = ANIMAL_EMOJIS.get(animal_id, "?")
            draw_text(self.screen, emoji, (SCREEN_WIDTH // 2, cy),
                      font_size=size, color=SERTAO_CREAM, center=True)

    def update(self):
        if self.state == GameState.COMBAT and self.combat_ui:
            self.combat_ui.update()
        if self.state == GameState.CAGE_REWARD and self.cage_reward_screen:
            self.cage_reward_screen.update()

    def render(self):
        renderers = {
            GameState.MAIN_MENU: lambda: self.main_menu.draw(self.screen),
            GameState.ANIMAL_SELECT: lambda: self.animal_select.draw(self.screen),
            GameState.BIOME_SELECT: lambda: self.biome_select.draw(self.screen),
            GameState.SETTINGS: lambda: self.settings_screen.draw(self.screen),
            GameState.ACAMPAMENTO: lambda: self.acampamento_screen.draw(self.screen) if self.acampamento_screen else None,
            GameState.BESTIARY: lambda: self.bestiary_screen.draw(self.screen) if self.bestiary_screen else None,
            GameState.CAGE_REWARD: lambda: self.cage_reward_screen.draw(self.screen) if self.cage_reward_screen else None,
            GameState.MAP: self._render_map,
            GameState.COMBAT: self._render_combat,
            GameState.EVENT: self._render_event,
            GameState.SHOP: self._render_shop,
            GameState.CAMP: self._render_camp,
            GameState.LEVEL_UP: self._render_level_up,
            GameState.RESCUE_ANIMAL: self._render_rescue,
            GameState.GAME_OVER: self._render_game_over,
            GameState.VICTORY: self._render_victory,
            GameState.PAUSE: self._render_pause,
            GameState.ANIMAL_ENCOUNTER: self._render_animal_encounter,
            GameState.SAVES: lambda: self.journey_select_screen.draw(self.screen) if self.journey_select_screen else None,
            GameState.SWAP_ANIMAL: lambda: self.swap_screen.draw(self.screen) if self.swap_screen else None,
            GameState.EVOLUTION: self._render_evolution,
        }

        renderer = renderers.get(self.state)
        if renderer:
            renderer()
        self._draw_save_status()
        self._blit_scaled()
        pygame.display.flip()

    def _draw_save_status(self):
        if self.save_status_timer <= 0 or not self.save_status_message:
            return
        font = get_font(22)
        text = self.save_status_message
        if self.save_status_success is None:
            color = YELLOW
        else:
            color = GREEN if self.save_status_success else RED
        surf = font.render(text, True, color)
        pad_x, pad_y = 16, 10
        rect = pygame.Rect(0, 0, surf.get_width() + pad_x * 2, surf.get_height() + pad_y * 2)
        rect.topright = (SCREEN_WIDTH - 15, 15)
        bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bg, (*SERTAO_PANEL, 220), (0, 0, rect.w, rect.h), border_radius=8)
        self.screen.blit(bg, rect.topleft)
        pygame.draw.rect(self.screen, SERTAO_BORDER, rect, 2, border_radius=8)
        self.screen.blit(surf, (rect.x + pad_x, rect.y + pad_y))

    def _blit_scaled(self):
        if self.actual_screen.get_size() == (SCREEN_WIDTH, SCREEN_HEIGHT):
            self.actual_screen.blit(self.screen, (0, 0))
            return
        scaled = pygame.transform.smoothscale(
            self.screen, (self.scaled_w, self.scaled_h))
        self.actual_screen.fill((0, 0, 0))
        self.actual_screen.blit(scaled, (self.scaled_offset_x, self.scaled_offset_y))

    def _render_map(self):
        if not self.map_ui:
            self.map_ui = MapUI(self.map_generator, self.current_biome, self.assets)
        self.map_ui.draw(self.screen)
        self._render_hud()

    def _render_hud(self):
        if not self.party:
            return
        hud_rect = pygame.Rect(0, SCREEN_HEIGHT - 55, SCREEN_WIDTH, 55)
        hud_surf = pygame.Surface((SCREEN_WIDTH, 55), pygame.SRCALPHA)
        hud_surf.fill((20, 15, 10, 220))
        self.screen.blit(hud_surf, (0, SCREEN_HEIGHT - 55))
        pygame.draw.rect(self.screen, SERTAO_BORDER, hud_rect, 1)

        x_offset = 15
        for i, animal in enumerate(self.party):
            emoji = ANIMAL_EMOJIS.get(animal.animal_id, "")
            hp_color = GREEN if animal.hp > animal.max_hp * 0.5 else (YELLOW if animal.hp > animal.max_hp * 0.25 else RED)
            draw_text(self.screen, f"{emoji} {animal.name} Lv.{animal.level}",
                      (x_offset, SCREEN_HEIGHT - 45), font_size=17, color=SERTAO_CREAM)
            draw_bar(self.screen, x_offset, SCREEN_HEIGHT - 25, 120, 14,
                     animal.hp, animal.max_hp, hp_color)
            x_offset += 160

        draw_text(self.screen, f"Gold: {self.party[0].gold}",
                  (x_offset + 10, SCREEN_HEIGHT - 45), font_size=18, color=SERTAO_GOLD)

    def _render_combat(self):
        if self.combat_ui and self.combat_system:
            self.combat_ui.draw(self.screen, self.assets)

    def _render_event(self):
        self.assets.draw_background(self.screen, "event")

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        layout = self._event_layout()
        panel = layout["panel"]
        _draw_panel(self.screen, panel, SERTAO_PANEL, SERTAO_BORDER)

        if self.current_event:
            draw_text_centered(self.screen, self.current_event["name"],
                               layout["title"].centerx, layout["title"].centery,
                               36, SERTAO_GOLD)

            pygame.draw.line(self.screen, SERTAO_BORDER,
                             (panel.x + 40, panel.y + 65),
                             (panel.right - 40, panel.y + 65), 1)

            draw_multiline_centered(self.screen, self.current_event["description"],
                                    layout["desc"], font_size=21,
                                    color=SERTAO_CREAM, line_spacing=2)

            for i, choice in enumerate(self.current_event["choices"]):
                btn_rect = layout["buttons"][i]
                is_hovered = (self.event_hover == i)

                bg_color = (50, 40, 25) if not is_hovered else (65, 55, 35)
                border_color = SERTAO_BORDER if not is_hovered else SERTAO_GOLD

                pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=10)
                pygame.draw.rect(self.screen, border_color, btn_rect, 2, border_radius=10)

                draw_descr_choice = choice["text"]
                draw_fitted_text(self.screen, draw_descr_choice, btn_rect,
                                 font_size=18, color=SERTAO_CREAM,
                                 min_font=14, max_lines=2)

    def _render_shop(self):
        self.assets.draw_background(self.screen, "shop")

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        layout = self._shop_layout()
        panel = layout["panel"]
        _draw_panel(self.screen, panel, SERTAO_PANEL, PURPLE)

        draw_text_centered(self.screen, "Loja do Sertao",
                           panel.centerx, panel.y + 35, 36, SERTAO_GOLD)

        gold = self.party[0].gold if self.party else 0
        draw_text_centered(self.screen, f"Seu Gold: {gold}",
                           panel.centerx, panel.y + 75, 22, SERTAO_GOLD)

        pygame.draw.line(self.screen, PURPLE,
                         (panel.x + 40, panel.y + 100),
                         (panel.x + panel.w - 40, panel.y + 100), 1)

        item_colors = {0: GREEN, 1: RED, 2: BLUE}
        cost_labels = {0: 20, 1: 25, 2: 25}
        for i, (name, desc, cost) in enumerate(layout["items"]):
            btn_rect = layout["buttons"][i]
            can_afford = gold >= cost
            is_hovered = (self.shop_hover == i and can_afford)

            bg_color = (50, 40, 25) if can_afford else (35, 28, 18)
            if is_hovered:
                bg_color = (65, 55, 35)

            border_color = PURPLE if can_afford else GRAY
            if is_hovered:
                border_color = SERTAO_GOLD

            pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=10)
            pygame.draw.rect(self.screen, border_color, btn_rect, 2, border_radius=10)

            icon_color = item_colors[i]
            icon_rect = pygame.Rect(btn_rect.x + 15, btn_rect.centery - 22, 45, 45)
            pygame.draw.rect(self.screen, icon_color, icon_rect, border_radius=8)

            text_color = SERTAO_CREAM if can_afford else GRAY
            cost_w = text_size(f"{cost} Gold", 18)[0]
            content_rect = pygame.Rect(btn_rect.x + 72, btn_rect.y,
                                       btn_rect.w - 84 - cost_w - 30,
                                       btn_rect.h)
            draw_text_block_colored(
                self.screen,
                [(name, 20, text_color), (desc, 15,
                                          SERTAO_CREAM if can_afford else GRAY)],
                content_rect, line_spacing=2)

            cost_surf = get_font(20).render(f"{cost} Gold", True,
                                            SERTAO_GOLD if can_afford else GRAY)
            cost_rect = cost_surf.get_rect(midright=(btn_rect.right - 16,
                                                     btn_rect.centery))
            self.screen.blit(cost_surf, cost_rect)

        draw_sertao_button(self.screen, layout["back"], "Voltar",
                           layout["back"].collidepoint(get_mouse_pos()))

    def _render_camp(self):
        self.assets.draw_background(self.screen, "camp")

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 500, 350
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        _draw_panel(self.screen, panel, (25, 35, 25), GREEN)

        draw_text_centered(self.screen, "Acampamento",
                           panel.centerx, panel.y + 40, 36, SERTAO_GOLD)

        pygame.draw.line(self.screen, GREEN,
                         (panel.x + 40, panel.y + 70),
                         (panel.x + panel.w - 40, panel.y + 70), 1)

        content_rect = pygame.Rect(panel.x + 20, panel.y + 90,
                                   panel.w - 40, panel.h - 150)
        draw_text_block_colored(self.screen, [
            ("Sua equipe descansa e recupera 30% da vida.", 22, SERTAO_CREAM),
            ("", 10, WHITE),
            ("Clique para continuar", 22, SERTAO_CREAM),
        ], content_rect, line_spacing=14)

    def _render_level_up(self):
        self.assets.draw_background(self.screen, "level_up")

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        draw_text_centered(self.screen, "Evolucao Disponivel!",
                           SCREEN_WIDTH // 2, 55, 44, SERTAO_GOLD)

        target = self.current_level_up_animal or (self.party[0] if self.party else None)
        if target:
            emoji = ANIMAL_EMOJIS.get(target.animal_id, "")
            draw_text_centered(self.screen,
                               f"{emoji} {target.name} Lv.{target.level} - Escolha uma evolucao:",
                               SCREEN_WIDTH // 2, 110, 22, SERTAO_CREAM)

        remaining = len(self.pending_level_up_animals)
        if remaining > 1:
            draw_text_centered(self.screen,
                               f"({remaining} evolucoes pendentes)",
                               SCREEN_WIDTH // 2, 160, 18, SERTAO_LIGHT)

        if self.level_up_offers:
            layout = self._level_up_layout()
            for i, upgrade in enumerate(self.level_up_offers):
                btn_rect = layout["buttons"][i]
                is_hovered = (self.level_up_hover == i)

                shadow = pygame.Surface((btn_rect.w, btn_rect.h), pygame.SRCALPHA)
                pygame.draw.rect(shadow, (0, 0, 0, 80), (4, 4, btn_rect.w, btn_rect.h),
                                 border_radius=12)
                self.screen.blit(shadow, btn_rect.topleft)

                bg = (55, 45, 30) if not is_hovered else (75, 60, 40)
                border = SERTAO_BORDER if not is_hovered else SERTAO_GOLD
                pygame.draw.rect(self.screen, bg, btn_rect, border_radius=12)
                pygame.draw.rect(self.screen, border, btn_rect, 2, border_radius=12)

                cat_colors = {"offense": RED, "defense": BLUE, "utility": GREEN}
                cat_color = cat_colors.get(upgrade["category"], GRAY)

                icon_rect = pygame.Rect(btn_rect.x + 15, btn_rect.y + 15, 50, 50)
                pygame.draw.rect(self.screen, cat_color, icon_rect, border_radius=10)

                content_rect = pygame.Rect(btn_rect.x + 80, btn_rect.y + 10,
                                           btn_rect.w - 100, btn_rect.h - 20)
                draw_text_block_colored(
                    self.screen,
                    [(upgrade["name"], 26, SERTAO_CREAM),
                     (upgrade["description"], 18, SERTAO_CREAM),
                     (f"[{upgrade['category']}]", 16, cat_color)],
                    content_rect, line_spacing=6)

    def _render_evolution(self):
        from src.entities.animal import (EVOLUTION_STAGE_NAMES,
                                         EVOLUTION_1_STAT_LABELS,
                                         get_evolution_1_details)
        self.assets.draw_background(self.screen, "level_up")
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 660, 580
        panel = pygame.Rect((SCREEN_WIDTH - panel_w) // 2,
                            (SCREEN_HEIGHT - panel_h) // 2, panel_w, panel_h)
        _draw_panel(self.screen, panel, (45, 25, 55), SERTAO_GOLD,
                    border_width=3)

        draw_text_centered(self.screen, "UMA NOVA FORMA!",
                           panel.centerx, panel.y + 32, 40, SERTAO_GOLD)
        draw_text_centered(self.screen, f"EVOLUCAO {self.current_evolution_stage}",
                           panel.centerx, panel.y + 70, 24, SERTAO_CREAM)

        target = self.current_evolution_animal
        if target:
            stage_name = EVOLUTION_STAGE_NAMES[
                min(self.current_evolution_stage, 1)]
            if self.assets:
                spr = self.assets.get_animal_sprite(
                    target.animal_id,
                    evolution_stage=self.current_evolution_stage,
                    max_width=84, max_height=84)
                if spr:
                    self.screen.blit(spr, spr.get_rect(center=(panel.centerx,
                                                               panel.y + 118)))
                else:
                    emoji = ANIMAL_EMOJIS.get(target.animal_id, "?")
                    draw_text_centered(self.screen, emoji,
                                       panel.centerx, panel.y + 118, 50,
                                       SERTAO_CREAM)
            draw_text_centered(self.screen,
                               f"{target.name} -- {stage_name}  "
                               f"(Nivel {target.level})",
                               panel.centerx, panel.y + 176, 24, SERTAO_GOLD)

            details = get_evolution_1_details(target.animal_id)
            deltas = details["deltas"]
            upgrade = details["upgrade"]

            stat_area = pygame.Rect(panel.x + 30, panel.y + 205,
                                    panel.w - 60, 200)
            draw_text_centered(self.screen, "STATUS AUMENTADOS",
                               panel.centerx, stat_area.y + 14, 20,
                               SERTAO_LIGHT)
            primary_effects = ["permanent_max_hp", "permanent_attack",
                               "permanent_defense", "permanent_speed"]
            primary = [(EVOLUTION_1_STAT_LABELS[e], deltas[e])
                       for e in primary_effects if e in deltas]
            extras = [(EVOLUTION_1_STAT_LABELS.get(e, e), v)
                      for e, v in deltas.items() if e not in primary_effects]
            col_left = panel.centerx - 130
            col_right = panel.centerx + 130
            rows = max(len(primary), len(extras))
            for i in range(rows):
                cy = stat_area.y + 44 + i * 24
                if i < len(primary):
                    label, val = primary[i]
                    draw_text_centered(self.screen, f"{label} +{val}",
                                       col_left, cy, 18, SERTAO_GREEN)
                if i < len(extras):
                    label, val = extras[i]
                    draw_text_centered(self.screen, f"{label} +{val}",
                                       col_right, cy, 18, SERTAO_GREEN)

            div_y = stat_area.y + 44 + rows * 24
            pygame.draw.line(self.screen, SERTAO_BORDER,
                             (panel.x + 40, div_y),
                             (panel.right - 40, div_y), 1)

            up_y = div_y + 22
            draw_text_centered(self.screen, "MELHORIA ESPECIFICA",
                               panel.centerx, up_y, 20, SERTAO_LIGHT)
            if upgrade:
                icon = upgrade.get("icon", "")
                name = upgrade.get("name", "")
                draw_text_centered(self.screen, f"{icon} {name}",
                                   panel.centerx, up_y + 26, 22, SERTAO_GOLD)
                desc_rect = pygame.Rect(panel.x + 45, up_y + 46,
                                        panel.w - 90, 100)
                draw_multiline_centered(
                    self.screen, upgrade.get("description", ""),
                    desc_rect, 16, SERTAO_CREAM, max_lines=3)
            else:
                draw_text_centered(self.screen, "(nenhuma)",
                                   panel.centerx, up_y + 26, 20,
                                   SERTAO_LIGHT)

        remaining = len(self.pending_evolutions)
        if remaining > 0:
            draw_text_centered(self.screen,
                               f"({remaining + 1} evolucao(oes) restantes)",
                               panel.centerx, panel.bottom - 52, 15,
                               SERTAO_LIGHT)
        draw_text_centered(self.screen, "Clique para continuar",
                           panel.centerx, panel.bottom - 26, 20,
                           SERTAO_CREAM)

    def _render_rescue(self):
        self.assets.draw_background(self.screen, "rescue")

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        draw_text_centered(self.screen, "ANIMAL REGISTRADO NO BESTIARIO",
                           SCREEN_WIDTH // 2, 80, 42, SERTAO_GOLD)

        if self.pending_rescue_animal:
            animals = load_animals()
            animal = animals.get(self.pending_rescue_animal, {})
            name = animal.get("name", "Desconhecido")
            role = animal.get("role", "")
            desc = animal.get("description", "")

            card_w, card_h = 420, 320
            card = pygame.Rect((SCREEN_WIDTH - card_w) // 2, 170, card_w, card_h)
            _draw_panel(self.screen, card, (30, 50, 30), GREEN, radius=15)

            draw_text_centered(self.screen, name, card.centerx, card.y + 40, 36,
                               SERTAO_GOLD)
            draw_text_centered(self.screen, role, card.centerx, card.y + 80, 22,
                               SERTAO_CREAM)

            pygame.draw.line(self.screen, GREEN,
                             (card.x + 40, card.y + 105),
                             (card.right - 40, card.y + 105), 1)

            desc_area = pygame.Rect(card.x + 15, card.y + 120, card.w - 30,
                                    card.h - 170)
            draw_multiline_centered(self.screen, desc, desc_area, 18,
                                    SERTAO_CREAM, max_lines=4)

        draw_text_centered(self.screen, "Clique para continuar",
                           SCREEN_WIDTH // 2, 550, 24, SERTAO_CREAM)

    def _render_game_over(self):
        self.assets.draw_background(self.screen, "combat")

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((30, 10, 10, 180))
        self.screen.blit(overlay, (0, 0))

        area = pygame.Rect(SCREEN_WIDTH // 2 - 400, 50, 800, 620)
        items = [
            ("GAME OVER", 72, RED),
            ("", 10, WHITE),
            ("Seus animais ainda precisam de voce...", 26, SERTAO_CREAM),
        ]
        if self.party:
            items.append(("", 8, WHITE))
            for animal in self.party:
                emoji = ANIMAL_EMOJIS.get(animal.animal_id, "")
                items.append((f"{emoji} {animal.name} - Nivel {animal.level}",
                              24, SERTAO_GOLD))
            items.append(("", 6, WHITE))
            items.append(("Progresso salvo permanentemente!", 20, GREEN))
        items.append(("", 12, WHITE))
        items.append(("Clique para voltar ao menu principal", 20, GRAY))
        draw_text_block_colored(self.screen, items, area, line_spacing=8)

    def _render_victory(self):
        self.assets.draw_background(self.screen, "combat")

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 30, 10, 160))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 550, 450
        panel = pygame.Rect((SCREEN_WIDTH - panel_w) // 2,
                            (SCREEN_HEIGHT - panel_h) // 2, panel_w, panel_h)
        _draw_panel(self.screen, panel, (20, 40, 20), GREEN)

        draw_text_centered(self.screen, "VITORIA!",
                           panel.centerx, panel.y + 40, 52, GREEN)

        pygame.draw.line(self.screen, GREEN,
                         (panel.x + 40, panel.y + 75),
                         (panel.x + panel.w - 40, panel.y + 75), 1)

        draw_text_centered(self.screen, f"+{self.victory_xp_gained} XP",
                           panel.centerx, panel.y + 105, 28, BLUE)
        draw_text_centered(self.screen, f"+{self.victory_gold_gained} Ouro",
                           panel.centerx, panel.y + 140, 28, SERTAO_GOLD)

        if self.party:
            y_off = panel.y + 180
            for animal in self.party:
                emoji = ANIMAL_EMOJIS.get(animal.animal_id, "")
                draw_text_centered(self.screen,
                                   f"{emoji} {animal.name} Lv.{animal.level}",
                                   panel.centerx, y_off, 20, SERTAO_CREAM)
                bar_x = panel.x + 80
                bar_w = panel.w - 160
                elapsed = time.time() - self.victory_time if self.victory_time else 1
                fill_ratio = min(1.0, elapsed / 1.0)
                pygame.draw.rect(self.screen, GRAY, (bar_x, y_off + 22, bar_w, 14))
                fill_w = int(bar_w * fill_ratio)
                pygame.draw.rect(self.screen, BLUE, (bar_x, y_off + 22, fill_w, 14))
                pygame.draw.rect(self.screen, WHITE, (bar_x, y_off + 22, bar_w, 14), 1)
                draw_text_centered(self.screen,
                                   f"XP: {animal.xp}/{animal.xp_to_level}",
                                   panel.centerx, y_off + 40, 14, SERTAO_CREAM)
                y_off += 60

            if self.victory_message and "|" in self.victory_message:
                parts = self.victory_message.split("|")
                msg_rect = pygame.Rect(panel.x + 20, y_off, panel.w - 40,
                                       panel.bottom - y_off - 45)
                draw_text_block_colored(
                    self.screen,
                    [(p.strip(), 18, SERTAO_GOLD) for p in parts],
                    msg_rect, line_spacing=4)

        if self.next_biome_pending:
            next_name = self.next_biome_pending.replace('_', ' ').title()
            draw_text_centered(self.screen,
                               f"Clique para avancar para {next_name}",
                               panel.centerx, panel.bottom - 40, 20, SERTAO_GOLD)
        else:
            draw_text_centered(self.screen, "Clique para voltar ao mapa",
                               panel.centerx, panel.bottom - 40, 20, SERTAO_CREAM)

    def _render_pause(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 400, 250
        panel = pygame.Rect((SCREEN_WIDTH - panel_w) // 2,
                            (SCREEN_HEIGHT - panel_h) // 2, panel_w, panel_h)
        _draw_panel(self.screen, panel, SERTAO_PANEL, SERTAO_GOLD)

        draw_text_block_colored(self.screen, [
            ("PAUSA", 52, SERTAO_GOLD),
            ("", 6, WHITE),
            ("ESC para continuar", 24, SERTAO_CREAM),
            ("Q para voltar ao menu", 20, GRAY),
        ], panel, line_spacing=10)

    def _render_animal_encounter(self):
        self.assets.draw_background(self.screen, "event")

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        rects = self._encounter_layout()
        panel = rects["panel"]
        self._draw_encounter_panel(panel)
        mouse = get_mouse_pos()
        step = self.encounter_step

        if step == "none":
            self._draw_encounter_title("ANIMAL ENCONTRADO")
            draw_text(self.screen,
                      "Voce explorou a area mas nao encontrou nenhum animal.",
                      (panel.centerx, panel.y + 220), font_size=24,
                      color=SERTAO_CREAM, center=True)
            draw_text(self.screen, "Tente novamente mais tarde.",
                      (panel.centerx, panel.y + 255), font_size=18,
                      color=GRAY, center=True)
            back = rects["continue_center"]
            draw_sertao_button(self.screen, back, "Voltar",
                               back.collidepoint(mouse))
            return

        animal_id = self.encounter_animal_id
        if not animal_id:
            self._finish_animal_encounter()
            return

        animals = load_animals()
        animal = animals.get(animal_id, {})
        name = animal.get("name", "Desconhecido")
        role = animal.get("role", "")
        emoji = ANIMAL_EMOJIS.get(animal_id, "")
        encounter_level = self.encounter_animal_level

        if step == "already_in_party":
            self._draw_encounter_title("ANIMAL ENCONTRADO")
            self._draw_encounter_sprite(animal_id, 90, panel.y + 135)
            draw_text(self.screen, f"{emoji} {name}",
                      (panel.centerx, panel.y + 205), font_size=30,
                      color=SERTAO_GOLD, center=True)
            draw_text(self.screen, "Este animal ja esta na sua equipe.",
                      (panel.centerx, panel.y + 250), font_size=24,
                      color=GREEN, center=True)
            cont = rects["continue_center"]
            draw_sertao_button(self.screen, cont, "Continuar com a Equipe",
                               cont.collidepoint(mouse))
            return

        if step == "main":
            party_full = len(self.party) >= MAX_PARTY_SIZE

            if party_full:
                self._draw_encounter_title("ESCOLHA UM MEMBRO PARA SUBSTITUIR")
                self._draw_encounter_sprite(animal_id, 70, panel.y + 125)
                draw_text(self.screen,
                          f"{emoji} {name} (Nv.{encounter_level} - {role})",
                          (panel.centerx, panel.y + 165), font_size=20,
                          color=SERTAO_GOLD, center=True)
                draw_text(self.screen,
                          "Equipe cheia! Escolha um membro para substituir:",
                          (panel.centerx, panel.y + 200), font_size=20,
                          color=SERTAO_CREAM, center=True)

                for i in range(len(self.party)):
                    slot_rect = rects[f"member_{i}"]
                    member = self.party[i]
                    is_hov = (self.encounter_swap_hover == i)
                    bg_c = (65, 55, 35) if is_hov else (45, 38, 25)
                    border_c = SERTAO_GOLD if is_hov else SERTAO_BORDER
                    pygame.draw.rect(self.screen, bg_c, slot_rect, border_radius=10)
                    pygame.draw.rect(self.screen, border_c, slot_rect, 2, border_radius=10)
                    m_emoji = ANIMAL_EMOJIS.get(member.animal_id, "")
                    draw_text(self.screen,
                              f"{m_emoji} {member.name} Lv.{member.level}",
                              (slot_rect.centerx, slot_rect.centery),
                              font_size=22, color=SERTAO_CREAM, center=True)

                cont = rects["continue_center"]
                draw_sertao_button(self.screen, cont, "Continuar com a Equipe",
                                   cont.collidepoint(mouse))
                return

            self._draw_encounter_title("ANIMAL ENCONTRADO")
            self._draw_encounter_sprite(animal_id, 100, panel.y + 135)
            draw_text(self.screen, f"{emoji} {name}",
                      (panel.centerx, panel.y + 205), font_size=34,
                      color=SERTAO_GOLD, center=True)
            draw_text(self.screen, f"Nivel {encounter_level} - {role}",
                      (panel.centerx, panel.y + 240), font_size=20,
                      color=SERTAO_CREAM, center=True)
            desc_rect = pygame.Rect(panel.x + 40, panel.y + 275,
                                    panel.w - 80, 70)
            draw_multiline_centered(self.screen, animal.get("description", ""),
                                    desc_rect, font_size=17, color=SERTAO_CREAM,
                                    line_spacing=4, max_lines=3)
            ds = animal.get("base_stats", {})
            draw_text(self.screen,
                      f"HP:{ds.get('hp', 0)}  ATK:{ds.get('attack', 0)}  "
                      f"DEF:{ds.get('defense', 0)}  SPD:{ds.get('speed', 0)}",
                      (panel.centerx, panel.y + 355), font_size=16,
                      color=SERTAO_LIGHT, center=True)

            add_rect = rects["add"]
            cont_rect = rects["continue_right"]
            draw_sertao_button(self.screen, add_rect, "Adicionar a Equipe",
                               add_rect.collidepoint(mouse), color=(60, 100, 50))
            draw_sertao_button(self.screen, cont_rect, "Continuar com a Equipe",
                               cont_rect.collidepoint(mouse))
            return

        if step == "swap_confirm":
            idx = self.encounter_swap_index
            old_name = name
            if 0 <= idx < len(self.party):
                old_name = self.party[idx].name
            self._draw_encounter_title("CONFIRMAR SUBSTITUICAO")
            self._draw_encounter_sprite(animal_id, 80, panel.y + 140)
            draw_text(self.screen, f"{emoji} {name}",
                      (panel.centerx, panel.y + 205), font_size=28,
                      color=SERTAO_GOLD, center=True)
            draw_text(self.screen, f"Substituir {old_name} por {name}?",
                      (panel.centerx, panel.y + 250), font_size=24,
                      color=SERTAO_CREAM, center=True)
            confirm_rect = rects["confirm"]
            cancel_rect = rects["cancel"]
            draw_sertao_button(self.screen, confirm_rect, "Confirmar",
                               confirm_rect.collidepoint(mouse), color=(60, 100, 50))
            draw_sertao_button(self.screen, cancel_rect, "Cancelar",
                               cancel_rect.collidepoint(mouse))
            return

        if step in ("added", "swapped"):
            title = "ANIMAL ADICIONADO" if step == "added" else "TROCA REALIZADA"
            self._draw_encounter_title(title)
            self._draw_encounter_sprite(animal_id, 90, panel.y + 135)
            draw_text(self.screen, f"{emoji} {name}",
                      (panel.centerx, panel.y + 205), font_size=30,
                      color=SERTAO_GOLD, center=True)
            if step == "added":
                draw_text(self.screen, f"{name} entrou para a sua equipe!",
                          (panel.centerx, panel.y + 250), font_size=22,
                          color=GREEN, center=True)
            else:
                draw_text(self.screen,
                          f"{name} substituiu o membro escolhido da equipe!",
                          (panel.centerx, panel.y + 250), font_size=22,
                          color=GREEN, center=True)
            cont = rects["continue_center"]
            draw_sertao_button(self.screen, cont, "Continuar",
                               cont.collidepoint(mouse))
            return
