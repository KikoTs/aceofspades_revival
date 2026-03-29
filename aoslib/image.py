import os, pyglet
from pyglet import gl
import math
from aoslib import loadingscreen
import StringIO
IMAGE_SKIN = None
OLD_IMAGE_SKIN = None
TEXTURE_QUALITY_PATHS = {0: 'png/low', 
   1: 'png/med', 
   2: 'png/high'}
TEXTURE_QUALITY = None

class Sprite(pyglet.sprite.Sprite):

    def copy(self):
        new_sprite = Sprite(self.image)
        new_sprite.x = self.x
        new_sprite.y = self.y
        new_sprite.rotation = self.rotation
        new_sprite.scale = self.scale
        new_sprite.opacity = self.opacity
        new_sprite.color = self.color
        return new_sprite


def get_skinned_path(skin, fullpath):
    if skin is not None:
        skinned_path = os.path.join('skins', skin, 'png\\ui', fullpath)
        if os.path.isfile(skinned_path):
            return skinned_path
    return


def get_image_path(name, extension='png', add_path=False):
    global TEXTURE_QUALITY
    if not getattr(name, '__iter__', False):
        name = [
         name]
    extra_path = ''
    if add_path:
        extra_path = TEXTURE_QUALITY_PATHS[TEXTURE_QUALITY]
    path = os.path.join(extra_path, *name)
    fullpath = '%s.%s' % (path, extension)
    parts = filter(None, fullpath.split(os.sep))
    dirpath = ('/').join(parts)
    return dirpath


def needs_reload(name, add_path=False):
    global IMAGE_SKIN
    global OLD_IMAGE_SKIN
    if OLD_IMAGE_SKIN != IMAGE_SKIN:
        file_name = name[:]
        normal_path = get_image_path(file_name, add_path=add_path)
        if os.path.isabs(normal_path):
            return False
        old_skin_valid = get_skinned_path(OLD_IMAGE_SKIN, normal_path)
        new_skin_valid = get_skinned_path(IMAGE_SKIN, normal_path)
        if OLD_IMAGE_SKIN and old_skin_valid:
            return True
        if OLD_IMAGE_SKIN and old_skin_valid is None and new_skin_valid:
            return True
        if OLD_IMAGE_SKIN is None and new_skin_valid:
            return True
    return False


def load_image_from_path(path, none_resource=False, silent=False):
    image = None
    if none_resource:
        if not os.path.isfile(path):
            if not silent:
                raise IOError('image with name %s not found' % path)
            else:
                return image
        image = pyglet.image.load(path)
    else:
        image = pyglet.resource.image(path)
    return image


def load_image(name, none_resource=False, add_path=False):
    loadingscreen.update_progress()
    full_name = get_image_path(name, add_path=add_path)
    image = load_image_from_path(full_name, none_resource)
    return image


def load_texture(name, filtered=True, center=False, scale=1.0, none_resource=False, add_path=False):
    tex = load_image(name, none_resource, add_path).get_texture()
    if not filtered:
        gl.glTexParameteri(tex.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(tex.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
    gl.glTexParameteri(tex.target, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(tex.target, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
    tex.width = int(tex.width * scale)
    tex.height = int(tex.height * scale)
    if center:
        tex.anchor_x = tex.width / 2
        tex.anchor_y = tex.height / 2
    tex.name = name
    return tex


def load_texture_from_memory(memory, filtered=True, center=False, scale=1.0):
    memory_stream = StringIO.StringIO(memory)
    image = pyglet.image.load('anyoldname.png', file=memory_stream)
    tex = image.get_texture()
    if not filtered:
        gl.glTexParameteri(tex.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(tex.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
    gl.glTexParameteri(tex.target, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(tex.target, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
    tex.width = int(tex.width * scale)
    tex.height = int(tex.height * scale)
    if center:
        tex.anchor_x = tex.width / 2
        tex.anchor_y = tex.height / 2
    return tex


def load(name, extension='png', transparent_color=None, tile=False, center=False, mag_filter=gl.GL_LINEAR, min_filter=gl.GL_LINEAR):
    path = get_image_path(name, extension=extension)
    image = load_image('png/ui/' + name, none_resource=True, add_path=False)
    if transparent_color is not None:
        r, g, b = transparent_color
        r_t = chr(r)
        g_t = chr(g)
        b_t = chr(b)
        new_data = ''
        data = image.get_data('BGR', -image.width * 3)
        for i in xrange(len(data) / 3):
            b = data[i * 3]
            g = data[i * 3 + 1]
            r = data[i * 3 + 2]
            new_data += r
            new_data += g
            new_data += b
            if r == r_t and g == g_t and b == b_t:
                new_data += '\x00'
            else:
                new_data += b'\xff'

        image = pyglet.image.ImageData(image.width, image.height, 'RGBA', new_data, -image.width * 4)
    if tile:
        texture = pyglet.image.TileableTexture.create_for_image(image)
    else:
        texture = image.get_texture()
    if center:
        texture.anchor_x = texture.width / 2
        texture.anchor_y = texture.height / 2
    else:
        texture.anchor_y = texture.height
    gl.glBindTexture(texture.target, texture.id)
    gl.glTexParameteri(texture.target, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(texture.target, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(texture.target, gl.GL_TEXTURE_MAG_FILTER, mag_filter)
    gl.glTexParameteri(texture.target, gl.GL_TEXTURE_MIN_FILTER, min_filter)
    gl.glBindTexture(texture.target, 0)
    return Sprite(texture)


def set_texture_quality(texture_quality):
    global TEXTURE_QUALITY
    if TEXTURE_QUALITY != texture_quality:
        if TEXTURE_QUALITY is not None:
            pyglet.resource.path.remove(TEXTURE_QUALITY_PATHS[TEXTURE_QUALITY])
        TEXTURE_QUALITY = texture_quality
        pyglet.resource.path.append(TEXTURE_QUALITY_PATHS[TEXTURE_QUALITY])
    return


def set_texture_skin(skin):
    global IMAGE_SKIN
    global OLD_IMAGE_SKIN
    OLD_IMAGE_SKIN = IMAGE_SKIN
    if OLD_IMAGE_SKIN is not None:
        pyglet.resource.path.remove('skins/' + OLD_IMAGE_SKIN + '/png/ui')
    IMAGE_SKIN = skin
    if IMAGE_SKIN is not None:
        pyglet.resource.path.insert(0, 'skins/' + IMAGE_SKIN + '/png/ui')
    if OLD_IMAGE_SKIN is not None or IMAGE_SKIN is not None:
        pyglet.resource.reindex()
    return
