import pygame
import os
import random


class MusicManager:
    def __init__(self, music_dir, volume=0.7):
        self.music_dir = music_dir
        self.volume = volume
        self._mixer_ok = False
        self.enabled = True

        self.playlist = [
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

        if not os.path.isdir(self.music_dir):
            print(f"[MUSIC] diretorio nao encontrado: {self.music_dir}")
            self.enabled = False
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self._mixer_ok = True
            pygame.mixer.music.set_volume(self.volume)
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

    def _play_file(self, filename, loops=-1):
        if not self.enabled or not self._mixer_ok:
            return False
        path = self._find_file(filename)
        if not path:
            return False
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loops)
            print(f"[MUSIC] tocando {filename}")
            return True
        except Exception as e:
            print(f"[MUSIC] ERRO ao tocar {filename}: {e}")
            return False

    def start_playlist(self):
        if not self.enabled or not self._mixer_ok:
            return
        self.is_playlist_mode = True
        self.boss_mode = False
        self.current_index = 0
        print("[MUSIC] playlist iniciada")
        self._play_file(self.playlist[self.current_index])

    def _advance_playlist(self):
        if not self.is_playlist_mode or self.boss_mode:
            return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self._play_file(self.playlist[self.current_index])

    def play_boss(self):
        if not self.enabled or not self._mixer_ok:
            return
        print("[MUSIC] boss detectado")
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.boss_mode = True
        track = random.choice(self.boss_tracks)
        print("[MUSIC] sorteando musica de chefe")
        self._play_file(track, loops=-1)

    def resume_playlist(self):
        if not self.enabled or not self._mixer_ok:
            return
        if self.boss_mode:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            self.boss_mode = False
            print("[MUSIC] retornando para playlist principal")
            self._play_file(self.playlist[self.current_index])

    def stop(self):
        if not self.enabled or not self._mixer_ok:
            return
        if not self.is_playlist_mode and not self.boss_mode:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.is_playlist_mode = False
        self.boss_mode = False
        self.current_index = 0
        print("[MUSIC] parada")

    def update(self, event):
        if event.type == self._music_end_event:
            if self.is_playlist_mode and not self.boss_mode:
                self._advance_playlist()

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))
        if self._mixer_ok:
            try:
                pygame.mixer.music.set_volume(self.volume)
            except Exception:
                pass
