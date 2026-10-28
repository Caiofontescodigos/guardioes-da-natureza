import pygame
import os
import random


class MusicManager:
    """Single source of truth for background music.

    Main music and boss music are real alternating playlists driven by the
    pygame music-end event. A track is played exactly once (no loop=-1); when
    it finishes the event handler advances to the next track in the playlist.
    """

    def __init__(self, music_dir, volume=0.7):
        self.music_dir = music_dir
        self.volume = volume
        self.muted = False
        self._mixer_ok = False
        self.enabled = True

        self.main_playlist = [
            "Rota da Caatinga.mp3",
            "Luta pela Terra.mp3",
        ]
        self.boss_tracks = [
            "BatalhaFinal.mp3",
            "Defesa de Fogo.mp3",
        ]

        self.current_index = 0
        self.is_playlist_mode = False
        self.boss_mode = False
        self._music_end_event = pygame.USEREVENT + 1
        self._active_tracks = list(self.main_playlist)
        self._playing_filename = None
        self._main_index = 0

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
        except Exception as e:
            print(f"[MUSIC] ERRO ao iniciar mixer: {e}")
            self._mixer_ok = False
            self.enabled = False

    @property
    def end_event(self):
        return self._music_end_event

    def _find_file(self, filename):
        path = os.path.join(self.music_dir, filename)
        if os.path.isfile(path):
            return path
        print(f"[MUSIC] arquivo nao encontrado: {path}")
        return None

    def _play_file(self, filename, loops=0):
        if not self.enabled or not self._mixer_ok:
            return False
        path = self._find_file(filename)
        if not path:
            return False
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loops)
            self._playing_filename = filename
            print(f"[MUSIC] tocando {filename}")
            return True
        except Exception as e:
            print(f"[MUSIC] ERRO ao tocar {filename}: {e}")
            self._playing_filename = None
            return False

    def _stop_music(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self._playing_filename = None

    def start_playlist(self):
        if not self.enabled or not self._mixer_ok:
            return
        if self.is_playlist_mode and not self.boss_mode:
            print("[MUSIC] playlist principal ja em andamento, nao reiniciando")
            return
        self.is_playlist_mode = True
        self.boss_mode = False
        self._active_tracks = list(self.main_playlist)
        self.current_index = random.choice(range(len(self.main_playlist)))
        print("[MUSIC] playlist principal iniciada (primeira faixa sorteada)")
        self._play_file(self._active_tracks[self.current_index], loops=0)

    def _advance_playlist(self):
        ended = self._playing_filename
        expected = self._active_tracks[self.current_index]
        if ended is not None and ended == expected:
            self.current_index = (self.current_index + 1) % len(self._active_tracks)
            self._play_file(self._active_tracks[self.current_index], loops=0)

    def play_boss(self):
        if not self.enabled or not self._mixer_ok:
            return
        if self.boss_mode:
            print("[MUSIC] modo boss ja ativo, mantendo playlist")
            return
        print("[MUSIC] boss detectado")
        self._main_index = self.current_index
        self._stop_music()
        self.boss_mode = True
        self.is_playlist_mode = True
        self._active_tracks = list(self.boss_tracks)
        self.current_index = random.choice(range(len(self.boss_tracks)))
        print("[MUSIC] sorteando musica de chefe")
        self._play_file(self._active_tracks[self.current_index], loops=0)

    def resume_playlist(self):
        if not self.enabled or not self._mixer_ok:
            return
        if self.boss_mode:
            self._stop_music()
            self.boss_mode = False
            self.is_playlist_mode = True
            self._active_tracks = list(self.main_playlist)
            self.current_index = self._main_index % len(self.main_playlist)
            print("[MUSIC] retornando para playlist principal")
            self._play_file(self._active_tracks[self.current_index], loops=0)

    def stop(self):
        if not self.enabled or not self._mixer_ok:
            return
        if not self.is_playlist_mode and not self.boss_mode:
            return
        self._stop_music()
        self.is_playlist_mode = False
        self.boss_mode = False
        self.current_index = 0
        self._active_tracks = list(self.main_playlist)
        self._main_index = 0
        print("[MUSIC] parada")

    def update(self, event):
        if event.type == self._music_end_event and self.is_playlist_mode:
            self._advance_playlist()

    def _apply_volume(self):
        if not self._mixer_ok:
            return
        try:
            pygame.mixer.music.set_volume(0.0 if self.muted else self.volume)
        except Exception:
            pass

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))
        self._apply_volume()

    def set_muted(self, muted):
        self.muted = bool(muted)
        self._apply_volume()