from aoslib import audio
import audioop, wave, os, glob, random
from aoslib.common import to_pitch_yaw
from cStringIO import StringIO
from shared.constants import DEFAULT_ATTENUATION, DEFAULT_MUSIC_FADE_TIME
from shared.glm import Vector3
from shared.constants import AUDIO_FORMAT_EXTENSION
from shared.constants_audio import HEARING_DISTANCE
MUTED = False
HUD_AUDIO_ZONE, IN_WORLD_AUDIO_ZONE, MUSIC_AUDIO_ZONE, DEFAULT_AUDIO_ZONE = xrange(4)
DEFAULT_MUSIC_FADE_SPEED = 1 / DEFAULT_MUSIC_FADE_TIME

class GameSound(audio.Sound):

    def set_position(self, x, y, z):
        self.position = (
         x + 0.5, -z + 0.5, y + 0.5)


class MediaManager(object):
    path = 'sounds'
    music_path = 'music'
    current_music = old_music = None
    music_name = None
    current_music_fade_speed = DEFAULT_MUSIC_FADE_SPEED
    old_music_fade_speed = DEFAULT_MUSIC_FADE_SPEED

    def __init__(self, manager):
        self.manager = manager
        self.config = manager.config
        audio.open()
        if MUTED:
            self.set_main_volume(0.0)
        self.players = []
        audio.load_all_buffers(self.path)

    def get_sound_name(self, name):
        actual_name = name
        if isinstance(name, list):
            full_sound_name = name[0]
            last_played = name[1]
            disallow_consecutive_plays = name[2] < 0
            play_chance = abs(name[2])
            if disallow_consecutive_plays and last_played >= 1000:
                name[1] -= 1000
                return
            random_percent = random.randint(0, 100)
            if play_chance >= random_percent:
                if '_' in full_sound_name and '-' in full_sound_name:
                    last_index = full_sound_name.rindex('_')
                    sound_name = full_sound_name[0:last_index + 1]
                    numbers = full_sound_name[last_index + 1:len(full_sound_name)]
                    start_str, end_str = numbers.split('-')
                    start_number = int(start_str)
                    end_number = int(end_str)
                    if start_number != end_number:
                        random_index = last_played
                        while random_index == last_played:
                            random_index = random.randint(start_number, end_number)

                    else:
                        random_index = start_number
                    name[1] = random_index
                    random_str = str(random_index)
                    while len(random_str) < 3:
                        random_str = '0' + random_str

                    actual_name = sound_name + random_str
                else:
                    actual_name = full_sound_name
                if disallow_consecutive_plays:
                    name[1] += 1000
            else:
                actual_name = None
        return actual_name

    def play_pitched(self, name, volume=1.0, pos=None, loops=1, attenuation=DEFAULT_ATTENUATION, zone=DEFAULT_AUDIO_ZONE):
        min_rand_pitch = 0.0
        max_rand_pitch = 0.0
        if isinstance(name, list):
            if len(name) > 3:
                min_rand_pitch = name[3]
                max_rand_pitch = name[4]
        self.play(name, volume, pos, loops, attenuation, zone, min_rand_pitch, max_rand_pitch)

    def play(self, name, volume=1.0, pos=None, loops=1, attenuation=DEFAULT_ATTENUATION, zone=DEFAULT_AUDIO_ZONE, min_rand_pitch=0.0, max_rand_pitch=0.0, streaming=False, max_distance=HEARING_DISTANCE):
        if max_distance is not None and pos is not None and audio.listener is not None and audio.listener.position is not None:
            listener_position = Vector3(*audio.listener.position)
            sound_position = Vector3(*pos)
            z = sound_position.y
            sound_position.y = -sound_position.z
            sound_position.z = z
            if sound_position.sq_distance(listener_position) > max_distance * max_distance:
                return
        if self.manager.showing_loading_screen:
            cancel_play = True
            if loops != 0:
                cancel_play = True
            else:
                for ambient_sound in self.manager.game_scene.ambient_sounds:
                    if ambient_sound.name == name:
                        cancel_play = False

            if cancel_play:
                return
        actual_sound_name = self.get_sound_name(name)
        if actual_sound_name is None or actual_sound_name == '':
            return
        else:
            try:
                if streaming:
                    player = GameSound(actual_sound_name, filename='ambients/' + actual_sound_name + '.' + AUDIO_FORMAT_EXTENSION, streaming=True)
                else:
                    player = GameSound(actual_sound_name, streaming=False)
            except:
                print 'Failed to play sound:', name
                return

            self.players.append(player)
            if pos is not None:
                x, y, z = pos
                player.set_position(x, y, z)
                player.attenuation = attenuation
                player.relative = False
            else:
                player.relative = True
            if zone is DEFAULT_AUDIO_ZONE:
                if pos is not None:
                    zone = IN_WORLD_AUDIO_ZONE
                else:
                    zone = HUD_AUDIO_ZONE
            if zone == IN_WORLD_AUDIO_ZONE:
                effect = audio.AOS_EFFECT_REVERB
            else:
                effect = audio.AOS_EFFECT_NONE
            if zone == MUSIC_AUDIO_ZONE:
                volume *= self.config.music_volume
            player.volume = volume
            pitch_semitones = min_rand_pitch
            if min_rand_pitch != max_rand_pitch:
                min_rand_pitch = min_rand_pitch / 12.0
                max_rand_pitch = max_rand_pitch / 12.0
                int_min_rand_pitch = int(min_rand_pitch * 1000)
                int_max_rand_pitch = int(max_rand_pitch * 1000)
                int_rand_pitch = random.randint(int_min_rand_pitch, int_max_rand_pitch)
                pitch_semitones = int_rand_pitch / 1000.0 * 12.0
            if pitch_semitones != 0:
                oneOverTwelve = 0.083333333333
                pitch = pow(2.0, pitch_semitones * oneOverTwelve)
                player.set_pitch(pitch)
            player.play(loops=loops, effect=effect)
            return player

    def get_music_family_name(self, name):
        actual_name = name
        if isinstance(name, list):
            full_sound_name = name[0]
            last_played = name[1]
            if '_' in full_sound_name and '-' in full_sound_name:
                last_index = full_sound_name.rindex('_')
                actual_name = full_sound_name[0:last_index + 1]
            else:
                actual_name = full_sound_name
        return actual_name

    def get_music_name(self, name):
        actual_name = name
        if isinstance(name, list):
            full_sound_name = name[0]
            last_played = name[1]
            if '_' in full_sound_name and '-' in full_sound_name:
                last_index = full_sound_name.rindex('_')
                sound_name = full_sound_name[0:last_index + 1]
                numbers = full_sound_name[last_index + 1:len(full_sound_name)]
                start_str, end_str = numbers.split('-')
                start_number = int(start_str)
                end_number = int(end_str)
                if start_number != end_number:
                    random_index = last_played
                    while random_index == last_played:
                        random_index = random.randint(start_number, end_number)

                else:
                    random_index = start_number
                name[1] = random_index
                random_str = str(random_index)
                while len(random_str) < 3:
                    random_str = '0' + random_str

                actual_name = sound_name + random_str
            else:
                actual_name = full_sound_name
        return actual_name

    def play_music(self, name, volume, start_offset=0.0, fade_speed_when_finished=DEFAULT_MUSIC_FADE_SPEED):
        if self.is_playing_music(name):
            return
        if self.old_music:
            self.old_music.volume = 0.0
        self.stop_music()
        music_name = self.get_music_name(name)
        path = os.path.join(self.music_path, music_name + '.' + AUDIO_FORMAT_EXTENSION)
        self.music_name = music_name
        self.current_music = audio.Sound(name=music_name, filename=path, streaming=True)
        self.current_music.set_time(start_offset % self.current_music.get_duration())
        self.current_music.play(loops=0)
        self.current_music.set_time(start_offset % self.current_music.get_duration())
        self.current_music.volume = volume
        self.current_music_fade_speed = fade_speed_when_finished

    def is_playing_music(self, music_name):
        if self.current_music is None or self.music_name is None:
            return False
        family_name = self.get_music_family_name(music_name)
        return self.music_name.lower().startswith(family_name.lower())

    def stop_music(self, instant=False):
        if self.current_music is not None:
            self.old_music = self.current_music
            self.current_music = self.music_name = None
            self.old_music_fade_speed = self.current_music_fade_speed
            self.current_music_fade_speed = DEFAULT_MUSIC_FADE_SPEED
            if instant:
                self.handle_old_music(0.0, instant)
        return

    def update(self, dt):
        for player in self.players[:]:
            if not player.is_playing():
                player.close()
                self.players.remove(player)

        self.handle_old_music(dt, False)

    def handle_old_music(self, dt, instant_end):
        if self.old_music:
            volume = self.old_music.volume
            volume = max(0, volume - dt * self.old_music_fade_speed)
            self.old_music.volume = volume
            if volume <= 0 or instant_end:
                self.old_music.close()
                self.old_music = None
        return

    def set_listener(self, position, up_vector, at_vector):
        x, y, z = position
        audio.listener.position = (x, -z, y)
        audio.listener.orientation = up_vector + at_vector

    def set_main_volume(self, volume):
        audio.listener.volume = volume

    def set_music_volume(self, volume):
        if self.current_music:
            self.current_music.volume = volume

    def stop_sounds(self, ignore_sounds=None):
        if ignore_sounds:
            ignored_sounds_only = [self.players[x] for x in range(len(self.players)) if x in ignore_sounds]
            sounds_to_close = list(set(self.players) - set(ignored_sounds_only))
            for player in sounds_to_close:
                player.close()

            self.players = ignored_sounds_only
        else:
            for player in self.players[:]:
                player.close()

            self.players = []

    def shutdown(self):
        self.stop_sounds()
        for music in (self.old_music, self.current_music):
            if music is None:
                continue
            music.close()

        self.old_music = self.current_music = None
        return
