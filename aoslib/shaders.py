from shared.constants import *
import os
from shader_source import *
SKYDOME_SHADER = None
MODEL_SHADER = None
MAP_SHADER = None
SEA_SHADER = None
NORMAL_MODEL_SHADER = None
MODEL_SHADER = None
NOISE_SHADER = None
PARTICLE_LUT_SHADER = None
MODEL_TEX_SHADER = None
PASSTHROUGH_SHADER = None
PASSTHROUGH_TEX_SHADER = None
FSQUAD_TEX_SHADER = None
detail_level = None
MAP_SHADER_AOTEX_LOC = None
SEA_SHADER_AOTEX_LOC = None
MODEL_SHADER_BLEND_COLOR_LOC = None
MODEL_TEX_SHADER_TEXTURE_LOC = None
FSQUAD_TEX_SHADER_TEXTURE_LOC = None
SKYDOME_SHADER_TEX_LOC = None
SKYDOME_SHADER_TIME_LOC = None
SKYDOME_SHADER_UVSPEED_LOC = None
PASSTHROUGH_TEX_SHADER_TEX_LOC = None
if USE_GLSL:
    VERTEX_EXTENSION = '.vert'
    FRAGMENT_EXTENSION = '.frag'
    SHADER_DIRECTORY = './shadersources/'
    from aoslib.glslshader import Shader
else:
    VERTEX_EXTENSION = '.vp'
    FRAGMENT_EXTENSION = '.fp'
    SHADER_DIRECTORY = './shadersources/'
    from aoslib.arbshader import Shader

def load_shader(name, attributes=(), **defaults):
    global detail_level
    if USE_GLSL:
        vert = globals()[name + '_vert']
        frag = globals()[name + '_frag']
        if detail_level is None:
            detail_level = 3
        if detail_level < 3:
            vert = vert.replace('#define DETAIL_LEVEL 3', '#define DETAIL_LEVEL %d' % detail_level)
            frag = frag.replace('#define DETAIL_LEVEL 3', '#define DETAIL_LEVEL %d' % detail_level)
        shader = Shader([vert], [frag], name)
    else:
        vert = globals()[name + '_vert_arb']
        frag = globals()[name + '_frag_arb']
        shader = Shader(vert, frag, name)
    shader.initialize()
    if USE_GLSL:
        for index, name in enumerate(attributes):
            gl_index = index + 1
            shader.bind_attrib(gl_index, name)

        shader.link()
        shader.bind()
    for k, v in defaults.iteritems():
        try:
            v = tuple(v)
        except TypeError:
            v = (
             v,)

        if isinstance(v[0], float):
            func = shader.uniformf
        elif isinstance(v[0], int):
            func = shader.uniformi
        func(k, *v)

    shader.unbind()
    return shader


def load_shaders(detail):
    global FSQUAD_TEX_SHADER
    global FSQUAD_TEX_SHADER_TEXTURE_LOC
    global MAP_SHADER
    global MAP_SHADER_AOTEX_LOC
    global MODEL_SHADER
    global MODEL_SHADER_BLEND_COLOR_LOC
    global MODEL_TEX_SHADER
    global MODEL_TEX_SHADER_TEXTURE_LOC
    global NORMAL_MODEL_SHADER
    global PARTICLE_LUT_SHADER
    global PASSTHROUGH_SHADER
    global PASSTHROUGH_TEX_SHADER
    global PASSTHROUGH_TEX_SHADER_TEX_LOC
    global SEA_SHADER
    global SEA_SHADER_AOTEX_LOC
    global SKYDOME_SHADER
    global SKYDOME_SHADER_TEX_LOC
    global SKYDOME_SHADER_TIME_LOC
    global SKYDOME_SHADER_UVSPEED_LOC
    global detail_level
    detail_level = detail
    FSQUAD_TEX_SHADER = load_shader('fsquad_tex')
    FSQUAD_TEX_SHADER_TEXTURE_LOC = FSQUAD_TEX_SHADER.get_uniform_location('texture')
    SKYDOME_SHADER = load_shader('skydome')
    SKYDOME_SHADER_TEX_LOC = SKYDOME_SHADER.get_uniform_location('the_texture')
    SKYDOME_SHADER_TIME_LOC = SKYDOME_SHADER.get_uniform_location('time')
    SKYDOME_SHADER_UVSPEED_LOC = SKYDOME_SHADER.get_uniform_location('uv_speed')
    PARTICLE_LUT_SHADER = load_shader('particle_lut')
    MAP_SHADER = load_shader('map', alpha=1.0)
    MAP_SHADER_AOTEX_LOC = MAP_SHADER.get_uniform_location('aotexture')
    SEA_SHADER = load_shader('sea')
    SEA_SHADER_AOTEX_LOC = SEA_SHADER.get_uniform_location('aotexture')
    NORMAL_MODEL_SHADER = load_shader('model', blend_color=(1.0, 1.0, 1.0, 1.0), attributes=[
     'face_normal'])
    MODEL_SHADER = NORMAL_MODEL_SHADER
    MODEL_SHADER_BLEND_COLOR_LOC = MODEL_SHADER.get_uniform_location('blend_color')
    MODEL_TEX_SHADER = load_shader('model_tex', blend_color=(1.0, 1.0, 1.0, 1.0), model_texture=0)
    MODEL_TEX_SHADER_TEXTURE_LOC = MODEL_TEX_SHADER.get_uniform_location('model_texture')
    PASSTHROUGH_SHADER = load_shader('passthrough')
    PASSTHROUGH_TEX_SHADER = load_shader('passthrough_tex')
    PASSTHROUGH_TEX_SHADER_TEX_LOC = PASSTHROUGH_TEX_SHADER.get_uniform_location('main_texture')


def unload_shader(shader):
    if shader is not None:
        shader.delete_shader()
    return


def unload_shaders():
    global FSQUAD_TEX_SHADER
    global MAP_SHADER
    global MODEL_SHADER
    global MODEL_TEX_SHADER
    global NORMAL_MODEL_SHADER
    global PARTICLE_LUT_SHADER
    global PASSTHROUGH_SHADER
    global PASSTHROUGH_TEX_SHADER
    global SEA_SHADER
    global SKYDOME_SHADER
    unload_shader(SKYDOME_SHADER)
    SKYDOME_SHADER = None
    unload_shader(PARTICLE_LUT_SHADER)
    PARTICLE_LUT_SHADER = None
    unload_shader(MAP_SHADER)
    MAP_SHADER = None
    unload_shader(SEA_SHADER)
    SEA_SHADER = None
    unload_shader(NORMAL_MODEL_SHADER)
    NORMAL_MODEL_SHADER = None
    MODEL_SHADER = None
    unload_shader(MODEL_TEX_SHADER)
    MODEL_TEX_SHADER = None
    unload_shader(PASSTHROUGH_SHADER)
    PASSTHROUGH_SHADER = None
    unload_shader(PASSTHROUGH_TEX_SHADER)
    PASSTHROUGH_TEX_SHADER = None
    unload_shader(FSQUAD_TEX_SHADER)
    FSQUAD_TEX_SHADER = None
    return


__all__ = [
 'MAP_SHADER', 'SEA_SHADER', 'MODEL_SHADER', 
 'PARTICLE_LUT_SHADER', 'MODEL_TEX_SHADER', 
 'PASSTHROUGH_SHADER', 'FSQUAD_TEX_SHADER', 
 'SKYDOME_SHADER', 'PASSTHROUGH_TEX_SHADER', 
 'MAP_SHADER_AOTEX_LOC', 
 'SEA_SHADER_AOTEX_LOC', 'MODEL_SHADER_BLEND_COLOR_LOC', 
 'MODEL_TEX_SHADER_TEXTURE_LOC', 
 'FSQUAD_TEX_SHADER_TEXTURE_LOC', 
 'SKYDOME_SHADER_TEX_LOC', 'SKYDOME_SHADER_TIME_LOC', 
 'SKYDOME_SHADER_UVSPEED_LOC', 
 'PASSTHROUGH_TEX_SHADER_TEX_LOC']
# okay decompiling out\aoslib.shaders.pyc
