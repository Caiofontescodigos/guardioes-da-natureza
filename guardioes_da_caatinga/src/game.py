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
                    load_items, IMAGES_DIR, MUSIC_DIR)
import random
import pygame
import sys
import time

sys.path.insert(0, '/home/caio-fontes/Documentos/Jogo 2/guardioes_da_caatinga')

SERTAO_DARK = (25, 18, 10)
SERTAO_PANEL = (45, 32, 18)
SERTAO_BORDER = (139, 90, 43)
SERTAO_LIGHT = (180, 140, 60)
SERTAO_CREAM = (255, 240, 210)
SERTAO_GOLD = (255, 215, 0)

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


def draw_text(surface, text, x_or_pos, y=None, font_size=24, color=WHITE, center=False):
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(str(text), True, color)
    if center and y is not None:
        text_rect = text_surface.get_rect(center=(x_or_pos, y))
    elif isinstance(x_or_pos, tuple):
        text_rect = text_surface.get_rect(topleft=x_or_pos)
    else:
        text_rect = text_surface.get_rect(topleft=(x_or_pos, y))
    surface.blit(text_surface, text_rect)


def draw_bar(surface, x, y, width, height, current, maximum, fill_color=GREEN):
    pygame.draw.rect(surface, GRAY, (x, y, width, height))
    fill_width = int((current / maximum) * width) if maximum > 0 else 0
    pygame.draw.rect(surface, fill_color, (x, y, fill_width, height))
    pygame.draw.rect(surface, WHITE, (x, y, width, height), 1)
    font = pygame.font.Font(None, 16)
    text = font.render(f"{current}/{maximum}", True, WHITE)
    text_rect = text.get_rect(center=(x + width // 2, y + height // 2))
    surface.blit(text, text_rect)


def word_wrap(text, max_chars=45):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test = current_line + " " + word if current_line else word
        if len(test) > max_chars:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test
    if current_line:
        lines.append(current_line)
    return lines


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

    font = pygame.font.Font(None, 24)
    txt_surf = font.render(text, True, text_color)
    txt_rect = txt_surf.get_rect(center=rect.center)
    surface.blit(txt_surf, txt_rect)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Guardioes da Caatinga")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MAIN_MENU

        self.save_manager = SaveManager()
        self.save_data = self.save_manager.load_game()
        if not self.save_data or self.save_data.get("version") != "2.0":
            self.save_data = self.save_manager.create_initial_save()
            if not self.save_manager.active_slot:
                self.save_manager.active_slot = 1
            self.save_manager.save_game(self.save_data)
        self.level_up_system = LevelUpSystem()
        self.assets = AssetManager(IMAGES_DIR)
        self.music_manager = MusicManager(MUSIC_DIR)

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

        self.cage_reward_screen = None
        self.pending_cage_animal = None
        self.save_screen = None
        self.swap_screen = None
        self.swap_pending_new_id = None
        self.swap_pending_new_name = None
        self.swap_return_state = GameState.VICTORY

        self._run_start_time = 0

        self.setup_screens()

    @property
    def current_animal(self):
        return self.party[0] if self.party else None

    def _load_save_slot(self, slot):
        data = self.save_manager.load_game(slot)
        if not data or data.get("version") != "2.0":
            data = self.save_manager.new_game(slot)
            data["version"] = "2.0"
            self.save_manager.save_game(data, slot)
        self.save_data = data
        self._rebuild_party_from_save()
        self.setup_screens()

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
            animal.hp = animal.max_hp
            animal.apply_item_bonuses()
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
                                  SaveScreen)
        self.main_menu = MainMenu(self.assets)
        unlocked = self.save_data.get("unlocked_animals", ["tatu_bola"]) if self.save_data else ["tatu_bola"]
        biomes = self.save_data.get("unlocked_biomes", ["caatinga"]) if self.save_data else ["caatinga"]
        self.animal_select = AnimalSelectScreen(unlocked, self.assets, self.save_data or {})
        self.biome_select = BiomeSelectScreen(biomes, self.assets)
        self.settings_screen = SettingsScreen(self.assets)
        self.bestiary_screen = BestiaryScreen(self.save_data or {}, self.assets)
        self.acampamento_screen = AcampamentoScreen(self.save_data or {}, self.assets, self.party)
        self.save_screen = SaveScreen(self.save_manager, self.assets)
        self.cage_reward_screen = None

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
        self.save_manager.save_game(self.save_data)

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._save_permanent_data()
                self.running = False
                return

            self.music_manager.update(event)

            if self.state == GameState.MAIN_MENU:
                self.music_manager.stop()
                result = self.main_menu.handle_event(event)
                if result is not None:
                    actions = {
                        0: lambda: setattr(self, 'state', GameState.ANIMAL_SELECT) if self.save_data else None,
                        1: lambda: self._open_bestiary(),
                        2: lambda: self._open_acampamento(),
                        3: lambda: setattr(self, 'state', GameState.SETTINGS),
                        4: lambda: self._open_saves(),
                        5: self._quit_game,
                    }
                    if result in actions:
                        actions[result]()

            elif self.state == GameState.ANIMAL_SELECT:
                result = self.animal_select.handle_event(event)
                if result == "back":
                    self.state = GameState.MAIN_MENU
                elif result and result != "back":
                    self._select_animal(result)

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
                if self.settings_screen.handle_event(event):
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
                    self._save_permanent_data()
                    self.music_manager.stop()
                    self.state = GameState.MAIN_MENU
                    self.map_ui = None
                    self.combat_system = None
                    self.combat_ui = None
                    self.pending_level_ups = 0
                    self.pending_level_up_animals = []
                    self.current_level_up_animal = None
                    self.next_biome_pending = None
                    self.pending_rescue_animal = None
                    self.pending_bonus_rescue = None
                    self.encounter_animal_id = None
                    self.cage_reward_screen = None
                    self.swap_screen = None
                    self.setup_screens()

            elif self.state == GameState.VICTORY:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.next_biome_pending:
                        self.current_biome = self.next_biome_pending
                        self.next_biome_pending = None
                        self.start_new_run()
                    elif self.map_generator and self.map_generator.is_map_complete():
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
                        self.next_biome_pending = None
                        self.pending_bonus_rescue = None
                        self.encounter_animal_id = None
                        self.cage_reward_screen = None
                        self.swap_screen = None
                        self.setup_screens()

            elif self.state == GameState.ANIMAL_ENCOUNTER:
                self.handle_animal_encounter_events(event)

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

    def _open_acampamento(self):
        from src.ui.menu import AcampamentoScreen
        self.acampamento_screen = AcampamentoScreen(self.save_data, self.assets, self.party)
        self.state = GameState.ACAMPAMENTO

    def _open_bestiary(self):
        from src.ui.menu import BestiaryScreen
        self.bestiary_screen = BestiaryScreen(self.save_data or {}, self.assets)
        self.state = GameState.BESTIARY

    def _open_saves(self):
        from src.ui.menu import SaveScreen
        self.save_screen = SaveScreen(self.save_manager, self.assets)
        self.state = GameState.SAVES

    def handle_saves_events(self, event):
        if not self.save_screen:
            return
        result = self.save_screen.handle_event(event)
        if result is None:
            return
        if result == "back":
            self.state = GameState.MAIN_MENU
            self.setup_screens()
        elif isinstance(result, tuple) and result[0] == "load":
            slot = result[1]
            self._load_save_slot(slot)
            self.state = GameState.ANIMAL_SELECT
        elif isinstance(result, tuple) and result[0] == "new":
            slot = result[1]
            self._load_save_slot(slot)
            self.state = GameState.ANIMAL_SELECT

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
            new_animal.hp = new_animal.max_hp
            new_animal.apply_item_bonuses()
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
            animal.hp = animal.max_hp
            animal.apply_item_bonuses()
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

    def _select_animal(self, animal_id):
        if len(self.party) < 3:
            animal = Animal(animal_id)
            animal.unlocked = True
            self.save_manager.restore_animal_stats(animal, self.save_data)
            animal.hp = animal.max_hp
            animal.apply_item_bonuses()
            self.party.append(animal)
            self.save_data = self.save_manager.save_party(self.save_data, self.party)
            self._save_permanent_data()
            self.state = GameState.BIOME_SELECT

    def handle_acampamento_events(self, event):
        result = self.acampamento_screen.handle_event(event)
        if result is None:
            return

        action = result[0]
        data = result[1]

        if action == "back":
            self.state = GameState.MAIN_MENU
        elif action == "equip":
            inventory = self.save_data.get("inventory", [])
            if data is not None and data < len(inventory):
                item_id = inventory[data]
                unlocked = self.acampamento_screen.unlocked
                if unlocked:
                    animal_id = unlocked[min(self.acampamento_screen.sel_animal, len(unlocked) - 1)]
                    self.save_data = self.save_manager.equip_item(
                        self.save_data, animal_id, item_id)
                    self.save_manager.save_game(self.save_data)
                    self.acampamento_screen.save_data = self.save_data
        elif action == "unequip":
            unlocked = self.acampamento_screen.unlocked
            if unlocked:
                animal_id = unlocked[min(self.acampamento_screen.sel_animal, len(unlocked) - 1)]
                self.save_data = self.save_manager.unequip_item(
                    self.save_data, animal_id)
                self.save_manager.save_game(self.save_data)
                self.acampamento_screen.save_data = self.save_data

    def start_new_run(self):
        self.map_generator = MapGenerator(self.current_biome)
        self.map_generator.generate()
        self.map_ui = None
        self.pending_level_ups = 0
        self.pending_level_up_animals = []
        self.current_level_up_animal = None
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
            self.start_combat(is_elite=False)
        elif node.node_type == NodeType.ELITE:
            self.node_xp_bonus = 2
            self.start_combat(is_elite=True)
        elif node.node_type == NodeType.BOSS:
            self.node_xp_bonus = 3
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
            enemies = [create_elite_enemy(enemy_types, level)]
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
            total_xp = rewards["xp"] * xp_multiplier

            leveled_animals = []
            for animal in self.party:
                if animal.is_alive:
                    leveled = animal.add_xp(total_xp)
                    if leveled:
                        leveled_animals.append(animal)
                    animal.gold += rewards["gold"]

            for animal in self.party:
                if not animal.is_alive:
                    animal.hp = max(1, animal.max_hp // 4)
                    animal.is_alive = True

            self.save_data = self.save_manager.update_statistics(self.save_data, "combats_won")
            self.save_data = self.save_manager.update_statistics(self.save_data, "gold_earned", rewards["gold"])
            self.save_data = self.save_manager.update_statistics(self.save_data, "enemies_defeated", len(self.combat_system.enemies))

            for enemy in self.combat_system.enemies:
                self.save_data, is_new = self.save_manager.discover_creature(
                    self.save_data, enemy.enemy_id)
                if is_new and not self.victory_message:
                    self.victory_message = f"NOVA ENTRADA DESBLOQUEADA: {enemy.name}"

            self._check_item_drop()

            boss_node = self._was_boss_node()

            if leveled_animals:
                self.pending_level_up_animals = list(leveled_animals)
                self.pending_level_ups = sum(1 for _ in leveled_animals)
                self._start_next_level_up()
                return

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

            self._save_permanent_data()
            self.victory_xp_gained = total_xp
            self.victory_gold_gained = rewards["gold"]
            self.victory_time = time.time()
            self.victory_message = f"Vitoria! +{total_xp} XP, +{rewards['gold']} Gold"
            self.music_manager.resume_playlist()
            self.state = GameState.VICTORY
        else:
            self.save_data = self.save_manager.update_statistics(self.save_data, "combats_lost")
            self._save_permanent_data()
            self.music_manager.stop()
            self.state = GameState.GAME_OVER

    def _start_next_level_up(self):
        if not self.pending_level_up_animals:
            self.pending_level_ups = 0
            self.current_level_up_animal = None
            return
        self.current_level_up_animal = self.pending_level_up_animals[0]
        self.level_up_offers = self.level_up_system.get_available_upgrades(
            self.current_level_up_animal)
        self.state = GameState.LEVEL_UP

    def _check_item_drop(self):
        drop_chance = 25
        if random.randint(1, 100) <= drop_chance:
            items_data = load_items()
            item_ids = list(items_data.keys())
            available_items = [iid for iid in item_ids
                               if iid not in self.save_data.get("inventory", [])]
            if available_items:
                dropped = random.choice(available_items)
                self.save_data = self.save_manager.add_item_to_inventory(
                    self.save_data, dropped)
                item_name = items_data[dropped].get("name", dropped)
                self.victory_message += f" | Item: {item_name}"

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

    def handle_event_screen(self, event):
        panel_w, panel_h = 620, 560
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2

        if event.type == pygame.MOUSEMOTION:
            self.event_hover = -1
            for i, choice in enumerate(self.current_event["choices"]):
                btn_rect = pygame.Rect(panel_x + 35, panel_y + 145 + i * 95, panel_w - 70, 80)
                if btn_rect.collidepoint(event.pos):
                    self.event_hover = i
                    break

        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, choice in enumerate(self.current_event["choices"]):
                btn_rect = pygame.Rect(panel_x + 35, panel_y + 145 + i * 95, panel_w - 70, 80)
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
                self._save_permanent_data()
                self.music_manager.stop()
                self.state = GameState.GAME_OVER
                return

        if "heal_amount" in choice:
            for animal in self.party:
                if animal.is_alive:
                    animal.heal(choice["heal_amount"])

        if "xp_reward" in choice and choice["xp_reward"] > 0:
            leveled_animals = []
            for animal in self.party:
                leveled = animal.add_xp(choice["xp_reward"])
                if leveled:
                    leveled_animals.append(animal)
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
                    self._save_permanent_data()
                    self.music_manager.stop()
                    self.state = GameState.GAME_OVER
                    return

        self._save_permanent_data()
        self.state = GameState.MAP
        self.map_ui = None

    def start_shop(self):
        self.shop_hover = -1
        self.state = GameState.SHOP

    def handle_shop_events(self, event):
        shop_items = [
            ("Pocao de Vida", "Cura 30 HP a todos", 20, lambda: self._shop_heal_all(30)),
            ("Elixir de Forca", "+3 ATK por 3 batalhas", 25, lambda: self._shop_buff_stat("attack", 3, 3)),
            ("Escudo Leve", "+5 DEF por 3 batalhas", 25, lambda: self._shop_buff_stat("defense", 5, 3)),
        ]

        if event.type == pygame.MOUSEMOTION:
            self.shop_hover = -1
            for i, (name, desc, cost, effect) in enumerate(shop_items):
                btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 260, 230 + i * 90, 520, 75)
                if btn_rect.collidepoint(event.pos):
                    self.shop_hover = i
                    break

        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, (name, desc, cost, effect) in enumerate(shop_items):
                btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 260, 230 + i * 90, 520, 75)
                if btn_rect.collidepoint(event.pos):
                    gold = self.party[0].gold if self.party else 0
                    if gold >= cost:
                        for a in self.party:
                            a.gold -= cost
                        effect()
                    break

            back_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 45)
            if back_rect.collidepoint(event.pos):
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

    def handle_level_up_events(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.level_up_hover = -1
            if self.level_up_offers:
                for i, upgrade in enumerate(self.level_up_offers):
                    btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 230, 220 + i * 140, 460, 120)
                    if btn_rect.collidepoint(event.pos):
                        self.level_up_hover = i
                        break

        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, upgrade in enumerate(self.level_up_offers):
                btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 230, 220 + i * 140, 460, 120)
                if btn_rect.collidepoint(event.pos):
                    target_animal = self.current_level_up_animal or self.party[0]
                    self.level_up_system.apply_upgrade(target_animal, upgrade)
                    self.level_up_offers = None

                    if self.pending_level_up_animals:
                        self.pending_level_up_animals.pop(0)
                    self.pending_level_ups = max(0, self.pending_level_ups - 1)

                    self._save_permanent_data()

                    if self.pending_level_up_animals:
                        self._start_next_level_up()
                        return

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

                    self.victory_message = f"Melhoria: {upgrade['name']}"
                    self.music_manager.resume_playlist()
                    self.state = GameState.VICTORY
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
                self.encounter_hover = -1
                self.encounter_swap_hover = -1
                self.state = GameState.ANIMAL_ENCOUNTER
                return
            self.encounter_animal_id = random.choice(candidates)

        self.encounter_animal_level = random.randint(level_range[0], level_range[1])
        self.encounter_hover = -1
        self.encounter_swap_hover = -1
        self.state = GameState.ANIMAL_ENCOUNTER

    def _create_encounter_animal(self, animal_id):
        animal = Animal(animal_id)
        animal.unlocked = True
        self.save_manager.restore_animal_stats(animal, self.save_data)
        if self.encounter_animal_level > 1:
            while animal.level < self.encounter_animal_level:
                animal.add_xp(animal.xp_to_level)
        animal.hp = animal.max_hp
        animal.apply_item_bonuses()
        return animal

    def handle_animal_encounter_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if not self.encounter_animal_id:
                self.encounter_animal_id = None
                self.state = GameState.MAP
                self.map_ui = None
                return

            party_full = len(self.party) >= MAX_PARTY_SIZE

            recruit_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, 500, 200, 45)
            swap_rect = pygame.Rect(SCREEN_WIDTH // 2 + 20, 500, 200, 45)
            ignore_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 560, 200, 45)

            if party_full:
                if swap_rect.collidepoint(event.pos):
                    if self.encounter_swap_hover >= 0 and self.encounter_swap_hover < len(self.party):
                        old = self.party[self.encounter_swap_hover]
                        self.save_data = self.save_manager.save_animal_stats(self.save_data, old)
                        new_animal = self._create_encounter_animal(self.encounter_animal_id)
                        self.party[self.encounter_swap_hover] = new_animal
                        self.save_data = self.save_manager.save_party(self.save_data, self.party)
                        self.save_data = self.save_manager.add_unlocked_animal(self.save_data, self.encounter_animal_id)
                        self._save_permanent_data()
                        self.encounter_animal_id = None
                        self.state = GameState.MAP
                        self.map_ui = None
                        return
                if ignore_rect.collidepoint(event.pos):
                    self.encounter_animal_id = None
                    self.state = GameState.MAP
                    self.map_ui = None
                    return
            else:
                if recruit_rect.collidepoint(event.pos):
                    new_animal = self._create_encounter_animal(self.encounter_animal_id)
                    self.party.append(new_animal)
                    self.save_data = self.save_manager.save_party(self.save_data, self.party)
                    self.save_data = self.save_manager.add_unlocked_animal(self.save_data, self.encounter_animal_id)
                    self._save_permanent_data()
                    self.encounter_animal_id = None
                    self.state = GameState.MAP
                    self.map_ui = None
                    return
                if ignore_rect.collidepoint(event.pos):
                    self.encounter_animal_id = None
                    self.state = GameState.MAP
                    self.map_ui = None
                    return

        if event.type == pygame.MOUSEMOTION:
            self.encounter_swap_hover = -1
            if len(self.party) >= MAX_PARTY_SIZE:
                for i in range(len(self.party)):
                    slot_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, 340 + i * 45, 500, 40)
                    if slot_rect.collidepoint(event.pos):
                        self.encounter_swap_hover = i
                        break

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
            GameState.SAVES: lambda: self.save_screen.draw(self.screen) if self.save_screen else None,
            GameState.SWAP_ANIMAL: lambda: self.swap_screen.draw(self.screen) if self.swap_screen else None,
        }

        renderer = renderers.get(self.state)
        if renderer:
            renderer()
        pygame.display.flip()

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

        panel_w, panel_h = 620, 560
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2

        shadow = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 120), (6, 6, panel_w, panel_h), border_radius=14)
        self.screen.blit(shadow, (panel_x, panel_y))

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (*SERTAO_PANEL, 230), (0, 0, panel_w, panel_h), border_radius=14)
        self.screen.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(self.screen, SERTAO_BORDER, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=14)

        if self.current_event:
            draw_text(self.screen, self.current_event["name"],
                      (SCREEN_WIDTH // 2, panel_y + 35), font_size=36, color=SERTAO_GOLD, center=True)

            pygame.draw.line(self.screen, SERTAO_BORDER,
                             (panel_x + 40, panel_y + 65), (panel_x + panel_w - 40, panel_y + 65), 1)

            desc_lines = word_wrap(self.current_event["description"], 55)
            for i, line in enumerate(desc_lines):
                draw_text(self.screen, line, (SCREEN_WIDTH // 2, panel_y + 85 + i * 26),
                          font_size=21, color=SERTAO_CREAM, center=True)

            for i, choice in enumerate(self.current_event["choices"]):
                btn_rect = pygame.Rect(panel_x + 35, panel_y + 145 + i * 95, panel_w - 70, 80)

                is_hovered = (self.event_hover == i)

                bg_color = (50, 40, 25) if not is_hovered else (65, 55, 35)
                border_color = SERTAO_BORDER if not is_hovered else SERTAO_GOLD

                pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=10)
                pygame.draw.rect(self.screen, border_color, btn_rect, 2, border_radius=10)

                text_lines = word_wrap(choice["text"], 50)
                total_text_h = len(text_lines) * 20
                text_start_y = btn_rect.centery - total_text_h // 2

                for j, line in enumerate(text_lines):
                    draw_text(self.screen, line, (btn_rect.centerx, text_start_y + j * 20),
                              font_size=18, color=SERTAO_CREAM, center=True)

    def _render_shop(self):
        self.assets.draw_background(self.screen, "shop")

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 600, 520
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2

        shadow = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 120), (6, 6, panel_w, panel_h), border_radius=14)
        self.screen.blit(shadow, (panel_x, panel_y))

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (*SERTAO_PANEL, 230), (0, 0, panel_w, panel_h), border_radius=14)
        self.screen.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(self.screen, PURPLE, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=14)

        draw_text(self.screen, "Loja do Sertao", (SCREEN_WIDTH // 2, panel_y + 35),
                  font_size=36, color=SERTAO_GOLD, center=True)

        gold = self.party[0].gold if self.party else 0
        draw_text(self.screen, f"Seu Gold: {gold}", (SCREEN_WIDTH // 2, panel_y + 75),
                  font_size=22, color=SERTAO_GOLD, center=True)

        pygame.draw.line(self.screen, PURPLE,
                         (panel_x + 40, panel_y + 100), (panel_x + panel_w - 40, panel_y + 100), 1)

        items = [
            ("Pocao de Vida", "Cura 30 HP a todos", 20, GREEN),
            ("Elixir de Forca", "+3 ATK por 3 batalhas", 25, RED),
            ("Escudo Leve", "+5 DEF por 3 batalhas", 25, BLUE),
        ]

        for i, (name, desc, cost, icon_color) in enumerate(items):
            btn_rect = pygame.Rect(panel_x + 35, panel_y + 120 + i * 90, panel_w - 70, 75)
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

            icon_rect = pygame.Rect(btn_rect.x + 15, btn_rect.y + 15, 45, 45)
            pygame.draw.rect(self.screen, icon_color, icon_rect, border_radius=8)

            text_color = SERTAO_CREAM if can_afford else GRAY
            draw_text(self.screen, name, (btn_rect.x + 75, btn_rect.y + 12),
                      font_size=22, color=text_color)
            draw_text(self.screen, desc, (btn_rect.x + 75, btn_rect.y + 38),
                      font_size=16, color=SERTAO_CREAM if can_afford else GRAY)
            draw_text(self.screen, f"{cost} Gold", (btn_rect.right - 20, btn_rect.y + 25),
                      font_size=20, color=SERTAO_GOLD if can_afford else GRAY, center=True)

        back_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 45)
        is_back_hover = back_rect.collidepoint(pygame.mouse.get_pos())
        draw_sertao_button(self.screen, back_rect, "Voltar", is_back_hover)

    def _render_camp(self):
        self.assets.draw_background(self.screen, "camp")

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 500, 350
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2

        shadow = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 120), (6, 6, panel_w, panel_h), border_radius=14)
        self.screen.blit(shadow, (panel_x, panel_y))

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (25, 35, 25, 230), (0, 0, panel_w, panel_h), border_radius=14)
        self.screen.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(self.screen, GREEN, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=14)

        draw_text(self.screen, "Acampamento", (SCREEN_WIDTH // 2, panel_y + 40),
                  font_size=36, color=SERTAO_GOLD, center=True)

        pygame.draw.line(self.screen, GREEN,
                         (panel_x + 40, panel_y + 70), (panel_x + panel_w - 40, panel_y + 70), 1)

        draw_text(self.screen, "Sua equipe descansa e recupera 30% da vida.",
                  (SCREEN_WIDTH // 2, panel_y + 110), font_size=22, color=SERTAO_CREAM, center=True)

        draw_text(self.screen, "Clique para continuar", (SCREEN_WIDTH // 2, panel_y + 270),
                  font_size=22, color=SERTAO_CREAM, center=True)

    def _render_level_up(self):
        self.assets.draw_background(self.screen, "level_up")

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        draw_text(self.screen, "Evolucao Disponivel!", (SCREEN_WIDTH // 2, 55),
                  font_size=44, color=SERTAO_GOLD, center=True)

        target = self.current_level_up_animal or (self.party[0] if self.party else None)
        if target:
            emoji = ANIMAL_EMOJIS.get(target.animal_id, "")
            draw_text(self.screen, f"{emoji} {target.name} Lv.{target.level} - Escolha uma evolucao:",
                      (SCREEN_WIDTH // 2, 110), font_size=22, color=SERTAO_CREAM, center=True)

        remaining = len(self.pending_level_up_animals)
        if remaining > 1:
            draw_text(self.screen, f"({remaining} evolucoes pendentes)",
                      (SCREEN_WIDTH // 2, 160), font_size=18, color=SERTAO_LIGHT, center=True)

        if self.level_up_offers:
            start_y = 190 if remaining <= 1 else 185
            for i, upgrade in enumerate(self.level_up_offers):
                btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 230, start_y + i * 140, 460, 120)
                is_hovered = (self.level_up_hover == i)

                shadow = pygame.Surface((btn_rect.w, btn_rect.h), pygame.SRCALPHA)
                pygame.draw.rect(shadow, (0, 0, 0, 80), (4, 4, btn_rect.w, btn_rect.h), border_radius=12)
                self.screen.blit(shadow, btn_rect.topleft)

                bg = (55, 45, 30) if not is_hovered else (75, 60, 40)
                border = SERTAO_BORDER if not is_hovered else SERTAO_GOLD
                pygame.draw.rect(self.screen, bg, btn_rect, border_radius=12)
                pygame.draw.rect(self.screen, border, btn_rect, 2, border_radius=12)

                cat_colors = {"offense": RED, "defense": BLUE, "utility": GREEN}
                cat_color = cat_colors.get(upgrade["category"], GRAY)

                icon_rect = pygame.Rect(btn_rect.x + 15, btn_rect.y + 15, 50, 50)
                pygame.draw.rect(self.screen, cat_color, icon_rect, border_radius=10)

                draw_text(self.screen, upgrade["name"], (btn_rect.x + 80, btn_rect.y + 18),
                          font_size=26, color=SERTAO_CREAM)
                draw_text(self.screen, upgrade["description"], (btn_rect.x + 80, btn_rect.y + 50),
                          font_size=18, color=SERTAO_CREAM)
                draw_text(self.screen, f"[{upgrade['category']}]", (btn_rect.x + 80, btn_rect.y + 82),
                          font_size=16, color=cat_color)

    def _render_rescue(self):
        self.assets.draw_background(self.screen, "rescue")

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        draw_text(self.screen, "ANIMAL REGISTRADO NO BESTIARIO", (SCREEN_WIDTH // 2, 80),
                  font_size=42, color=SERTAO_GOLD, center=True)

        if self.pending_rescue_animal:
            animals = load_animals()
            animal = animals.get(self.pending_rescue_animal, {})
            name = animal.get("name", "Desconhecido")
            role = animal.get("role", "")
            desc = animal.get("description", "")

            card_w, card_h = 420, 320
            card_x = (SCREEN_WIDTH - card_w) // 2
            card_y = 170

            shadow = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 120), (6, 6, card_w, card_h), border_radius=15)
            self.screen.blit(shadow, (card_x, card_y))

            card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card, (30, 50, 30, 230), (0, 0, card_w, card_h), border_radius=15)
            self.screen.blit(card, (card_x, card_y))
            pygame.draw.rect(self.screen, GREEN, (card_x, card_y, card_w, card_h), 3, border_radius=15)

            draw_text(self.screen, name, (SCREEN_WIDTH // 2, card_y + 40),
                      font_size=36, color=SERTAO_GOLD, center=True)
            draw_text(self.screen, role, (SCREEN_WIDTH // 2, card_y + 80),
                      font_size=22, color=SERTAO_CREAM, center=True)

            pygame.draw.line(self.screen, GREEN,
                             (card_x + 40, card_y + 105), (card_x + card_w - 40, card_y + 105), 1)

            desc_lines = word_wrap(desc, 45)
            for i, line in enumerate(desc_lines[:5]):
                draw_text(self.screen, line, (SCREEN_WIDTH // 2, card_y + 125 + i * 24),
                          font_size=18, color=SERTAO_CREAM, center=True)

        draw_text(self.screen, "Clique para continuar", (SCREEN_WIDTH // 2, 550),
                  font_size=24, color=SERTAO_CREAM, center=True)

    def _render_game_over(self):
        self.assets.draw_background(self.screen, "combat")

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((30, 10, 10, 180))
        self.screen.blit(overlay, (0, 0))

        draw_text(self.screen, "GAME OVER", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120),
                  font_size=72, color=RED, center=True)
        draw_text(self.screen, "Seus animais ainda precisam de voce...",
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30), font_size=26, color=SERTAO_CREAM, center=True)

        if self.party:
            y_off = SCREEN_HEIGHT // 2 + 20
            for animal in self.party:
                emoji = ANIMAL_EMOJIS.get(animal.animal_id, "")
                draw_text(self.screen, f"{emoji} {animal.name} - Nivel {animal.level}",
                          (SCREEN_WIDTH // 2, y_off), font_size=24, color=SERTAO_GOLD, center=True)
                y_off += 30

            draw_text(self.screen, "Progresso salvo permanentemente!",
                      (SCREEN_WIDTH // 2, y_off + 10), font_size=20, color=GREEN, center=True)

        draw_text(self.screen, "Clique para voltar ao menu principal",
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 110), font_size=20, color=GRAY, center=True)

    def _render_victory(self):
        self.assets.draw_background(self.screen, "combat")

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 30, 10, 160))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 550, 450
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2

        shadow = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 120), (6, 6, panel_w, panel_h), border_radius=14)
        self.screen.blit(shadow, (panel_x, panel_y))

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (20, 40, 20, 230), (0, 0, panel_w, panel_h), border_radius=14)
        self.screen.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(self.screen, GREEN, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=14)

        draw_text(self.screen, "VITORIA!", (SCREEN_WIDTH // 2, panel_y + 40),
                  font_size=52, color=GREEN, center=True)

        pygame.draw.line(self.screen, GREEN,
                         (panel_x + 40, panel_y + 75), (panel_x + panel_w - 40, panel_y + 75), 1)

        draw_text(self.screen, f"+{self.victory_xp_gained} XP", (SCREEN_WIDTH // 2, panel_y + 105),
                  font_size=28, color=BLUE, center=True)
        draw_text(self.screen, f"+{self.victory_gold_gained} Ouro", (SCREEN_WIDTH // 2, panel_y + 140),
                  font_size=28, color=SERTAO_GOLD, center=True)

        if self.party:
            y_off = panel_y + 180
            for animal in self.party:
                emoji = ANIMAL_EMOJIS.get(animal.animal_id, "")
                draw_text(self.screen, f"{emoji} {animal.name} Lv.{animal.level}", (SCREEN_WIDTH // 2, y_off),
                          font_size=20, color=SERTAO_CREAM, center=True)
                bar_x = panel_x + 80
                bar_w = panel_w - 160
                elapsed = time.time() - self.victory_time if self.victory_time else 1
                fill_ratio = min(1.0, elapsed / 1.0)
                pygame.draw.rect(self.screen, GRAY, (bar_x, y_off + 22, bar_w, 14))
                fill_w = int(bar_w * fill_ratio)
                pygame.draw.rect(self.screen, BLUE, (bar_x, y_off + 22, fill_w, 14))
                pygame.draw.rect(self.screen, WHITE, (bar_x, y_off + 22, bar_w, 14), 1)
                draw_text(self.screen, f"XP: {animal.xp}/{animal.xp_to_level}",
                          (SCREEN_WIDTH // 2, y_off + 40), font_size=14, color=SERTAO_CREAM, center=True)
                y_off += 60

            if self.victory_message and "|" in self.victory_message:
                parts = self.victory_message.split("|")
                for i, part in enumerate(parts):
                    draw_text(self.screen, part.strip(), (SCREEN_WIDTH // 2, y_off + 5 + i * 20),
                              font_size=18, color=SERTAO_GOLD, center=True)

        if self.next_biome_pending:
            next_name = self.next_biome_pending.replace('_', ' ').title()
            draw_text(self.screen, f"Clique para avancar para {next_name}",
                      (SCREEN_WIDTH // 2, panel_y + panel_h - 40),
                      font_size=20, color=SERTAO_GOLD, center=True)
        else:
            draw_text(self.screen, "Clique para voltar ao mapa",
                      (SCREEN_WIDTH // 2, panel_y + panel_h - 40),
                      font_size=20, color=SERTAO_CREAM, center=True)

    def _render_pause(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 400, 250
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (*SERTAO_PANEL, 240), (0, 0, panel_w, panel_h), border_radius=14)
        self.screen.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(self.screen, SERTAO_GOLD, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=14)

        draw_text(self.screen, "PAUSA", (SCREEN_WIDTH // 2, panel_y + 45),
                  font_size=52, color=SERTAO_GOLD, center=True)
        draw_text(self.screen, "ESC para continuar", (SCREEN_WIDTH // 2, panel_y + 120),
                  font_size=24, color=SERTAO_CREAM, center=True)
        draw_text(self.screen, "Q para voltar ao menu", (SCREEN_WIDTH // 2, panel_y + 165),
                  font_size=20, color=GRAY, center=True)

    def _render_animal_encounter(self):
        self.assets.draw_background(self.screen, "event")

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 650, 540
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2

        shadow = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 120), (6, 6, panel_w, panel_h), border_radius=14)
        self.screen.blit(shadow, (panel_x, panel_y))

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (*SERTAO_PANEL, 230), (0, 0, panel_w, panel_h), border_radius=14)
        self.screen.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(self.screen, GREEN, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=14)

        draw_text(self.screen, "ENCONTRO!", (SCREEN_WIDTH // 2, panel_y + 30),
                  font_size=40, color=SERTAO_GOLD, center=True)

        pygame.draw.line(self.screen, GREEN,
                         (panel_x + 40, panel_y + 60), (panel_x + panel_w - 40, panel_y + 60), 1)

        if not self.encounter_animal_id:
            draw_text(self.screen, "Voce explorou a area mas nao encontrou nenhum animal.",
                      (SCREEN_WIDTH // 2, panel_y + 120), font_size=22, color=SERTAO_CREAM, center=True)
            draw_text(self.screen, "Tente novamente mais tarde.",
                      (SCREEN_WIDTH // 2, panel_y + 155), font_size=18, color=GRAY, center=True)
            ok_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, panel_y + 300, 200, 45)
            oh = ok_rect.collidepoint(pygame.mouse.get_pos())
            draw_sertao_button(self.screen, ok_rect, "Voltar", oh)
            return

        encounter_text = getattr(self, 'encounter_text', ENCOUNTER_TEXTS[0])
        text_lines = word_wrap(encounter_text, 55)
        for i, line in enumerate(text_lines):
            draw_text(self.screen, line, (SCREEN_WIDTH // 2, panel_y + 80 + i * 24),
                      font_size=20, color=SERTAO_CREAM, center=True)

        animals = load_animals()
        animal = animals.get(self.encounter_animal_id, {})
        name = animal.get("name", "Desconhecido")
        role = animal.get("role", "")
        encounter_level = getattr(self, 'encounter_animal_level', 1)

        card_w, card_h = 400, 160
        card_x = (SCREEN_WIDTH - card_w) // 2
        card_y = panel_y + 150

        card_bg = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(card_bg, (30, 50, 30, 220), (0, 0, card_w, card_h), border_radius=12)
        self.screen.blit(card_bg, (card_x, card_y))
        pygame.draw.rect(self.screen, GREEN, (card_x, card_y, card_w, card_h), 2, border_radius=12)

        emoji = ANIMAL_EMOJIS.get(self.encounter_animal_id, "")
        if self.assets:
            spr = self.assets.get_animal_sprite(self.encounter_animal_id, max_width=80, max_height=80)
            if spr:
                self.screen.blit(spr, spr.get_rect(center=(card_x + 55, card_y + card_h // 2)))

        draw_text(self.screen, f"{emoji} {name}", (card_x + 110, card_y + 20),
                  font_size=28, color=SERTAO_GOLD)
        draw_text(self.screen, f"Nivel {encounter_level} - {role}", (card_x + 110, card_y + 55),
                  font_size=18, color=SERTAO_CREAM)

        s = animal.get("base_stats", {})
        draw_text(self.screen, f"HP:{s.get('hp',0)} ATK:{s.get('attack',0)} DEF:{s.get('defense',0)} SPD:{s.get('speed',0)}",
                  (card_x + 110, card_y + 85), font_size=14, color=SERTAO_CREAM)

        draw_text(self.screen, "Animal entrou para sua equipe!", (SCREEN_WIDTH // 2, card_y + card_h + 15),
                  font_size=20, color=GREEN, center=True)

        party_full = len(self.party) >= MAX_PARTY_SIZE
        btn_y = panel_y + 370

        if party_full:
            draw_text(self.screen, "Equipe cheia! Escolha um animal para trocar:",
                      (SCREEN_WIDTH // 2, btn_y - 5), font_size=18, color=SERTAO_CREAM, center=True)

            for i, member in enumerate(self.party):
                slot_rect = pygame.Rect(panel_x + 50, btn_y + 25 + i * 45, panel_w - 100, 40)
                is_hov = (self.encounter_swap_hover == i)
                bg_c = (65, 55, 35) if is_hov else (45, 38, 25)
                border_c = SERTAO_GOLD if is_hov else SERTAO_BORDER
                pygame.draw.rect(self.screen, bg_c, slot_rect, border_radius=8)
                pygame.draw.rect(self.screen, border_c, slot_rect, 2, border_radius=8)

                m_emoji = ANIMAL_EMOJIS.get(member.animal_id, "")
                draw_text(self.screen, f"{m_emoji} {member.name} Lv.{member.level}",
                          (slot_rect.x + 15, slot_rect.y + 8), font_size=20, color=SERTAO_CREAM)

            swap_rect = pygame.Rect(SCREEN_WIDTH // 2 + 20, btn_y + 25 + len(self.party) * 45 + 10, 200, 42)
            ignore_rect = pygame.Rect(SCREEN_WIDTH // 2 - 220, btn_y + 25 + len(self.party) * 45 + 10, 200, 42)

            sh = swap_rect.collidepoint(pygame.mouse.get_pos())
            ih = ignore_rect.collidepoint(pygame.mouse.get_pos())
            draw_sertao_button(self.screen, swap_rect, "Trocar", sh,
                               enabled=(self.encounter_swap_hover >= 0))
            draw_sertao_button(self.screen, ignore_rect, "Manter Equipe", ih)
        else:
            recruit_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, btn_y + 40, 200, 45)
            ignore_rect = pygame.Rect(SCREEN_WIDTH // 2 + 20, btn_y + 40, 200, 45)

            rh = recruit_rect.collidepoint(pygame.mouse.get_pos())
            ih = ignore_rect.collidepoint(pygame.mouse.get_pos())
            draw_sertao_button(self.screen, recruit_rect, "Recrutar", rh)
            draw_sertao_button(self.screen, ignore_rect, "Ignorar", ih)
