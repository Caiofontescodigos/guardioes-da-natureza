"""Central background-music manager for Guardioes da Natureza.

The whole game must use this single manager as the source of truth for
background music.  Callers describe *what is happening* (menu, journey,
common combat, a specific boss, or a manual preview from the music box); the
manager resolves the right file, avoids overlapping tracks and only restarts a
track when the context really changes.
"""

import os
import random
import unicodedata

import pygame


def _normalized_name(value):
    """Return a comparison key tolerant to accents, case and separators."""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.casefold().strip()


def _track_key(filename):
    """Comparison key for a track, ignoring extension and separators."""
    name = os.path.splitext(os.path.basename(str(filename)))[0]
    return "".join(ch for ch in _normalized_name(name)
                   if ch.isalnum())


class MusicManager:
    """Single source of truth for background music.

    Contexts
    --------
    menu     -> main theme (looped)
    journey  -> exploration playlist (random start and random next track)
    combat   -> optional common battle track (not used automatically; common
                and elite fights intentionally keep the journey playlist)
    boss     -> random track from the available boss pool (looped)
    manual   -> preview selected in the music box (looped)
    """

    CONTEXT_MENU = "menu"
    CONTEXT_JOURNEY = "journey"
    CONTEXT_COMBAT = "combat"
    CONTEXT_BOSS = "boss"
    CONTEXT_MANUAL = "manual"

    MENU_TRACK = "GuardiõesdaNatureza.mp3"
    MENU_ALIASES = [
        "GuardiõesdaNatureza.mp3",
        "GuardioesdaNatureza.mp3",
        "Guardiões da Natureza.mp3",
        "Guardioes da Natureza.mp3",
        "GuardioesDaNatureza.mp3",
        "guardioes_da_natureza.mp3",
    ]
    EXPLORATION_TRACKS = [
        "Rota da Caatinga.mp3",
        "Luta pela Terra.mp3",
    ]
    COMBAT_TRACKS = [
        "BatalhaFinal.mp3",
    ]
    # Boss tracks.  Both files below are real project assets and form the
    # randomised boss pool.  The mapping keeps a sensible preference per boss,
    # while play_boss() draws from the whole pool each encounter.
    BOSS_TRACKS = {
        "lobo_alfa_de_fogo": "Defesa de Fogo.mp3",
        "vendaval_de_fogo": "BatalhaFinal.mp3",
    }
    BOSS_FALLBACK_TRACKS = [
        "Defesa de Fogo.mp3",
        "BatalhaFinal.mp3",
    ]

    # Tracks shown by the music box.  This catalog is explicit on purpose:
    # files not listed here are never auto-selected by the game.
    MUSIC_BOX_CATALOG = [
        ("GuardiõesdaNatureza.mp3", "Guardiões da Natureza", "Menu"),
        ("Rota da Caatinga.mp3", "Rota da Caatinga", "Exploração"),
        ("Luta pela Terra.mp3", "Luta pela Terra", "Exploração"),
        ("BatalhaFinal.mp3", "Batalha Final", "Batalha / Chefe"),
        ("Defesa de Fogo.mp3", "Defesa de Fogo", "Chefe"),
    ]

    # This track must never be selected automatically or manually by the game.
    EXCLUDED_TRACK_MARKERS = ("momentoderradeiro",)

    def __init__(self, music_dir, volume=0.7):
        self.music_dir = music_dir
        self.volume = max(0.0, min(1.0, float(volume)))
        self.muted = False
        self._mixer_ok = False
        self.enabled = True

        # Compatibility aliases kept for callers/tests that inspect them.
        self.main_playlist = list(self.EXPLORATION_TRACKS)
        self.boss_tracks = list(self.BOSS_FALLBACK_TRACKS)

        self._music_end_event = pygame.USEREVENT + 1
        self._context = None
        self._active_tracks = []
        self._track_index = 0
        self._loop_current = False
        self._playing_filename = None
        self._playing_path = None
        self._paused = False
        self._hold_current = False
        self._boss_key = None
        self._last_boss_track = None

        if not os.path.isdir(self.music_dir):
            print(f"[MUSIC] diretorio nao encontrado: {self.music_dir}")
            self.enabled = False
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self._mixer_ok = True
            self._apply_volume()
            pygame.mixer.music.set_endevent(self._music_end_event)
            print("[MUSIC] mixer iniciado")
        except Exception as exc:
            print(f"[MUSIC] ERRO ao iniciar mixer: {exc}")
            self._mixer_ok = False
            self.enabled = False

    # --------------------------------------------------------------- helpers

    @property
    def end_event(self):
        return self._music_end_event

    @property
    def context(self):
        return self._context

    @property
    def current_track(self):
        return self._playing_filename

    @property
    def paused(self):
        return self._paused

    @property
    def is_playing(self):
        if not self._playing_filename:
            return False
        try:
            return bool(pygame.mixer.music.get_busy() or self._paused)
        except Exception:
            return False

    def _is_excluded(self, filename):
        key = _track_key(filename)
        return any(marker in key for marker in self.EXCLUDED_TRACK_MARKERS)

    def _find_file(self, filename):
        """Resolve a track by name, case/accent/separator insensitive."""
        if self._is_excluded(filename):
            print(f"[MUSIC] faixa bloqueada: {filename}")
            return None

        path = os.path.join(self.music_dir, filename)
        if os.path.isfile(path):
            return path

        target = _track_key(filename)
        try:
            for entry in os.listdir(self.music_dir):
                if self._is_excluded(entry):
                    continue
                if not entry.lower().endswith((".mp3", ".ogg", ".wav")):
                    continue
                if _track_key(entry) == target:
                    candidate = os.path.join(self.music_dir, entry)
                    if os.path.isfile(candidate):
                        return candidate
        except Exception:
            pass

        print(f"[MUSIC] arquivo nao encontrado: {path}")
        return None

    def _resolve_track(self, filename):
        """Return the real basename of an allowed, existing track."""
        if not filename or self._is_excluded(filename):
            return None
        path = self._find_file(filename)
        if not path:
            return None
        return os.path.basename(path)

    def _resolve_tracks(self, filenames):
        tracks = []
        seen = set()
        for filename in filenames:
            actual = self._resolve_track(filename)
            if actual and actual not in seen:
                seen.add(actual)
                tracks.append(actual)
        return tracks

    def _play_file(self, filename, loops=0):
        if not self.enabled or not self._mixer_ok:
            return False
        if self._is_excluded(filename):
            print(f"[MUSIC] recusando faixa bloqueada: {filename}")
            return False
        path = self._find_file(filename)
        if not path:
            return False
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loops)
            self._playing_filename = os.path.basename(path)
            self._playing_path = path
            self._paused = False
            print(f"[MUSIC] tocando {self._playing_filename} ({self._context})")
            return True
        except Exception as exc:
            print(f"[MUSIC] ERRO ao tocar {filename}: {exc}")
            self._playing_filename = None
            self._playing_path = None
            return False

    def _stop_music(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self._playing_filename = None
        self._playing_path = None
        self._paused = False

    def _random_index(self, tracks, avoid_track=None):
        """Pick a random track index, avoiding ``avoid_track`` when possible."""
        if len(tracks) <= 1:
            return 0
        avoid_key = _track_key(avoid_track) if avoid_track else None
        candidates = [index for index, track in enumerate(tracks)
                      if _track_key(track) != avoid_key]
        if not candidates:
            candidates = list(range(len(tracks)))
        return random.choice(candidates)

    def _play_context(self, context, requested_tracks, loop=False,
                      start_index=0, force=False, randomize=False,
                      avoid_track=None):
        """Switch to ``context`` and play the first resolvable track.

        Re-requesting the exact same track in the same context is a no-op
        (unless ``force`` is used), so navigation between screens never
        restarts the music.
        """
        if not self.enabled or not self._mixer_ok:
            return False

        if context != self.CONTEXT_JOURNEY:
            # Any explicit non-journey context releases a combat hold.
            self._hold_current = False

        tracks = self._resolve_tracks(requested_tracks)
        if not tracks:
            print(f"[MUSIC] nenhuma faixa valida para o contexto {context}")
            return False

        if randomize:
            index = self._random_index(tracks, avoid_track)
        else:
            index = start_index % len(tracks)
        track = tracks[index]
        same_context = self._context == context
        same_playlist = self._active_tracks == tracks
        same_track = self._playing_filename == track

        if not force and same_context and same_playlist and same_track:
            self._loop_current = bool(loop)
            if self._paused:
                try:
                    pygame.mixer.music.unpause()
                except Exception:
                    pass
                self._paused = False
                return True
            try:
                if pygame.mixer.music.get_busy():
                    return True
            except Exception:
                pass

        self._context = context
        self._active_tracks = tracks
        self._track_index = index
        self._loop_current = bool(loop)
        return self._play_file(track, loops=-1 if loop else 0)

    # ------------------------------------------------------------- contexts

    def play_menu_music(self):
        """Play the main menu theme on a loop."""
        return self._play_context(
            self.CONTEXT_MENU, [self.MENU_TRACK] + self.MENU_ALIASES,
            loop=True)

    def start_playlist(self, new_track=False):
        """Play/resume the exploration playlist (journey context).

        With ``new_track`` a fresh random journey track is chosen, avoiding an
        immediate repeat.  Without it, an already active journey track is
        preserved so ordinary screen navigation never restarts the music.
        """
        if (not new_track and self._context == self.CONTEXT_JOURNEY
                and self._active_tracks and self._playing_filename):
            return self._play_context(
                self.CONTEXT_JOURNEY, self.EXPLORATION_TRACKS,
                loop=False, start_index=self._track_index)
        return self._play_context(
            self.CONTEXT_JOURNEY, self.EXPLORATION_TRACKS,
            loop=False, randomize=True, avoid_track=self._playing_filename)

    def play_journey(self, new_track=False):
        """Resume the normal exploration playlist.

        ``new_track=True`` asks for a fresh random journey track (used when a
        run starts, is resumed, or when the map/biome changes).
        Also releases the temporary hold used by common/elite combat.
        """
        self._hold_current = False
        return self.start_playlist(new_track=new_track)

    def hold_journey(self):
        """Keep the current journey track during a common/elite battle.

        The track is not switched or restarted when it is already playing.
        If it reaches the end during the fight, the same track repeats instead
        of advancing the exploration playlist.  Calling :meth:`play_journey`
        afterwards restores normal playlist progression.
        """
        if not (self._context == self.CONTEXT_JOURNEY
                and self._playing_filename):
            if not self.start_playlist():
                return False
        self._hold_current = True
        return True

    def play_combat(self):
        """Play the optional common battle track on a loop.

        Common and elite fights intentionally stay on the journey playlist,
        so the game does not call this automatically. It remains available
        for explicit/manual use or future battle-specific screens.
        """
        return self._play_context(
            self.CONTEXT_COMBAT, self.COMBAT_TRACKS, loop=True)

    def play_boss(self, boss_id=None):
        """Play a random boss track (looped).

        ``boss_id`` is the enemy identifier.  The available boss tracks are
        selected randomly for each encounter, avoiding an immediate repeat of
        the previous boss track.  Requesting the same boss again while its
        fight is already active keeps the current track without restarting.
        """
        boss_key = _normalized_name(boss_id or "")

        if (self._context == self.CONTEXT_BOSS
                and self._boss_key == boss_key and self._active_tracks):
            return self._play_context(
                self.CONTEXT_BOSS, self._active_tracks, loop=True,
                start_index=self._track_index)

        requested = []
        if boss_key in self.BOSS_TRACKS:
            requested.append(self.BOSS_TRACKS[boss_key])
        else:
            print(f"[MUSIC] chefe sem mapa dedicado ({boss_id!r}); "
                  f"usando faixas de chefe")
        requested.extend(self.BOSS_FALLBACK_TRACKS)

        self._boss_key = boss_key
        result = self._play_context(
            self.CONTEXT_BOSS, requested, loop=True, randomize=True,
            avoid_track=self._last_boss_track)
        if result and self._playing_filename:
            self._last_boss_track = self._playing_filename
        return result

    def play_manual(self, filename):
        """Preview a track from the music box (looped)."""
        return self._play_context(
            self.CONTEXT_MANUAL, [filename], loop=True, force=True)

    def resume_playlist(self, new_track=False):
        """Return from combat/boss to the journey playlist."""
        return self.start_playlist(new_track=new_track)

    # ------------------------------------------------------------- playback

    def stop(self, force=False):
        """Stop music and clear the current context."""
        if not self._mixer_ok:
            return
        self._stop_music()
        self._context = None
        self._active_tracks = []
        self._track_index = 0
        self._loop_current = False
        self._hold_current = False
        self._boss_key = None
        print("[MUSIC] parada")

    def stop_menu_music(self):
        if self._context == self.CONTEXT_MENU:
            self.stop()

    def pause(self):
        if not self._mixer_ok or self._paused:
            return False
        try:
            pygame.mixer.music.pause()
            self._paused = True
            return True
        except Exception:
            return False

    def resume(self):
        if not self._mixer_ok:
            return False
        if self._paused:
            try:
                pygame.mixer.music.unpause()
                self._paused = False
                return True
            except Exception:
                return False
        if self._playing_filename and not self.is_playing:
            return self._play_file(
                self._playing_filename, loops=-1 if self._loop_current else 0)
        return False

    def toggle_pause(self):
        if self._paused:
            self.resume()
        else:
            self.pause()
        return self._paused

    def update(self, event):
        """Advance the exploration playlist when a track finishes."""
        if event.type != self._music_end_event:
            return
        if self._context != self.CONTEXT_JOURNEY or not self._active_tracks:
            return
        if self._hold_current:
            # Common/elite combat holds the current journey track: repeat it
            # instead of changing the song in the middle of the battle.
            self._play_file(self._active_tracks[self._track_index], loops=0)
            return
        if self._loop_current:
            return
        next_index = self._random_index(
            self._active_tracks, self._active_tracks[self._track_index])
        self._track_index = next_index
        self._play_file(self._active_tracks[self._track_index], loops=0)

    # --------------------------------------------------------------- volume

    def _apply_volume(self):
        if not self._mixer_ok:
            return
        try:
            pygame.mixer.music.set_volume(0.0 if self.muted else self.volume)
        except Exception:
            pass

    def set_volume(self, volume):
        try:
            self.volume = max(0.0, min(1.0, float(volume)))
        except (TypeError, ValueError):
            return
        self._apply_volume()

    def set_muted(self, muted):
        self.muted = bool(muted)
        self._apply_volume()

    # ------------------------------------------------------------ music box

    def track_label(self, filename):
        key = _track_key(filename)
        for catalog_name, title, _category in self.MUSIC_BOX_CATALOG:
            if _track_key(catalog_name) == key:
                return title
        return os.path.splitext(os.path.basename(str(filename)))[0]

    def available_tracks(self):
        """Return the playable catalog for the music box.

        Only files that actually exist are returned.  The forbidden track is
        filtered out both by the catalog (it is not listed) and by
        :meth:`_resolve_track`.
        """
        result = []
        seen = set()
        for filename, title, category in self.MUSIC_BOX_CATALOG:
            actual = self._resolve_track(filename)
            if not actual or actual in seen:
                continue
            seen.add(actual)
            result.append({
                "filename": actual,
                "title": title,
                "category": category,
            })
        return result

    def context_label(self):
        labels = {
            self.CONTEXT_MENU: "Menu principal",
            self.CONTEXT_JOURNEY: "Jornada / exploração",
            self.CONTEXT_COMBAT: "Batalha comum",
            self.CONTEXT_BOSS: "Chefe",
            self.CONTEXT_MANUAL: "Caixa de música (manual)",
        }
        return labels.get(self._context, "Sem música")
