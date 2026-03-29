import ctypes
from ctypes import *
import sys, os, atexit
from aoslib.lib import load_library
from aoslib import loadingscreen
from time import clock
from aoslib.physfs import phys_open
from shared.constants import AUDIO_FORMAT_EXTENSION
import glob
openal_lib = load_library('openal', win32='openal32', darwin='libopenal.dylib')
alure_lib = load_library('alure', win32='alure32', darwin='libalure.dylib')
ALboolean = c_int
ALchar = c_char
ALbyte = c_char
ALubyte = c_ubyte
ALshort = c_short
ALushort = c_ushort
ALint = c_int
ALuint = c_uint
ALsizei = c_int
ALenum = c_int
ALfloat = c_float
ALdouble = c_double
ALvoid = None
ALCchar = c_char
ALCint = c_int
alureInt64 = c_longlong
alureUInt64 = c_ulonglong
AL_EXT_EFX = hasattr(openal_lib, 'alIsAuxiliaryEffectSlot')
if AL_EXT_EFX:
    alIsAuxiliaryEffectSlot = openal_lib.alIsAuxiliaryEffectSlot
    alIsAuxiliaryEffectSlot.restype = ALboolean
    alIsAuxiliaryEffectSlot.argtypes = [ALuint]
    alIsFilter = openal_lib.alIsFilter
    alIsFilter.restype = ALboolean
    alIsFilter.argtypes = [ALuint]
    alGenFilters = openal_lib.alGenFilters
    alGenFilters.restype = None
    alGenFilters.argtypes = [ALsizei, POINTER(ALuint)]
    alFilteri = openal_lib.alFilteri
    alFilteri.restype = None
    alFilteri.argtypes = [ALuint, ALenum, ALint]
    alFilterf = openal_lib.alFilterf
    alFilterf.restype = None
    alFilterf.argtypes = [ALuint, ALenum, ALfloat]
    alGenEffects = openal_lib.alGenEffects
    alGenEffects.restype = None
    alGenEffects.argtypes = [ALsizei, POINTER(ALuint)]
    alEffectf = openal_lib.alEffectf
    alEffectf.restype = None
    alEffectf.argtypes = [ALuint, ALenum, ALfloat]
    alEffecti = openal_lib.alEffecti
    alEffecti.restype = None
    alEffecti.argtypes = [ALuint, ALenum, ALuint]
    alAuxiliaryEffectSloti = openal_lib.alAuxiliaryEffectSloti
    alAuxiliaryEffectSloti.restype = None
    alAuxiliaryEffectSloti.argtypes = [ALuint, ALenum, ALint]
    alGenAuxiliaryEffectSlots = openal_lib.alGenAuxiliaryEffectSlots
    alGenAuxiliaryEffectSlots.restype = None
    alGenAuxiliaryEffectSlots.argtypes = [ALsizei, POINTER(ALuint)]
alGenBuffers = openal_lib.alGenBuffers
alGenBuffers.restype = None
alGenBuffers.argtypes = [ALsizei, POINTER(ALuint)]
alDeleteBuffers = openal_lib.alDeleteBuffers
alDeleteBuffers.restype = None
alDeleteBuffers.argtypes = [ALsizei, POINTER(ALuint)]
alBufferData = openal_lib.alBufferData
alBufferData.restype = None
alBufferData.argtypes = [ALuint, ALenum, c_char_p, ALsizei, ALsizei]
alSourcef = openal_lib.alSourcef
alSourcef.restype = None
alSourcef.argtypes = [ALuint, ALenum, ALfloat]
alSourcei = openal_lib.alSourcei
alSourcei.restype = None
alSourcei.argtypes = [ALuint, ALenum, ALint]
alSource3i = openal_lib.alSource3i
alSource3i.restype = None
alSource3i.argtypes = [ALuint, ALenum, ALint, ALint, ALint]
alGetSourcef = openal_lib.alGetSourcef
alGetSourcef.restype = None
alGetSourcef.argtypes = [ALuint, ALenum, POINTER(ALfloat)]
alGetSource3f = openal_lib.alGetSource3f
alGetSource3f.restype = None
alGetSource3f.argtypes = [ALuint, ALenum, POINTER(ALfloat), POINTER(ALfloat),
 POINTER(ALfloat)]
alSource3f = openal_lib.alSource3f
alSource3f.restype = None
alSource3f.argtypes = [ALuint, ALenum, ALfloat, ALfloat, ALfloat]
alGetSourcei = openal_lib.alGetSourcei
alGetSourcei.restype = None
alGetSourcei.argtypes = [ALuint, ALenum, POINTER(ALint)]
alGenSources = openal_lib.alGenSources
alGenSources.restype = None
alGenSources.argtypes = [ALsizei, POINTER(ALuint)]
alDeleteSources = openal_lib.alDeleteSources
alDeleteSources.restype = None
alDeleteSources.argtypes = [ALsizei, POINTER(ALuint)]
alGetSource3f = openal_lib.alGetSource3f
alGetSource3f.restype = None
alGetSource3f.argtypes = [ALuint, ALenum, POINTER(ALfloat), POINTER(ALfloat),
 POINTER(ALfloat)]
alListenerf = openal_lib.alListenerf
alListenerf.restype = None
alListenerf.argtypes = [ALenum, ALfloat]
alListenerfv = openal_lib.alListenerfv
alListenerfv.restype = None
alListenerfv.argtypes = [ALenum, POINTER(ALfloat)]
alListener3f = openal_lib.alListener3f
alListener3f.restype = None
alListener3f.argtypes = [ALenum, ALfloat, ALfloat, ALfloat]
alGetError = openal_lib.alGetError
alGetError.restype = ALenum
alGetError.argtypes = []
alIsExtensionPresent = openal_lib.alIsExtensionPresent
alIsExtensionPresent.restype = ALboolean
alIsExtensionPresent.argtypes = [POINTER(ALchar)]
alGetString = openal_lib.alGetString
alGetString.restype = POINTER(ALchar)
alGetString.argtypes = [ALenum]

class alureStream(Structure):
    pass


alureStream_p = POINTER(alureStream)
alureCreateBufferFromMemory = alure_lib.alureCreateBufferFromMemory
alureCreateBufferFromMemory.restype = ALuint
alureCreateBufferFromMemory.argtypes = [POINTER(ALchar), ALsizei]
alureInitDevice = alure_lib.alureInitDevice
alureInitDevice.restype = ALboolean
alureInitDevice.argtypes = [POINTER(ALCchar), POINTER(ALCint)]
alureShutdownDevice = alure_lib.alureShutdownDevice
alureShutdownDevice.restype = ALboolean
alureShutdownDevice.argtypes = []
alureGetErrorString = alure_lib.alureGetErrorString
alureGetErrorString.restype = c_char_p
alureGetErrorString.argtypes = []
alureResumeSource = alure_lib.alureResumeSource
alureResumeSource.restype = ALboolean
alureResumeSource.argtypes = [ALuint]
alureUpdateInterval = alure_lib.alureUpdateInterval
alureUpdateInterval.restype = ALboolean
alureUpdateInterval.argtypes = [ALfloat]
alurePauseSource = alure_lib.alurePauseSource
alurePauseSource.restype = ALboolean
alurePauseSource.argtypes = [ALuint]
alureStopSource = alure_lib.alureStopSource
alureStopSource.restype = ALboolean
alureStopSource.argtypes = [ALuint]
CALLBACK_FUNC = CFUNCTYPE(None, py_object, ALuint)
alurePlaySource = alure_lib.alurePlaySource
alurePlaySource.restype = ALboolean
alurePlaySource.argtypes = [ALuint, c_void_p, py_object]
alurePlaySourceStream = alure_lib.alurePlaySourceStream
alurePlaySourceStream.restype = ALboolean
alurePlaySourceStream.argtypes = [ALuint, alureStream_p, ALsizei, ALsizei, 
 c_void_p, c_void_p]
alureRewindStream = alure_lib.alureRewindStream
alureRewindStream.restype = ALboolean
alureRewindStream.argtypes = [alureStream_p]
alureDestroyStream = alure_lib.alureDestroyStream
alureDestroyStream.restype = ALboolean
alureDestroyStream.argtypes = [alureStream_p, ALsizei, POINTER(ALuint)]
alureGetStreamLength = alure_lib.alureGetStreamLength
alureGetStreamLength.restype = alureInt64
alureGetStreamLength.argtypes = [alureStream_p]
alureSetStreamOrder = alure_lib.alureSetStreamOrder
alureSetStreamOrder.restype = ALboolean
alureSetStreamOrder.argtypes = [alureStream_p, ALsizei]
alureCreateStreamFromFile = alure_lib.alureCreateStreamFromFile
alureCreateStreamFromFile.restype = alureStream_p
alureCreateStreamFromFile.argtypes = [POINTER(ALchar), ALsizei, ALsizei,
 POINTER(ALuint)]
alureCreateStreamFromStaticMemory = alure_lib.alureCreateStreamFromStaticMemory
alureCreateStreamFromStaticMemory.restype = alureStream_p
alureCreateStreamFromStaticMemory.argtypes = [POINTER(ALchar), ALuint, ALsizei,
 ALsizei, POINTER(ALuint)]
alureStreamSizeIsMicroSec = alure_lib.alureStreamSizeIsMicroSec
alureStreamSizeIsMicroSec.restype = ALboolean
alureStreamSizeIsMicroSec.argtypes = [ALboolean]
alureGetStreamFrequency = alure_lib.alureGetStreamFrequency
alureGetStreamFrequency.restype = ALsizei
alureGetStreamFrequency.argtypes = [alureStream_p]
alureSetStreamPatchset = alure_lib.alureSetStreamPatchset
alureSetStreamPatchset.restype = ALboolean
alureSetStreamPatchset.argtypes = [alureStream_p, POINTER(ALchar)]
AL_NO_ERROR = 0
AL_FALSE = 0
AL_TRUE = 1
AL_GAIN = 4106
AL_PITCH = 4099
AL_POSITION = 4100
AL_DIRECT_CHANNELS_SOFT = 4147
AL_INITIAL = 4113
AL_PLAYING = 4114
AL_PAUSED = 4115
AL_STOPPED = 4116
AL_SOURCE_STATE = 4112
AL_ROLLOFF_FACTOR = 4129
AL_SOURCE_RELATIVE = 514
AL_ORIENTATION = 4111
AL_VENDOR = 45057
AL_VERSION = 45058
AL_RENDERER = 45059
AL_BUFFER = 4105
AL_LOOPING = 4103
AL_SEC_OFFSET = 4132
AL_EFFECT_REVERB = 1
AL_EFFECT_TYPE = 32769
AL_EFFECTSLOT_AUXILIARY_SEND_AUTO = 3
AL_EFFECTSLOT_EFFECT = 1
AL_AUXILIARY_SEND_FILTER = 131078
AL_REVERB_DENSITY = 1
AL_REVERB_DIFFUSION = 2
AL_REVERB_GAIN = 3
AL_REVERB_GAINHF = 4
AL_REVERB_DECAY_TIME = 5
AL_REVERB_DECAY_HFRATIO = 6
AL_REVERB_REFLECTIONS_GAIN = 7
AL_REVERB_REFLECTIONS_DELAY = 8
AL_REVERB_LATE_REVERB_GAIN = 9
AL_REVERB_LATE_REVERB_DELAY = 10
AL_REVERB_AIR_ABSORPTION_GAINHF = 11
AL_REVERB_ROOM_ROLLOFF_FACTOR = 12
AL_REVERB_DECAY_HFLIMIT = 13
AL_FILTER_TYPE = 32769
AL_FILTER_LOWPASS = 1
AL_LOWPASS_GAIN = 1
AL_LOWPASS_GAINHF = 2
AOS_EFFECT_REVERB, AOS_EFFECTS_NOOF, AOS_EFFECT_NONE = xrange(3)
AOS_FILTER_LOWPASS, AOS_FILTERS_NOOF, AOS_FILTER_NONE = xrange(3)

def get_alure_error():
    return alureGetErrorString() + ': ' + str(alGetError())


def check_al_error():
    error = alGetError()
    if error != AL_NO_ERROR:
        error_str = 'OpenAL Error: ' + alureGetErrorString() + ': ' + str(error)
        print error_str
        raise AudioError(error_str)


class AudioDevice(object):
    opened = False

    def __init__(self):
        self.sounds = []
        atexit.register(self.close)

    def open(self):
        if self.opened:
            return
        else:
            self.opened = True
            if not alureInitDevice(None, None):
                raise AudioError('Failed to open OpenAL device: %s' % get_alure_error())
            self.direct_channels = alIsExtensionPresent('AL_SOFT_direct_channels')
            self.version = string_at(alGetString(AL_VERSION))
            print 'OpenAL version:', self.version
            alureStreamSizeIsMicroSec(AL_TRUE)
            alureUpdateInterval(0.05)
            if AL_EXT_EFX:
                self.allocate_filters()
                self.allocate_effects()
                self.initialise_effects()
            return

    def allocate_filters(self):
        self.filter = [
         None] * AOS_FILTERS_NOOF
        for f in range(AOS_FILTERS_NOOF):
            self.filter[f] = ALuint()
            alGenFilters(1, byref(self.filter[f]))

        return

    def allocate_effects(self):
        self.effect = [
         None] * AOS_EFFECTS_NOOF
        for e in range(AOS_EFFECTS_NOOF):
            self.effect[e] = ALuint()
            alGenEffects(1, byref(self.effect[e]))

        return

    def initialise_effects(self):
        alEffecti(self.effect[AOS_EFFECT_REVERB], AL_EFFECT_TYPE, AL_EFFECT_REVERB)
        alEffectf(self.effect[AOS_EFFECT_REVERB].value, AL_REVERB_GAIN, 1.0)
        alEffectf(self.effect[AOS_EFFECT_REVERB].value, AL_REVERB_DECAY_TIME, 2.5)
        alEffectf(self.effect[AOS_EFFECT_REVERB].value, AL_REVERB_GAINHF, 0.89)
        alFilteri(self.filter[AOS_FILTER_LOWPASS], AL_FILTER_TYPE, AL_FILTER_LOWPASS)
        alFilterf(self.filter[AOS_FILTER_LOWPASS], AL_LOWPASS_GAIN, 0.2)
        alFilterf(self.filter[AOS_FILTER_LOWPASS], AL_LOWPASS_GAINHF, 0.2)
        self.effect_slot = [
         ALuint(), ALuint()]
        alGenAuxiliaryEffectSlots(1, byref(self.effect_slot[0]))
        alGenAuxiliaryEffectSlots(1, byref(self.effect_slot[1]))
        alAuxiliaryEffectSloti(self.effect_slot[0], AL_EFFECTSLOT_EFFECT, self.effect[AOS_EFFECT_REVERB].value)
        alAuxiliaryEffectSloti(self.effect_slot[1], AL_EFFECTSLOT_EFFECT, self.effect[AOS_EFFECT_REVERB].value)

    def set_global_reverb(self, reverb_size=1.49, reverb_amount=0.32, gainHF=0.89):
        if not AL_EXT_EFX:
            return
        alEffectf(self.effect[AOS_EFFECT_REVERB].value, AL_REVERB_GAIN, reverb_amount)
        alEffectf(self.effect[AOS_EFFECT_REVERB].value, AL_REVERB_DECAY_TIME, reverb_size)
        alEffectf(self.effect[AOS_EFFECT_REVERB].value, AL_REVERB_GAINHF, gainHF)
        alAuxiliaryEffectSloti(self.effect_slot[0], AL_EFFECTSLOT_EFFECT, self.effect[AOS_EFFECT_REVERB].value)
        alAuxiliaryEffectSloti(self.effect_slot[1], AL_EFFECTSLOT_EFFECT, self.effect[AOS_EFFECT_REVERB].value)

    def __del__(self):
        self.close()

    def close(self):
        if not self.opened:
            return
        self.opened = False
        for sound in self.sounds[:]:
            sound.close()

        self.sounds = []
        for buffer in buffer_pool.itervalues():
            alDeleteBuffers(1, byref(ALuint(buffer[0])))

        alureUpdateInterval(0)
        alureShutdownDevice()


audio_device = AudioDevice()
open = audio_device.open
close = audio_device.close

def load_all_buffers(path):
    paths = glob.glob(os.path.join(path, '*.' + AUDIO_FORMAT_EXTENSION))
    counter = 0
    for path in paths:
        name = os.path.basename(path).split('.')[0]
        get_buffer(name, path)
        counter += 1
        if counter % 3 == 0:
            loadingscreen.update_progress()


buffer_pool = {}

def get_buffer(name, path=None):
    data_id = name
    if data_id not in buffer_pool:
        if not path:
            print "Attempted to load sound that wasn't pre-loaded : '%s'" % name
            return
        current_time = clock()
        error = alGetError()
        if not os.path.exists(path):
            print 'Missing audio file %s.%s' % (name, AUDIO_FORMAT_EXTENSION)
            return
        file = phys_open(path.replace('\\', '/'))
        data = file.read()
        new_buffer = [alureCreateBufferFromMemory(data, len(data)), current_time, name]
        file.close()
        check_al_error()
        while not new_buffer[0]:
            oldest_buffer = None
            oldest_buffer_key = 0
            for key, buf in buffer_pool.items():
                if not oldest_buffer or buf[1] < oldest_buffer[1]:
                    oldest_buffer = buf
                    oldest_buffer_key = key

            if oldest_buffer:
                alDeleteBuffers(1, byref(ALuint(oldest_buffer[0])))
                check_al_error()
                if error == AL_NO_ERROR:
                    print 'Deleting audio buffer for %s' % buffer_pool[key][2]
                    del buffer_pool[key]
                else:
                    print 'alureCreateBufferFromMemory failed to create buffer for %s. Possibly out of audio memory' % name
                    break
            else:
                print 'alureCreateBufferFromMemory failed to create buffer for %s. Possibly out of audio memory' % name
                break
            new_buffer[0] = alureCreateBufferFromMemory(data, len(data))
            check_al_error()

        buffer_pool[data_id] = new_buffer
    buffer_pool[data_id][1] = clock()
    return buffer_pool[data_id][0]


class AudioError(Exception):
    pass


CHUNK_LENGTH = 250000
NUM_BUFS = 3

class Sound(object):
    closed = True
    callback = None
    _paused = False
    _volume = 1.0
    _pitch = 1.0
    _x = _y = _z = 0.0

    def __init__(self, name, filename=None, streaming=False):
        if not audio_device.opened:
            raise AudioError('Audio device not initialized')
        self.source = ALuint()
        alGenSources(1, byref(self.source))
        if audio_device.direct_channels:
            alSourcei(self.source, AL_DIRECT_CHANNELS_SOFT, AL_TRUE)
        if name is not None:
            if streaming:
                if not filename:
                    print 'Filename required for streaming audio:', name
                self.buffer_id = -1
                self.stream = alureCreateStreamFromFile(filename, CHUNK_LENGTH, 0, None)
                if not self.stream:
                    print 'Could not load sound:', filename, get_alure_error()
            else:
                self.buffer_id = get_buffer(name)
                if self.buffer_id:
                    alSourcei(self.source, AL_BUFFER, self.buffer_id)
        else:
            raise AudioError('No input specified: %s' % get_alure_error())
        audio_device.sounds.append(self)
        self.closed = False
        return

    def get_volume(self):
        return self._volume

    def set_volume(self, value):
        self._volume = value
        alSourcef(self.source, AL_GAIN, value)

    volume = property(get_volume, set_volume)

    def get_pitch(self):
        return self._pitch

    def set_pitch(self, value):
        self._pitch = value
        alSourcef(self.source, AL_PITCH, value)

    pitch = property(get_pitch, set_pitch)

    def get_rate(self):
        return alureGetStreamFrequency(self.stream)

    rate = property(get_rate)

    def get_frequency(self):
        return self._pitch * self.get_rate()

    def set_frequency(self, value):
        self.set_pitch(float(value) / self.get_rate())

    frequency = property(get_frequency, set_frequency)

    def get_pan(self):
        return self._x * 100.0

    def set_pan(self, pan):
        pan = max(-1.0, min(1.0, pan / 100.0))
        x = pan
        y = -math.sqrt(1.0 - pan ** 2)
        z = 0.0
        self.set_position(x, y, z)

    pan = property(get_pan, set_pan)

    def get_position(self):
        return (
         self._x, self._y, self._z)

    def set_position(self, (x, y, z)):
        self._x = x
        self._y = y
        self._z = z
        alSource3f(self.source, AL_POSITION, x, y, z)

    position = property(get_position, set_position)

    def get_duration(self):
        return alureGetStreamLength(self.stream)

    duration = property(get_duration)

    def get_paused(self):
        return self._paused

    def set_paused(self, value):
        if value == self._paused:
            return
        self._paused = value
        if value:
            alurePauseSource(self.source)
        else:
            alureResumeSource(self.source)

    paused = property(get_paused, set_paused)

    def get_position(self):
        return self._position

    def set_position(self, value):
        self._position = value
        x, y, z = value
        alSource3f(self.source, AL_POSITION, x, y, z)

    position = property(get_position, set_position)

    def get_attenuation(self):
        return self._attenuation

    def set_attenuation(self, value):
        self._attenuation = value
        alSourcef(self.source, AL_ROLLOFF_FACTOR, value)

    attenuation = property(get_attenuation, set_attenuation)

    def get_relative(self):
        return self._relative

    def set_relative(self, value):
        self._relative = value
        alSourcei(self.source, AL_SOURCE_RELATIVE, value)

    relative = property(get_relative, set_relative)

    def get_time(self):
        return self._time

    def set_time(self, value):
        self._time = value
        alSourcef(self.source, AL_SEC_OFFSET, value)

    time = property(get_time, set_time)

    def play(self, loops=1, effect=AOS_EFFECT_NONE):
        loops -= 1
        if self.buffer_id == -1:
            if not alurePlaySourceStream(self.source, self.stream, NUM_BUFS, loops, None, None):
                print 'Could not play sound', get_alure_error()
                return
        else:
            if loops:
                alSourcei(self.source, AL_LOOPING, AL_TRUE)
            else:
                alSourcei(self.source, AL_LOOPING, AL_FALSE)
            prev_error = alGetError()
            if not alurePlaySource(self.source, None, None):
                print 'Could not play sound', get_alure_error()
                return
        if effect == AOS_EFFECT_REVERB and AL_EXT_EFX:
            alSource3i(self.source.value, AL_AUXILIARY_SEND_FILTER, audio_device.effect_slot[0].value, 0, 0)
        return

    def stop(self):
        try:
            alureStopSource(self.source, AL_FALSE)
            check_al_error()
        except:
            pass

    def is_playing(self):
        if self.closed:
            return False
        state = ALint()
        alGetSourcei(self.source, AL_SOURCE_STATE, byref(state))
        return state.value == AL_PLAYING

    def close(self):
        if self.closed:
            return
        else:
            self.closed = True
            audio_device.sounds.remove(self)
            if self.buffer_id == -1:
                try:
                    alureDestroyStream(self.stream, 0, None)
                    check_al_error()
                except:
                    pass

            else:
                try:
                    alureStopSource(self.source, AL_FALSE)
                    check_al_error()
                except:
                    pass

            try:
                alDeleteSources(1, byref(self.source))
                check_al_error()
            except:
                pass

            return

    def __del__(self):
        self.close()


ALFLOAT_6 = ALfloat * 6

class Listener(object):
    _volume = 1.0
    _position = (0, 0, 0)

    def get_volume(self):
        return self._volume

    def set_volume(self, value):
        self._volume = value
        alListenerf(AL_GAIN, value)

    volume = property(get_volume, set_volume)

    def get_position(self):
        return self._position

    def set_position(self, value):
        self._position = value
        x, y, z = value
        alListener3f(AL_POSITION, x, y, z)

    position = property(get_position, set_position)

    def get_orientation(self):
        return self._orientation

    def set_orientation(self, value):
        self._orientation = value
        ux, uy, uz, ax, ay, az = value
        alListenerfv(AL_ORIENTATION, ALFLOAT_6(ux, uy, uz, ax, ay, az))

    orientation = property(get_orientation, set_orientation)


listener = Listener()
if __name__ == '__main__':
    open()
    sound = Sound(filename='test.mod', name='test.mod')
    sound.play()
    import time
    time.sleep(10.0)
