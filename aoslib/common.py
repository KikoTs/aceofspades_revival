import math, time, colorsys
from shared.glm import Vector3
from pyglet import gl

class globals:
    multiplier = 1.0


MAX_WAVE = 2 * math.pi

def wrap_angle(angle):
    return wrap(angle, -180, 180)


def get_map_value_safe(map, key, silent=False, default_value=None):
    value = default_value
    try:
        value = map[key]
    except KeyError:
        if type(key) == str:
            try:
                value = map[key.lower()]
            except KeyError:
                if not silent:
                    print 'map does not contain key ', str(key)

        elif not silent:
            print 'map does not contain key ', str(key)

    return value


def to_pitch_yaw(x, y, z):
    try:
        pitch = math.degrees(math.asin(z))
    except ValueError:
        pitch = 90.0

    try:
        yaw = math.degrees(math.atan2(x, y))
    except:
        yaw = 0.0

    return (
     pitch, yaw)


def multiply_float_color(color, mul):
    new_color = []
    for c in color:
        new_color.append(max(0.0, min(1.0, c * mul)))

    return tuple(new_color)


def multiply_color(color, mul):
    new_color = []
    for c in color:
        new_color.append(max(0, min(255, c * mul)))

    return tuple(new_color)


def to_rotation_vector(pitch, yaw):
    yaw = math.radians(yaw)
    pitch = math.radians(pitch)
    x = math.sin(yaw) * math.cos(pitch)
    y = math.cos(yaw) * math.cos(pitch)
    z = math.sin(pitch)
    return (x, y, z)


def wave(value, a=0.0, b=1.0, length=1.0):
    value /= length
    ret = (math.sin(value % MAX_WAVE) + 1.0) / 2.0 * (b - a) + a
    return ret


def switch_interval(a=2, speed=1.0):
    return int(time.time() * speed % a)


def vector_collides(a, b, distance):
    return math.fabs(a.x - b.x) < distance and math.fabs(a.y - b.y) < distance and math.fabs(a.z - b.z) < distance


def distance_3d(x1, y1, z1, x2, y2, z2):
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2) ** 0.5


def distance_squared_3d(x1, y1, z1, x2, y2, z2):
    return (x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2


def vector_angle_2d(x1, y1, x2, y2):
    return math.atan2(y1, x1) - math.atan2(y2, x2)


def collides(a_x1, a_y1, a_x2, a_y2, b_x1, b_y1, b_x2, b_y2):
    if a_x2 <= b_x1 or a_y2 <= b_y1 or a_x1 >= b_x2 or a_y1 >= b_y2:
        return 0
    return 1


def in_zone(a_x, a_y, b_x1, b_y1, b_x2, b_y2):
    if a_x >= b_x2 or a_x <= b_x1 or a_y >= b_y2 or a_y <= b_y1:
        return 0
    return 1


def interpolate(old, new, div):
    return old + (new - old) / float(div * globals.multiplier)


def interpolate_limit(old, new, div, range):
    return old + min(range, max(-range, new - old)) / float(div * globals.multiplier)


def extrapolate_position(old, new, mul):
    diff = new - old
    return old + diff * mul


def interpolate_position(cur, new, old, dt):
    diff = new - old
    ret = cur + diff * (dt / (1 / 30.0))
    if diff < 0:
        return max(ret, new)
    else:
        if diff > 0:
            return min(ret, new)
        return new


def wrap(value, a, b):
    diff = b - a
    return (value - a) % diff + a


def interpolate_angle(old, new, div):
    diff = new - old
    if diff > 180.0:
        diff = diff - 360
    elif diff < -180.0:
        diff = diff + 360
    return old + diff / float(div * globals.multiplier)


def interpolate_angle_limit(old, new, div, range):
    diff = new - old
    if diff > 180.0:
        diff = diff - 360
    elif diff < -180.0:
        diff = diff + 360
    return old + min(range, max(-range, diff)) / float(div * globals.multiplier)


def sane_interpolate(old, new, div, cutoff=5.0):
    diff = new - old
    if math.fabs(diff) >= cutoff:
        return new
    return old + diff / float(div * globals.multiplier)


def get_block_color(color):
    b = color & 255
    g = (color & 65280) >> 8
    r = (color & 16711680) >> 16
    return (r, g, b)


def make_block_color((r, g, b)):
    return r << 16 | g << 8 | b


def to_float_color(color):
    r, g, b = color
    return (r / 255.0, g / 255.0, b / 255.0)


def get_lighter_colour(base_colour, factor=25):
    return (base_colour[0] + factor, base_colour[1] + factor, base_colour[2] + factor, base_colour[3])


def get_darker_colour(base_colour, factor=25):
    return (base_colour[0] - factor, base_colourr[1] - factor, base_colour[2] - factor, base_colour[3])


def to_float_color_alpha(color):
    r, g, b, a = color
    return (r / 255.0, g / 255.0, b / 255.0, a / 255.0)


def to_ubyte_color(color):
    r, g, b = color
    return (int(r * 255), int(g * 255), int(b * 255))


def set_hue(color, value):
    h, l, s = colorsys.rgb_to_hls(*to_float_color(color))
    h = value / 255.0
    return to_ubyte_color(colorsys.hls_to_rgb(h, l, s))


def add_hue(color, value):
    h, l, s = colorsys.rgb_to_hls(*to_float_color(color))
    h += value / 255.0
    return to_ubyte_color(colorsys.hls_to_rgb(h, l, s))


def tint_colour(colour1, colour2):
    colour3 = [
     0, 0, 0, 0]
    colour3[0] = min(round(colour1[0] * colour2[0]), 255)
    colour3[1] = min(round(colour1[1] * colour2[1]), 255)
    colour3[2] = min(round(colour1[2] * colour2[2]), 255)
    colour3[3] = min(round(colour1[3] * colour2[3]), 255)
    return colour3


def draw_image_resized(image, x, y, width, height, alignment='default', clear_colours=False):
    scale_x = 1.0
    scale_y = 1.0
    if width != image.width and width != 0:
        scale_x = float(width) / float(image.width)
    if height != image.height and height != 0:
        scale_y = float(height) / float(image.height)
    draw_image_scaled(image, x, y, scale_x, scale_y, alignment, clear_colours)


def draw_image_scaled(image, x, y, scale_x, scale_y, alignment='default', clear_colours=False):
    old_anchor_x = image.anchor_x
    old_anchor_y = image.anchor_y
    if alignment == 'center':
        image.anchor_x = tex.width / 2
        image.anchor_y = tex.height / 2
    elif alignment != 'default':
        image.anchor_x = 0
        image.anchor_y = 0
    if clear_colours:
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
    gl.glPushMatrix()
    gl.glTranslated(x, y, 0)
    gl.glScaled(scale_x, scale_y, 1.0)
    image.blit(0, 0)
    gl.glPopMatrix()
    if alignment != 'default':
        image.anchor_x = old_anchor_x
        image.anchor_y = old_anchor_y
