import pyglet
from pyglet.gl import glPushMatrix, glPopMatrix, glTranslatef, glEnable, GL_TEXTURE_2D, glColor4ub, glScalef, glColor4f
from aoslib.font import Font, Layout, ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT, ALIGN_TOP, ALIGN_BOTTOM, ALIGN_JUSTIFY
import os
FONTS_DIRECTORY = './fonts'
STANDARD_FONT = 'A750-Sans-Medium'
ALDO_FONT = 'Spades'
EDO_FONT = 'Edo'
TUFFY_FONT = 'Tuffy_Bold'
BIG_TEXT_COLOR = None
BIG_TEXT_FONT = None
BIG_TEXT_FONT_SIZE = None
HUD_FONT = None
HUD_FONT_SIZE = None
NAME_FONT = None
NAME_FONT_SIZE = None
CHAT_FONT = None
CHAT_FONT_TUFFY = None
CHAT_FONT_SIZE = None
INPUT_IP_FONT_SIZE = None
START_FONT = None
START_FONT_SIZE = None
MAP_GRID_FONT = None
MAP_GRID_SIZE = None
LIST_FONT_SIZE = None
DEFAULT_FONT_SIZE = None
SELECT_FONT = None
SELECT_FONT_SIZE = None
BUTTON_FONT = None
CATEGORY_FONT = None
CATEGORY_FONT_SIZE = None
KILL_FEED_FONT = None
KILL_FEED_FONT_TUFFY = None
KILL_FEED_FONT_SIZE = None
HELP_FONT = None
HELP_FONT_SIZE = None
EQUIPPED_TOOL_TIP_FONT = None
EQUIPPED_TOOL_TIP_FONT_SIZE = None
CREDITS_MENU_CREDITS_TEXT_FONT_NAME = None
CREDITS_MENU_CREDITS_TEXT_FONT_SIZE = None
big_name_font = None
text3d_font = None
over_player_font = None
over_player_font_tuffy = None
list_font = None
list_font_tuffy = None
key_input_font = None
welcome_font = None
title_font = None
network_font = None
brushed_font = None
map_info_font = None
navigation_font = None
option_font = None
settings_description_font = None
settings_value_font = None
settings_font = None
settings_changed_font = None
mode_name_font = None
edit_font = None
weapon_name_font = None
ammo_font = None
ammo_font_hud = None
reserve_font = None
team_list_font = None
prefab_name_font = None
prefab_description_font = None
class_name_font = None
change_class_name_font = None
class_description_font = None
class_loadout_title_font = None
class_prefab_cost_font = None
score_text_font = None
rankup_text_font = None
rankup_bar_font = None
score_types_heading_font = None
score_types_subheading_font = None
score_types_font = None
score_hud_font = None
map_name_font = None
map_tagline_font = None
class_loadout_description_font = None
hc_font = None
score_feed_title_font = None
score_feed_item_font = None
chat_font = None
chat_font_tuffy = None
small_aldo_ui_font = None
medium_aldo_ui_font = None
big_aldo_ui_font = None
medium_button_aldo_font = None
big_button_aldo_font = None
small_title_aldo_font = None
medium_title_aldo_font = None
big_title_aldo_font = None
kill_feed_font = None
kill_feed_font_tuffy = None
help_font = None
equipped_tool_tip_font = None
level_up_font = None
small_standard_ui_font = None
medium_standard_ui_font = None
big_edo_ui_font = None
big_standard_ui_font = None
medium_edo_ui_font = None
small_edo_ui_font = None
tiny_edo_ui_font = None
credits_text_font = None
generate_fonts = False

def generate_font_maps():
    print 'font_map_edo = {'
    for i in xrange(4, 120):
        font = Font(os.path.join(FONTS_DIRECTORY, 'Edo.ttf'), i, 'Edo')
        print i, " : { 'pixel_size' : ", font.get_char_height(), '},'

    print '}'
    print 'font_map_standard_med = {'
    for i in xrange(4, 120):
        font = Font(os.path.join(FONTS_DIRECTORY, 'A750-Sans-Medium.ttf'), i, 'A750-Sans-Medium')
        print i, " : { 'pixel_size' : ", font.get_char_height(), '},'

    print '}'
    print 'font_map_standard_bold = {'
    for i in xrange(4, 120):
        font = Font(os.path.join(FONTS_DIRECTORY, 'A750-Sans-Bold.ttf'), i, 'A750-Sans-Bold')
        print i, " : { 'pixel_size' : ", font.get_char_height(), '},'

    print '}'
    print 'font_map_tuffy_bold = {'
    for i in xrange(4, 120):
        font = Font(os.path.join(FONTS_DIRECTORY, 'Tuffy_Bold.ttf'), i, 'Tuffy_Bold')
        print i, " : { 'pixel_size' : ", font.get_char_height(), '},'

    print '}'


def load_font(name, size, enable_resize = True):
    global generate_fonts
    if generate_fonts == True:
        generate_font_maps()
        generate_fonts = False
    if not name:
        name = STANDARD_FONT
    font = Font(os.path.join(FONTS_DIRECTORY, name + '.ttf'), size, name, enable_resize)
    return font


def set_fonts():
    global BIG_TEXT_COLOR
    global score_types_font
    global ammo_font
    global welcome_font
    global SELECT_FONT
    global prefab_description_font
    global equipped_tool_tip_font
    global settings_value_font
    global score_text_font
    global map_tagline_font
    global big_name_font
    global map_name_font
    global HUD_FONT_SIZE
    global rankup_text_font
    global class_prefab_cost_font
    global over_player_font_tuffy
    global big_edo_ui_font
    global START_FONT_SIZE
    global HELP_FONT_SIZE
    global CHAT_FONT
    global map_info_font
    global score_types_heading_font
    global kill_feed_font_tuffy
    global SELECT_FONT_SIZE
    global DEFAULT_FONT_SIZE
    global settings_changed_font
    global KILL_FEED_FONT
    global prefab_name_font
    global CHAT_FONT_TUFFY
    global ammo_font_hud
    global BIG_TEXT_FONT_SIZE
    global chat_font
    global input_ip
    global settings_font
    global HUD_FONT
    global small_aldo_ui_font
    global medium_edo_ui_font
    global key_input_font
    global small_title_aldo_font
    global NAME_FONT_SIZE
    global rankup_bar_font
    global score_feed_title_font
    global level_up_font
    global navigation_font
    global medium_button_aldo_font
    global CATEGORY_FONT_SIZE
    global MAP_GRID_FONT
    global small_standard_ui_font
    global help_font
    global CATEGORY_FONT
    global CHAT_FONT_SIZE
    global INPUT_IP_FONT_SIZE
    global option_font
    global class_loadout_description_font
    global medium_title_aldo_font
    global big_standard_ui_font
    global network_font
    global over_player_font
    global class_loadout_title_font
    global BUTTON_FONT
    global mode_name_font
    global score_hud_font
    global LIST_FONT_SIZE
    global START_FONT
    global class_description_font
    global change_class_name_font
    global kill_feed_font
    global credits_text_font
    global big_aldo_ui_font
    global list_font
    global small_edo_ui_font
    global medium_aldo_ui_font
    global text3d_font
    global team_list_font
    global brushed_font
    global BIG_TEXT_FONT
    global big_button_aldo_font
    global score_types_subheading_font
    global hc_font
    global title_font
    global score_feed_item_font
    global reserve_font
    global KILL_FEED_FONT_SIZE
    global HELP_FONT
    global medium_standard_ui_font
    global class_name_font
    global weapon_name_font
    global big_title_aldo_font
    global MAP_GRID_SIZE
    global NAME_FONT
    global settings_description_font
    global list_font_tuffy
    global KILL_FEED_FONT_TUFFY
    global edit_font
    global tiny_edo_ui_font
    global chat_font_tuffy
    BIG_TEXT_COLOR = (231, 74, 25, 255)
    BIG_TEXT_FONT = EDO_FONT
    BIG_TEXT_FONT_SIZE = 30
    HUD_FONT = ALDO_FONT
    HUD_FONT_SIZE = 40
    NAME_FONT = STANDARD_FONT
    NAME_FONT_SIZE = 12
    CHAT_FONT = STANDARD_FONT
    CHAT_FONT_TUFFY = TUFFY_FONT
    CHAT_FONT_SIZE = 12
    INPUT_IP_FONT_SIZE = 25
    START_FONT = STANDARD_FONT
    START_FONT_SIZE = 20
    MAP_GRID_FONT = STANDARD_FONT
    MAP_GRID_SIZE = 12
    LIST_FONT_SIZE = 14
    DEFAULT_FONT_SIZE = 17
    SELECT_FONT = STANDARD_FONT
    SELECT_FONT_SIZE = 26
    BUTTON_FONT = ALDO_FONT
    CATEGORY_FONT = EDO_FONT
    CATEGORY_FONT_SIZE = 12
    KILL_FEED_FONT = STANDARD_FONT
    KILL_FEED_FONT_TUFFY = TUFFY_FONT
    KILL_FEED_FONT_SIZE = 14
    HELP_FONT = ALDO_FONT
    HELP_FONT_SIZE = 20
    EQUIPPED_TOOL_TIP_FONT = STANDARD_FONT
    EQUIPPED_TOOL_TIP_FONT_SIZE = 20
    CREDITS_TEXT_FONT_NAME = STANDARD_FONT
    CREDITS_TEXT_FONT_SIZE = 16
    big_name_font = load_font(STANDARD_FONT, 20, False)
    text3d_font = load_font(EDO_FONT, 22, False)
    over_player_font = load_font(STANDARD_FONT, 14, False)
    over_player_font_tuffy = load_font(TUFFY_FONT, 14, False)
    list_font = load_font(STANDARD_FONT, 11)
    list_font_tuffy = load_font(TUFFY_FONT, 11)
    key_input_font = load_font(STANDARD_FONT, 10)
    welcome_font = load_font(STANDARD_FONT, 16)
    title_font = load_font(ALDO_FONT, 46)
    network_font = load_font(ALDO_FONT, 19)
    brushed_font = load_font(EDO_FONT, 14)
    map_info_font = load_font(EDO_FONT, 18)
    navigation_font = load_font(ALDO_FONT, 24)
    option_font = load_font(ALDO_FONT, 23)
    settings_description_font = load_font(EDO_FONT, 12)
    settings_value_font = load_font(EDO_FONT, 12)
    settings_font = load_font(EDO_FONT, 18)
    settings_changed_font = load_font(STANDARD_FONT, 10)
    mode_name_font = load_font(EDO_FONT, 30)
    edit_font = load_font(ALDO_FONT, 18)
    weapon_name_font = load_font(ALDO_FONT, 18)
    ammo_font = load_font(ALDO_FONT, 26)
    ammo_font_hud = load_font(ALDO_FONT, 26, False)
    reserve_font = load_font(ALDO_FONT, 18, False)
    team_list_font = load_font(ALDO_FONT, 32)
    prefab_name_font = load_font(EDO_FONT, 10)
    prefab_description_font = load_font(STANDARD_FONT, 9)
    class_name_font = load_font(EDO_FONT, 20)
    change_class_name_font = load_font(EDO_FONT, 14)
    class_description_font = load_font(EDO_FONT, 10)
    class_loadout_title_font = load_font(EDO_FONT, 28)
    class_prefab_cost_font = load_font(STANDARD_FONT, 18)
    score_text_font = load_font(ALDO_FONT, 14)
    rankup_text_font = load_font(ALDO_FONT, 14)
    rankup_bar_font = load_font(ALDO_FONT, 14)
    score_types_heading_font = load_font(ALDO_FONT, 20)
    score_types_subheading_font = load_font(ALDO_FONT, 20)
    score_types_font = load_font(ALDO_FONT, 15)
    score_hud_font = load_font(ALDO_FONT, 26, False)
    map_name_font = load_font(ALDO_FONT, 40)
    map_tagline_font = load_font(ALDO_FONT, 20)
    class_loadout_description_font = load_font(STANDARD_FONT, 11)
    hc_font = load_font(ALDO_FONT, 26)
    score_feed_title_font = load_font(ALDO_FONT, 20)
    score_feed_item_font = load_font(ALDO_FONT, 16)
    input_ip = load_font(CHAT_FONT, INPUT_IP_FONT_SIZE, False)
    chat_font = load_font(CHAT_FONT, CHAT_FONT_SIZE, False)
    chat_font_tuffy = load_font(CHAT_FONT_TUFFY, CHAT_FONT_SIZE, False)
    kill_feed_font = load_font(KILL_FEED_FONT, KILL_FEED_FONT_SIZE, False)
    kill_feed_font_tuffy = load_font(KILL_FEED_FONT_TUFFY, KILL_FEED_FONT_SIZE, False)
    help_font = load_font(HELP_FONT, HELP_FONT_SIZE, False)
    equipped_tool_tip_font = load_font(EQUIPPED_TOOL_TIP_FONT, EQUIPPED_TOOL_TIP_FONT_SIZE)
    level_up_font = load_font(ALDO_FONT, 72)
    small_aldo_ui_font = load_font(ALDO_FONT, 11)
    medium_aldo_ui_font = load_font(ALDO_FONT, 14)
    big_aldo_ui_font = load_font(ALDO_FONT, 18)
    medium_button_aldo_font = load_font(ALDO_FONT, 18)
    big_button_aldo_font = load_font(ALDO_FONT, 36)
    small_title_aldo_font = load_font(ALDO_FONT, 20)
    medium_title_aldo_font = load_font(ALDO_FONT, 38)
    big_title_aldo_font = load_font(ALDO_FONT, 48)
    tiny_edo_ui_font = load_font(EDO_FONT, 8)
    small_edo_ui_font = load_font(EDO_FONT, 11)
    medium_edo_ui_font = load_font(EDO_FONT, 16)
    big_edo_ui_font = load_font(EDO_FONT, 20)
    small_standard_ui_font = load_font(STANDARD_FONT, 11)
    medium_standard_ui_font = load_font(STANDARD_FONT, 16)
    big_standard_ui_font = load_font(STANDARD_FONT, 20)
    credits_text_font = load_font(CREDITS_TEXT_FONT_NAME, CREDITS_TEXT_FONT_SIZE)


def add_space_before_capitals(name):
    if name is None:
        return ''
    capitals = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    new_name = ''
    for index, char in enumerate(name):
        if index == 0:
            new_name += char
            continue
        if char in capitals and name[index - 1] not in capitals:
            new_name += ' '
        new_name += char

    return new_name


def modify_name_to_fix_width(original_name, width, font):
    name = original_name
    char_count = len(original_name)
    name_length = font.get_content_width(name)
    while name_length > width:
        char_count -= 1
        name = original_name[0:char_count]
        name_length = font.get_content_width(name + '...')

    if name != original_name:
        return name + '...'
    return name


def get_fitting_lines(text, width, height, font, line_spacing):
    if text is None or text == '' or font is None:
        return (None, None)
    text_to_draw = split_text_to_fit_screen(font, text, width, 10)
    lines = text_to_draw.split('\n')
    line_count = len(lines)
    line_height = line_spacing + font.size
    max_line_count = height / line_height
    if len(lines) > max_line_count:
        fitting_lines = lines[0:max_line_count]
    else:
        fitting_lines = lines[:]
    return (lines, fitting_lines)


def get_resized_font_and_formatted_text_to_fit_boundaries(text, width, height, font, line_spacing, allow_word_breaking = False, dont_split = False):
    if text is None or text == '' or font is None:
        return (font, text)
    font_to_use = font
    current_font_size = font_to_use.original_size
    if not dont_split:
        text_to_draw = split_text_to_fit_screen(font, text, width, 10, allow_word_breaking)
        lines = text_to_draw.split('\n')
    else:
        lines = [text]
    line_count = len(lines)
    lines_height = line_spacing * line_count + float(font_to_use.get_char_height()) * line_count
    while lines_height > height:
        if current_font_size > 1:
            current_font_size -= 1
        else:
            break
        font_to_use = load_font(font.name, current_font_size)
        if not dont_split:
            text_to_draw = split_text_to_fit_screen(font_to_use, text, width, 10, allow_word_breaking)
            lines = text_to_draw.split('\n')
        else:
            lines = [text]
        line_count = len(lines)
        lines_height = line_spacing * line_count + font_to_use.get_char_height() * line_count

    return (font_to_use, lines)


def draw_text_lines(lines, x, y, width, height, font_to_use, line_spacing, color, horizontal_alignment = 'left', vertical_alignment = 'top', force_line_scale = None, shadowed = False, stroked = False, shadow_offset = 2, stroke_size = 1):
    glPushMatrix()
    if len(lines) < 1:
        return
    scale = 1
    if force_line_scale:
        scale = force_line_scale
    else:
        for line in lines:
            line_scale = get_line_scale_from_text_and_width(line, width, font_to_use)
            if line_scale < scale:
                scale = line_scale

    single_line_height = (font_to_use.get_ascender() + font_to_use.get_descender()) * scale
    if vertical_alignment == 'center':
        number_of_lines = len(lines)
        y_size = float(single_line_height + line_spacing) * float(number_of_lines)
        y = y + float(height) / 2.0 - float(y_size) * 0.5 + (float(number_of_lines - 1) * single_line_height + line_spacing * number_of_lines)
    for line in lines:
        draw_text_with_alignment_and_size_validation(line, x, y, width, height, color, font_to_use, alignment_x=horizontal_alignment, alignment_y='bottom', shadowed=shadowed, stroked=stroked, shadow_offset=shadow_offset, stroke_size=stroke_size, forced_scale=scale)
        y -= single_line_height + line_spacing * 2.0

    glPopMatrix()


def draw_text_within_boundaries(text, x, y, width, height, font, line_spacing, color, alignment = 'left', scale_font_to_fit = True):
    if text is None or text == '' or font is None:
        return
    if scale_font_to_fit:
        font_to_use, fitting_lines = get_resized_font_and_formatted_text_to_fit_boundaries(text, width, height, font, line_spacing)
    else:
        font_to_use = font
        lines, fitting_lines = get_fitting_lines(text, width, height, font, line_spacing)
    draw_text_lines(fitting_lines, x, y, width, height, font_to_use, line_spacing, color, alignment)


def draw_text_shadowed(text, x, y, font, center_text, alignment_right, offset = 2.0, shadow_color = (0, 0, 0, 255)):
    glPushMatrix()
    glTranslatef(offset, -offset, 0.0)
    font.draw(text, x, y, shadow_color, center=center_text, right=alignment_right)
    glPopMatrix()


def draw_text_stroked(text, x, y, font, center_text, alignment_right, stroke_size = 1, stroke_color = (0, 0, 0, 255)):
    for offset in xrange(1, stroke_size + 1):
        glPushMatrix()
        glTranslatef(offset, -offset, 0.0)
        font.draw(text, x, y, stroke_color, center=center_text, right=alignment_right)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(offset, offset, 0.0)
        font.draw(text, x, y, stroke_color, center=center_text, right=alignment_right)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-offset, offset, 0.0)
        font.draw(text, x, y, stroke_color, center=center_text, right=alignment_right)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-offset, -offset, 0.0)
        font.draw(text, x, y, stroke_color, center=center_text, right=alignment_right)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-offset, 0.0, 0.0)
        font.draw(text, x, y, stroke_color, center=center_text, right=alignment_right)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(offset, 0.0, 0.0)
        font.draw(text, x, y, stroke_color, center=center_text, right=alignment_right)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.0, -offset, 0.0)
        font.draw(text, x, y, stroke_color, center=center_text, right=alignment_right)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.0, offset, 0.0)
        font.draw(text, x, y, stroke_color, center=center_text, right=alignment_right)
        glPopMatrix()


def draw_text_with_size_validation(text, x, y, width, height, color, font, center_text = True, shadowed = False, stroked = False, shadow_offset = 2, stroke_size = 1):
    if text is None or font is None or width is None:
        return
    content_width = float(font.get_content_width(text))
    width = float(width)
    scale = 1.0 if content_width < width else width / content_width
    if center_text:
        middle_x = x + width / 2.0
        middle_y = y + height / 3.0
    else:
        middle_x = x
        middle_y = y
    x = middle_x / scale
    y = middle_y / scale
    glPushMatrix()
    glScalef(scale, scale, 1.0)
    if shadowed:
        draw_text_shadowed(text, x, y, font, center_text, False, offset=shadow_offset)
    if stroked:
        draw_text_stroked(text, x, y, font, center_text, False, stroke_size=stroke_size)
    font.draw(text, x, y, color, center=center_text)
    glPopMatrix()


def get_line_scale_from_text_and_width(text, width, font):
    content_width = float(font.get_content_width(text))
    if content_width <= 0:
        return 1
    width = float(width)
    scale = 1.0 if content_width < width else width / content_width
    if scale > 0:
        return scale
    else:
        return 1


def draw_text_with_alignment_and_size_validation(text, x, y, width, height, color, font, alignment_x = 'center', alignment_y = 'bottom', shadowed = False, stroked = False, shadow_offset = 2, stroke_size = 1, forced_scale = None):
    if text is None or font is None or width is None:
        return
    if forced_scale == None:
        content_width = float(font.get_content_width(text))
        width = float(width)
        scale = 1.0 if content_width < width else width / content_width
    else:
        scale = forced_scale
    if scale == 0:
        return
    center_text = False
    alignment_right = False
    if alignment_x == 'center':
        center_text = True
        middle_x = x + width / 2.0
    elif alignment_x == 'right':
        alignment_right = True
        middle_x = x + width
    else:
        middle_x = x
    if alignment_y == 'center':
        middle_y = y + float(height) * 0.5 - float(font.get_ascender() + font.get_descender()) * 0.5
    elif alignment_y == 'top':
        middle_y = y + float(height) - float(font.get_ascender() + font.get_descender())
    else:
        middle_y = y
    x = middle_x / scale
    y = middle_y / scale
    glPushMatrix()
    glScalef(scale, scale, 1.0)
    if shadowed:
        draw_text_shadowed(text, x, y, font, center_text, alignment_right, offset=shadow_offset)
    if stroked:
        draw_text_stroked(text, x, y, font, center_text, alignment_right, stroke_size=stroke_size)
    font.draw(text, x, y, color, center=center_text, right=alignment_right)
    glPopMatrix()


def draw_big_text(label, x, y, window):
    if label is None or label.text is None or label.text == '':
        return
    from aoslib.images import global_images
    label.text = split_text_to_fit_screen(label.font, label.text, window.width, 60)
    lines = label.text.split('\n')
    line_count = len(lines)
    scale_y = float(line_count)
    content_width = 0
    for line in lines:
        if label.font.get_content_width(line) > content_width:
            content_width = label.font.get_content_width(line)
        if len(line) == 0:
            line_count -= 1

    frame_y = y - 19.5 * line_count + 10
    scale_x = float(content_width + 40) / float(global_images.big_text_frame.width)
    glColor4f(1.0, 1.0, 1.0, 1.0)
    glPushMatrix()
    glTranslatef(x, frame_y, 0.0)
    glScalef(scale_x, scale_y, 1.0)
    global_images.big_text_frame.blit(0.0, 0.0)
    glPopMatrix()
    from aoslib.draw import draw_offset
    draw_offset(label.draw_shadowed, x, y)


def split_text_to_fit_screen(font, text, window_width, frame_offset, allow_word_breaking = False):
    lines = text.split('\n')
    new_text = None
    for line in lines:
        if font.get_content_width(line) + frame_offset < window_width:
            new_text = __add_new_text_line__(new_text, line)
            continue
        sub_lines = line.split(' ')
        temp_text = None
        for sub_line in sub_lines:
            if temp_text is None:
                temp_text = sub_line
                continue
            if allow_word_breaking and font.get_content_width(sub_line) + frame_offset > window_width:
                temp_text += ' '
                characters = list(sub_line)
                for character in characters:
                    if font.get_content_width(temp_text + character) + frame_offset < window_width:
                        temp_text += character
                    else:
                        new_text = __add_new_text_line__(new_text, temp_text)
                        temp_text = character

                continue
            if font.get_content_width(temp_text + ' ' + sub_line) + frame_offset < window_width:
                temp_text += ' ' + sub_line
                continue
            new_text = __add_new_text_line__(new_text, temp_text)
            temp_text = sub_line

        if temp_text is not None:
            new_text = __add_new_text_line__(new_text, temp_text)
            temp_text = None

    return new_text


def translate_controls_in_message(scene, message):
    from aoslib.gui import translate_key
    controls_to_translate = ['forward',
     'backward',
     'left',
     'right',
     'jump',
     'crouch',
     'change_class',
     'view_scores',
     'palette_up',
     'palette_down',
     'palette_left',
     'palette_right',
     'weapon_custom',
     'cancel_prefab_placement',
     'carve_prefab',
     'tool_help',
     'hover',
     'sprint',
     'ugc_settings',
     'menu']
    for control in controls_to_translate:
        text_to_match = '{key_' + control + '}'
        if text_to_match in message:
            message = message.replace(text_to_match, '[' + translate_key(scene.config.__dict__[control]) + ']')

    return message


def __add_new_text_line__(text, aditional_text):
    if text is None:
        text = aditional_text
    else:
        text += '\n' + aditional_text
    return text


class Label(object):
    scale = 1.0

    def __init__(self, text = '', font_name = None, font_size = None, font = None, bold = False, italic = False, color = (255, 255, 255, 255), x = 0, y = 0, width = None, height = None, anchor_x = 'left', anchor_y = 'baseline', align = 'left', enable_resize = True):
        if font:
            self.font = font
        else:
            self.font = load_font(font_name, font_size or 14, enable_resize)
        self.font_name = font_name
        self.width = width
        self.height = height
        if width is None:
            width = float('inf')
        if height is None:
            height = -1
        self.layout = Layout(self.font, width, height, enable_resize)
        self.font = self.layout.pFont
        self.x = x
        self.y = y
        self.color = color
        self.set_horizontal_align(align)
        self.anchor_y = anchor_y
        self.anchor_x = anchor_x
        self.text = text

    def set_font_size(self, size):
        del self.font
        self.font = load_font(self.font_name, size)
        self.delete()
        self.layout = Layout(self.font, self.width, self.height)

    def set_vertical_align(self, value):
        if value == 'center':
            value = ALIGN_CENTER
        elif value == 'top':
            value = ALIGN_TOP
        else:
            value = ALIGN_BOTTOM
        self.layout.set_vertical_align(value)

    def set_horizontal_align(self, value):
        if value == 'center':
            value = ALIGN_CENTER
        elif value == 'right':
            value = ALIGN_RIGHT
        else:
            value = ALIGN_LEFT
        self.layout.set_horizontal_align(value)

    def _set_alpha(self, value):
        self.color = self.color[:3] + (int(value),)

    def _get_alpha(self):
        return self.color[3]

    alpha = property(_get_alpha, _set_alpha)

    def _set_scale(self, value):
        self.layout.set_scale(value)

    def _get_scale(self):
        return self.layout.scale

    scale = property(_get_scale, _set_scale)

    def _get_content_width(self):
        if '\n' in self._text:
            longest_width = 0
            for line in self._text.split('\n'):
                width = self.layout.pFont.get_content_width(line)
                if width > longest_width:
                    longest_width = width

            return longest_width
        else:
            return self.layout.pFont.get_content_width(self._text)

    content_width = property(_get_content_width)

    def _get_line_height(self):
        return self.layout.pFont.get_line_height()

    content_height = property(_get_line_height)

    def _set_content_valign(self, value):
        self.set_vertical_align(value)

    content_valign = property(fset=_set_content_valign)

    def _get_text(self):
        return self._text

    def _set_text(self, value):
        self._text = value
        if self.width and self.content_width >= self.width:
            self.scale = self.width / (float(self.content_width) + 1.0)
        else:
            self.scale = 1.0

    text = property(_get_text, _set_text)

    def draw_shadowed(self, draw_text = True, shadow_color = None, offset = 2.0):
        color = self.color
        if shadow_color is None:
            shadow_color = (64, 64, 64) + (self.color[-1],)
        glPushMatrix()
        glTranslatef(offset, -offset, 0.0)
        self.color = shadow_color
        self.draw()
        glPopMatrix()
        self.color = color
        if draw_text:
            self.draw()

    def draw_stroked(self, draw_text = True, stroke_size = 1, stroke_color = None):
        color = self.color
        if stroke_color is None:
            stroke_color = (64, 64, 64) + (self.color[-1],)
        self.color = stroke_color
        for x in xrange(1, stroke_size + 1):
            glPushMatrix()
            glTranslatef(x, -x, 0.0)
            self.draw()
            glPopMatrix()
            glPushMatrix()
            glTranslatef(x, x, 0.0)
            self.draw()
            glPopMatrix()
            glPushMatrix()
            glTranslatef(-x, x, 0.0)
            self.draw()
            glPopMatrix()
            glPushMatrix()
            glTranslatef(-x, -x, 0.0)
            self.draw()
            glPopMatrix()
            glPushMatrix()
            glTranslatef(-x, 0.0, 0.0)
            self.draw()
            glPopMatrix()
            glPushMatrix()
            glTranslatef(x, 0.0, 0.0)
            self.draw()
            glPopMatrix()
            glPushMatrix()
            glTranslatef(0.0, -x, 0.0)
            self.draw()
            glPopMatrix()
            glPushMatrix()
            glTranslatef(0.0, x, 0.0)
            self.draw()
            glPopMatrix()

        self.color = color
        if draw_text:
            self.draw()

    def draw(self):
        if self._text is None:
            return
        glColor4ub(*self.color)
        x, y = self.x, self.y
        height = self.content_height
        font = self.layout.pFont
        if self.anchor_y == 'bottom':
            y -= font.get_descender()
        elif self.anchor_y == 'center':
            y -= height * 0.5
        elif self.anchor_y == 'top':
            y -= font.get_ascender()
        self.layout.height = self.height or -1
        if '\n' in self._text:
            for line in self._text.split('\n'):
                x = self.x
                width = font.get_content_width(line)
                if self.anchor_x == 'center':
                    x -= width * 0.5
                elif self.anchor_x == 'right':
                    x -= width
                self.layout.draw(line, x, y)
                y -= height

        else:
            width = self.content_width
            if self.anchor_x == 'center':
                x -= width * 0.5
            elif self.anchor_x == 'right':
                x -= width
            self.layout.draw(self._text, x, y)

    def delete(self):
        self.layout.delete()
        self.layout = None


__all__ = ['HUD_FONT',
 'CHAT_FONT',
 'INPUT_IP',
 'Label',
 'HUD_FONT_SIZE',
 'CHAT_FONT_SIZE',
 'INPUT_IP_FONT_SIZE',
 'NAME_FONT',
 'NAME_FONT_SIZE',
 'MAP_GRID_FONT',
 'MAP_GRID_SIZE',
 'LIST_FONT_SIZE',
 'START_FONT',
 'START_FONT_SIZE',
 'DEFAULT_FONT_SIZE',
 'SELECT_FONT',
 'SELECT_FONT_SIZE',
 'load_font',
 'BUTTON_FONT',
 'CHAT_FONT_TUFFY']
